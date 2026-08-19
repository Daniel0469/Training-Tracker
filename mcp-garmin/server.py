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
import os, re, sys, json, base64, datetime, time, urllib.request, urllib.error

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
    """The extra info Garmin adds on top of a logged run. Only keys the device
    actually recorded, so this stays honest across watches: Daniel's Forerunner 255
    reports running power and ground contact time, Cerys's Vivoactive 5 reports
    neither, and her sessions simply come back without those keys rather than with
    zeros. Everything here is read from a summary we already fetch - no extra calls.

    `vo2max` is kept even though it has never had a value for either of them:
    Garmin only estimates VO2max from outdoor GPS runs and all the recent running
    is on a treadmill, so the key is simply absent. It costs nothing and starts
    working the day someone runs outside."""
    m = {}
    def put(key, val, rnd=None):
        if val is None:
            return
        m[key] = round(val, rnd) if rnd is not None else val
    put("avg_hr", _num(_field(a, "averageHR")), 0)
    put("max_hr", _num(_field(a, "maxHR")), 0)
    # The lowest HR in the session - on an interval workout that's the bottom of a
    # recovery block, which is what HR recovery is measured against.
    put("min_hr", _num(_field(a, "minHR")), 0)
    put("cadence_spm", _num(_field(a, "averageRunningCadenceInStepsPerMinute")
                            or _field(a, "averageRunCadence")), 0)
    put("max_cadence_spm", _num(_field(a, "maxRunCadence")), 0)
    put("elevation_gain_m", _num(_field(a, "elevationGain")), 0)
    put("calories", _num(_field(a, "calories") or _field(a, "activeKilocalories")), 0)
    mov = _num(_field(a, "movingDuration"))
    if mov:
        m["moving_time"] = _mmss(mov)
    put("training_effect", _num(_field(a, "aerobicTrainingEffect")
                                or _field(a, "trainingEffect")), 1)
    put("vo2max", _num(_field(a, "vO2MaxValue")), 1)
    # --- load and effort ---------------------------------------------------
    put("anaerobic_effect", _num(_field(a, "anaerobicTrainingEffect")), 1)
    put("training_load", _num(_field(a, "activityTrainingLoad")), 1)
    lbl = _field(a, "trainingEffectLabel")
    if lbl:
        m["effect_label"] = str(lbl).replace("_", " ").title()
    put("steps", _num(_field(a, "steps")), 0)
    put("moderate_minutes", _num(_field(a, "moderateIntensityMinutes")), 0)
    put("vigorous_minutes", _num(_field(a, "vigorousIntensityMinutes")), 0)
    put("sweat_loss_ml", _num(_field(a, "waterEstimated")), 0)
    # --- running dynamics --------------------------------------------------
    put("ground_contact_ms", _num(_field(a, "groundContactTime")), 0)
    put("vertical_oscillation_cm", _num(_field(a, "verticalOscillation")), 1)
    put("vertical_ratio_pct", _num(_field(a, "verticalRatio")), 1)
    put("stride_length_cm", _num(_field(a, "strideLength")), 0)
    # --- running power (Forerunner-class watches only) ---------------------
    put("avg_power_w", _num(_field(a, "averagePower")), 0)
    put("max_power_w", _num(_field(a, "maxPower")), 0)
    put("normalized_power_w", _num(_field(a, "normalizedPower")), 0)
    # --- what the person told the watch afterwards -------------------------
    # Garmin stores its post-workout prompts on a 0-100 scale in steps of 10 and
    # shows them as 1-10 (RPE) and a five-point Feel. Kept as the 1-10 the app
    # already uses for its own RPE, so the two are directly comparable - and they
    # are two different answers to the same question, not one duplicated: the
    # watch asks at the end of the run, the app asks per exercise.
    rpe = _num(_field(a, "directWorkoutRpe"))
    if rpe:
        m["watch_rpe"] = int(round(rpe / 10))
    feel = _num(_field(a, "directWorkoutFeel"))
    if feel is not None:
        m["watch_feel"] = _FEEL_LABELS.get(int(round(feel / 25)) * 25, str(int(feel)))
    return {k: (int(v) if isinstance(v, float) and v.is_integer() else v) for k, v in m.items()}

# Garmin's five-point "how did that feel?" prompt, as stored (0-100) and shown.
_FEEL_LABELS = {0: "very weak", 25: "weak", 50: "normal", 75: "strong", 100: "very strong"}

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

# ---------------------------------------------------------------- per-rep interval detail
# A rep has to be a real one: Garmin's run/walk detection also emits 1-8 second
# fragments where the belt was spinning up or the person stumbled a stride. On the
# two real interval sessions every prescribed rep clears both of these easily
# (Daniel's shortest was 228 m / 64 s, Cerys's 195 m / 69 s) and every fragment
# fails both (0-2 m, 0.2-8 s), so the gap is wide - no session sits near the line.
_REP_MIN_M = 50
_REP_MIN_SEC = 20

def _gmt_dt(s):
    s = str(s or "").replace("T", " ").strip()[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

def fetch_typed_splits(activity_id):
    """Garmin's run/walk-detected splits. Unlike laps (which a treadmill fires every
    1 km, swallowing whole reps) these are typed RWD_RUN / RWD_WALK / RWD_STAND, so
    the running blocks ARE the reps. Returns [] when unavailable; optional to every
    caller."""
    try:
        return (garmin_client().get_activity_typed_splits(activity_id) or {}).get("splits") or []
    except Exception:
        return []

def fetch_power_zone_times(activity_id):
    """Seconds in each of the five running-power zones, [Z1..Z5]. None on a watch
    that doesn't record power (Cerys's Vivoactive 5), same contract as
    fetch_hr_zone_times."""
    try:
        rows = garmin_client().get_activity_power_in_timezones(activity_id) or []
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

def _series_min_hr(series, lo, hi):
    """Lowest HR in the elapsed-seconds window [lo, hi) of the per-second trace."""
    hrs = [h for t, _kmh, h in series if h is not None and lo <= t < hi]
    return int(round(min(hrs))) if hrs else None

def reps_from_typed_splits(typed, a, series=None):
    """Per-rep detail for an interval session, from Garmin's own run/walk splits.

    detect_intervals() (below/above) recovers the same structure from the speed
    trace and is kept as a cross-check, but this is richer and comes from Garmin's
    own segmentation rather than a threshold we picked: every rep arrives with its
    distance, duration, average and max HR, cadence and - on a watch that records
    it - power. Verified against both 29 Jul sessions: 6 reps for Daniel and 5 for
    Cerys, matching what they typed and what the trace says.

    Speed here is the rep AVERAGE, which is a different number from the peak the
    trace shows. That matters: the peak reads 10-15% above the typed speed, which is
    why speed was treated as unusable, but the rep average came out at 13.1 km/h
    against Daniel's typed 13. Included on that basis, still alongside what he typed.
    """
    act_start = _gmt_dt(_field(a, "startTimeGMT"))
    if act_start is None or not typed:
        return None
    blocks = []
    for s in typed:
        st = _gmt_dt(s.get("startTimeGMT"))
        dur = _num(s.get("duration")) or 0
        if st is None or dur <= 0:
            continue
        blocks.append({"type": str(s.get("type") or s.get("splitType") or ""),
                       "at": (st - act_start).total_seconds(), "sec": dur,
                       "m": _num(s.get("distance")) or 0,
                       "avg_hr": _num(s.get("averageHR")), "max_hr": _num(s.get("maxHR")),
                       "cad": _num(s.get("averageRunCadence")),
                       "pwr": _num(s.get("averagePower"))})
    blocks.sort(key=lambda b: b["at"])
    runs = [b for b in blocks
            if b["type"] == "RWD_RUN" and b["m"] >= _REP_MIN_M and b["sec"] >= _REP_MIN_SEC]
    if len(runs) < 2:
        return None
    series = series or []
    reps = []
    for i, b in enumerate(runs):
        end = b["at"] + b["sec"]
        km = b["m"] / 1000.0
        rep = {"n": i + 1, "dist_m": int(round(b["m"])), "sec": int(round(b["sec"])),
               "kmh": round(b["m"] / b["sec"] * 3.6, 1), "pace": _pace(km, b["sec"])}
        for key, val, rnd in (("avg_hr", b["avg_hr"], 0), ("max_hr", b["max_hr"], 0),
                              ("cadence_spm", b["cad"], 0), ("power_w", b["pwr"], 0)):
            if val is not None:
                rep[key] = int(round(val)) if rnd == 0 else round(val, rnd)
        if i + 1 < len(runs):
            nxt = runs[i + 1]["at"]
            gap = nxt - end
            if gap > 0:
                rep["recovery_sec"] = int(round(gap))
                # Average speed over everything between the two reps (walking and
                # standing both), which is what the "Easy speed" column means.
                rm = sum(b["m"] for b in blocks if end <= b["at"] < nxt)
                if rm > 0:
                    rep["recovery_kmh"] = round(rm / gap * 3.6, 1)
                # The bottom of the recovery, from the per-second trace. The walk
                # splits only carry an average, and an average over a block that
                # starts at 155 bpm hides the point of the measurement.
                lo = _series_min_hr(series, end, runs[i + 1]["at"])
                if lo is not None:
                    rep["recovery_min_hr"] = lo
                    if b["max_hr"]:
                        rep["hr_drop"] = int(round(b["max_hr"] - lo))
        reps.append(rep)
    return {"count": len(reps), "reps": reps, "derived": rep_derived(reps),
            "source": "Garmin's own run/walk split detection (RWD_RUN blocks). Speed "
                      "is the rep average, not the peak."}

def rep_derived(reps):
    """The numbers worth trending session to session, from the per-rep list.

    Deliberately conservative about drift: comparing the first rep's HR with the
    last one's only means anything if they were run at a similar speed. Daniel's
    29 Jul reps sat within 3% of each other and his HR went 130 -> 139, which is
    real cardiac drift. Cerys's last rep was 25% slower than her best, so the same
    subtraction would be measuring her slowing down, not her heart drifting - hence
    the speed guard and the explicit reason when it can't be computed."""
    if not reps:
        return {}
    speeds = [r["kmh"] for r in reps if r.get("kmh")]
    d = {}
    if len(speeds) >= 2:
        mean = sum(speeds) / len(speeds)
        best = max(speeds)
        if mean:
            # Spread of the reps around their own mean: how evenly it was paced.
            d["consistency_pct"] = round((max(speeds) - min(speeds)) / mean * 100, 1)
        if best:
            # Negative = the last rep was slower than the best one.
            d["fade_pct"] = round((speeds[-1] - best) / best * 100, 1)
        d["kmh_avg"] = round(mean, 1)
        d["kmh_best"] = round(best, 1)
    first_hr, last_hr = reps[0].get("avg_hr"), reps[-1].get("avg_hr")
    if first_hr and last_hr and len(reps) >= 3:
        if speeds and min(speeds[0], speeds[-1]) >= 0.9 * max(speeds[0], speeds[-1]):
            d["drift_bpm"] = int(last_hr - first_hr)
        else:
            d["drift_skipped"] = ("first and last rep were run at different speeds, "
                                  "so the HR difference isn't drift")
    drops = [r["hr_drop"] for r in reps if r.get("hr_drop") is not None]
    if drops:
        d["hr_recovery_bpm"] = int(round(sum(drops) / len(drops)))
        d["hr_recovery_best"] = max(drops)
    return d

def activity_efficiency(a, typed=None, bodyweight_kg=None):
    """How much speed each heartbeat and each watt is buying - the numbers that
    should improve as someone gets fitter at an unchanged pace.

    `ef` is the standard efficiency factor, metres per minute per bpm. It is taken
    over the RUNNING blocks only where Garmin's run/walk detection gives them: the
    whole-activity average is diluted by the walking either side (on Daniel's 1 Aug
    Zone 2 the activity averages 7:32/km against 6:43/km for the running), and an EF
    that moves because someone walked a bit more is worthless for trending.

    `watts_per_kg` uses the bodyweight already in the app as at the session date, so
    it comes from the same place as the lifting load calculations rather than a
    second, drifting copy of someone's weight."""
    out = {}
    runs = [s for s in (typed or [])
            if str(s.get("type") or "") == "RWD_RUN"
            and (_num(s.get("distance")) or 0) >= _REP_MIN_M
            and (_num(s.get("duration")) or 0) >= _REP_MIN_SEC]
    dist = sum(_num(s.get("distance")) or 0 for s in runs)
    dur = sum(_num(s.get("duration")) or 0 for s in runs)
    hrs = [(_num(s.get("averageHR")) or 0) * (_num(s.get("duration")) or 0) for s in runs]
    basis = "running blocks only"
    if not (dist > 0 and dur > 0 and sum(hrs) > 0):
        # No typed splits (an older activity, or a watch that didn't segment it):
        # fall back to the whole activity and say so, rather than skip the metric.
        dist = _num(_field(a, "distance")) or 0
        dur = _num(_field(a, "movingDuration")) or _num(_field(a, "duration")) or 0
        hr = _num(_field(a, "averageHR")) or 0
        hrs = [hr * dur]
        basis = "whole activity, diluted by any walking"
    if dist > 0 and dur > 0:
        avg_hr = sum(hrs) / dur
        out["run_km"] = round(dist / 1000, 2)
        out["run_pace"] = _pace(dist / 1000, dur)
        if avg_hr > 0:
            out["ef"] = round((dist / dur * 60) / avg_hr, 2)
            out["ef_avg_hr"] = int(round(avg_hr))
        out["ef_basis"] = basis
    pwr = _num(_field(a, "averagePower"))
    if pwr and bodyweight_kg:
        out["watts_per_kg"] = round(pwr / bodyweight_kg, 2)
    return out

def bodyweight_on(data, person, date):
    """The person's bodyweight as at a date - latest entry on or before it, else the
    earliest one after. Mirrors bodyweightOn in js/app.js (and the port in mcp-coach)
    so every load calculation in the project agrees."""
    rows = [b for b in (data.get("bodyweights") or [])
            if b and b.get("person") == person and _num(b.get("kg"))]
    if not rows:
        return None
    before = [b for b in rows if str(b.get("date") or "") <= str(date or "")]
    if before:
        return _num(max(before, key=lambda b: str(b.get("date")))["kg"])
    return _num(min(rows, key=lambda b: str(b.get("date")))["kg"])

def _touch(log):
    """Stamp a log as edited now, in the same ms-epoch the app uses.

    The app's mergeRecord (js/app.js) resolves a log edited on both sides by this
    field. Without it, a phone holding a local edit looks 'newer' than everything
    this server writes and Garmin enrichment would stop landing. Every place that
    mutates a log has to call this - see the merge comment in js/app.js for why the
    old wholesale-replace had to go."""
    log["updatedAt"] = int(time.time() * 1000)


def enrich_log(log, a, splits, zone_secs=None, program=None, extras=None):
    """Attach Garmin's extra info to an already-logged session, without overwriting
    what the person entered. Fills splits only if the run entry was left empty, and
    recreates that entry entirely when the session hasn't got one (see below).
    `zone_secs` (from fetch_hr_zone_times) adds time-in-HR-zone when available;
    `program` places a recreated run entry in the right spot in the exercise order.
    `extras` carries everything that needs its own Garmin call or a look at the rest
    of the store - typed splits, the speed/HR trace, power zones, bodyweight - so
    those all happen up front and a write retry never re-fetches them."""
    extras = extras or {}
    _touch(log)
    log["garminActivityId"] = a.get("activityId")
    log["garminWanted"] = False
    metrics = activity_metrics(a)
    if zone_secs:
        metrics["hr_zone_secs"] = zone_secs
    if extras.get("power_zone_secs"):
        metrics["power_zone_secs"] = extras["power_zone_secs"]
    eff = activity_efficiency(a, extras.get("typed_splits"), extras.get("bodyweight_kg"))
    if eff:
        metrics["efficiency"] = eff
    if metrics:
        # Merged, not replaced: re-running this (refresh_metrics does) must not drop
        # a field whose fetch happened to fail this time - time-in-zone comes from a
        # separate call that returns None on a run with no HR data.
        log.setdefault("garmin", {}).update(metrics)
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
    # A steady Zone 2 run has no structure worth recovering, and neither the trace
    # heuristic nor the run/walk splits return reps for one.
    if run_entry is None and log.get("garmin"):
        series = extras.get("series") or []
        reps = reps_from_typed_splits(extras.get("typed_splits"), a, series)
        if reps:
            log["garmin"]["reps"] = reps
            _fill_blank_interval_rows(log, program, reps)
        # The trace heuristic stays as a second opinion. It measures the rep
        # differently (it thresholds at the midpoint of the session's speed range,
        # so it clips the belt's ramp up and down and reads ~10s shorter per rep),
        # and it is the only source when Garmin didn't segment the activity.
        iv = detect_intervals(series)
        if iv:
            log["garmin"]["intervals"] = iv
    return log

def _interval_entry(log, program):
    """The logged entry for an interval piece - reps typed as speeds. A logged entry
    doesn't carry the program's `garminRun` flag, so it's resolved back by name, the
    same fallback _program_run_slot and the app's isIntervalEntry use."""
    sess = ((program or {}).get("sessions") or {}).get(log.get("sessionKey")) or {}
    named = {e.get("name") for e in (sess.get("exercises") or []) if e.get("garminRun") is True}
    if not named:
        return None
    return next((e for e in (log.get("entries") or []) if e.get("name") in named), None)

def _fill_blank_interval_rows(log, program, reps):
    """Write the per-rep speeds into the interval entry, but ONLY when it was left
    blank - Daniel's call, matching how the Zone 2 splits already behave: anything
    typed is his data and stays untouched, and an empty entry gets filled rather
    than staying empty.

    Guarded on the column actually being km/h. The speed Garmin reports is km/h, and
    writing it into a column labelled mph or "(level)" would silently record a wrong
    number - the same reasoning as bestSpeedFromEntry in js/app.js only converting
    for km/h."""
    e = _interval_entry(log, program)
    if e is None or _entry_has_rows(e):
        return
    cols = e.get("cols") or []
    if len(cols) < 2 or not all(re.search(r"km\s*/\s*h", str(c), re.I) for c in cols[:2]):
        return
    rows = [[r.get("kmh", ""), r.get("recovery_kmh", "")] for r in reps.get("reps") or []]
    if rows:
        e["rows"] = rows

def fetch_activity_extras(activity_id):
    """Everything about one activity that needs its own Garmin call: the run/walk
    splits, the per-second speed/HR trace, and power time-in-zones. Gathered in one
    place so callers fetch it once, up front, outside the store write - a write that
    has to retry must never re-run these."""
    return {"typed_splits": fetch_typed_splits(activity_id),
            "series": fetch_detail_series(activity_id),
            "power_zone_secs": fetch_power_zone_times(activity_id)}

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
        matches[str(l.get("id"))] = (a, splits, fetch_hr_zone_times(aid),
                                     fetch_activity_extras(aid))
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
            a, splits, zsecs, extras = m
            aid = a.get("activityId")
            if aid in taken:
                continue
            extras = dict(extras, bodyweight_kg=bodyweight_on(data, person, l.get("date")))
            enrich_log(l, a, splits, zsecs, data.get("program"), extras)
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
            _touch(l)
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
            _touch(l)
            done.append({"session": l.get("sessionName"), "date": l.get("date"), "added_as": name})
        return done or None
    filled = _github_update(
        mutate, lambda f: f"Restore the run entry on {len(f)} of {person}'s cardio session(s)") or []
    return {"ok": True, "person": person, "filled": len(filled), "details": filled,
            "message": f"Restored the run on {len(filled)} session(s)."}

# ---------------------------------------------------------------- overnight / recovery
def fetch_wellness_day(date):
    """Sleep, overnight HRV, resting HR and readiness for one night. Returns None for
    a night the watch wasn't worn, which is most of them so far - both Daniel and
    Cerys currently put the watch on for a workout and take it off after, so the whole
    of this comes back empty. That's the point of returning None rather than a row of
    nulls: nothing is stored, so the app has nothing to show and shows nothing.

    HRV needs about three weeks of consistent overnight wear before `status` becomes
    anything other than NONE - Garmin won't call an HRV reading high or low until it
    has a baseline to compare against. Expect the number before the verdict.

    A night with no sleep recorded returns None even when Garmin offers other numbers
    for that date, because they aren't trustworthy without it. Garmin's "resting" HR is
    the lowest it saw all day, so on a day the watch went on for the gym and came off
    after, it reports the bottom of a warm-up - Daniel's 25 and 29 Jul came back as 91
    and 80 bpm against the 52 measured on the one night he actually wore it. Storing
    those would have drawn a resting-HR trend out of three warm-ups."""
    w = {}
    try:
        s = garmin_client().get_sleep_data(date) or {}
    except Exception:
        s = {}
    dto = s.get("dailySleepDTO") or {}
    secs = _num(dto.get("sleepTimeSeconds"))
    if secs:
        w["sleep_sec"] = int(secs)
        w["sleep"] = _mmss_hours(secs)
        for key, field in (("deep_sec", "deepSleepSeconds"), ("light_sec", "lightSleepSeconds"),
                           ("rem_sec", "remSleepSeconds"), ("awake_sec", "awakeSleepSeconds")):
            v = _num(dto.get(field))
            if v is not None:
                w[key] = int(v)
        for key, field in (("overnight_hr", "avgHeartRate"), ("sleep_stress", "avgSleepStress"),
                           ("respiration", "averageRespirationValue")):
            v = _num(dto.get(field))
            if v is not None:
                w[key] = round(v, 1) if key == "respiration" else int(round(v))
        score = ((dto.get("sleepScores") or {}).get("overall") or {}).get("value")
        if _num(score) is not None:
            w["sleep_score"] = int(_num(score))
        qual = ((dto.get("sleepScores") or {}).get("totalDuration") or {}).get("qualifierKey")
        if qual:
            w["sleep_quality"] = str(qual).replace("_", " ").lower()
    if not w:
        return None                        # watch wasn't worn overnight - see docstring
    hrv = _num(s.get("avgOvernightHrv"))
    status = s.get("hrvStatus")
    if hrv is None or status is None:
        try:
            h = garmin_client().get_hrv_data(date) or {}
        except Exception:
            h = {}
        summ = h.get("hrvSummary") or {}
        hrv = hrv if hrv is not None else _num(summ.get("lastNightAvg"))
        status = status or summ.get("status")
    if hrv is not None:
        w["hrv_ms"] = int(round(hrv))
    # NONE means "no baseline yet", which is not a verdict - don't store it as one.
    if status and str(status).upper() != "NONE":
        w["hrv_status"] = str(status).lower()
    rhr = _num(s.get("restingHeartRate"))
    if rhr is None:
        try:
            rhr = _num((garmin_client().get_stats(date) or {}).get("restingHeartRate"))
        except Exception:
            rhr = None
    if rhr:
        w["resting_hr"] = int(round(rhr))
    try:
        rd = garmin_client().get_training_readiness(date) or []
    except Exception:
        rd = []
    row = (rd or [{}])[0] if isinstance(rd, list) else rd
    if isinstance(row, dict):
        sc = _num(row.get("score"))
        if sc is not None:
            w["readiness"] = int(sc)
            if row.get("level"):
                w["readiness_level"] = str(row["level"]).lower()
    return w or None

def _mmss_hours(sec):
    """Seconds -> "8h 56m", for a duration that's hours long rather than minutes."""
    sec = int(sec or 0)
    return f"{sec // 3600}h {sec % 3600 // 60:02d}m"

def sync_wellness(person, days=14):
    """Store `person`'s overnight numbers for the last `days` days, so the app can show
    a recovery card and the coach can put a bad session next to a bad night.

    Only days with data are written, and the whole call no-ops when there are none, so
    running this against a watch that never gets worn overnight costs one commit's
    worth of nothing. Idempotent: a day already stored isn't refetched."""
    have = set()
    try:
        data, _sha, _url, _token = _github_read_with_sha()
        have = set(((data.get("wellness") or {}).get(person) or {}).keys())
    except Exception:
        pass
    today = datetime.date.today()
    fetched = {}
    for n in range(1, max(1, days) + 1):
        d = (today - datetime.timedelta(days=n)).isoformat()
        if d in have:
            continue                       # already stored - don't call Garmin again
        w = fetch_wellness_day(d)
        if w:
            fetched[d] = w
    if not fetched:
        return {"ok": True, "person": person, "added": 0,
                "message": (f"No overnight data in the last {days} days that isn't already "
                            "stored. Expected while the watch is only worn for workouts.")}
    def mutate(data):
        wl = data.setdefault("wellness", {}).setdefault(person, {})
        added = [d for d in fetched if d not in wl]
        if not added:
            return None
        for d in added:
            wl[d] = fetched[d]
        return sorted(added)
    added = _github_update(
        mutate, lambda a: f"Add {len(a)} night(s) of {person}'s overnight data") or []
    return {"ok": True, "person": person, "added": len(added), "dates": added,
            "message": f"Stored {len(added)} night(s). Shows in the app after a sync."}

def refresh_metrics(person, limit=50):
    """Re-read Garmin for `person`'s ALREADY-linked sessions, so sessions linked
    before a field existed pick it up. Neither the scheduled `--sync` nor
    garmin_enrich_session can reach them: both deliberately skip anything that
    already has a garminActivityId, which is right for linking and wrong for adding
    new fields to old links.

    Runs the same enrich_log as the sync, so it inherits the never-overwrite rule -
    typed data is safe, blanks may get filled. Garmin calls all happen up front, so
    a write retry never re-fetches them."""
    data, _sha, _url, _token = _github_read_with_sha()
    todo = [l for l in data.get("logs", [])
            if l and l.get("person") == person and l.get("garminActivityId")][:limit]
    fetched = {}
    for l in todo:
        aid = l.get("garminActivityId")
        try:
            a, splits = fetch_activity(aid)
        except Exception:
            continue
        fetched[str(l.get("id"))] = (a, splits, fetch_hr_zone_times(aid),
                                    fetch_activity_extras(aid))
    if not fetched:
        return {"ok": True, "person": person, "refreshed": 0,
                "message": f"Nothing to refresh ({len(todo)} linked session(s) checked)."}
    def mutate(data):
        done = []
        for l in data.get("logs", []):
            m = fetched.get(str(l.get("id"))) if l else None
            if not m:
                continue
            a, splits, zsecs, extras = m
            before = sorted((l.get("garmin") or {}).keys())
            extras = dict(extras, bodyweight_kg=bodyweight_on(data, person, l.get("date")))
            enrich_log(l, a, splits, zsecs, data.get("program"), extras)
            after = sorted((l.get("garmin") or {}).keys())
            done.append({"session": l.get("sessionName"), "date": l.get("date"),
                         "added": [k for k in after if k not in before]})
        return done or None
    done = _github_update(
        mutate, lambda f: f"Refresh Garmin metrics on {len(f)} of {person}'s session(s)") or []
    return {"ok": True, "person": person, "refreshed": len(done), "details": done,
            "message": f"Refreshed {len(done)} session(s). They show after a sync."}

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
    extras0 = fetch_activity_extras(activity_id)
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
        extras = dict(extras0, bodyweight_kg=bodyweight_on(data, person, log.get("date")))
        enrich_log(log, a, splits, zsecs, data.get("program"), extras)
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
    def garmin_wellness(person: str, days: int = 14) -> str:
        """Store `person`'s overnight numbers - sleep and its stages, sleep score,
        overnight HRV, resting HR, respiration, and training readiness where Garmin has
        it - for the last `days` days. Only nights with data are written and days already
        stored aren't refetched, so it's cheap and safe to re-run. Expect nothing back
        while the watch is only worn for workouts; HRV also needs ~3 weeks of overnight
        wear before its status means anything."""
        return json.dumps(sync_wellness(person, days), indent=2)

    @mcp.tool()
    def garmin_refresh_metrics(person: str) -> str:
        """Re-read Garmin for `person`'s already-linked sessions and add any metrics
        they're missing (per-rep interval detail, running dynamics, power, the watch's
        own RPE/Feel, efficiency). Use after this server gains a new field: the normal
        sync skips anything already linked, so old sessions never pick one up. Same
        never-overwrite merge - what was typed stays."""
        return json.dumps(refresh_metrics(person), indent=2)

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

def _refresh(args):
    """`--refresh [server-name]`: add any missing metrics to already-linked sessions.
    Deliberately not part of `--sync` (which stays cheap by not contacting Garmin when
    nothing is pending) - this one always calls Garmin once per linked session, so it
    is a run-it-when-the-server-gains-a-field job, not an hourly one."""
    if args:
        _load_server_env(args[0])
        _ensure_ca_bundle()
    person = os.environ.get("TT_PERSON")
    if not person:
        raise SystemExit("Set TT_PERSON (or pass a server name whose .mcp.json env has it), "
                         "e.g. `python server.py --refresh training-garmin`.")
    print(json.dumps(refresh_metrics(person), indent=2))

def _wellness(args):
    """`--wellness [server-name] [days]`: store the overnight numbers. Worth a daily
    scheduled run once someone actually wears the watch at night; pointless before
    that, and it no-ops when there's nothing new."""
    if args and not args[0].isdigit():
        _load_server_env(args[0])
        _ensure_ca_bundle()
        args = args[1:]
    person = os.environ.get("TT_PERSON")
    if not person:
        raise SystemExit("Set TT_PERSON (or pass a server name whose .mcp.json env has it), "
                         "e.g. `python server.py --wellness training-garmin`.")
    print(json.dumps(sync_wellness(person, int(args[0]) if args else 14), indent=2))

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
    if len(sys.argv) >= 2 and sys.argv[1] == "--refresh":
        _refresh(sys.argv[2:]); sys.exit(0)
    if len(sys.argv) >= 2 and sys.argv[1] == "--wellness":
        _wellness(sys.argv[2:]); sys.exit(0)
    if len(sys.argv) >= 3 and sys.argv[1] == "--selftest":
        _selftest(sys.argv[2]); sys.exit(0)
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("training-garmin")
    _register(mcp)
    mcp.run()
