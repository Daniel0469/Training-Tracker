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
import os, sys, json, base64, datetime, urllib.request

# Use the OS (Windows) trust store if available, so SSL works behind antivirus /
# proxy TLS inspection that injects a root CA the default verifier rejects.
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

def _ensure_ca_bundle():
    """The Garmin login (garth) also talks over `curl_cffi` (libcurl) and `requests`,
    which use their OWN trust stores — not the OS one truststore patches. Behind
    antivirus/proxy TLS inspection that yields 'unable to get local issuer certificate'.
    Fix: export the Windows Root+CA stores (incl. the AV/proxy root) to a PEM and point
    the standard CA-bundle env vars at it, so all three HTTP stacks trust it. Windows-only,
    idempotent, and respects any bundle you set yourself."""
    if os.name != "nt":
        return
    if os.environ.get("CURL_CA_BUNDLE") and os.environ.get("REQUESTS_CA_BUNDLE"):
        return
    try:
        import ssl, tempfile
        parts, seen = [], set()
        try:
            import certifi
            with open(certifi.where(), encoding="utf-8") as f:
                parts.append(f.read())
        except Exception:
            pass
        for store in ("ROOT", "CA"):
            try:
                for cert, enc, _trust in ssl.enum_certificates(store):
                    if enc == "x509_asn" and cert not in seen:
                        seen.add(cert)
                        parts.append(ssl.DER_cert_to_PEM_cert(cert))
            except Exception:
                pass
        if not parts:
            return
        bundle = os.path.join(tempfile.gettempdir(), "tt_garmin_cacert.pem")
        with open(bundle, "w", encoding="utf-8") as f:
            f.write("\n".join(parts))
        for var in ("CURL_CA_BUNDLE", "REQUESTS_CA_BUNDLE", "SSL_CERT_FILE"):
            os.environ.setdefault(var, bundle)
    except Exception:
        pass

_ensure_ca_bundle()

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
def _num(x):
    try:
        return float(str(x).strip())
    except (TypeError, ValueError):
        return None

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

# ---------------------------------------------------------------- enrichment (link Garmin -> a logged session)
def activity_metrics(a):
    """The extra info Garmin adds on top of a logged run: HR, cadence, elevation,
    calories, moving time, training effect, VO2max. Only keys the device recorded."""
    m = {}
    def put(key, val, rnd=None):
        if val is None:
            return
        m[key] = round(val, rnd) if rnd is not None else val
    put("avg_hr", _num(_field(a, "averageHR")), 0)
    put("max_hr", _num(_field(a, "maxHR")), 0)
    put("cadence_spm", _num(_field(a, "averageRunningCadenceInStepsPerMinute")), 0)
    put("elevation_gain_m", _num(_field(a, "elevationGain")), 0)
    put("calories", _num(_field(a, "calories") or _field(a, "activeKilocalories")), 0)
    mov = _num(_field(a, "movingDuration"))
    if mov:
        m["moving_time"] = _mmss(mov)
    put("training_effect", _num(_field(a, "aerobicTrainingEffect")), 1)
    put("vo2max", _num(_field(a, "vO2MaxValue")), 1)
    return {k: (int(v) if isinstance(v, float) and v.is_integer() else v) for k, v in m.items()}

def splits_to_rows_hr(splits, a=None):
    """Like splits_to_rows, but appends per-lap average HR as a 4th value when the
    watch recorded it (so the session gains an HR column). Falls back to one summary
    split from the activity if there are no laps."""
    laps = (splits or {}).get("lapDTOs") or []
    rows, any_hr = [], False
    for lap in laps:
        km = round((lap.get("distance") or 0) / 1000, 2)
        sec = int(lap.get("duration") or 0)
        if km <= 0 and sec <= 0:
            continue
        hr = _num(lap.get("averageHR"))
        if hr is not None:
            any_hr = True
        rows.append([km, _mmss(sec), _pace(km, sec), round(hr) if hr is not None else ""])
    if not any_hr:
        rows = [r[:3] for r in rows]
    if not rows and a is not None:
        dist_km = round((_field(a, "distance") or 0) / 1000, 2)
        dur = int(_field(a, "duration") or 0)
        if dist_km > 0:
            rows = [[dist_km, _mmss(dur), _pace(dist_km, dur)]]
    return rows

def _is_run_entry(e):
    cols = e.get("cols") or []
    return any("dist" in str(c).lower() for c in cols) and any("time" in str(c).lower() for c in cols)

def _entry_has_rows(e):
    return any(any(str(v).strip() for v in (row or [])) for row in (e.get("rows") or []))

def enrich_log(log, a, splits):
    """Attach Garmin's extra info to an already-logged session, without overwriting
    what the person entered. Fills splits only if the run entry was left empty."""
    log["garminActivityId"] = a.get("activityId")
    log["garminWanted"] = False
    metrics = activity_metrics(a)
    if metrics:
        log["garmin"] = metrics
    run_entry = next((e for e in log.get("entries", []) if _is_run_entry(e)), None)
    if run_entry is not None and not _entry_has_rows(run_entry):
        rows = splits_to_rows_hr(splits, a)
        if rows:
            has_hr = any(len(r) > 3 and r[3] != "" for r in rows)
            run_entry["cols"] = ["Distance (km)", "Time", "Pace"] + (["HR"] if has_hr else [])
            run_entry["rows"] = rows
    if not log.get("durationSec"):
        log["durationSec"] = int(_field(a, "duration") or 0)
    return log

def _start_dt(a):
    s = str(_field(a, "startTimeLocal") or "").replace("T", " ").strip()[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

def match_run(runs, date, used_ids):
    """Pick the Garmin run for a session logged on `date`. Uses the app's ~5am
    training-day window (see trainingDateStr in js/app.js: it subtracts 5h before
    dating a session): a session dated D covers runs that start in [D 05:00, D+1 05:00),
    so a run started after midnight still links to the prior day's session. Skips runs
    already linked; if several qualify, picks the longest (the day's main run)."""
    try:
        lo = datetime.datetime.strptime(date, "%Y-%m-%d") + datetime.timedelta(hours=5)
    except (ValueError, TypeError):
        return None
    hi = lo + datetime.timedelta(days=1)
    cands = []
    for a in runs:
        if a.get("activityId") in used_ids:
            continue
        sdt = _start_dt(a)
        if sdt is not None and lo <= sdt < hi:
            cands.append(a)
    if not cands:
        return None
    return max(cands, key=lambda a: _num(_field(a, "duration")) or 0)

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

def fill_pending(person, lookback=30):
    """Link Garmin runs to cardio sessions the app flagged `garminWanted`. Reads the
    store; only contacts Garmin if there's something to fill (so it's cheap to run
    often). Matches by person + date, enriches in place, writes back once."""
    data, sha, url, token = _github_read_with_sha()
    logs = data.get("logs", [])
    pending = [l for l in logs
               if l and l.get("person") == person and l.get("garminWanted") and not l.get("garminActivityId")]
    if not pending:
        return {"ok": True, "person": person, "filled": 0,
                "message": "No cardio sessions awaiting a Garmin run."}
    runs = [a for a in fetch_recent_activities(lookback) if is_run(a)]
    used = {l.get("garminActivityId") for l in logs if l and l.get("garminActivityId")}
    filled = []
    for l in pending:
        a = match_run(runs, l.get("date"), used)
        if not a:
            continue
        aid = a.get("activityId")
        try:
            splits = garmin_client().get_activity_splits(aid)
        except Exception:
            splits = {}
        enrich_log(l, a, splits)
        used.add(aid)
        filled.append({"session": l.get("sessionName"), "date": l.get("date"),
                       "activity_id": aid, "added": list((l.get("garmin") or {}).keys())})
    if filled:
        _github_write(data, sha, url, token,
                      f"Link {len(filled)} Garmin run(s) to {person}'s cardio session(s)")
    return {"ok": True, "person": person, "filled": len(filled), "details": filled,
            "unmatched": len(pending) - len(filled),
            "message": f"Linked {len(filled)} run(s). They show in the app after a sync."}

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

    @mcp.tool()
    def garmin_fill_pending(person: str) -> str:
        """Link Garmin runs to `person`'s cardio sessions that the app flagged as
        awaiting a run (adds HR, cadence, elevation, calories, training effect, and fills
        splits if empty). Matches by date, never overwrites entered data. This is what the
        scheduled `--sync` runs; call it to fill on demand."""
        return json.dumps(fill_pending(person), indent=2)

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

def _load_server_env(server_name):
    """Pull a server's env block out of the repo's .mcp.json so a scheduled `--sync`
    reuses the exact credentials already configured (no secrets in the Task Scheduler
    command). Existing environment values win, so you can still override per-run."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, ".mcp.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    env = (cfg.get("mcpServers", {}).get(server_name, {}) or {}).get("env", {})
    if not env:
        raise SystemExit(f"No env for server '{server_name}' in .mcp.json")
    for k, v in env.items():
        os.environ.setdefault(k, v)

def _sync(args):
    """`--sync [server-name]`: link Garmin runs to flagged cardio sessions. If a
    server name is given, its .mcp.json env (creds + TT_PERSON) is loaded first."""
    if args:
        _load_server_env(args[0])
        _ensure_ca_bundle()               # tokenstore/certs may have just been set
    person = os.environ.get("TT_PERSON")
    if not person:
        raise SystemExit("Set TT_PERSON (or pass a server name whose .mcp.json env has it), "
                         "e.g. `python server.py --sync training-garmin`.")
    print(json.dumps(fill_pending(person), indent=2))

def _selftest(path):
    with open(path, encoding="utf-8") as fh:
        fx = json.load(fh)
    a, splits = fx.get("activity", fx), fx.get("splits", {})
    print("summary:", json.dumps(summarize_activity(a), indent=2))
    print("\nGarmin extra metrics:", json.dumps(activity_metrics(a), indent=2))
    print("\nas a standalone import log:", json.dumps(activity_to_log(a, splits, "Daniel"), indent=2))
    # demo the enrichment path: a manually-logged cardio session gains Garmin's info
    logged = {"id": 999, "date": (_field(a, "startTimeLocal") or "")[:10], "person": "Daniel",
              "sessionName": "Cardio: Endurance + Core", "garminWanted": True,
              "entries": [{"name": "Run", "cols": ["Distance (km)", "Time", "Pace"], "rows": []},
                          {"name": "Plank", "cols": ["Weight (kg)", "Reps"], "rows": [["", "60"]]}]}
    print("\nlogged cardio session AFTER linking:",
          json.dumps(enrich_log(logged, a, splits), indent=2))

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--login":
        _login_interactive(); sys.exit(0)
    if len(sys.argv) >= 2 and sys.argv[1] == "--sync":
        _sync(sys.argv[2:]); sys.exit(0)
    if len(sys.argv) >= 3 and sys.argv[1] == "--selftest":
        _selftest(sys.argv[2]); sys.exit(0)
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("training-garmin")
    _register(mcp)
    mcp.run()
