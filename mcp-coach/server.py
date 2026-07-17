#!/usr/bin/env python3
"""Training Tracker — MCP coaching server.

Exposes Daniel & Cerys's training data to Claude (Desktop / Code / claude.ai)
so it can act as their coach: pull recent workouts, PRs, bodyweight trend, runs
and goals, and give feedback toward each person's goals.

Runs on your Claude subscription via MCP — no Anthropic API billing.

Data source (read-only), chosen by environment variables:
  * GitHub store (recommended — the same private repo the app syncs to):
      TT_GITHUB_REPO   e.g. danielmorris/training-data
      TT_GITHUB_TOKEN  a fine-grained token with Contents:read on that repo
      TT_GITHUB_PATH   optional, default data.json
  * or a local exported JSON file:
      TT_DATA_FILE     path to a training-data-*.json export

Setup + Claude config: see mcp-coach/README.md.

Self-test without an MCP client:
    python server.py --selftest ../sample-daniel.json
"""
import os, sys, json, base64, re, urllib.request

# Use the OS (Windows) trust store if available, so SSL works behind antivirus /
# proxy TLS inspection that injects a root CA the default verifier rejects.
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

# ---------------------------------------------------------------- data loading
def load_data():
    repo = os.environ.get("TT_GITHUB_REPO")
    token = os.environ.get("TT_GITHUB_TOKEN")
    path = os.environ.get("TT_GITHUB_PATH", "data.json")
    if repo and token:
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "tt-coach",
        })
        with urllib.request.urlopen(req, timeout=20) as r:
            j = json.load(r)
        return json.loads(base64.b64decode(j["content"]))
    f = os.environ.get("TT_DATA_FILE")
    if f:
        with open(f, encoding="utf-8") as fh:
            return json.load(fh)
    raise RuntimeError(
        "No data source. Set TT_GITHUB_REPO + TT_GITHUB_TOKEN (recommended) "
        "or TT_DATA_FILE. See mcp-coach/README.md."
    )

# ---------------------------------------------------------------- writing (coaching)
def _github_cfg():
    repo = os.environ.get("TT_GITHUB_REPO")
    token = os.environ.get("TT_GITHUB_TOKEN")
    path = os.environ.get("TT_GITHUB_PATH", "data.json")
    if not (repo and token):
        raise RuntimeError("Writing needs the GitHub store: set TT_GITHUB_REPO + TT_GITHUB_TOKEN "
                           "(token needs Contents: read AND write).")
    return repo, token, path

def _github_read_with_sha():
    repo, token, path = _github_cfg()
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "tt-coach"})
    with urllib.request.urlopen(req, timeout=20) as r:
        j = json.load(r)
    return json.loads(base64.b64decode(j["content"])), j["sha"], url, token

def _github_write(data, sha, url, token, message):
    body = {"message": message,
            "content": base64.b64encode(json.dumps(data, indent=2).encode("utf-8")).decode("ascii"),
            "sha": sha}
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="PUT", headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "tt-coach"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def _today():
    import datetime
    return datetime.date.today().isoformat()

def set_coaching(person, overall="", by_exercise=None, by_session=None):
    """Write coaching for a person into the shared data. `overall` is a general
    note; `by_session` maps session name -> a focus note for that session;
    `by_exercise` maps exercise name -> a short next-step cue. All are merged into
    any existing coaching. Shows in the app on Home + the log form after the person syncs."""
    data, sha, url, token = _github_read_with_sha()
    coaching = data.get("coaching") or {}
    entry = coaching.get(person) or {}
    if overall:
        entry["overall"] = overall
    if by_session:
        merged = dict(entry.get("bySession") or {})
        merged.update(by_session)
        entry["bySession"] = merged
    if by_exercise:
        merged = dict(entry.get("byExercise") or {})
        merged.update(by_exercise)
        entry["byExercise"] = merged
    entry["updated"] = _today()
    coaching[person] = entry
    data["coaching"] = coaching
    # Append this write to the coaching history so progress can be tracked over time.
    import time
    hist = data.get("coachingLog")
    if not isinstance(hist, list):
        hist = []
    rec = {"id": int(time.time() * 1000), "date": _today(), "person": person}
    if overall: rec["overall"] = overall
    if by_session: rec["bySession"] = dict(by_session)
    if by_exercise: rec["byExercise"] = dict(by_exercise)
    if len(rec) > 3:                      # something beyond id/date/person was written
        hist.append(rec)
        data["coachingLog"] = hist
    _github_write(data, sha, url, token, f"Coaching update for {person}")
    return {"ok": True, "person": person,
            "message": f"Saved. {person} will see it in the app after tapping Sync now."}

def get_coaching_history(data, person, limit=10):
    log = [e for e in (data.get("coachingLog") or []) if e.get("person") == person]
    log.sort(key=lambda e: e.get("id", 0), reverse=True)
    return log[:limit]

# ---------------------------------------------------------------- helpers
def _is_lifting(cols):
    cols = cols or []
    c0 = cols[0] if len(cols) > 0 else ""
    c1 = cols[1] if len(cols) > 1 else ""
    return bool(re.search(r"kg|assist", c0, re.I) and re.search(r"rep", c1, re.I))

def _person_logs(data, person):
    logs = [l for l in data.get("logs", []) if l.get("person") == person]
    logs.sort(key=lambda l: (l.get("date", ""), l.get("id", 0)), reverse=True)
    return logs

def _num(x):
    try:
        return float(str(x).strip())
    except (TypeError, ValueError):
        return None

# ---------------------------------------------------------------- logic (testable)
def list_people(data):
    out = []
    for i, name in enumerate(data.get("people", [])):
        bws = sorted([b for b in data.get("bodyweights", []) if b.get("person") == name],
                     key=lambda b: b.get("date", ""))
        goals = (data.get("goals") or ["", ""])
        out.append({
            "person": name,
            "goals": goals[i] if i < len(goals) else "",
            "latest_bodyweight_kg": bws[-1]["kg"] if bws else None,
            "sessions_logged": len(_person_logs(data, name)),
        })
    return out

def get_goals(data, person):
    people = data.get("people", [])
    goals = data.get("goals") or []
    if person in people:
        i = people.index(person)
        return {"person": person, "goals": goals[i] if i < len(goals) else ""}
    return {"error": f"Unknown person '{person}'"}

def list_sessions(data, person, limit=10):
    rows = []
    for l in _person_logs(data, person)[:limit]:
        rows.append({
            "id": l.get("id"),
            "date": l.get("date"),
            "session": l.get("sessionName"),
            "volume_kg": l.get("volume"),
            "difficulty": l.get("difficulty"),
            "duration_sec": l.get("durationSec"),
            "feedback": l.get("feedback") or "",
        })
    return rows

def get_session(data, session_id):
    for l in data.get("logs", []):
        if str(l.get("id")) == str(session_id):
            return l
    return {"error": f"No session with id {session_id}"}

def get_prs(data, person):
    best = {}
    for l in _person_logs(data, person):
        for e in l.get("entries", []):
            if not _is_lifting(e.get("cols")):
                continue
            warm = set(e.get("warmup") or [])
            top = None
            for ri, row in enumerate(e.get("rows", [])):
                if ri in warm:
                    continue
                w = _num(row[0]) if row else None
                if w is not None and (top is None or w > top):
                    top = w
            if top is not None:
                name = e.get("name")
                if name not in best or top > best[name]["kg"]:
                    best[name] = {"kg": top, "date": l.get("date")}
    return best

def get_bodyweight(data, person):
    bws = [b for b in data.get("bodyweights", []) if b.get("person") == person]
    bws.sort(key=lambda b: b.get("date", ""))
    return [{"date": b.get("date"), "kg": b.get("kg")} for b in bws]

def get_suggestions(data, include_done=False):
    subs = data.get("suggestions") or []
    return [s for s in subs if include_done or s.get("status") != "done"]

def resolve_suggestion(sid):
    data, sha, url, token = _github_read_with_sha()
    found = False
    for s in data.get("suggestions") or []:
        if str(s.get("id")) == str(sid):
            s["status"] = "done"; found = True
    if not found:
        return {"ok": False, "message": f"No suggestion with id {sid}"}
    _github_write(data, sha, url, token, f"Resolve suggestion {sid}")
    return {"ok": True, "id": sid}

def get_progress(data, person, exercise):
    pts = []
    for l in _person_logs(data, person):
        for e in l.get("entries", []):
            if e.get("name") != exercise:
                continue
            vals = [_num(r[0]) for r in e.get("rows", []) if r and _num(r[0]) is not None]
            if vals:
                pts.append({"date": l.get("date"), "top": max(vals)})
    pts.sort(key=lambda p: p["date"])
    return pts

# ---------------------------------------------------------------- MCP wiring
def _register(mcp):
    @mcp.tool()
    def people() -> str:
        """List both people with their goals, latest bodyweight and session count."""
        return json.dumps(list_people(load_data()), indent=2)

    @mcp.tool()
    def goals(person: str) -> str:
        """Get a person's stated training/health goals."""
        return json.dumps(get_goals(load_data(), person), indent=2)

    @mcp.tool()
    def recent_sessions(person: str, limit: int = 10) -> str:
        """List a person's most recent workout sessions (summary)."""
        return json.dumps(list_sessions(load_data(), person, limit), indent=2)

    @mcp.tool()
    def session(session_id: str) -> str:
        """Get one session in full (every exercise, set, plan and note)."""
        return json.dumps(get_session(load_data(), session_id), indent=2)

    @mcp.tool()
    def prs(person: str) -> str:
        """Current best weight per lifting exercise for a person."""
        return json.dumps(get_prs(load_data(), person), indent=2)

    @mcp.tool()
    def bodyweight(person: str) -> str:
        """A person's bodyweight history (date, kg)."""
        return json.dumps(get_bodyweight(load_data(), person), indent=2)

    @mcp.tool()
    def progress(person: str, exercise: str) -> str:
        """Top-set weight over time for one exercise, for tracking progression."""
        return json.dumps(get_progress(load_data(), person, exercise), indent=2)

    @mcp.tool()
    def suggestions(include_done: bool = False) -> str:
        """In-app improvement suggestions / bug reports Daniel & Cerys logged. Each has id,
        person, date, text, status. Use for the app's dev backlog."""
        return json.dumps(get_suggestions(load_data(), include_done), indent=2)

    @mcp.tool()
    def resolve_suggestion_tool(suggestion_id: str) -> str:
        """Mark a suggestion done (by id) once handled, so it drops off the app's pending list."""
        return json.dumps(resolve_suggestion(suggestion_id), indent=2)

    @mcp.tool()
    def coaching_history(person: str, limit: int = 10) -> str:
        """Past coaching you've written for a person (newest first) — each entry has a date
        plus the overall / per-session (bySession) / per-exercise (byExercise) notes from that
        write. Read this before coaching to see what you last advised, then judge whether it
        was followed and whether the numbers actually improved since."""
        return json.dumps(get_coaching_history(load_data(), person, limit), indent=2)

    @mcp.tool()
    def write_coaching(person: str, overall: str = "", by_exercise: dict | None = None,
                       by_session: dict | None = None) -> str:
        """Push coaching to a person so it shows in their app (Home + Log) during workouts.
        `by_session` = {exact session name: focus note} shown on that session (Home shows
        today's; Log shows the open session's). Prefer this for session-level guidance.
        `by_exercise` = {exact exercise name: a concrete next step} shown on that exercise
        (e.g. "hit 5x5 @100 — add 2.5kg next time"). Give one per exercise you have advice on.
        `overall` = an optional general note shown on every session.
        All merge into existing coaching. They see it after tapping Sync now."""
        return json.dumps(set_coaching(person, overall, by_exercise or {}, by_session or {}), indent=2)

def _selftest(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    print("people:", json.dumps(list_people(data), indent=2))
    if data.get("people"):
        p = data["people"][0]
        print(f"\nrecent_sessions({p}):", json.dumps(list_sessions(data, p, 3), indent=2))
        print(f"\nprs({p}):", json.dumps(get_prs(data, p), indent=2))
        print(f"\nbodyweight({p}):", json.dumps(get_bodyweight(data, p), indent=2))

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--selftest":
        _selftest(sys.argv[2])
        sys.exit(0)
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("training-tracker")
    _register(mcp)
    mcp.run()
