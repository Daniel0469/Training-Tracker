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
import os, sys, json, base64, datetime, time, urllib.request, urllib.error

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
        if km <= 0:            # skip 0-distance rest/auto laps — not real splits
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
        if km <= 0:            # skip 0-distance rest/auto laps — not real splits
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

def _run_cols(rows):
    """Column labels for a run entry - HR only when the watch actually recorded it."""
    has_hr = any(len(r) > 3 and r[3] != "" for r in rows)
    return ["Distance (km)", "Time", "Pace"] + (["HR"] if has_hr else [])

def _program_run_slot(program, session_key, log):
    """Where a missing run entry belongs in a logged session: the program's own name
    for the running exercise, plus the index to insert it at so it keeps its place in
    the exercise order rather than being tacked on the end. Falls back to appending
    under a generic name when the program has no running exercise to go by."""
    sess = ((program or {}).get("sessions") or {}).get(session_key) or {}
    exs = sess.get("exercises") or []
    run_i = next((i for i, e in enumerate(exs) if _is_run_entry(e)), None)
    if run_i is None:
        return "Run", None
    before = {e.get("name") for e in exs[:run_i] if e.get("name")}
    idx = 0
    for e in (log.get("entries") or []):
        if e.get("name") not in before:
            break
        idx += 1
    return exs[run_i].get("name") or "Run", idx

def fetch_detail_series(activity_id, max_points=2000):
    """Per-second (elapsed, speed m/s, HR) samples - the data behind Garmin Connect's
    own pace/HR charts. Returns [] if unavailable; every caller treats it as optional."""
    try:
        d = garmin_client().get_activity_details(activity_id, maxchart=max_points, maxpoly=0)
    except Exception:
        return []
    descs = d.get("metricDescriptors") or []
    idx = {m.get("key"): m.get("metricsIndex") for m in descs}
    ti, si, hi = idx.get("sumElapsedDuration"), idx.get("directSpeed"), idx.get("directHeartRate")
    if ti is None or si is None:
        return []
    out = []
    for m in d.get("activityDetailMetrics") or []:
        v = m.get("metrics") or []
        def at(i):
            return v[i] if i is not None and i < len(v) else None
        t, s, h = at(ti), at(si), at(hi)
        if t is None or s is None:
            continue
        out.append((float(t), float(s) * 3.6, h))
    return out

def detect_intervals(series, min_rep_sec=20, merge_gap_sec=15):
    """Recover the rep structure of an interval session from its speed trace.

    Garmin's LAPS cannot do this: a treadmill session auto-laps every 1km, and six
    1-minute reps at 13 km/h are ~217m each, so several reps and their recoveries
    land inside one lap. The per-second trace can - on a treadmill the belt holds a
    constant speed through a rep, so the trace is close to a square wave.

    Threshold at the midpoint of the session's own speed range, take contiguous
    runs above it, then MERGE blocks separated by less than `merge_gap_sec`. That
    merge is not cosmetic: verified against Cerys's 29 Jul session, where her last
    rep sagged below the threshold mid-way (she was ten minutes into Zone 4/5 and
    hanging on) and split into a 4s and a 30s fragment. Without merging she reads
    as 5 reps when she did 6.

    Reports the STRUCTURE only - rep count, how long each rep was, how long the
    recoveries were. Deliberately not the speed: treadmill pace is estimated from
    the wrist, and on the two sessions checked it read 10-15% above what was
    actually typed in (Daniel typed 13 km/h, the trace says ~14.5). What the person
    typed stays the truth for speed.
    """
    pts = [(t, kmh) for t, kmh, _h in series if kmh is not None]
    if len(pts) < 30:
        return None
    speeds = [p[1] for p in pts]
    lo, hi = min(speeds), max(speeds)
    if hi - lo < 3:                 # a steady run, not an interval session
        return None
    thr = lo + (hi - lo) * 0.5
    blocks = []
    cur = None
    for t, kmh in pts:
        if kmh >= thr:
            if cur is None:
                cur = [t, t]
            else:
                cur[1] = t
        elif cur is not None:
            blocks.append(cur)
            cur = None
    if cur:
        blocks.append(cur)
    merged = []
    for b in blocks:
        if merged and b[0] - merged[-1][1] <= merge_gap_sec:
            merged[-1][1] = b[1]
        else:
            merged.append(list(b))
    reps = [b for b in merged if b[1] - b[0] >= min_rep_sec]
    if len(reps) < 2:
        return None
    rep_secs = [int(round(b[1] - b[0])) for b in reps]
    # Reps are prescribed, so they come out roughly equal. A run/walk session
    # oscillates too, but raggedly - checked against Daniel's 4 Jul Zone 2
    # (28s to 356s, ratio 12.7) and Cerys's 1 Aug (29s to 155s, ratio 5.3),
    # against 1.15 and 1.26 for their two real interval sessions. Anything
    # above 2 is someone running and walking, not doing reps. enrich_log only
    # calls this for interval-shaped sessions anyway; this makes the function
    # safe to call on its own.
    if max(rep_secs) > 2 * max(1, min(rep_secs)):
        return None
    recoveries = [int(round(reps[i + 1][0] - reps[i][1])) for i in range(len(reps) - 1)]
    # Garmin downsamples the trace for shorter activities (Cerys's 18-minute
    # session came back as 161 samples, ~7s apart, against 1429 at 1s for
    # Daniel's 24 minutes), so rep edges are only as sharp as the sampling.
    span = pts[-1][0] - pts[0][0]
    res = round(span / max(1, len(pts) - 1), 1)
    return {
        "reps": len(reps),
        "rep_secs": rep_secs,
        "rep_sec_avg": int(round(sum(rep_secs) / len(rep_secs))),
        "recovery_secs": recoveries,
        "recovery_sec_avg": int(round(sum(recoveries) / len(recoveries))) if recoveries else None,
        "sample_sec": res,
        "source": "derived from the Garmin speed trace; structure only, "
                  "the typed speeds are the record for speed. Rep edges are "
                  "accurate to about the sample interval (sample_sec).",
    }

def enrich_log(log, a, splits, zone_secs=None, program=None):
    """Attach Garmin's extra info to an already-logged session, without overwriting
    what the person entered. Fills splits only if the run entry was left empty, and
    recreates that entry entirely when the session hasn't got one (see below).
    `zone_secs` (from fetch_hr_zone_times) adds time-in-HR-zone when available;
    `program` places a recreated run entry in the right spot in the exercise order."""
    log["garminActivityId"] = a.get("activityId")
    log["garminWanted"] = False
    metrics = activity_metrics(a)
    if zone_secs:
        metrics["hr_zone_secs"] = zone_secs
    if metrics:
        log["garmin"] = metrics
    run_entry = next((e for e in log.get("entries", []) if _is_run_entry(e)), None)
    if run_entry is None:
        # No run entry to fill: sessions saved before the app kept a blank one lost it
        # at save time, so the run only ever showed as the Garmin summary line. Put it
        # back where the program says it belongs, as if it had been logged by hand.
        # Only when the program HAS a running exercise for this session, though: an
        # interval session ("Hard pace"/"Easy pace" columns) links to Garmin too but
        # has no run entry to restore, and inventing one would add an exercise that
        # was never done - its paces are typed in by hand.
        name, idx = _program_run_slot(program, log.get("sessionKey"), log)
        if idx is not None:
            rows = splits_to_rows_hr(splits, a)
            if rows:
                log.setdefault("entries", []).insert(
                    idx, {"name": name, "cols": _run_cols(rows), "rows": rows})
    elif not _entry_has_rows(run_entry):
        rows = splits_to_rows_hr(splits, a)
        if rows:
            run_entry["cols"] = _run_cols(rows)
            run_entry["rows"] = rows
    if not log.get("durationSec"):
        log["durationSec"] = int(_field(a, "duration") or 0)
    # Interval sessions only - one without a run entry, i.e. reps typed as speeds.
    # A steady Zone 2 run has no structure worth recovering, and detect_intervals
    # returns None for one anyway.
    if run_entry is None and log.get("garmin"):
        iv = detect_intervals(fetch_detail_series(a.get("activityId")))
        if iv:
            log["garmin"]["intervals"] = iv
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
def _dump_session(g, tokenstore):
    """Persist the signed-in session to the token store. garminconnect exposes the
    underlying garth client as `.garth` in older versions and `.client` in newer
    ones — save via whichever provides dump(), so this survives library upgrades."""
    for attr in ("garth", "client"):
        obj = getattr(g, attr, None)
        if obj is not None and hasattr(obj, "dump"):
            obj.dump(tokenstore)
            return
    raise RuntimeError("Couldn't persist the Garmin session — this garminconnect "
                       "version exposes neither g.garth nor g.client with dump().")

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
            _dump_session(g, tokenstore)
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

def _github_update(mutate, message, attempts=3):
    """Read -> mutate -> write the shared store, retrying if another writer got in
    first. data.json has several writers (both phones' sync, the coach, this job);
    each sends the file's sha, so a race 409s instead of silently losing the other
    side's data - but without a retry that just surfaced as an error. `mutate` edits
    the data in place and returns a result; returning None aborts (no write).
    `message` is the commit message, or a callable taking the result. Keep Garmin
    fetches OUT of `mutate` - it can run more than once."""
    for attempt in range(attempts):
        data, sha, url, token = _github_read_with_sha()
        result = mutate(data)
        if result is None:
            return None
        try:
            _github_write(data, sha, url, token, message(result) if callable(message) else message)
        except urllib.error.HTTPError as e:
            # 409/412 = someone else wrote between our read and write: re-read and reapply.
            if e.code not in (409, 412):
                raise
            if attempt == attempts - 1:
                raise RuntimeError(
                    "Could not write to the shared store: another writer (a phone sync, or the "
                    f"coach) kept beating us to it, {attempts} times. Try again in a moment.")
            time.sleep(0.5 * (attempt + 1))
            continue
        return result

def import_run(activity_id, person):
    """Fetch a Garmin run and upsert it into the shared data as a Training Tracker
    session (merges by id, so re-importing is safe)."""
    a, splits = fetch_activity(activity_id)
    if not is_run(a):
        return {"ok": False, "message": f"Activity {activity_id} is a "
                f"'{activity_type(a) or 'non-run'}', not a run. Import skipped."}
    log = activity_to_log(a, splits, person)
    def mutate(data):
        logs = data.setdefault("logs", [])
        for i, l in enumerate(logs):
            if l and str(l.get("id")) == str(log["id"]):
                logs[i] = log
                return {"replaced": True}
        logs.append(log)
        return {"replaced": False}
    replaced = _github_update(mutate, f"Import Garmin run {activity_id} for {person}")["replaced"]
    return {"ok": True, "person": person, "session": log["sessionName"], "date": log["date"],
            "distance_km": log["entries"][0]["rows"] and sum(r[0] for r in log["entries"][0]["rows"]),
            "updated_existing": replaced,
            "message": f"{'Updated' if replaced else 'Imported'} run for {person}. "
                       f"They'll see it after tapping Sync now."}

def fill_pending(person, lookback=30):
    """Link Garmin runs to cardio sessions the app flagged `garminWanted`. Reads the
    store; only contacts Garmin if there's something to fill (so it's cheap to run
    often). Matches by person + date, enriches in place, writes back once."""
    data, _sha, _url, _token = _github_read_with_sha()
    logs = data.get("logs", [])
    pending = [l for l in logs
               if l and l.get("person") == person and l.get("garminWanted") and not l.get("garminActivityId")]
    if not pending:
        return {"ok": True, "person": person, "filled": 0,
                "message": "No cardio sessions awaiting a Garmin run."}
    # Match against Garmin first, outside the write: these calls are slow and must
    # not be repeated if the write has to retry. Keyed by log id so the matches can
    # be reapplied to a freshly read copy of the store.
    runs = [a for a in fetch_recent_activities(lookback) if is_run(a)]
    used = {l.get("garminActivityId") for l in logs if l and l.get("garminActivityId")}
    matches = {}
    for l in pending:
        a = match_run(runs, l.get("date"), used)
        if not a:
            continue
        aid = a.get("activityId")
        try:
            splits = garmin_client().get_activity_splits(aid)
        except Exception:
            splits = {}
        matches[str(l.get("id"))] = (a, splits, fetch_hr_zone_times(aid))
        used.add(aid)
    if not matches:
        return {"ok": True, "person": person, "filled": 0, "details": [], "unmatched": len(pending),
                "message": "No Garmin run matched the session(s) awaiting one."}

    def mutate(data):
        cur = data.get("logs", [])
        taken = {l.get("garminActivityId") for l in cur if l and l.get("garminActivityId")}
        done = []
        for l in cur:
            if not l or l.get("garminActivityId"):
                continue                       # another run of this job already linked it
            m = matches.get(str(l.get("id")))
            if not m:
                continue
            a, splits, zsecs = m
            aid = a.get("activityId")
            if aid in taken:
                continue
            enrich_log(l, a, splits, zsecs, data.get("program"))
            taken.add(aid)
            done.append({"session": l.get("sessionName"), "date": l.get("date"),
                         "activity_id": aid, "added": list((l.get("garmin") or {}).keys())})
        return done or None                    # None = nothing left to link, don't write
    filled = _github_update(
        mutate, lambda f: f"Link {len(f)} Garmin run(s) to {person}'s cardio session(s)") or []
    return {"ok": True, "person": person, "filled": len(filled), "details": filled,
            "unmatched": len(pending) - len(filled),
            "message": f"Linked {len(filled)} run(s). They show in the app after a sync."}

def fetch_hr_zone_times(activity_id):
    """Seconds spent in each of the five HR zones during one activity, as [Z1..Z5].
    Returns None when the watch logged no HR for it (no strap / wrist data), so
    callers can just leave the field off rather than storing a row of zeros."""
    try:
        rows = garmin_client().get_activity_hr_in_timezones(activity_id) or []
    except Exception:
        return None
    secs = {}
    for r in rows:
        n = r.get("zoneNumber")
        if n is None:
            continue
        secs[int(n)] = int(round(_num(r.get("secsInZone")) or 0))
    if not any(secs.values()):
        return None
    return [secs.get(i, 0) for i in range(1, 6)]

def fetch_hr_zones():
    """The person's configured heart-rate zones from Garmin: max / resting / lactate
    threshold HR plus the five zone floors. Reference data (not per-activity) - one
    DEFAULT entry unless sport-specific zones have been set up, in which case DEFAULT
    still wins as the general-purpose one."""
    rows = garmin_client().connectapi("/biometric-service/heartRateZones/") or []
    row = next((r for r in rows if str(r.get("sport") or "").upper() == "DEFAULT"), None)
    if row is None:
        row = rows[0] if rows else None
    if not row:
        return None
    floors = [row.get("zone%dFloor" % i) for i in range(1, 6)]
    if any(f is None for f in floors):
        return None
    def _int(v):
        n = _num(v)
        return int(n) if n is not None else None
    z = {"floors": [int(f) for f in floors],
         "maxHr": _int(row.get("maxHeartRateUsed")),
         "restingHr": _int(row.get("restingHeartRateUsed")),
         "thresholdHr": _int(row.get("lactateThresholdHeartRateUsed")),
         "method": row.get("trainingMethod"),
         "updated": datetime.datetime.now().isoformat(timespec="seconds")}
    return {k: v for k, v in z.items() if v is not None}

def fetch_race_predictions():
    """Garmin's own race-time predictions in seconds, from its VO2max model. Objective
    input for the coach's 5k estimate - it is NOT displayed raw as fact, because the
    model runs optimistic when there's little hard running to go on."""
    try:
        rp = garmin_client().get_race_predictions() or {}
    except Exception:
        return None
    out = {}
    for key, field in (("5k", "time5K"), ("10k", "time10K"),
                       ("half", "timeHalfMarathon"), ("marathon", "timeMarathon")):
        v = _num(rp.get(field))
        if v:
            out[key] = int(v)
    if not out:
        return None
    if rp.get("calendarDate"):
        out["calendarDate"] = rp["calendarDate"]
    out["updated"] = datetime.datetime.now().isoformat(timespec="seconds")
    return out

_RACE_KEYS = ("5k", "10k", "half", "marathon")

def sync_race_predictions(person):
    """Store Garmin's race predictions for the coach to reason from. No-ops when the
    numbers haven't moved, so re-running never writes a pointless commit."""
    rp = fetch_race_predictions()
    if not rp:
        return {"ok": False, "message": "Garmin returned no race predictions."}
    def mutate(data):
        preds = data.setdefault("racePredictions", {})
        cur = preds.get(person) or {}
        if all(cur.get(k) == rp.get(k) for k in _RACE_KEYS):
            return None
        preds[person] = rp
        return rp
    changed = _github_update(mutate, f"Update {person}'s Garmin race predictions")
    return {"ok": True, "person": person, "predictions": rp, "changed": bool(changed),
            "message": "Stored." if changed else "Already up to date - nothing written."}

# Fields that decide whether the stored zones are actually stale (`updated` always
# differs, so comparing the whole dict would rewrite the store on every run).
_HRZ_KEYS = ("floors", "maxHr", "restingHr", "thresholdHr", "method")

def sync_hr_zones(person):
    """Fetch `person`'s Garmin heart-rate zones and store them for the app to show on
    Home. No-ops (no write, no commit) when nothing has changed since last time."""
    z = fetch_hr_zones()
    if not z:
        return {"ok": False, "message": "Garmin returned no heart-rate zone configuration."}
    def mutate(data):
        zones = data.setdefault("hrZones", {})
        cur = zones.get(person) or {}
        if all(cur.get(k) == z.get(k) for k in _HRZ_KEYS):
            return None                       # unchanged - skip the write entirely
        zones[person] = z
        return z
    changed = _github_update(mutate, f"Update {person}'s Garmin heart-rate zones")
    return {"ok": True, "person": person, "zones": z, "changed": bool(changed),
            "message": ("Stored. They'll see it after tapping Sync now."
                        if changed else "Already up to date - nothing written.")}

def backfill_hr_zone_times(person, limit=50):
    """Add time-in-HR-zone to runs that were linked before that field existed. Garmin
    calls happen up front, outside the write, so a retry never re-fetches them."""
    data, _sha, _url, _token = _github_read_with_sha()
    todo = [l for l in data.get("logs", [])
            if l and l.get("person") == person and l.get("garminActivityId")
            and not (l.get("garmin") or {}).get("hr_zone_secs")][:limit]
    fetched = {}
    for l in todo:
        z = fetch_hr_zone_times(l.get("garminActivityId"))
        if z:
            fetched[str(l.get("id"))] = z
    if not fetched:
        return {"ok": True, "person": person, "filled": 0,
                "message": f"No runs needed zone times ({len(todo)} checked)."}
    def mutate(data):
        done = []
        for l in data.get("logs", []):
            z = fetched.get(str(l.get("id")))
            if not z:
                continue
            g = l.setdefault("garmin", {})
            if g.get("hr_zone_secs"):
                continue                       # another run of this job got there first
            g["hr_zone_secs"] = z
            done.append({"session": l.get("sessionName"), "date": l.get("date")})
        return done or None
    filled = _github_update(
        mutate, lambda f: f"Backfill HR zone times on {len(f)} of {person}'s runs") or []
    return {"ok": True, "person": person, "filled": len(filled), "details": filled,
            "message": f"Added zone times to {len(filled)} run(s)."}

def backfill_run_entries(person, limit=50):
    """Restore the run on linked cardio sessions that have no run entry at all. Those
    predate the app keeping a blank one on save, so the run showed only as the Garmin
    summary line rather than in the exercise list. Garmin calls happen up front, so a
    write retry never re-fetches them."""
    data, _sha, _url, _token = _github_read_with_sha()
    todo = [l for l in data.get("logs", [])
            if l and l.get("person") == person and l.get("garminActivityId")
            and not any(_is_run_entry(e) for e in (l.get("entries") or []))][:limit]
    fetched = {}
    for l in todo:
        try:
            a, splits = fetch_activity(l.get("garminActivityId"))
        except Exception:
            continue
        rows = splits_to_rows_hr(splits, a)
        if rows:
            fetched[str(l.get("id"))] = rows
    if not fetched:
        return {"ok": True, "person": person, "filled": 0,
                "message": f"No sessions needed their run restoring ({len(todo)} checked)."}
    def mutate(data):
        done = []
        for l in data.get("logs", []):
            rows = fetched.get(str(l.get("id")))
            if not rows or any(_is_run_entry(e) for e in (l.get("entries") or [])):
                continue                       # gone, or another run of this job did it
            name, idx = _program_run_slot(data.get("program"), l.get("sessionKey"), l)
            entries = l.setdefault("entries", [])
            entries.insert(len(entries) if idx is None else idx,
                           {"name": name, "cols": _run_cols(rows), "rows": rows})
            done.append({"session": l.get("sessionName"), "date": l.get("date"), "added_as": name})
        return done or None
    filled = _github_update(
        mutate, lambda f: f"Restore the run entry on {len(f)} of {person}'s cardio session(s)") or []
    return {"ok": True, "person": person, "filled": len(filled), "details": filled,
            "message": f"Restored the run on {len(filled)} session(s)."}

def enrich_session(session_id, activity_id, person):
    """Manually link one specific Garmin run to one specific already-logged session,
    by id - for a session that has no way to be picked up by fill_pending (e.g. it
    was saved before the app started setting garminWanted on a blank cardio save).
    Reuses enrich_log(), the same merge fill_pending uses - never overwrites what was
    typed, only fills gaps and adds the Garmin metrics."""
    a, splits = fetch_activity(activity_id)
    if not is_run(a):
        return {"ok": False, "message": f"Activity {activity_id} is a "
                f"'{activity_type(a) or 'non-run'}', not a run. Nothing linked."}
    zsecs = fetch_hr_zone_times(activity_id)
    outcome = {}
    def mutate(data):
        logs = data.get("logs", [])
        log = next((l for l in logs
                    if l and str(l.get("id")) == str(session_id) and l.get("person") == person), None)
        if log is None:
            outcome["status"] = "not_found"
            return None
        if log.get("garminActivityId"):
            outcome["status"] = "already_linked"
            outcome["session"] = log.get("sessionName")
            return None
        enrich_log(log, a, splits, zsecs, data.get("program"))
        outcome.update(status="linked", session=log.get("sessionName"), date=log.get("date"),
                        added=list((log.get("garmin") or {}).keys()))
        return outcome
    _github_update(mutate, f"Link Garmin run {activity_id} to session {session_id} for {person}")
    if outcome.get("status") == "not_found":
        return {"ok": False, "message": f"No session {session_id} found for {person}."}
    if outcome.get("status") == "already_linked":
        return {"ok": True, "already_linked": True, "session": outcome["session"],
                "message": "That session already has a linked Garmin run - nothing changed."}
    return {"ok": True, "person": person, "session": outcome["session"], "date": outcome["date"],
            "added": outcome["added"], "message": "Linked. They'll see it after tapping Sync now."}

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

    @mcp.tool()
    def garmin_hr_zones(person: str) -> str:
        """Refresh `person`'s configured Garmin heart-rate zones (max / resting / lactate
        threshold HR and the five zone floors) shown on the app's Home tab, and backfill
        time-in-zone onto any already-linked runs missing it. Safe to re-run: both halves
        no-op when nothing changed."""
        return json.dumps({"zones": sync_hr_zones(person),
                           "race_predictions": sync_race_predictions(person),
                           "run_zone_backfill": backfill_hr_zone_times(person),
                           "run_entry_backfill": backfill_run_entries(person)}, indent=2)

    @mcp.tool()
    def garmin_enrich_session(session_id: str, activity_id: str, person: str) -> str:
        """Manually link one specific Garmin run to one specific already-logged session
        by id (find the id with the training-tracker `session`/recent-sessions tools,
        and the activity_id with garmin_recent_runs). For a session fill_pending can't
        reach - e.g. it was saved before the app started flagging blank cardio saves as
        awaiting a run. Same never-overwrite merge as fill_pending; refuses if that
        session already has a linked run."""
        return json.dumps(enrich_session(session_id, activity_id, person), indent=2)

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
    try:
        g.login()
    except Exception as e:
        msg = str(e)
        print("\nGarmin sign-in failed:", msg)
        if "429" in msg or "rate limit" in msg.lower():
            print("  * Garmin has rate-limited this IP after repeated attempts. WAIT ~1 hour "
                  "(longer after several tries) before retrying — retrying now only extends the "
                  "block, and the delay can also expire your MFA code mid-login. A different "
                  "network (e.g. a phone hotspot) gives a fresh IP.")
        if "mfa" in msg.lower() or "authentication application" in msg.lower():
            print("  * This account uses app-based 2-step verification. At the 'MFA code' prompt, "
                  "open the Garmin authenticator, type the current 6-digit code and press Enter "
                  "promptly (codes rotate ~30s) — don't leave it blank. If it keeps failing, "
                  "switch 2-step verification to email in Garmin account settings, which the "
                  "library handles more reliably.")
        raise SystemExit(1)
    _dump_session(g, tokenstore)
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

def _hrzones(args):
    """`--hrzones [server-name]`: refresh the person's Garmin heart-rate zones (shown on
    Home) and backfill time-in-zone onto any already-linked runs missing it. Deliberately
    NOT folded into `--sync`: zones barely ever change, and --sync stays cheap by not
    contacting Garmin when nothing's pending. Run it after changing zones on Garmin;
    both halves no-op when there's nothing to do, so re-running is free."""
    if args:
        _load_server_env(args[0])
        _ensure_ca_bundle()
    person = os.environ.get("TT_PERSON")
    if not person:
        raise SystemExit("Set TT_PERSON (or pass a server name whose .mcp.json env has it), "
                         "e.g. `python server.py --hrzones training-garmin`.")
    print(json.dumps({"zones": sync_hr_zones(person),
                      "race_predictions": sync_race_predictions(person),
                      "run_zone_backfill": backfill_hr_zone_times(person),
                      "run_entry_backfill": backfill_run_entries(person)}, indent=2))

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
        # `--login [server-name]`: with a server name, pull that server's creds +
        # tokenstore from .mcp.json (same as --sync) so a second person can sign in
        # without re-typing their password — only the MFA prompt remains.
        if len(sys.argv) >= 3:
            _load_server_env(sys.argv[2])
            _ensure_ca_bundle()           # tokenstore/certs may have just been set
        _login_interactive(); sys.exit(0)
    if len(sys.argv) >= 2 and sys.argv[1] == "--sync":
        _sync(sys.argv[2:]); sys.exit(0)
    if len(sys.argv) >= 2 and sys.argv[1] == "--hrzones":
        _hrzones(sys.argv[2:]); sys.exit(0)
    if len(sys.argv) >= 3 and sys.argv[1] == "--selftest":
        _selftest(sys.argv[2]); sys.exit(0)
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("training-garmin")
    _register(mcp)
    mcp.run()
