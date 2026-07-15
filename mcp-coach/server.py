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
            top = None
            for row in e.get("rows", []):
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
