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
import os, sys, json, base64, datetime, re, time, urllib.request, urllib.error

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

def _github_update(mutate, message, attempts=3):
    """Read -> mutate -> write the shared store, retrying if another writer got in
    first. data.json has several writers (both phones' sync, this coach, the Garmin
    job); each sends the file's sha, so a race 409s instead of silently losing the
    other side's data - but without a retry that just surfaced as an error. `mutate`
    edits the data in place and returns a result; returning None aborts (no write).
    `message` is the commit message, or a callable taking the result."""
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
                    f"Garmin job) kept beating us to it, {attempts} times. Try again in a moment.")
            time.sleep(0.5 * (attempt + 1))
            continue
        return result

def _today():
    return datetime.date.today().isoformat()

def set_coaching(person, overall="", by_exercise=None, by_session=None, five_k=None,
                 next_cardio=None):
    """Write coaching for a person into the shared data. `overall` is a general
    note; `by_session` maps session name -> a focus note for that session;
    `by_exercise` maps exercise name -> a short next-step cue; `five_k` is the
    estimated-5k card; `next_cardio` assigns which cardio session comes next and
    what to do in it. All are merged into any existing coaching. Shows in the app on
    Home + the log form after the person syncs."""
    def mutate(data):
        coaching = data.get("coaching") or {}
        entry = coaching.get(person) or {}
        if overall:
            entry["overall"] = overall
        if five_k:
            fk = dict(five_k)
            fk["updated"] = _today()
            entry["fiveK"] = fk
        if next_cardio:
            nc = dict(next_cardio)
            nc["updated"] = _today()
            entry["nextCardio"] = nc
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
        hist = data.get("coachingLog")
        if not isinstance(hist, list):
            hist = []
        rec = {"id": int(time.time() * 1000), "date": _today(), "person": person}
        if overall: rec["overall"] = overall
        if by_session: rec["bySession"] = dict(by_session)
        if by_exercise: rec["byExercise"] = dict(by_exercise)
        if five_k: rec["fiveK"] = dict(five_k)
        if next_cardio: rec["nextCardio"] = dict(next_cardio)
        if len(rec) > 3:                  # something beyond id/date/person was written
            hist.append(rec)
            data["coachingLog"] = hist
        return True
    _github_update(mutate, f"Coaching update for {person}")
    return {"ok": True, "person": person,
            "message": f"Saved. {person} will see it in the app after tapping Sync now."}

def get_limiters(data, person=None):
    """What the athletes SAY is holding each session back, in their own words.

    Deliberately separate from `coaching` (which is the coach writing to them)
    and from anything derived from the numbers. A limiter is the thing the coach
    would otherwise have to guess at and would probably guess wrong: "top working
    speed not found yet, building up" is not visible in a HR trace, and neither
    is "Zone 2 is a walk, not a run". Read these BEFORE interpreting the data -
    they say which lever is actually available.

    Shape: limiters[person][exact session name] = "free text".
    """
    lim = data.get("limiters") or {}
    if person:
        return {"person": person, "limiters": lim.get(person) or {}}
    return lim

def set_limiter(person, session, text):
    """Record (or clear, with an empty string) what's holding a session back for
    one person. Written when the athlete tells you, not inferred by you."""
    def mutate(data):
        lim = data.get("limiters") or {}
        entry = dict(lim.get(person) or {})
        if str(text).strip():
            entry[session] = str(text).strip()
        else:
            entry.pop(session, None)
        lim[person] = entry
        data["limiters"] = lim
        return True
    _github_update(mutate, f"Limiter for {person} / {session}")
    return {"ok": True, "person": person, "session": session}

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

def _bodyweight_on(data, person, date):
    """Bodyweight as at a session date - the same rule as bodyweightOn in js/app.js:
    the most recent weigh-in on or before that date, else the earliest on record,
    else the figure in Settings."""
    bws = sorted((b for b in data.get("bodyweights", []) if b.get("person") == person),
                 key=lambda b: b.get("date") or "")
    best = None
    for b in bws:
        if (b.get("date") or "") <= (date or ""):
            best = b
        else:
            break
    if best is None and bws:
        best = bws[0]
    if best is not None:
        return _num(best.get("kg"))
    people = data.get("people") or []
    if person in people:
        i = people.index(person)
        w = (data.get("weights") or [])
        return _num(w[i]) if i < len(w) else None
    return None

def _load_def(data, entry, session_key):
    """A logged entry is stamped with its load type on save, but older ones aren't -
    fall back to the program's exercise of the same name, exactly as loadTypeOf does
    in js/app.js."""
    if entry.get("load"):
        return entry.get("load"), _num(entry.get("bwPct")) or 100
    sessions = (data.get("program") or {}).get("sessions") or {}
    candidates = [sessions[session_key]] if session_key in sessions else list(sessions.values())
    for s in candidates:
        for ex in (s.get("exercises") or []):
            if ex.get("name") == entry.get("name") and ex.get("load"):
                return ex.get("load"), _num(ex.get("bwPct")) or 100
    return None, 100

def _set_load(data, entry, typed, person, date, session_key):
    """What one set actually loaded, in kg. Mirrors setLoad in js/app.js: a bodyweight
    movement adds your own weight, an assisted one subtracts the machine's help - so
    LESS assistance scores HIGHER, which is the whole point. Without this the coach
    read Cerys's pull-up as 36kg and getting worse, when her assist dropping 36 -> 32
    is her only stated goal getting closer."""
    v = _num(typed)
    load, pct = _load_def(data, entry, session_key)
    if not load:
        return v
    bw = _bodyweight_on(data, person, date)
    if bw is None:
        return v            # never weighed in: nothing better than the typed number
    own = bw * (pct / 100.0)
    if load == "assist":
        return own - (v or 0)
    return own + (v or 0)

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
                w = _set_load(data, e, row[0] if row else None, person,
                              l.get("date"), l.get("sessionKey"))
                if w is not None and (top is None or w > top):
                    top = w
            if top is not None:
                name = e.get("name")
                if name not in best or top > best[name]["kg"]:
                    rec = {"kg": round(top, 1), "date": l.get("date")}
                    load, pct = _load_def(data, e, l.get("sessionKey"))
                    if load:
                        # Say so, or "43.8 kg" on a pull-up is a puzzle.
                        rec["scoring"] = ("bodyweight%s plus what was added" if load == "bw"
                                          else "bodyweight%s minus the machine's help") % (
                                              "" if pct == 100 else " x %g%%" % pct)
                    best[name] = rec
    return best

def get_bodyweight(data, person):
    bws = [b for b in data.get("bodyweights", []) if b.get("person") == person]
    bws.sort(key=lambda b: b.get("date", ""))
    return [{"date": b.get("date"), "kg": b.get("kg")} for b in bws]

def _is_run_entry(e):
    """A running entry carries both a distance and a time column (same test as
    isRunning in js/app.js and _is_run_entry in mcp-garmin)."""
    cols = e.get("cols") or []
    return (any("dist" in str(c).lower() for c in cols)
            and any("time" in str(c).lower() for c in cols))

def _mmss(sec):
    sec = round(sec or 0)
    m, s = divmod(int(sec), 60)
    return f"{m}:{s:02d}"

def get_running_form(data, person):
    """Raw material for estimating a 5k: every logged run, the person's Garmin HR zones,
    Garmin's race predictions, and whatever estimate is currently on their Home tab."""
    runs = []
    for l in data.get("logs", []):
        if not l or l.get("person") != person:
            continue
        for e in (l.get("entries") or []):
            if not _is_run_entry(e):
                continue
            km = 0.0
            for r in (e.get("rows") or []):
                try:
                    km += float(str(r[0]).strip())
                except (TypeError, ValueError, IndexError):
                    pass
            if km <= 0:
                continue
            g = l.get("garmin") or {}
            sec = l.get("durationSec") or 0
            runs.append({"date": l.get("date"), "session": l.get("sessionName"),
                         "distance_km": round(km, 2), "duration_sec": sec,
                         "pace_per_km": _mmss((sec / km)) if sec and km else None,
                         "avg_hr": g.get("avg_hr"), "max_hr": g.get("max_hr"),
                         "min_hr": g.get("min_hr"),
                         "hr_zone_secs": g.get("hr_zone_secs"),
                         # Efficiency is measured over the RUNNING blocks only, so it
                         # doesn't move just because someone walked more of a session -
                         # which matters a lot here, where a "Zone 2 run" is often
                         # part walked. See activity_efficiency in mcp-garmin.
                         "efficiency": g.get("efficiency"),
                         "watch_rpe": g.get("watch_rpe"), "watch_feel": g.get("watch_feel"),
                         "form": {k: g[k] for k in
                                  ("cadence_spm", "stride_length_cm", "ground_contact_ms",
                                   "vertical_oscillation_cm", "avg_power_w",
                                   "normalized_power_w", "training_load")
                                  if g.get(k) is not None} or None})
    runs.sort(key=lambda r: r.get("date") or "")
    # Interval / speed work: not distance+time entries, so they're not "runs", but they
    # are the hard efforts a 5k estimate most needs. Values are passed through verbatim
    # under the person's own column names - see interval_units_warning below.
    intervals = []
    for l in data.get("logs", []):
        if not l or l.get("person") != person:
            continue
        for e in (l.get("entries") or []):
            if _is_run_entry(e):
                continue
            cols = [str(c) for c in (e.get("cols") or [])]
            if not any(("pace" in c.lower() or "speed" in c.lower()) for c in cols):
                continue
            rows = e.get("rows") or []
            if not any(any(str(v).strip() for v in (r or [])) for r in rows):
                continue
            g = l.get("garmin") or {}
            intervals.append({"date": l.get("date"), "session": l.get("sessionName"),
                              "exercise": e.get("name"), "target": None,
                              "columns": cols, "rows": rows,
                              "avg_hr": g.get("avg_hr"), "max_hr": g.get("max_hr"),
                              "hr_zone_secs": g.get("hr_zone_secs"),
                              "watch_rpe": g.get("watch_rpe"), "watch_feel": g.get("watch_feel"),
                              "efficiency": g.get("efficiency"),
                              # Every rep individually, off Garmin's own run/walk split
                              # detection: distance, duration, average speed, pace,
                              # avg + max HR, cadence, power, and the recovery that
                              # followed (duration, average speed, and the LOWEST HR
                              # reached). `derived` holds the trend numbers - drift,
                              # HR recovery, consistency, fade. See reps_from_typed_splits.
                              "actual_reps": g.get("reps"),
                              # The older speed-trace heuristic. Same structure, measured
                              # differently (it clips the belt's ramp, so its reps read
                              # ~10s shorter) and it is the only source when Garmin didn't
                              # segment the activity. Prefer actual_reps when both exist.
                              "actual_structure": g.get("intervals")})
    intervals.sort(key=lambda r: r.get("date") or "")
    preds = (data.get("racePredictions") or {}).get(person) or {}
    return {
        "person": person,
        "runs": runs,
        "run_count": len(runs),
        "interval_sessions": intervals,
        "actual_structure_note": (
            "`actual_reps` is what they ACTUALLY did, rep by rep, off the watch rather than "
            "typed - use it to check whether a prescription was followed, and read it in "
            "preference to `actual_structure` (the older whole-session heuristic) whenever "
            "both are present. Each rep carries its distance, duration, average speed and "
            "pace, avg + max HR, cadence, power where the watch records it, and the recovery "
            "that followed it including the LOWEST HR reached. `derived` holds the numbers "
            "worth trending: drift_bpm (HR climb from first rep to last at a comparable "
            "speed), hr_recovery_bpm (average beats dropped between reps), consistency_pct "
            "(spread of rep speeds) and fade_pct (last rep against the best one).\n"
            "Worked examples from 29 Jul 2026. Daniel: 6 reps, speeds within 14.7% and HR "
            "130 -> 139 across them, i.e. he held the prescribed 6x1min and drifted 9 bpm. "
            "Cerys: 5 reps at 13.5 / 12.5 / 14.1 / 13.1 / 10.2 km/h - a 28% fade by the last "
            "one, at 175-180 bpm against a 192 max. Her typed row said a flat 11 km/h and "
            "recorded none of that. When drift can't be computed honestly (her first and last "
            "rep were at different speeds, so the HR difference would be measuring her "
            "slowing down) `drift_skipped` says so instead - don't work around it.\n"
            "On speed: what they typed is still the record, and `rows` is what they typed. But "
            "an earlier version of this note said the watch reads 10-15% high and to ignore its "
            "speed entirely - that figure was the PEAK of the speed trace, not the rep average. "
            "The rep average came out at 13.1 km/h against Daniel's typed 13. So per-rep speed "
            "is usable, and where it disagrees with the typed number by a lot (Cerys, above) "
            "the disagreement is itself the finding. Absent on sessions logged before this "
            "existed, and on any session done without the watch."),
        "interval_units_warning": (
            "Interval values are passed through EXACTLY as typed, under the person's own "
            "column names. A column called 'pace' may actually hold treadmill SPEED in km/h "
            "(e.g. 12 means 12 km/h = 5:00/km), not minutes per km - reading it the wrong "
            "way round gives a wildly wrong estimate. Work out which from context (a 'hard' "
            "value LOWER than the 'easy' one means minutes per km; higher means km/h), and "
            "if it's still ambiguous, ask rather than guessing."),
        "hr_zones": (data.get("hrZones") or {}).get(person) or None,
        "garmin_race_predictions_sec": {k: v for k, v in preds.items() if k in
                                        ("5k", "10k", "half", "marathon")} or None,
        "garmin_predictions_updated": preds.get("updated"),
        "current_estimate": ((data.get("coaching") or {}).get(person) or {}).get("fiveK"),
    }

# A suggestion's life: "proposed" (the coach raised it, Daniel hasn't looked yet)
# -> "open" (he approved it, so the dev chat should action it) -> "done". "declined"
# is the other terminal state, and it is NOT the same as "done": it means he said no,
# so the coach can see that and not raise it again.
SUGGESTION_TERMINAL = ("done", "declined")

def get_suggestions(data, include_done=False, include_proposed=False):
    """The dev backlog. `proposed` items are withheld by default, which is the whole
    point of letting the coach raise things: Daniel approves them in the app first, and
    only then do they become work. Pass include_proposed to see what's waiting on him."""
    subs = data.get("suggestions") or []
    out = []
    for s in subs:
        st = s.get("status")
        if st == "proposed" and not include_proposed:
            continue
        if st in SUGGESTION_TERMINAL and not include_done:
            continue
        out.append(s)
    return out

def propose_suggestion(text, why="", about=""):
    """Raise an app/tracker improvement for Daniel to approve, from the coaching chat.

    This is for things noticed while looking at the data that the APP should do
    differently - not training advice, which belongs in write_coaching. It lands in the
    same backlog Daniel and Cerys type into, but as `status: "proposed"`, so it does not
    reach the dev chat until he has approved it in the gear menu. He asked for exactly
    that gate: "put behind for me to agree before applied"."""
    text = (text or "").strip()
    if not text:
        return {"ok": False, "message": "Nothing to propose - `text` was empty."}
    item = {"id": int(time.time() * 1000), "person": "Coach", "source": "coach",
            "date": datetime.date.today().isoformat(), "text": text,
            "status": "proposed"}
    if why:
        item["why"] = why.strip()
    if about:
        item["about"] = about.strip()
    def mutate(data):
        subs = data.setdefault("suggestions", [])
        # Don't raise the same thing twice, including something already declined -
        # re-proposing a rejected idea every week is exactly the annoyance the
        # declined state exists to prevent.
        norm = " ".join(text.lower().split())
        for s in subs:
            if " ".join(str(s.get("text") or "").lower().split()) == norm:
                return None
        subs.append(item)
        return item
    if _github_update(mutate, f"Coach proposes: {text[:60]}") is None:
        return {"ok": True, "duplicate": True,
                "message": "An identical suggestion is already on the list (possibly "
                           "already declined) - nothing added."}
    return {"ok": True, "id": item["id"], "status": "proposed",
            "message": "Proposed. Daniel sees it in the app's gear menu and can approve "
                       "or decline it; the dev chat won't see it until he approves."}

def resolve_suggestion(sid):
    def mutate(data):
        found = False
        for s in data.get("suggestions") or []:
            if str(s.get("id")) == str(sid):
                s["status"] = "done"; found = True
        return True if found else None    # None = nothing to do, don't write
    if _github_update(mutate, f"Resolve suggestion {sid}") is None:
        return {"ok": False, "message": f"No suggestion with id {sid}"}
    return {"ok": True, "id": sid}

def get_progress(data, person, exercise):
    """Top set per session over time. Scored through _set_load, so a bodyweight or
    assisted movement trends by what it actually loaded rather than by the number
    typed - otherwise an assisted pull-up appears to go backwards as it improves."""
    pts = []
    for l in _person_logs(data, person):
        for e in l.get("entries", []):
            if e.get("name") != exercise:
                continue
            warm = set(e.get("warmup") or [])
            vals = []
            for ri, r in enumerate(e.get("rows", [])):
                if ri in warm or not r:
                    continue
                v = _set_load(data, e, r[0], person, l.get("date"), l.get("sessionKey"))
                if v is not None:
                    vals.append(v)
            if vals:
                pts.append({"date": l.get("date"), "top": round(max(vals), 1)})
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
    def suggestions(include_done: bool = False, include_proposed: bool = False) -> str:
        """In-app improvement suggestions / bug reports Daniel & Cerys logged. Each has id,
        person, date, text, status. Use for the app's dev backlog.

        Coach-raised items (`source: "coach"`) start as `status: "proposed"` and are NOT
        returned unless you pass include_proposed - Daniel approves them in the app first,
        and approval is what turns one into work. `status: "declined"` means he said no:
        don't re-raise it and don't build it."""
        return json.dumps(get_suggestions(load_data(), include_done, include_proposed), indent=2)

    @mcp.tool()
    def propose_suggestion_tool(text: str, why: str = "", about: str = "") -> str:
        """Raise an improvement to the APP for Daniel to approve - use this whenever a
        coaching note ends up mentioning something the tracker itself should do
        differently, so the idea reaches the dev chat instead of being buried in a note
        he has to remember. Training advice is not this: that goes in write_coaching.

        `text` is the change, phrased as the thing to do. `why` is the evidence from the
        data that prompted it. `about` optionally names the person or session it concerns.
        It lands as `proposed`, visible to Daniel in the app's gear menu, and the dev chat
        cannot see it until he approves. Identical text is not added twice, so re-running
        is safe and a declined idea won't come back."""
        return json.dumps(propose_suggestion(text, why, about), indent=2)

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
    def running_form(person: str) -> str:
        """Everything needed to estimate `person`'s 5k: every logged run (date, distance,
        duration, pace, avg HR, seconds per HR zone), their Garmin HR zones, Garmin's own
        race predictions, and the 5k estimate currently showing in the app.

        Garmin's prediction is INPUT, not the answer - it comes from a VO2max model and
        runs optimistic when someone has little hard running logged. Weigh it against the
        actual runs: easy Zone-2 runs understate race pace, so a naive Riegel
        extrapolation (T2 = T1 x (D2/D1)^1.06) of an easy run reads far too slow. Land on
        a considered figure, and be honest in `basis`/`confidence` about how thin the
        evidence is. Write it with write_coaching(five_k=...)."""
        return json.dumps(get_running_form(load_data(), person), indent=2)

    @mcp.tool()
    def limiters(person: str = "") -> str:
        """What Daniel and Cerys SAY is holding each session back, in their own words.
        Read this before you interpret anyone's numbers - it tells you which lever is
        actually available, and it is not derivable from the data. "Top working speed
        not found yet, building up" and "Zone 2 is a walk, not a run" both look like
        the same flat HR trace, and they need opposite advice.

        Where a limiter contradicts what you would have concluded from the numbers,
        the limiter wins - it is the athlete's own account. Say so plainly in your
        coaching rather than quietly overriding it. Omit `person` for everyone."""
        return json.dumps(get_limiters(load_data(), person or None), indent=2)

    @mcp.tool()
    def write_limiter(person: str, session: str, text: str) -> str:
        """Record what's holding a session back for one person, in their words - use the
        EXACT session name. Only when they tell you; never your own inference (that is
        what your coaching notes are for). Empty `text` clears it."""
        return json.dumps(set_limiter(person, session, text), indent=2)

    @mcp.tool()
    def write_coaching(person: str, overall: str = "", by_exercise: dict | None = None,
                       by_session: dict | None = None, five_k: dict | None = None,
                       next_cardio: dict | None = None) -> str:
        """Push coaching to a person so it shows in their app (Home + Log) during workouts.
        `by_session` = {exact session name: focus note} shown on that session (Home shows
        today's; Log shows the open session's). Prefer this for session-level guidance.
        `by_exercise` = {exact exercise name: a concrete next step} shown on that exercise
        (e.g. "hit 5x5 @100 — add 2.5kg next time"). Give one per exercise you have advice on.
        `overall` = an optional general note shown on every session.
        `five_k` = the estimated-5k card on Home, as
        {"time": "24:30", "pace": "4:54", "basis": "one line on what it's from",
         "confidence": "low" | "medium" | "high"}. Read running_form(person) first - it
        explains how to weigh Garmin's prediction against the actual logged runs. Say
        plainly in `basis` what it rests on; use "low" while there's no hard effort or
        time trial to go on. Re-write it whenever a new run changes the picture.
        `next_cardio` = which cardio session they should do NEXT and what to do in it, as
        {"session": "Cardio: Speed + Core", "focus": "4 x 3 min @ 12 km/h, 3 min easy
         between", "why": "one line of reasoning"}. `session` must be an EXACT session
        name from their program. This is not just a note: the app opens that session on
        their cardio day instead of falling back to the automatic alternation, so only
        name a session you actually want them doing. It is per person, so Daniel and
        Cerys can get different numbers for the same session - read limiters(person)
        first, because the two of them are usually limited by different things. The card
        marks itself done once they log a cardio session, and the app returns to
        alternating on its own until you write a new one.
        All merge into existing coaching. They see it after tapping Sync now."""
        return json.dumps(set_coaching(person, overall, by_exercise or {}, by_session or {},
                                       five_k or None, next_cardio or None), indent=2)

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
