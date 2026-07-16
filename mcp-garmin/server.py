#!/usr/bin/env python3
"""Training Tracker — Garmin MCP server.

Lets Claude read Daniel's & Cerys's runs straight from **Garmin Connect** (via the
unofficial `garminconnect` login) and, optionally, **import a run** into the shared
Training Tracker data so it shows up in the app's History like any logged session.

Runs on your Claude subscription via MCP — no Anthropic API billing. Garmin has no
official personal-data API for this, so we use the community `garminconnect` library
(same mechanism Garmin's own site uses). Credentials stay on this laptop.

Auth (do the one-time login first, then the server resumes a cached session):
  * GARMIN_EMAIL / GARMIN_PASSWORD  — your Garmin Connect login
  * GARMIN_TOKENSTORE               — optional, where the session is cached
                                      (default ~/.garminconnect)
  MFA-protected accounts: run `python server.py --login` once, interactively, to
  answer the MFA prompt and write the token cache. After that the MCP server signs
  in from the cache with no prompt (tokens last ~a year).

Importing a run also needs the GitHub store the app syncs to (write access):
  * TT_GITHUB_REPO   e.g. Daniel0469/Training-Data
  * TT_GITHUB_TOKEN  a fine-grained token with Contents: read AND write on that repo
  * TT_GITHUB_PATH   optional, default data.json

Setup + Claude config: see mcp-garmin/README.md.

Self-test the pure mapping (no Garmin/network needed):
    python server.py --selftest sample-activity.json
"""
import os, sys, json, base64, urllib.request

# Use the OS (Windows) trust store if available, so SSL works behind antivirus /
# proxy TLS inspection that injects a root CA the default verifier rejects.
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

# ---------------------------------------------------------------- formatting (matches the app)
def _mmss(sec):
    """Seconds -> "m:ss" (same shape as fmtMmSs / fmtPace in js/app.js)."""
    sec = round(sec or 0)
    m, s = divmod(sec, 60)
    return f"{m}:{s:02d}"

def _pace(km, sec):
    """Minutes-per-km as "m:ss", matching the app's fmtPace. Empty if unknown."""
    if not km or not sec or km <= 0 or sec <= 0:
        return ""
    mpk = (sec / 60) / km
    m = int(mpk)
    s = round((mpk - m) * 60)
    if s == 60:
        m += 1; s = 0
    return f"{m}:{s:02d}"

# ---------------------------------------------------------------- Garmin field access
# The list endpoint returns flat fields; the single-activity endpoint nests some of
# them under summaryDTO. Read from either so both shapes work.
def _field(a, name):
    if a.get(name) is not None:
        return a[name]
    return (a.get("summaryDTO") or {}).get(name)

def activity_type(a):
    t = a.get("activityType") or a.get("activityTypeDTO") or {}
    return (t.get("typeKey") or "") if isinstance(t, dict) else ""

def is_run(a):
    return "run" in activity_type(a).lower()

# ---------------------------------------------------------------- pure logic (testable)
def summarize_activity(a):
    """One-line summary of a Garmin activity, distances in km."""
    dist = _field(a, "distance") or 0
    dur = _field(a, "duration") or 0
    dist_km = round(dist / 1000, 2)
    return {
        "activity_id": a.get("activityId"),
        "name": a.get("activityName") or "Activity",
        "type": activity_type(a),
        "date": (_field(a, "startTimeLocal") or "")[:10] or None,
        "start_local": _field(a, "startTimeLocal"),
        "distance_km": dist_km,
        "duration": _mmss(dur) if dur else None,
        "duration_sec": int(dur),
        "avg_pace_per_km": _pace(dist_km, dur),
        "avg_hr": _field(a, "averageHR"),
    }

def splits_to_rows(splits):
    """Garmin split laps -> the app's running rows: [km, "m:ss" time, "m:ss" pace]."""
    laps = (splits or {}).get("lapDTOs") or []
    rows = []
    for lap in laps:
        km = round((lap.get("distance") or 0) / 1000, 2)
        sec = int(lap.get("duration") or 0)
        if km <= 0 and sec <= 0:
            continue
        rows.append([km, _mmss(sec), _pace(km, sec)])
    return rows

def activity_to_log(a, splits, person):
    """Map a Garmin run (+ its splits) to a Training Tracker log entry, matching the
    shape saveSession() writes in js/app.js. Uses the Garmin activityId as the log id
    so re-importing the same run merges (updates) instead of duplicating."""
    dist = _field(a, "distance") or 0
    dur = int(_field(a, "duration") or 0)
    dist_km = round(dist / 1000, 2)
    rows = splits_to_rows(splits)
    if not rows and dist_km > 0:          # no per-lap data -> one summary split
        rows = [[dist_km, _mmss(dur), _pace(dist_km, dur)]]
    entry = {"name": "Run", "cols": ["Distance (km)", "Time", "Pace"], "rows": rows}
    hr = _field(a, "averageHR")
    fb = "Imported from Garmin"
    if hr:
        fb += f" · avg HR {round(hr)}"
    return {
        "id": a.get("activityId"),
        "date": (_field(a, "startTimeLocal") or "")[:10],
        "person": person,
        "sessionKey": "garmin-run",
        "sessionName": a.get("activityName") or "Run",
        "entries": [entry],
        "feedback": fb,
        "difficulty": None,
        "suggestions": [],
        "volume": 0,
        "durationSec": dur,
        "source": "garmin",
        "garminActivityId": a.get("activityId"),
    }

# ---------------------------------------------------------------- Garmin client (network)
_client = None
def garmin_client():
    """Sign in to Garmin Connect, resuming a cached session if one exists."""
    global _client
    if _client is not None:
        return _client
    from garminconnect import Garmin
    tokenstore = os.path.expanduser(os.environ.get("GARMIN_TOKENSTORE", "~/.garminconnect"))
    try:
        g = Garmin()
        g.login(tokenstore)               # resume from cached tokens
    except Exception:
        email = os.environ.get("GARMIN_EMAIL")
        pw = os.environ.get("GARMIN_PASSWORD")
        if not (email and pw):
            raise RuntimeError(
                "No cached Garmin session and GARMIN_EMAIL/GARMIN_PASSWORD not set. "
                "Run `python server.py --login` once to sign in (handles MFA)."
            )
        g = Garmin(email, pw)
        g.login()
        try:
            g.garth.dump(tokenstore)
        except Exception:
            pass
    _client = g
    return g

def fetch_recent_activities(limit=10):
    return garmin_client().get_activities(0, limit) or []

def fetch_activity(activity_id):
    g = garmin_client()
    a = g.get_activity(activity_id)
    try:
        splits = g.get_activity_splits(activity_id)
    except Exception:
        splits = {}
    return a, splits

# ---------------------------------------------------------------- GitHub store (for import)
def _github_cfg():
    repo = os.environ.get("TT_GITHUB_REPO")
    token = os.environ.get("TT_GITHUB_TOKEN")
    path = os.environ.get("TT_GITHUB_PATH", "data.json")
    if not (repo and token):
        raise RuntimeError("Importing needs the GitHub store: set TT_GITHUB_REPO + TT_GITHUB_TOKEN "
                           "(token needs Contents: read AND write).")
    return repo, token, path

def _github_read_with_sha():
    repo, token, path = _github_cfg()
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "tt-garmin"})
    with urllib.request.urlopen(req, timeout=20) as r:
        j = json.load(r)
    return json.loads(base64.b64decode(j["content"])), j["sha"], url, token

def _github_write(data, sha, url, token, message):
    body = {"message": message,
            "content": base64.b64encode(json.dumps(data, indent=2).encode("utf-8")).decode("ascii"),
            "sha": sha}
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="PUT", headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "tt-garmin"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def import_run(activity_id, person):
    """Fetch a Garmin run and upsert it into the shared data as a Training Tracker
    session (merges by id, so re-importing is safe)."""
    a, splits = fetch_activity(activity_id)
    if not is_run(a):
        return {"ok": False, "message": f"Activity {activity_id} is a "
                f"'{activity_type(a) or 'non-run'}', not a run. Import skipped."}
    log = activity_to_log(a, splits, person)
    data, sha, url, token = _github_read_with_sha()
    logs = data.setdefault("logs", [])
    replaced = False
    for i, l in enumerate(logs):
        if l and str(l.get("id")) == str(log["id"]):
            logs[i] = log; replaced = True; break
    if not replaced:
        logs.append(log)
    _github_write(data, sha, url, token, f"Import Garmin run {activity_id} for {person}")
    return {"ok": True, "person": person, "session": log["sessionName"], "date": log["date"],
            "distance_km": log["entries"][0]["rows"] and sum(r[0] for r in log["entries"][0]["rows"]),
            "updated_existing": replaced,
            "message": f"{'Updated' if replaced else 'Imported'} run for {person}. "
                       f"They'll see it after tapping Sync now."}

# ---------------------------------------------------------------- MCP wiring
def _register(mcp):
    @mcp.tool()
    def garmin_recent_runs(limit: int = 10) -> str:
        """List your most recent Garmin **runs** (id, date, distance, time, pace, avg HR).
        Use the activity_id with garmin_activity or garmin_import_run."""
        acts = fetch_recent_activities(max(limit * 3, limit))   # over-fetch, then keep runs
        runs = [summarize_activity(a) for a in acts if is_run(a)][:limit]
        return json.dumps(runs, indent=2)

    @mcp.tool()
    def garmin_recent_activities(limit: int = 10) -> str:
        """List your most recent Garmin activities of any type (runs, rides, walks, …)."""
        acts = fetch_recent_activities(limit)
        return json.dumps([summarize_activity(a) for a in acts], indent=2)

    @mcp.tool()
    def garmin_activity(activity_id: str) -> str:
        """One Garmin activity in detail: summary plus per-split rows (km / time / pace)."""
        a, splits = fetch_activity(activity_id)
        out = summarize_activity(a)
        out["splits"] = splits_to_rows(splits)
        return json.dumps(out, indent=2)

    @mcp.tool()
    def garmin_import_run(activity_id: str, person: str) -> str:
        """Import a Garmin run into Training Tracker for `person` so it appears in the
        app's History. Merges by activity id (safe to run twice). Needs the GitHub store
        env vars with write access."""
        return json.dumps(import_run(activity_id, person), indent=2)

# ---------------------------------------------------------------- CLI (login / selftest)
def _login_interactive():
    from garminconnect import Garmin
    import getpass
    tokenstore = os.path.expanduser(os.environ.get("GARMIN_TOKENSTORE", "~/.garminconnect"))
    email = os.environ.get("GARMIN_EMAIL") or input("Garmin email: ")
    pw = os.environ.get("GARMIN_PASSWORD") or getpass.getpass("Garmin password: ")
    try:
        g = Garmin(email, pw, prompt_mfa=lambda: input("MFA code (blank if none): ").strip())
    except TypeError:                     # older garminconnect without prompt_mfa
        g = Garmin(email, pw)
    g.login()
    g.garth.dump(tokenstore)
    print("Signed in. Session cached at", tokenstore)
    print("Recent activity:", (fetch_recent_activities(1) or [{}])[0].get("activityName", "(none)"))

def _selftest(path):
    with open(path, encoding="utf-8") as fh:
        fx = json.load(fh)
    a, splits = fx.get("activity", fx), fx.get("splits", {})
    print("summary:", json.dumps(summarize_activity(a), indent=2))
    print("\nsplit rows:", json.dumps(splits_to_rows(splits), indent=2))
    print("\nas Training Tracker log:", json.dumps(activity_to_log(a, splits, "Daniel"), indent=2))

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--login":
        _login_interactive(); sys.exit(0)
    if len(sys.argv) >= 3 and sys.argv[1] == "--selftest":
        _selftest(sys.argv[2]); sys.exit(0)
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("training-garmin")
    _register(mcp)
    mcp.run()
