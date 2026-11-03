#!/usr/bin/env python3
"""Training Tracker - MCP coaching server.

Exposes two athletes' training data to Claude (Desktop / Code / claude.ai)
so it can act as their coach: pull recent workouts, PRs, bodyweight trend, runs
and goals, and give feedback toward each person's goals.

Runs on your Claude subscription via MCP - no Anthropic API billing.

Data source (read-only), chosen by environment variables:
  * GitHub store (recommended - the same private repo the app syncs to):
      TT_GITHUB_REPO   e.g. owner/training-data
      TT_GITHUB_TOKEN  a fine-grained token with Contents:read on that repo
      TT_GITHUB_PATH   optional, default data.json
  * or a local exported JSON file:
      TT_DATA_FILE     path to a training-data-*.json export

Setup + Claude config: see mcp-coach/README.md.

Self-test without an MCP client:
    python server.py --selftest ../sample-person.json
"""
import os, sys, json, base64, datetime, re, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import progression

# Use the OS (Windows) trust store if available, so SSL works behind antivirus /
# proxy TLS inspection that injects a root CA the default verifier rejects.
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

# ---------------------------------------------------------------- data loading
def load_data():
    if os.environ.get("TT_GITHUB_REPO") and os.environ.get("TT_GITHUB_TOKEN"):
        return _github_read_with_sha()[0]
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

def _gh_request(url, token, body=None):
    """One call to the GitHub contents API: a GET, or a PUT of `body`. Returns the parsed reply."""
    req = urllib.request.Request(
        url, data=None if body is None else json.dumps(body).encode("utf-8"),
        method=None if body is None else "PUT",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "User-Agent": "tt-coach"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def _gh_put(url, token, data, message, sha=None, indent=2):
    body = {"message": message,
            "content": base64.b64encode(json.dumps(data, indent=indent).encode("utf-8")).decode("ascii")}
    if sha:
        body["sha"] = sha
    return _gh_request(url, token, body)

# The coaching history lives in its OWN file, not in data.json. It is the coach's
# working memory - what it has already said, so each week builds on the last - and
# nothing in the app reads it. Kept in the store it had grown to 367KB of a 609KB
# file, 60% of everything both phones push and pull on every sync, for a collapsed
# card that was removed on 14 Sep. Same repo, same token, one file along.
def _log_cfg():
    repo, token, path = _github_cfg()
    log = os.environ.get("TT_GITHUB_LOG_PATH")
    if not log:
        base = path.rsplit("/", 1)
        log = (base[0] + "/coaching-log.json") if len(base) > 1 else "coaching-log.json"
    return repo, token, log

def _log_read_with_sha():
    """The history file as (entries, sha, url, token). A missing file is not an
    error - it is what the first write looks like - and comes back as ([], None)."""
    repo, token, path = _log_cfg()
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    try:
        j = _gh_request(url, token)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return [], None, url, token
        raise
    entries = json.loads(base64.b64decode(j["content"]))
    return (entries if isinstance(entries, list) else []), j["sha"], url, token

def _log_append(rec, message, attempts=3):
    """Append one entry to the history file, retrying on a race like _github_update.

    Deliberately called after the data.json write has succeeded, never inside its
    `mutate`: that mutate is re-run on a 409, which would append the same entry
    twice. The history is also the less important of the two - if this fails, the
    coaching the athlete reads still landed."""
    for attempt in range(attempts):
        entries, sha, url, token = _log_read_with_sha()
        if any(e.get("id") == rec.get("id") for e in entries if isinstance(e, dict)):
            return True                       # already there, from an earlier attempt
        entries.append(rec)
        try:
            _gh_put(url, token, entries, message, sha, indent=1)
            return True
        except urllib.error.HTTPError as e:
            if e.code not in (409, 412, 422) or attempt == attempts - 1:
                raise
    return False

def _github_read_with_sha():
    repo, token, path = _github_cfg()
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    j = _gh_request(url, token)
    return json.loads(base64.b64decode(j["content"])), j["sha"], url, token

def _github_write(data, sha, url, token, message):
    return _gh_put(url, token, data, message, sha)

def _github_update(mutate, message, attempts=3, read=None, write=None, conflicts=(409, 412)):
    """Read -> mutate -> write the shared store, retrying if another writer got in
    first. data.json has several writers (both phones' sync, this coach, the Garmin
    job); each sends the file's sha, so a race 409s instead of silently losing the
    other side's data - but without a retry that just surfaced as an error. `mutate`
    edits the data in place and returns a result; returning None aborts (no write).
    `message` is the commit message, or a callable taking the result. `read` and `write`
    swap in another file (see _text_io); `conflicts` are the codes that mean "re-read"."""
    read, write = read or _github_read_with_sha, write or _github_write
    for attempt in range(attempts):
        data, sha, url, token = read()
        result = mutate(data)
        if result is None:
            return None
        try:
            write(data, sha, url, token, message(result) if callable(message) else message)
        except urllib.error.HTTPError as e:
            # 409/412 = someone else wrote between our read and write: re-read and reapply.
            if e.code not in conflicts:
                raise
            if attempt == attempts - 1:
                raise RuntimeError(
                    "Could not write to the shared store: another writer (a phone sync, or the "
                    f"Garmin job) kept beating us to it, {attempts} times. Try again in a moment.")
            time.sleep(0.5 * (attempt + 1))
            continue
        return result

def _write(mutate, failed, commit, message, **io):
    """_github_update, then the reply a write tool returns: the mutate's result with ok and
    `message` (text, or a callable taking the result), or ok False with what `mutate` put in `failed`."""
    result = _github_update(mutate, commit, **io)
    if result is None:
        return {"ok": False, **failed}
    result["ok"] = True
    result["message"] = message(result) if callable(message) else message
    return result

def _today():
    return datetime.date.today().isoformat()

def _coach_off(person):
    """The refusal for a write that would put coach notes, targets or questions in front of a
    person who turned Garmin and coach off in the app."""
    return (f"{person} has Garmin and coach switched off in the app, so the coach writes no notes, targets or "
            "questions for them. They turn it back on under Settings > Profile.")

def _merge_lowest_rung(data, person, entry, lowest_rung):
    """Merge `lowest_rung` into entry["lowestRung"], per skill, so re-assessing one skill
    leaves the other alone. None/empty clears a skill (its rung got fixed and the next
    one isn't known until the re-test). Returns a warning for each test that isn't on
    the person's ladder."""
    merged = dict(entry.get("lowestRung") or {})
    # The app only tags a row it can find on the ladder, i.e. a cm test this
    # person has logged under that exact name. Say so rather than letting a
    # typo (or a training drill like the wedge squat hold) vanish silently.
    on_ladder = {e.get("name") for l in data.get("logs") or [] if l and l.get("person") == person
                 for e in l.get("entries") or []
                 if str((e.get("cols") or [""])[0]).strip().lower() == "cm"}
    warnings = []
    for skill, rung in lowest_rung.items():
        if rung and (rung.get("test") or "").strip():
            r = dict(rung)
            r["updated"] = _today()
            merged[skill] = r
            if r["test"] not in on_ladder:
                warnings.append(
                    f'{skill}: "{r["test"]}" is not a flexibility test {person} has logged, '
                    f'so no ladder row will be tagged. Use one of: {", ".join(sorted(n for n in on_ladder if n))}')
        else:
            merged.pop(skill, None)
    if merged:
        entry["lowestRung"] = merged
    else:
        entry.pop("lowestRung", None)
    return warnings

def set_coaching(person, overall="", by_exercise=None, by_session=None, five_k=None,
                 next_cardio=None, session_swap=None, lowest_rung=None, targets=None):
    """Write coaching for a person into the shared data. `overall` is a general
    note; `by_session` maps session name -> a focus note for that session;
    `by_exercise` maps exercise name -> the next step on that exercise (a few
    sentences, not a clipped cue - the card renders it in full); `five_k` is the
    estimated-5k card; `next_cardio` assigns which cardio session comes next and
    what to do in it; `session_swap` puts a different session on one weekday for one
    week; `lowest_rung` maps skill -> {"test", "why"}, the flexibility test that
    is currently limiting that skill (a None value clears that skill). All are
    merged into any existing coaching; `targets` maps exercise name -> {"kg", "reps"?, "why"}
    (None clears one), the coach's weight for the next session, refused when its kg differs
    from the progression rule and has no why. Shows in the app on
    Home + the log form after the person syncs."""
    def mutate(data):
        for key in ("warn", "error", "targets"):
            pending.pop(key, None)        # mutate reruns on a conflict; its warnings must not stack
        if not progression.coach_on(data, person):
            pending["error"] = _coach_off(person)
            return None
        coaching = data.get("coaching") or {}
        entry = coaching.get(person) or {}
        if overall:
            entry["overall"] = overall
        for key, card in (("fiveK", five_k), ("nextCardio", next_cardio), ("sessionSwap", session_swap)):
            if card:
                entry[key] = dict(card, updated=_today())
        if lowest_rung:
            warnings = _merge_lowest_rung(data, person, entry, lowest_rung)
            if warnings:
                pending.setdefault("warn", []).extend(warnings)
        if targets:
            pending["targets"] = {}
            pending["error"] = _merge_targets(data, person, entry, targets, pending["targets"])
            if pending["error"]:
                return None
        for key, notes in (("bySession", by_session), ("byExercise", by_exercise)):
            if notes:
                entry[key] = {**(entry.get(key) or {}), **notes}
        entry["updated"] = _today()
        coaching[person] = entry
        data["coaching"] = coaching
        # Record this write in the coaching history - see _log_append for why it is
        # staged here and written after, rather than inside this mutate.
        rec = {"id": int(time.time() * 1000), "date": _today(), "person": person}
        for key, val in (("overall", overall), ("bySession", by_session), ("byExercise", by_exercise),
                         ("fiveK", five_k), ("nextCardio", next_cardio), ("sessionSwap", session_swap),
                         ("lowestRung", lowest_rung), ("targets", targets)):
            if val:
                rec[key] = val if isinstance(val, str) else dict(val)
        if len(rec) > 3:                  # something beyond id/date/person was written
            pending["rec"] = rec
        return True
    pending = {}
    _github_update(mutate, f"Coaching update for {person}")
    if pending.get("error"):
        return {"ok": False, "error": pending["error"]}
    if pending.get("rec"):
        _log_append(pending["rec"], f"Coaching history: {person}")
    out = {"ok": True, "person": person,
           "message": f"Saved. {person} will see it in the app after tapping Sync now."}
    if pending.get("warn"):
        out["warnings"] = pending["warn"]
    if pending.get("targets"):
        out["targets"] = pending["targets"]
    return out

def _merge_targets(data, person, entry, targets, saved):
    """Fold the coach's `targets` ({exercise: {kg, reps?, why?} or None to clear}) into
    entry["targets"], stamping each with what the rule says now and the person's latest log
    of it. Returns an error text when one is refused, else None. A kg that differs from the
    rule needs a why."""
    known = {ex["name"]: ex for _, _, ex in progression.program_exercises(data, person)}
    merged = dict(entry.get("targets") or {})
    for name, t in targets.items():
        if not t:
            merged.pop(name, None)
            continue
        if name not in known:
            return f"{person} has no exercise named {name!r} in the program."
        kg = _num(t.get("kg"))
        if kg is None or kg < 0:
            return f"{name}: kg must be a number."
        kg = int(kg) if kg == int(kg) else round(kg, 2)
        rule = progression.progression_for(data, person, known[name])
        why = str(t.get("why") or "").strip()
        if (rule["target"] is None or abs(kg - rule["target"]) > 0.001) and not why:
            says = f"{rule['status']} at {rule['target']:g} kg" if rule["target"] is not None else f"status {rule['status']}, no target"
            return f"{name}: {kg:g} kg differs from the rule ({says}), so it needs a why."
        rec = {"kg": kg}
        if t.get("reps") not in (None, ""):
            rec["reps"] = t["reps"]
        if why:
            rec["why"] = why
        rec.update(rule=rule["target"], asOfLog=progression.latest_log_id(data, person, name), updated=_today())
        merged[name] = saved[name] = rec
    if merged:
        entry["targets"] = merged
    else:
        entry.pop("targets", None)
    return None

def get_limiters(data, person=None):
    """What the athletes SAY is holding each session back, in their own words.

    Deliberately separate from `coaching` (which is the coach writing to them)
    and from anything derived from the numbers. A limiter is the thing the coach
    would otherwise have to guess at and would probably guess wrong: "top working
    speed not found yet, building up" is not visible in a HR trace, and neither
    is "Zone 2 is a walk, not a run". Read these before interpreting the data -
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

# ---------------------------------------------------------------- session notes
# The warm-up / cool-down notes live on the PROGRAM, not on `coaching`, so unlike
# everything else the coach writes they are shared: one text, seen by both people.
# That is a deliberate choice for this tool - the alternative,
# a per-person overlay, was offered and turned down. Two consequences to respect:
#   * an injury note aimed at one of them is read by both, so name who it's for;
#   * the notes are hand-written and long (the mobility blocks), and a replace
#     wipes the lot - hence `append`, and hence returning the previous text.
def _now_iso():
    """Match JavaScript's `new Date().toISOString()` exactly - `...mmmZ`, not
    `+00:00`. mergeInData compares these stamps as plain STRINGS, and '+' sorts
    below 'Z', so a `+00:00` stamp would read as older than the phone's copy and
    the edit would simply never be adopted."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"

def _find_session(data, session):
    sessions = ((data.get("program") or {}).get("sessions")) or {}
    want = str(session or "").strip()
    if not want:
        return None, sessions
    for key, s in sessions.items():                       # exact name
        if (s or {}).get("name") == want:
            return key, sessions
    for key, s in sessions.items():                       # then case-insensitive, then the key
        if str((s or {}).get("name") or "").strip().lower() == want.lower() or key == want:
            return key, sessions
    return None, sessions

NOTE_FIELDS = ("garminNote", "setupNote", "recordingNote", "warmupNote", "cooldownNote")

def _notes_of(s, fields=NOTE_FIELDS):
    return {f: s.get(f, "") for f in fields}

def get_session_notes(data, session=""):
    """The warm-up / cool-down notes on each session of the program, as they stand.

    Read this before writing one. The notes are long, hand-written and mostly
    mobility work built up over months; write_session_notes replaces by default,
    so writing blind throws away whatever is already there.
    """
    key, sessions = _find_session(data, session)
    if session and key is None:
        return {"error": f"No session named {session!r}.",
                "sessions": [(s or {}).get("name") for s in sessions.values()]}
    keys = [key] if key else list(sessions.keys())
    return [{"session": (sessions.get(k) or {}).get("name"),
             "day": (sessions.get(k) or {}).get("day"),
             **_notes_of(sessions.get(k) or {}, NOTE_FIELDS)}
            for k in keys]

def set_session_notes(session, warmup=None, cooldown=None, append=False, recording=None,
                      setup=None, garmin=None):
    """Rewrite a session's warm-up and/or cool-down note. Shared by both people.

    Passing None for a field leaves it alone; passing "" clears it. `append` adds
    the text as a new paragraph instead of replacing, which is what an injury or
    niggle line usually wants - the mobility work below stays put.
    """
    failed = {}
    def mutate(data):
        key, sessions = _find_session(data, session)
        if key is None:
            failed["error"] = f"No session named {session!r}."
            failed["sessions"] = [(s or {}).get("name") for s in sessions.values()]
            return None
        s = sessions[key]
        before = _notes_of(s, NOTE_FIELDS)
        changed = []
        for field, text in zip(NOTE_FIELDS, (garmin, setup, recording, warmup, cooldown)):
            if text is None:
                continue
            text = str(text).strip()
            if append and text and before[field]:
                text = before[field].rstrip() + "\n\n" + text
            if text == before[field]:
                continue
            s[field] = text
            changed.append(field)
        if not changed:
            failed["error"] = "Nothing to change - the note already reads exactly that."
            return None
        # The program only reaches the phones when its stamp is newer than theirs.
        data.setdefault("program", {})["updatedAt"] = _now_iso()
        return {"session": s.get("name"), "changed": changed, "previous": before,
                **_notes_of(s, NOTE_FIELDS)}
    return _write(mutate, failed, lambda r: f"Session notes for {r['session']}",
                  "Saved to the shared program. BOTH people see this text; it reaches "
                  "their phones on the next Sync now, unless one is mid-workout.")

def _step_line_re(exercise):
    return re.compile(r"^\s*step:\s*" + re.escape(exercise) + r"\s*=.*$", re.I)

def _with_step_line(note, exercise, step, add):
    """`note` with the "Step: <exercise> = <step>" line set (None removes it). Every other
    line is kept as it is. A missing line is added only when `add` is true."""
    pattern = _step_line_re(exercise)
    new = None if step is None else f"Step: {exercise} = {step:g}"
    lines, out, placed = str(note or "").split("\n"), [], False
    if not (new and add) and not any(pattern.match(line) for line in lines):
        return note
    for line in lines:
        if pattern.match(line):
            if new and not placed:
                out.append(new)
                placed = True
            continue
        out.append(line)
    if new and not placed:
        last = [i for i, line in enumerate(out) if progression.parse_step_lines(line)]
        if last:
            out.insert(last[-1] + 1, new)
        else:
            out = out + [""] if "".join(out).strip() else []
            out.append(new)
    return "\n".join(out).rstrip()

def set_machine_step(exercise, step, session=None):
    """Add, replace or remove the "Step: <exercise> = <step>" line in a session's setupNote.
    Touches no other text. Without `session`, every line for the exercise is replaced (or
    removed) and a missing one is added to the first session that has the exercise."""
    if step is not None:
        step = _num(step)
        if step is None or step < 0:
            return {"ok": False, "error": "step must be a number of kg, or null to remove the line."}
        step = round(step, 2) or None
    failed = {}
    def mutate(data):
        sessions = ((data.get("program") or {}).get("sessions")) or {}
        having = [k for k, s in sessions.items()
                  if any((e or {}).get("name") == exercise for e in (s or {}).get("exercises") or [])]
        if not having:
            failed["error"] = f"No exercise named {exercise!r} in the program."
            return None
        if session:
            key, _ = _find_session(data, session)
            if key not in having:
                failed["error"] = f"{exercise!r} is not in the session {session!r}."
                failed["sessions"] = [sessions[k].get("name") for k in having]
                return None
            keys, add_to = [key], key
        else:
            pattern = _step_line_re(exercise)
            keys = [k for k, s in sessions.items()
                    if any(pattern.match(line) for line in str((s or {}).get("setupNote") or "").split("\n"))]
            add_to = None if keys else having[0]
            keys = keys or [add_to]
        previous = {}
        for k in keys:
            s = sessions[k]
            before = str(s.get("setupNote") or "")
            after = _with_step_line(before, exercise, step, k == add_to)
            if after != before:
                s["setupNote"] = after
                previous[s.get("name")] = before
        if not previous:
            failed["error"] = "Nothing to change - the Step line already reads exactly that."
            return None
        data.setdefault("program", {})["updatedAt"] = _now_iso()
        return {"exercise": exercise, "step": step, "sessions": list(previous), "previous": previous}
    return _write(mutate, failed, f"Machine step: {exercise}",
                  "Saved to the shared program. Both people use the same step; it reaches "
                  "their phones on the next Sync now.")

def _session_key(name, sessions):
    """A stable camelCase key from a session name - "Mobility assessment" becomes
    "mobilityAssessment". The key is what every log points at, so it is set once
    here and never edited afterwards; renaming a session changes only its `name`.
    """
    words = re.findall(r"[A-Za-z0-9]+", name) or ["session"]
    base = words[0].lower() + "".join(w[:1].upper() + w[1:].lower() for w in words[1:])
    base = base[:40] or "session"
    # Underscore rather than a bare digit: "Lower 1" already keys to "lower1", so a
    # plain suffix would give "lower12", which reads as Lower 12.
    key, n = base, 2
    while key in sessions:
        key, n = f"{base}_{n}", n + 1
    return key


def _name_taken(sessions, wanted, skip_key=None):
    """Whether another session already has this name. Names are the lookup key
    everywhere - logs are stored by sessionName, the next-cardio card matches one by
    name, and _find_session resolves by name. Two sessions called the same thing
    quietly break all three."""
    return any(str((s or {}).get("name") or "").strip().lower() == wanted.lower()
               for k, s in sessions.items() if k != skip_key)

def add_session(name, day="Optional", exercises=None, person="", warmup="", cooldown="",
                setup="", recording="", garmin=""):
    """Add a whole new session to the program. See the create_session tool docstring."""
    failed = {}

    def mutate(data):
        wanted = str(name or "").strip()
        if not wanted:
            failed["error"] = "A session needs a name."
            return None
        program = data.setdefault("program", {})
        sessions = program.setdefault("sessions", {})
        if _name_taken(sessions, wanted):
            failed["error"] = (f"A session called {wanted!r} already exists. Names must be "
                               "unique - change what is in it with write_session_notes or "
                               "write_program_change instead of adding a second one.")
            return None
        if person and person not in (data.get("people") or []):
            failed["error"] = f"No such person {person!r}. People: {data.get('people')}"
            return None
        try:
            cleaned = [_clean_exercise(e, i) for i, e in enumerate(exercises or [])]
        except ValueError as err:
            failed["error"] = str(err)
            return None

        key = _session_key(wanted, sessions)
        s = {"name": wanted, "day": str(day or "Optional").strip(), "exercises": cleaned}
        for field, text in zip(NOTE_FIELDS, (garmin, setup, recording, warmup, cooldown)):
            if str(text or "").strip():
                s[field] = str(text).strip()
        if person:
            s["person"] = person
        sessions[key] = s
        order = program.setdefault("order", [])
        if key not in order:
            order.append(key)
        program["updatedAt"] = _now_iso()
        return {"session": wanted, "key": key, "day": s["day"],
                "person": s.get("person", ""), "exercises": cleaned}

    return _write(mutate, failed, lambda r: f"New session: {r['session']}", lambda r: (
        f"Created. {r['person'] or 'Both people'} will see it on the next Sync now. Nothing is "
        "logged against it yet, so deleting it costs nothing if it is wrong - but once a "
        "session has been logged, its key is what that history points at."))


def _find_run_session(data, person, which=None):
    """The run session that BELONGS to `person` - the one the coach re-prescribes each
    week. Ownership is the `person` field on the session, which is also what stops the
    other one being offered it in the app.

    A person can own more than one (the term routine gives each of them an easy run and
    a quality run), so `which` picks between them. It matches, case-insensitively, the
    session key, its DAY, or any distinctive part of its name - so "easy", "quality",
    "tuesday", "Easy run: Sam" and "easySam" all work. Day is the stable handle: a
    session gets renamed when its content changes shape, and the day usually does not.
    With one session owned, `which` is optional and only has to not contradict it.
    Returns (key, session) or (None, why).
    """
    sessions = ((data.get("program") or {}).get("sessions")) or {}
    hits = [(k, s) for k, s in sessions.items() if (s or {}).get("person") == person]
    if not hits:
        owned = {(s or {}).get("name"): (s or {}).get("person")
                 for s in sessions.values() if (s or {}).get("person")}
        return None, (f"No session belongs to {person!r}. Owned sessions: {owned or 'none'}.")

    want = str(which or "").strip().lower()
    if want:
        picked = [(k, s) for k, s in hits
                  if k.lower() == want
                  or str(s.get("day") or "").lower() == want
                  or want in str(s.get("name") or "").lower()]
        if not picked:
            owned = [f"{s.get('name')} ({s.get('day')}, key={k})" for k, s in hits]
            return None, (f"No session of {person}'s matches which={which!r}. "
                          f"They own: {owned}.")
        if len(picked) > 1:
            return None, (f"which={which!r} matches more than one of {person}'s sessions "
                          f"({[s.get('name') for _, s in picked]}) - be more specific.")
        return picked[0][0], picked[0][1]

    if len(hits) > 1:
        owned = [f"{s.get('name')} ({s.get('day')}, key={k})" for k, s in hits]
        return None, (f"{person} owns more than one run session ({owned}) - pass `which` to say "
                      "which one you mean. It matches the key, the day, or part of the name, so "
                      "which=\"tuesday\" or which=\"quality\" both work. A write replaces only "
                      "the session you name.")
    return hits[0][0], hits[0][1]


def _clean_exercise(e, i):
    """One exercise, validated into the exact shape the app's program model wants."""
    where = f"exercises[{i}]"
    if not isinstance(e, dict):
        raise ValueError(f"{where} must be an object, got {type(e).__name__}")
    name = str(e.get("name") or "").strip()
    if not name:
        raise ValueError(f"{where} has no name")
    cols = e.get("cols")
    if not (isinstance(cols, list) and 2 <= len(cols) <= 3
            and all(str(c).strip() for c in cols)):
        raise ValueError(f"{where} ({name}) needs 2 or 3 non-empty column names, e.g. "
                         '["Distance (km)", "Time (mm:ss)", "Pace"] or ["Min", "Notes"]')
    try:
        sets = int(e.get("sets") or 1)
    except (TypeError, ValueError):
        raise ValueError(f"{where} ({name}) has a non-numeric `sets`")
    if not 1 <= sets <= 30:
        raise ValueError(f"{where} ({name}) has sets={sets}; it must be 1-30")
    # No `notes`: machine settings are each person's own since 13 Oct (data
    # machineSettings[person][exercise name]) and only they write them, in the app.
    # Anything passed as notes is dropped rather than stored on the program.
    out = {"name": name, "warmup": str(e.get("warmup") or ""),
           "target": str(e.get("target") or "").strip(),
           "sets": sets, "cols": [str(c).strip() for c in cols]}
    if e.get("garminRun"):
        out["garminRun"] = True
    # betterWhen says which way is progress on a flexibility test ("higher" for
    # ankle range, absent for a gap you want to close). Dropping it makes every
    # improvement render as a loss on the ladder.
    if str(e.get("betterWhen") or "").strip().lower() == "higher":
        out["betterWhen"] = "higher"
    # Suggested rest in seconds, shown on the exercise and counted against by the
    # rest bar (14 Oct). Kept when a session is rewritten.
    try:
        if int(e.get("restSec") or 0) > 0:
            out["restSec"] = int(e["restSec"])
    except (TypeError, ValueError):
        raise ValueError(f"{where} ({name}) has a non-numeric `restSec`")
    for opt in ("groupId", "load", "bwPct", "timed"):
        if e.get(opt):
            out[opt] = e[opt]
    if e.get("muscles"):
        out["muscles"] = list(e["muscles"])
    return out


def get_run(data, person, which=None):
    """`person`'s current run session, exactly as their phone will draw it."""
    key, s = _find_run_session(data, person, which)
    if key is None:
        return {"error": s}
    return {"person": person, "session": s.get("name"), "day": s.get("day"),
            **_notes_of(s), "exercises": s.get("exercises") or []}


def get_program_session(data, name=""):
    """One PROGRAMMED session in full - what is prescribed, not what was logged.

    The mirror of get_run for everything that isn't a run. Without it the only way to
    see a lifting session's exercises was to send a deliberately-failing
    write_program_change and read the list out of the error, which writes nothing but
    looks like a write. Read this before proposing any change: it is the difference
    between retiring the right row and leaving the session with none.
    """
    sessions = ((data.get("program") or {}).get("sessions") or {})
    if not sessions:
        return {"error": "No program yet."}
    want = str(name or "").strip().lower()
    key = None
    if want:
        for k, s in sessions.items():
            s = s or {}
            if want in (k.lower(), str(s.get("name") or "").lower(),
                        str(s.get("day") or "").lower()):
                key = k
                break
        if key is None:                       # fall back to a distinctive fragment
            hits = [k for k, s in sessions.items()
                    if want in str((s or {}).get("name") or "").lower()]
            if len(hits) == 1:
                key = hits[0]
            elif len(hits) > 1:
                return {"error": "%r matches more than one session" % name,
                        "matches": [sessions[k].get("name") for k in hits]}
    if key is None:
        return {"error": "Name a session. Match on its name, key or day.",
                "sessions": [{"name": (s or {}).get("name"), "day": (s or {}).get("day"),
                              "person": (s or {}).get("person") or "both"}
                             for s in sessions.values()]}
    s = sessions[key] or {}
    return {"session": s.get("name"), "key": key, "day": s.get("day"),
            "person": s.get("person") or "both",
            "cardio": bool(s.get("cardio")),
            **_notes_of(s),
            "exercises": s.get("exercises") or [],
            # Read-only. Each person's own machine settings, by exercise name - the
            # coach can see them but has no way to write them.
            "machine_settings": _settings_for(data, [e.get("name") for e in (s.get("exercises") or [])])}


def _settings_for(data, names):
    ms = data.get("machineSettings") or {}
    out = {}
    for person, by in ms.items():
        got = {n: (by.get(n) or {}).get("text", "") for n in names if (by.get(n) or {}).get("text")}
        if got:
            out[person] = got
    return out


def _clean_exercises(exercises):
    if not isinstance(exercises, list) or not exercises:
        raise ValueError("`exercises` must be a non-empty list of exercise objects.")
    return [_clean_exercise(e, i) for i, e in enumerate(exercises)]


def _note_on_session(data, person, session_name, note):
    """Store `note` as `person`'s coach note on a session and return its history record."""
    coaching = data.get("coaching") or {}
    entry = coaching.get(person) or {}
    by_session = dict(entry.get("bySession") or {})
    by_session[session_name] = note
    entry["bySession"] = by_session
    entry["updated"] = _today()
    coaching[person] = entry
    data["coaching"] = coaching
    return {"id": int(time.time() * 1000), "date": _today(),
            "person": person, "bySession": {session_name: note}}


def set_run(person, exercises=None, why="", name=None, day=None,
            warmup=None, cooldown=None, recording=None, setup=None, which=None,
            garmin=None):
    """Re-prescribe `person`'s own run session. See the write_run tool docstring."""
    failed = {}

    def mutate(data):
        if person not in (data.get("people") or []):
            failed["error"] = f"No such person {person!r}. People: {data.get('people')}"
            return None
        key, s = _find_run_session(data, person, which)
        if key is None:
            failed["error"] = s
            return None
        try:
            cleaned = None if exercises is None else _clean_exercises(exercises)
        except ValueError as err:
            failed["error"] = str(err)
            return None

        previous = {"name": s.get("name"), "day": s.get("day"), **_notes_of(s),
                    "exercises": json.loads(json.dumps(s.get("exercises") or []))}
        changed = []
        if cleaned is not None and cleaned != previous["exercises"]:
            s["exercises"] = cleaned
            changed.append("exercises")
        if name and str(name).strip() and str(name).strip() != s.get("name"):
            wanted = str(name).strip()
            if _name_taken(((data.get("program") or {}).get("sessions")) or {}, wanted, key):
                failed["error"] = (f"Another session is already called {wanted!r}. Session names "
                                   "must be unique - logs, the next-cardio card and every "
                                   "lookup key on it.")
                return None
            s["name"] = wanted
            changed.append("name")
        if day and str(day).strip() != s.get("day"):
            s["day"] = str(day).strip()
            changed.append("day")
        for field, text in zip(NOTE_FIELDS, (garmin, setup, recording, warmup, cooldown)):
            if text is None:
                continue
            text = str(text).strip()
            if text != s.get(field, ""):
                s[field] = text
                changed.append(field)
        if not changed:
            failed["error"] = "Nothing to change - the session already reads exactly that."
            return None

        # The phones adopt the program only when its stamp is newer than theirs.
        data.setdefault("program", {})["updatedAt"] = _now_iso()

        # `why` rides along as the session's coach note, so the reason for this
        # week's prescription is on the card they read while they train, and lands
        # in the coaching history next to every other note.
        note = str(why or "").strip()
        out = {"person": person, "session": s.get("name"), "changed": changed,
               "previous": previous, "exercises": s.get("exercises")}
        if note and progression.coach_on(data, person):
            pending["rec"] = _note_on_session(data, person, s.get("name"), note)
        elif note:
            out["note_skipped"] = _coach_off(person)

        return out

    pending = {}
    result = _write(mutate, failed, lambda r: f"Run session for {r['person']}: {r['session']}",
                    f"Saved. Only {person} sees this session; it reaches their phone on the next "
                    "Sync now, and never mid-workout. `previous` above is the whole session as it "
                    "was - keep it if you might want to put it back.")
    if result["ok"] and pending.get("rec"):
        _log_append(pending["rec"], f"Coaching history: {person}")
    return result


def get_program_changes(data, include_done=False):
    """Program changes you have proposed, and what became of them."""
    out = []
    for c in (data.get("programChanges") or []):
        if not include_done and c.get("status") != "pending":
            continue
        out.append(c)
    out.sort(key=lambda c: c.get("id", 0), reverse=True)
    return out

class _Refused(Exception):
    """A write tool turning a request down: args[0] holds the fields of the reply."""

def _change_op(session, exercise, names, sets, target, add, remove, warmup, move_after, rest_sec):
    """The (op, fields) of a proposed program change. Raises _Refused when it can't be made."""
    if move_after is not None:
        # Order is the one thing the coach could never change, and it is the
        # reason work gets missed: an exercise at the end of a session goes unlogged
        # review after review when the session overruns. "" means move it
        # to the front; otherwise name the exercise it should follow.
        dest = str(move_after).strip()
        if dest and dest not in names:
            raise _Refused({"error": f"{dest!r} is not in {session!r}, so nothing to move after.",
                            "exercises": names})
        if dest == str(exercise).strip():
            raise _Refused({"error": "An exercise cannot be moved after itself."})
        op, fields = "move", {}
    elif remove:
        op, fields = "remove", {}
    elif add is not None:
        op, fields = "add", dict(add)
        fields.pop("name", None)
        fields.pop("notes", None)   # settings are the athlete's, never the coach's
    else:
        op, fields = "edit", {}
        if sets is not None:
            fields["sets"] = int(sets)
        if target is not None:
            fields["target"] = str(target)
        # warmup and notes were unreachable on an edit until 6 Oct, which made two
        # jobs already assigned to the coach impossible rather than merely undone:
        # restoring the warm-up ramps (none of the exercises had one) and
        # stripping the settings box back to machine settings. Deliberately not
        # "any field add accepts" - `cols` decides how an exercise is scored and
        # drawn, and changing it under a logged history is a different, worse thing.
        if warmup is not None:
            fields["warmup"] = str(warmup)
        if rest_sec is not None:
            fields["restSec"] = int(rest_sec)
        if not fields:
            raise _Refused({"error": "Nothing to change - pass sets, target, warmup, "
                                     "rest_sec, add or remove."})
    if op in ("edit", "remove", "move") and exercise not in names:
        raise _Refused({"error": f"{exercise!r} is not in {session!r}.", "exercises": names})
    if op == "add" and exercise in names:
        raise _Refused({"error": f"{exercise!r} is already in {session!r}."})
    return op, fields

def propose_program_change(session, exercise, why, sets=None, target=None,
                           add=None, remove=False, after="", warmup=None,
                           move_after=None, rest_sec=None):
    """Propose one change to the program. It waits on that exercise in the app's
    Program tab until someone ticks it, and the app applies it - see the tool
    docstring for why that matters.
    """
    failed = {}

    def mutate(data):
        sessions = ((data.get("program") or {}).get("sessions")) or {}
        sess = next((s for s in sessions.values()
                     if str((s or {}).get("name") or "").strip() == str(session).strip()), None)
        if sess is None:
            failed["error"] = f"No session called {session!r}."
            failed["sessions"] = [s.get("name") for s in sessions.values()]
            return None
        names = [e.get("name") for e in (sess.get("exercises") or [])]
        try:
            op, fields = _change_op(session, exercise, names, sets, target, add, remove,
                                    warmup, move_after, rest_sec)
        except _Refused as why_not:
            failed.update(why_not.args[0])
            return None
        pending = [c for c in (data.get("programChanges") or [])
                   if c.get("status") == "pending" and c.get("session") == session
                   and c.get("exercise") == exercise and c.get("op") == op]
        if pending:
            failed["error"] = ("The same change is already waiting for a tick - don't raise "
                               "it twice. Ask them to look at the Program tab instead.")
            return None
        rec = {"id": int(time.time() * 1000), "at": _now_iso(), "status": "pending",
               "session": session, "exercise": exercise, "op": op,
               "fields": fields, "why": str(why or "").strip(), "source": "coach"}
        if op == "add" and after:
            rec["after"] = str(after)
        if op == "move":
            # "" is meaningful here and must survive: it means move to the front,
            # where `add` treats a missing `after` as "put it at the end".
            rec["after"] = str(move_after).strip()
        data.setdefault("programChanges", []).append(rec)
        return rec

    return _write(mutate, failed, lambda r: "Coach proposes: %s on %s" % (r["op"], r["session"]),
                  "Waiting on a tick in the Program tab, on that exercise. They see it "
                  "after Sync now; applying it changes the program on both phones.")

def get_coaching_history(data, person, limit=10):
    """Past coaching writes, newest first, from the history file.

    `data` is still read as a FALLBACK and unioned by id. Two reasons it earns its
    keep: a phone on a build older than tt-v128 still carries `coachingLog` and will
    push it back into data.json on its next sync, and the migration that moved the
    history out is a one-off that could be run against a store someone had written
    to in the meantime. Either way the entry is found rather than silently missing.
    """
    try:
        entries, _sha, _url, _tok = _log_read_with_sha()
    except Exception:
        entries = []                       # no token, no network - fall back below
    seen = {e.get("id") for e in entries if isinstance(e, dict)}
    for e in (data.get("coachingLog") or []):
        if isinstance(e, dict) and e.get("id") not in seen:
            entries.append(e)
    log = [e for e in entries if e.get("person") == person]
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

def _person_bodyweights(data, person):
    """A person's weigh-ins minus the deleted ones - every bodyweight read goes
    through here. Same rule as bwIsDeleted in js/app.js: a `deletedBodyweights`
    tombstone for the row's person+date deletes it when deletedAt >= the row's
    updatedAt (unstamped = 0), so a stale copy pushed back by an old build stays
    gone while a weigh-in taken after the delete stands. Unsorted."""
    dead = {}
    for t in data.get("deletedBodyweights") or []:
        if isinstance(t, dict) and t.get("person") == person and t.get("date"):
            dead[t["date"]] = max(dead.get(t["date"], 0), _num(t.get("deletedAt")) or 0)
    return [b for b in data.get("bodyweights") or []
            if isinstance(b, dict) and b.get("person") == person
            and not (b.get("date") in dead
                     and (_num(b.get("updatedAt")) or 0) <= dead[b.get("date")])]

# ---------------------------------------------------------------- logic (testable)
def list_people(data):
    out = []
    for i, name in enumerate(data.get("people", [])):
        bws = sorted(_person_bodyweights(data, name), key=lambda b: b.get("date", ""))
        goals = (data.get("goals") or ["", ""])
        out.append({
            "person": name,
            "goals": goals[i] if i < len(goals) else "",
            "latest_bodyweight_kg": bws[-1]["kg"] if bws else None,
            "sessions_logged": len(_person_logs(data, name)),
            "coach_on": progression.coach_on(data, name),
        })
    return out

def get_goals(data, person):
    people = data.get("people", [])
    goals = data.get("goals") or []
    if person in people:
        i = people.index(person)
        return {"person": person, "goals": goals[i] if i < len(goals) else ""}
    return {"error": f"Unknown person '{person}'"}

def _adherence(data, log):
    """Sets logged and sets ticked against what the session prescribes.

    Adherence is most of what a weekly review is, and judging it one get_session
    call at a time is expensive. `done` is only saved from 6 Oct, so `ticked` is
    absent on anything older rather than reported as zero - a missing tick is not
    the same claim as a set that was skipped.
    """
    sessions = ((data.get("program") or {}).get("sessions") or {})
    sess = sessions.get(log.get("sessionKey")) or {}
    planned = sum(max(1, int(e.get("sets") or 1)) for e in (sess.get("exercises") or []))
    logged = ticked = 0
    any_done = False
    for e in log.get("entries") or []:
        warm = e.get("warmup") or []
        rows = e.get("rows") or []
        logged += sum(1 for i, r in enumerate(rows)
                      if i not in warm and any(str(v).strip() for v in (r or [])))
        done = e.get("done")
        if isinstance(done, list) and done:
            any_done = True
            ticked += sum(1 for i in done if i not in warm)
    out = {"sets_logged": logged}
    if planned:
        out["sets_planned"] = planned
    if any_done:
        out["sets_ticked"] = ticked
    return out

def list_sessions(data, person, limit=10):
    rows = []
    for l in _person_logs(data, person)[:limit]:
        row = {
            "id": l.get("id"),
            "date": l.get("date"),
            "session": l.get("sessionName"),
            "volume_kg": _log_volume(data, l),
            "difficulty": l.get("difficulty"),
            "duration_sec": l.get("durationSec"),
            "feedback": l.get("feedback") or "",
        }
        row.update(_adherence(data, l))
        rows.append(row)
    return rows

def withdraw_program_change_tool(change_id):
    """Take back a pending program change the coach got wrong.

    Without this a bad proposal sat in the Program tab until someone ticked or
    declined it, and could not be corrected in place - propose_program_change
    refuses a duplicate on (session, exercise, op) while one is pending, so the
    coach could not even replace it. Only `pending` can be withdrawn: a decision
    someone has already made is theirs, not the coach's to erase.
    """
    failed = {}

    def mutate(data):
        c = next((x for x in (data.get("programChanges") or [])
                  if str(x.get("id")) == str(change_id)), None)
        if c is None:
            failed["error"] = f"No program change with id {change_id}."
            return None
        if c.get("status") != "pending":
            failed["error"] = (f"That change is already {c.get('status')!r} - "
                               "a decision they have made is not yours to undo.")
            return None
        c["status"] = "withdrawn"
        c["withdrawnAt"] = _now_iso()
        return {"session": c.get("session"), "exercise": c.get("exercise"), "op": c.get("op")}

    return _write(mutate, failed, lambda r: "Coach withdraws: %s on %s" % (r["op"], r["session"]),
                  "Withdrawn - it disappears from their Program tab on the next sync.")

def get_session(data, session_id):
    for l in data.get("logs", []):
        if str(l.get("id")) == str(session_id):
            return l
    return {"error": f"No session with id {session_id}"}

def set_log_entry(session_id, exercise, rows, why=""):
    """Correct the rows of one exercise on one already-logged session.

    The Garmin sync fills a run entry automatically - from the per-rep detail where
    it has it, from the treadmill's laps otherwise - and it gets it wrong when the
    activity held something other than the session it was matched to. An example: an
    entry filled from three laps, one of which was an incline WALK, so the app
    reported a far slower running pace than was run. This is the way to
    put that right rather than leaving a wrong number in the record.

    It is a correction tool, not a logging tool: never invent a session that didn't
    happen, and never "tidy" numbers a person typed. The previous rows come back in
    the response so a bad correction can be undone.

    Safe against the sync: it only auto-replaces rows that exactly match what the
    laps would produce, and a corrected row won't, so what you write here stays.
    """
    failed = {}

    def mutate(data):
        log = next((l for l in data.get("logs", []) if str(l.get("id")) == str(session_id)), None)
        if log is None:
            failed["error"] = f"No session with id {session_id}"
            return None
        want = str(exercise).strip()
        entry = next((e for e in (log.get("entries") or [])
                      if str(e.get("name") or "").strip().lower() == want.lower()), None)
        if entry is None:
            failed["error"] = f"No exercise named {exercise!r} on that session."
            failed["exercises"] = [e.get("name") for e in (log.get("entries") or [])]
            return None
        if not isinstance(rows, list) or not rows:
            failed["error"] = "`rows` must be a non-empty list of rows."
            return None
        clean = [[("" if v is None else v) for v in (row or [])] for row in rows]
        if clean == entry.get("rows"):
            failed["error"] = "Nothing to change - the entry already reads exactly that."
            return None
        previous = json.loads(json.dumps(entry.get("rows")))
        entry["rows"] = clean
        # The app's mergeRecord settles a log edited on both sides by updatedAt, so without
        # this stamp a phone holding any newer edit kept its old rows over this correction.
        log["updatedAt"] = _now_ms()
        note = str(why or "").strip()
        # Stamped so the next reader can tell a corrected entry from a synced one.
        log.setdefault("corrections", []).append(
            {"at": _now_iso(), "exercise": entry.get("name"),
             "why": note, "previous": previous})
        return {"session": log.get("sessionName"), "date": log.get("date"),
                "person": log.get("person"), "exercise": entry.get("name"),
                "previous": previous, "rows": clean}

    return _write(mutate, failed,
                  lambda r: "Correct %s on %s's %s" % (r["exercise"], r["person"], r["date"]),
                  "Corrected. It reaches their phones on the next Sync now, and the "
                  "Garmin sync will not overwrite it.")

def _bodyweight_on(data, person, date):
    """Bodyweight as at a session date - the same rule as bodyweightOn in js/app.js:
    the most recent weigh-in on or before that date, else the earliest on record,
    else the figure in Settings."""
    bws = sorted(_person_bodyweights(data, person), key=lambda b: b.get("date") or "")
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

def _set_scorer(data, entry, person, date, session_key):
    """A function giving what one typed set actually loaded, in kg. Mirrors setLoad in
    js/app.js: a bodyweight movement adds your own weight, an assisted one subtracts the
    machine's help - so LESS assistance scores HIGHER, which is the whole point. Without
    this the coach read an assisted pull-up as getting worse while the assistance
    dropped, which is the goal getting closer. The load type and the
    bodyweight are the same for every set of an entry, so they are looked up once."""
    load, pct = _load_def(data, entry, session_key)
    bw = _bodyweight_on(data, person, date) if load else None
    def score(typed):
        v = _num(typed)
        if bw is None:         # not a loaded movement, or never weighed in: the typed number
            return v
        own = bw * (pct / 100.0)
        return own - (v or 0) if load == "assist" else own + (v or 0)
    return score

def _hold_sec(v):
    """Seconds from a typed hold: "45", "45s" or "1:05" (parseRest in js/app.js)."""
    v = str(v or "").strip().lower()
    m = re.match(r"^(\d+):(\d{1,2})$", v)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = re.match(r"^(\d+)\s*s?$", v)
    return int(m.group(1)) if m else 0

def _log_volume(data, l):
    """Weight x reps sets only, worked out from the sets (logVolume in js/app.js).
    A timed hold, a run or metres on an erg is not volume, whatever total was saved."""
    total = 0.0
    for e in l.get("entries", []):
        if e.get("timed") or not _is_lifting(e.get("cols")):
            continue
        warm = set(e.get("warmup") or [])
        score = _set_scorer(data, e, l.get("person"), l.get("date"), l.get("sessionKey"))
        for ri, row in enumerate(e.get("rows", [])):
            if ri in warm or len(row) < 2:
                continue
            w = score(row[0])
            try:
                reps = int(str(row[1]).strip())
            except ValueError:
                continue
            if w is not None:
                total += w * reps
    return round(total)

def get_prs(data, person):
    """Lifts: heaviest set. Timed holds: longest hold at each weight (no weight = 0),
    listed under the exercise name as {"holds": [{"kg", "sec", "date"}]}."""
    best = {}
    for l in _person_logs(data, person):
        for e in l.get("entries", []):
            if e.get("timed"):
                warm = set(e.get("warmup") or [])
                holds = best.setdefault(e.get("name"), {"holds": []})["holds"]
                for ri, row in enumerate(e.get("rows", [])):
                    if ri in warm or len(row) < 2:
                        continue
                    try:
                        kg = float(row[0])
                    except (TypeError, ValueError):
                        kg = 0.0
                    sec = _hold_sec(row[1])
                    cur = next((h for h in holds if h["kg"] == kg), None)
                    if sec and (cur is None or sec > cur["sec"]):
                        if cur:
                            holds.remove(cur)
                        holds.append({"kg": kg, "sec": sec, "date": l.get("date")})
                continue
            if not _is_lifting(e.get("cols")):
                continue
            warm = set(e.get("warmup") or [])
            score = _set_scorer(data, e, person, l.get("date"), l.get("sessionKey"))
            top = None
            for ri, row in enumerate(e.get("rows", [])):
                if ri in warm:
                    continue
                w = score(row[0] if row else None)
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
    bws = _person_bodyweights(data, person)
    bws.sort(key=lambda b: b.get("date", ""))
    return [{"date": b.get("date"), "kg": b.get("kg")} for b in bws]

def get_measurements(data, person):
    rows = [m for m in data.get("measurements") or [] if m.get("person") == person and m.get("date")]
    rows.sort(key=lambda m: m["date"])
    return [{"date": m["date"], "cm": m.get("cm") or {}} for m in rows]

def get_nutrition(data, person, days=14, today=None):
    """Daily food totals for the last `days` local days, ending today, against the
    person's targets. A day with no meals is not logged rather than a zero day: the
    hub only knows what was scanned or typed. `estimated` counts free-text guesses.
    Meals the hub deleted (`deletedMeals`) are left out. Fibre is None on a day with
    none recorded, since meals from before 26 Oct 2026 carry none."""
    today = today or datetime.date.today()
    target = (data.get("nutritionTargets") or {}).get(person) or {}
    gone = {t.get("id"): t.get("deletedAt") or 0 for t in data.get("deletedMeals") or []}
    meals = [m for m in data.get("meals") or [] if m.get("person") == person and m.get("date")
             and not (m.get("id") in gone and (m.get("updatedAt") or 0) <= gone[m.get("id")])]
    out = []
    for i in range(days - 1, -1, -1):
        d = (today - datetime.timedelta(days=i)).isoformat()
        day = [m for m in meals if m["date"] == d]
        if not day:
            out.append({"date": d, "logged": False})
            continue
        tot = {k: round(sum(float(m.get(k) or 0) for m in day), 1) for k in ("kcal", "protein", "carbs", "fat")}
        fibre = [float(m["fibre"]) for m in day if m.get("fibre") is not None]
        out.append(dict(tot, date=d, logged=True, meals=len(day), fibre=round(sum(fibre), 1) if fibre else None,
                        estimated=sum(1 for m in day if m.get("estimated"))))
    logged = [d for d in out if d["logged"]]
    avg = lambda k: round(sum(d[k] for d in logged) / len(logged)) if logged else None
    with_fibre = [d["fibre"] for d in logged if d["fibre"] is not None]
    summary = {"days": days, "days_logged": len(logged), "avg_kcal": avg("kcal"),
               "avg_protein": avg("protein"),
               "avg_fibre": round(sum(with_fibre) / len(with_fibre)) if with_fibre else None,
               "target_kcal": target.get("kcal"), "target_protein": target.get("protein")}
    if target.get("protein") and logged:
        summary["days_protein_met"] = sum(1 for d in logged if d["protein"] >= target["protein"])
    return {"person": person, "summary": summary, "days": out}

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

RACE_KEYS = ("5k", "10k", "half", "marathon")

ACTUAL_STRUCTURE_NOTE = (
    "`actual_reps` is what they ACTUALLY did, rep by rep, off the watch rather than "
    "typed - use it to check whether a prescription was followed, and read it in "
    "preference to `actual_structure` (the older whole-session heuristic) whenever "
    "both are present. Each rep carries its distance, duration, average speed and "
    "pace, avg + max HR, cadence, power where the watch records it, and the recovery "
    "that followed it including the LOWEST HR reached. `derived` holds the numbers "
    "worth trending: drift_bpm (HR climb from first rep to last at a comparable "
    "speed), hr_recovery_bpm (average beats dropped between reps), consistency_pct "
    "(spread of rep speeds) and fade_pct (last rep against the best one).\n"
    "Reading it: reps held at a similar speed with HR climbing a few bpm across them "
    "means the prescription was held with mild drift. Reps that fade badly by the last "
    "one, at an HR near max, while the typed row says one flat speed, show what the "
    "typed row recorded none of. When drift can't be computed honestly (the first and "
    "last rep were at different speeds, so the HR difference would be measuring "
    "slowing down) `drift_skipped` says so instead - don't work around it.\n"
    "On speed: what they typed is still the record, and `rows` is what they typed. The "
    "peak of the speed trace reads high, but the rep average comes out close to the "
    "typed speed. So per-rep speed is usable, and where it disagrees with the typed "
    "number by a lot the disagreement is itself the finding. Absent on sessions logged before this "
    "existed, and on any session done without the watch.")

INTERVAL_UNITS_WARNING = (
    "Interval values are passed through EXACTLY as typed, under the person's own "
    "column names. A column called 'pace' may actually hold treadmill SPEED in km/h "
    "(e.g. 12 means 12 km/h = 5:00/km), not minutes per km - reading it the wrong "
    "way round gives a wildly wrong estimate. Work out which from context (a 'hard' "
    "value LOWER than the 'easy' one means minutes per km; higher means km/h), and "
    "if it's still ambiguous, ask rather than guessing.")

def _person_entries(data, person):
    """Every (log, entry) pair `person` has logged."""
    for l in data.get("logs", []):
        if not l or l.get("person") != person:
            continue
        for e in (l.get("entries") or []):
            yield l, e

def _run_row(l, e):
    """One logged run as get_running_form reports it, or None when it has no distance."""
    km = 0.0
    for r in (e.get("rows") or []):
        try:
            km += float(str(r[0]).strip())
        except (TypeError, ValueError, IndexError):
            pass
    if km <= 0:
        return None
    g = l.get("garmin") or {}
    return {"date": l.get("date"), "session": l.get("sessionName"),
            "distance_km": round(km, 2), "duration_sec": l.get("durationSec") or 0,
            # pace_per_km used to sit here and was WRONG: it divided the
            # whole logged session's duration by the running distance, so
            # a mixed session read as a very slow pace - a short run plus a long
            # incline walk and core work, all counted as running time. It was
            # always slightly wrong for a mixed session; it
            # only became obvious once run rows held per-rep distances
            # rather than the whole activity's. The right figure is
            # efficiency.run_pace below, computed over the running blocks
            # only, and one correct pace beats two that disagree.
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
                     if g.get(k) is not None} or None}

def _interval_row(l, e):
    """One interval / speed entry as get_running_form reports it, or None when it has no
    pace or speed column or nothing typed."""
    cols = [str(c) for c in (e.get("cols") or [])]
    if not any(("pace" in c.lower() or "speed" in c.lower()) for c in cols):
        return None
    rows = e.get("rows") or []
    if not any(any(str(v).strip() for v in (r or [])) for r in rows):
        return None
    g = l.get("garmin") or {}
    return {"date": l.get("date"), "session": l.get("sessionName"),
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
            "actual_structure": g.get("intervals")}

def get_running_form(data, person):
    """Raw material for estimating a 5k: every logged run, the person's Garmin HR zones,
    Garmin's race predictions, and whatever estimate is currently on their Home tab."""
    entries = list(_person_entries(data, person))
    runs = [r for r in (_run_row(l, e) for l, e in entries if _is_run_entry(e)) if r]
    runs.sort(key=lambda r: r.get("date") or "")
    # Interval / speed work: not distance+time entries, so they're not "runs", but they
    # are the hard efforts a 5k estimate most needs. Values are passed through verbatim
    # under the person's own column names - see INTERVAL_UNITS_WARNING.
    intervals = [r for r in (_interval_row(l, e) for l, e in entries if not _is_run_entry(e)) if r]
    intervals.sort(key=lambda r: r.get("date") or "")
    preds = (data.get("racePredictions") or {}).get(person) or {}
    return {
        "person": person,
        "runs": runs,
        "run_count": len(runs),
        "interval_sessions": intervals,
        "actual_structure_note": ACTUAL_STRUCTURE_NOTE,
        "interval_units_warning": INTERVAL_UNITS_WARNING,
        "hr_zones": (data.get("hrZones") or {}).get(person) or None,
        "garmin_race_predictions_sec": {k: v for k, v in preds.items() if k in RACE_KEYS} or None,
        "garmin_predictions_updated": preds.get("updated"),
        "current_estimate": ((data.get("coaching") or {}).get(person) or {}).get("fiveK"),
    }

# A suggestion's life: "proposed" (the coach raised it, the owner hasn't looked yet)
# -> "open" (approved, so the dev chat should action it) -> "done". "declined"
# is the other terminal state, and it is not the same as "done": it means he said no,
# so the coach can see that and not raise it again.
SUGGESTION_TERMINAL = ("done", "declined")

def get_suggestions(data, include_done=False, include_proposed=False):
    """The dev backlog. `proposed` items are withheld by default, which is the whole
    point of letting the coach raise things: the owner approves them in the app first, and
    only then do they become work. Pass include_proposed to see what's waiting on them."""
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
    """Raise an app/tracker improvement for the owner to approve, from the coaching chat.

    This is for things noticed while looking at the data that the APP should do
    differently - not training advice, which belongs in write_coaching. It lands in the
    same backlog the athletes type into, but as `status: "proposed"`, so it does not
    reach the dev chat until the owner has approved it in the gear menu."""
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
    """Top set per session over time, with the RPE that produced it where they gave
    one. Scored through _set_scorer, so a bodyweight or assisted movement trends by
    what it actually loaded rather than by the number typed - otherwise an assisted
    pull-up appears to go backwards as it improves.

    **Read `rpe` alongside `top`, not after it.** The weight alone cannot tell you
    whether to add load: the same number can mean opposite things. A squat that went
    from a lower weight at a high RPE to a higher weight at a lower RPE is more weight
    for less effort, which is the clearest possible case for adding more. A twist that
    sat at one weight across several sessions while the RPE fell says the load stopped
    being a stimulus rather than that the athlete stalled. Same weight at a rising RPE means the
    opposite again, and is the one pattern worth acting on quickly.

    They do not rate every exercise - only 26 of 59 sessions carry any RPE - so a
    point with no `rpe` key means it was not given, never that it was easy.
    """
    pts = []
    for l in _person_logs(data, person):
        for e in l.get("entries", []):
            if e.get("name") != exercise:
                continue
            warm = set(e.get("warmup") or [])
            score = _set_scorer(data, e, person, l.get("date"), l.get("sessionKey"))
            vals = []
            for ri, r in enumerate(e.get("rows", [])):
                if ri in warm or not r:
                    continue
                v = score(r[0])
                if v is not None:
                    vals.append(v)
            if vals:
                pt = {"date": l.get("date"), "top": round(max(vals), 1)}
                # Per-exercise, as the app collects it: one rating for the card, not
                # per set. Omitted entirely when absent, so "no rpe" cannot be
                # misread as a low one.
                rpe = e.get("rpe")
                if rpe not in (None, "", []):
                    try:
                        pt["rpe"] = float(rpe) if isinstance(rpe, str) else rpe
                    except (TypeError, ValueError):
                        pt["rpe"] = rpe
                # Done on a Smith machine. Present only when ticked, and it does not
                # split the trend: the load is the same either way, so this
                # annotates a point rather than forking the history. It is here so
                # nobody has to be asked to write it in the Notes.
                if e.get("smith"):
                    pt["smith"] = True
                pts.append(pt)
    pts.sort(key=lambda p: p["date"])
    return pts

def get_progression(data, person):
    """The progression rule's answer for each weight x reps exercise in `person`'s program,
    with the coach's target where one still applies. `steps_to_confirm` lists the exercises
    that apply but have no known step yet."""
    if person not in (data.get("people") or []):
        return {"error": f"No person named {person!r}.", "people": data.get("people") or []}
    out = progression.report(data, person)
    if not progression.coach_on(data, person):
        out["coach_off"] = _coach_off(person)
    out["steps_to_confirm"] = [r["exercise"] for r in out["exercises"]
                               if r["status"] in ("hold", "unsure") and r.get("step") is None]
    return out

# ---------------------------------------------------------------- coach memory
# Per person, the coach keeps two files next to the coaching log, in the same private repo:
#   coach/<name>/profile.md    current truth, replaced as a whole
#   coach/<name>/decisions.md  append-only, with an index of active and due decisions on top
# and the open questions in data.json (coachQuestions[person]) so the app can show and answer them.
# The method is docs/methods/coaching-behaviour-method.md.
def _coach_path(person, name):
    log = _log_cfg()[2]
    return (log.rsplit("/", 1)[0] + "/" if "/" in log else "") + f"coach/{person}/{name}"

def _text_read_with_sha(path):
    """A file's text as ({"text", "exists"}, sha, url, token). A missing file is a first write."""
    repo, token, _ = _github_cfg()
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    try:
        j = _gh_request(url, token)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"text": "", "exists": False}, None, url, token
        raise
    return {"text": base64.b64decode(j["content"]).decode("utf-8"), "exists": True}, j["sha"], url, token

def _text_write(box, sha, url, token, message):
    body = {"message": message, "content": base64.b64encode(box["text"].encode("utf-8")).decode("ascii")}
    if sha:
        body["sha"] = sha
    return _gh_request(url, token, body)

def _text_io(path):
    """The read, write and conflict codes that make _github_update work on a text file. 422 is
    what GitHub answers when two writers both try to create the same file."""
    return {"read": lambda: _text_read_with_sha(path), "write": _text_write, "conflicts": (409, 412, 422)}

def _person_named(data, person):
    """The person's exact name from data.json (case-insensitive match), or None."""
    return next((p for p in data.get("people") or []
                 if p and str(p).strip().lower() == str(person).strip().lower() and "/" not in p and ".." not in p), None)

def _unknown_person(data, person):
    return {"error": f"No person named {person!r}.", "people": [p for p in data.get("people") or [] if p]}

def _line(value):
    return re.sub(r"\s+", " ", str(value if value is not None else "")).strip()

def _valid_date(text):
    try:
        datetime.date.fromisoformat(str(text))
        return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(text)))
    except ValueError:
        return False

def _in_days(days):
    return (datetime.date.today() + datetime.timedelta(days=days)).isoformat()

def _numbered_id(prefix, taken):
    n = 1
    while f"{prefix}-{n:02d}" in taken:
        n += 1
    return f"{prefix}-{n:02d}"

MAX_PROFILE_CHARS = 60000

def get_coach_profile(data, person):
    name = _person_named(data, person)
    if not name:
        return _unknown_person(data, person)
    box = _text_read_with_sha(_coach_path(name, "profile.md"))[0]
    return {"person": name, "exists": box["exists"], "text": box["text"]}

def set_coach_profile(person, text):
    """Replace coach/<person>/profile.md with `text`."""
    data = load_data()
    name = _person_named(data, person)
    if not name:
        return {"ok": False, **_unknown_person(data, person)}
    text = str(text or "").replace("\r\n", "\n").strip() + "\n"
    if len(text) < 20 or len(text) > MAX_PROFILE_CHARS:
        return {"ok": False, "error": f"The profile must be between 20 and {MAX_PROFILE_CHARS} characters."}
    def mutate(box):
        replaced = box["text"] if box["exists"] else None
        box["text"], box["exists"] = text, True
        return {"person": name, "path": _coach_path(name, "profile.md"), "chars": len(text), "replaced": replaced is not None}
    return _write(mutate, {}, f"Coach profile: {name}",
                  "Saved. It replaced the whole file, so read it back (coach_profile) to check it.",
                  **_text_io(_coach_path(name, "profile.md")))

# Decisions: one "### <id>" block per decision, "- field: value" lines, then dated review lines.
DECISION_STATUSES = ("proposed", "approved", "applied", "declined", "superseded", "reviewed")
ACTIVE_DECISION_STATUSES = ("proposed", "approved", "applied")
DECISION_VALUES = {
    "agreement": ("agreed", "agreed_with_changes", "pushed_back", "declined", "no_response"),
    "implementation": ("not_due", "completed", "partly_completed", "not_completed", "unknown"),
    "satisfaction": ("liked", "disliked", "mixed", "neutral", "not_asked"),
    "outcome": ("pending", "helpful", "unhelpful", "mixed", "uncertain", "not_yet_evaluable"),
    "status": DECISION_STATUSES,
}
DECISION_FIELDS = ("date", "status", "scope", "authority", "rule", "before", "after", "reason", "expected", "watch",
                   "exposure_needed", "review_due", "agreement", "implementation", "satisfaction", "response_quote",
                   "outcome", "next_action", "supersedes", "superseded_by", "linked_questions", "profile_update")
ENTRIES_HEADING = "## Entries"

def _decision_block(decision_id, fields, reviews, extra=()):
    lines = [f"### {decision_id}"]
    ordered = [k for k in DECISION_FIELDS if k in fields] + [k for k in fields if k not in DECISION_FIELDS]
    lines += [f"- {k}: {fields[k]}" for k in ordered if fields[k] != ""]
    lines += list(extra)
    if reviews:
        lines += ["- reviews:"] + [f"  - {r}" for r in reviews]
    return "\n".join(lines) + "\n"

def _parse_decision_block(block):
    """(id, fields, reviews, extra) - extra keeps any line that is not a field, so a hand edit survives."""
    lines = block.rstrip().split("\n")
    fields, reviews, extra, in_reviews = {}, [], [], False
    for line in lines[1:]:
        if line.startswith("- reviews:"):
            in_reviews = True
        elif in_reviews and line.startswith("  - "):
            reviews.append(line[4:])
        elif re.match(r"- [a-z_]+:", line):
            key, _, value = line[2:].partition(":")
            fields[key], in_reviews = value.strip(), False
        elif line.strip():
            extra.append(line)
    return lines[0][4:].strip(), fields, reviews, extra

def _split_decisions(text):
    head, sep, body = text.partition(ENTRIES_HEADING + "\n")
    if text.strip() and not sep:
        return None
    return [b for b in re.split(r"(?m)^(?=### )", body) if b.strip()]

def _decision_index(blocks):
    today = _today()
    active, due = [], []
    for decision_id, f, _, _ in map(_parse_decision_block, blocks):
        if f.get("status") in ACTIVE_DECISION_STATUSES:
            when = f.get("review_due") or ""
            row = f"- {decision_id} | {f.get('status')} | {f.get('scope', '')} | " + (f"review due {when}" if when else "no review date")
            active.append((when or "9999", row))
            if when and when <= today:
                due.append((when, row))
    rows = lambda items: [r for _, r in sorted(items)] or ["- none"]
    return {"active": rows(active), "due": rows(due), "today": today}

def _decisions_text(person, blocks):
    index = _decision_index(blocks)
    return "\n".join([
        f"# Decisions: {person}", "",
        "Append-only. New decisions go at the end. A review adds dated lines and sets the response fields.",
        "The index is rebuilt on every write. Method: docs/methods/coaching-behaviour-method.md.", "",
        "## Index", "", f"Active (proposed, approved, applied). Today is {index['today']}.", "",
        *index["active"], "", "Due for review (review date is today or earlier):", "", *index["due"], "",
        ENTRIES_HEADING, "", "\n".join(b.rstrip() + "\n" for b in blocks)])

def _bad_decision_value(fields):
    for key, allowed in DECISION_VALUES.items():
        if key in fields and fields[key] not in allowed:
            return f"{key} must be one of {', '.join(allowed)}."
    for key in ("review_due",):
        if fields.get(key) and not _valid_date(fields[key]):
            return f"{key} must be a date like 2026-11-16."
    return None

def get_coach_decisions(data, person):
    name = _person_named(data, person)
    if not name:
        return _unknown_person(data, person)
    box = _text_read_with_sha(_coach_path(name, "decisions.md"))[0]
    blocks = _split_decisions(box["text"]) or []
    return {"person": name, "exists": box["exists"], "index": _decision_index(blocks), "text": box["text"]}

def add_decision(person, scope, before, after, reason, expected, review_due, authority="", status="applied",
                 rule="", watch="", exposure_needed="", agreement="no_response", implementation="not_due",
                 satisfaction="not_asked", response_quote="", supersedes="", linked_questions=None,
                 profile_update="", decision_id=""):
    """Append one decision to coach/<person>/decisions.md and rebuild the index."""
    data = load_data()
    name = _person_named(data, person)
    if not name:
        return {"ok": False, **_unknown_person(data, person)}
    fields = {"date": _today(), "status": status, "scope": scope, "authority": authority, "rule": rule,
              "before": before, "after": after, "reason": reason, "expected": expected, "watch": watch,
              "exposure_needed": exposure_needed, "review_due": review_due, "agreement": agreement,
              "implementation": implementation, "satisfaction": satisfaction, "response_quote": response_quote,
              "outcome": "pending", "supersedes": supersedes,
              "linked_questions": ", ".join(linked_questions or []), "profile_update": profile_update}
    fields = {k: _line(v) for k, v in fields.items()}
    missing = [k for k in ("scope", "before", "after", "reason", "expected", "review_due") if not fields[k]]
    error = f"Needs a value for: {', '.join(missing)}." if missing else _bad_decision_value(fields)
    if not error and decision_id and not re.fullmatch(r"D-[A-Za-z0-9-]+", decision_id):
        error = "decision_id looks like D-20261102-01."
    if error:
        return {"ok": False, "error": error}
    failed = {}
    def mutate(box):
        blocks = _split_decisions(box["text"])
        if blocks is None:
            failed["error"] = "decisions.md does not follow the entry format. Fix it by hand before adding to it."
            return None
        parsed = [_parse_decision_block(b) for b in blocks]
        taken = {p[0] for p in parsed}
        new_id = decision_id or _numbered_id("D-" + _today().replace("-", ""), taken)
        if new_id in taken:
            failed["error"] = f"{new_id} already exists. Decisions are append-only: use review_coach_decision."
            return None
        if fields["supersedes"]:
            old = next((i for i, p in enumerate(parsed) if p[0] == fields["supersedes"]), None)
            if old is None:
                failed["error"] = f"supersedes {fields['supersedes']} is not in the log."
                return None
            did, f, reviews, extra = parsed[old]
            blocks[old] = _decision_block(did, dict(f, status="superseded", superseded_by=new_id), reviews, extra)
        blocks.append(_decision_block(new_id, fields, []))
        box["text"] = _decisions_text(name, blocks)
        return {"person": name, "decision_id": new_id, "index": _decision_index(blocks)}
    return _write(mutate, failed, f"Coach decision: {name}", "Saved to decisions.md. Read it back to check the index.",
                  **_text_io(_coach_path(name, "decisions.md")))

def review_decision(person, decision_id, implementation=None, agreement=None, satisfaction=None,
                    response_quote=None, status=None, outcome=None, observed="", next_action=None,
                    next_review=None, uncertainty="", profile_update=None):
    """Set the response and review fields on an existing decision, add a dated review line and
    rebuild the index. The change, reason and expected result are never touched."""
    data = load_data()
    name = _person_named(data, person)
    if not name:
        return {"ok": False, **_unknown_person(data, person)}
    given = {"implementation": implementation, "agreement": agreement, "satisfaction": satisfaction,
             "response_quote": response_quote, "status": status, "outcome": outcome,
             "next_action": next_action, "review_due": next_review, "profile_update": profile_update}
    given = {k: _line(v) for k, v in given.items() if v is not None}
    if not given and not _line(observed):
        return {"ok": False, "error": "Nothing to change. Pass at least one field or `observed`."}
    error = _bad_decision_value(given)
    if error:
        return {"ok": False, "error": error}
    failed = {}
    def mutate(box):
        blocks = _split_decisions(box["text"]) or []
        at = next((i for i, b in enumerate(blocks) if _parse_decision_block(b)[0] == decision_id), None)
        if at is None:
            failed["error"] = f"No decision {decision_id!r} in decisions.md."
            return None
        did, fields, reviews, extra = _parse_decision_block(blocks[at])
        fields = dict(fields)
        fields.update(given)
        if "outcome" in given and "status" not in given and "review_due" not in given and fields.get("status") in ACTIVE_DECISION_STATUSES:
            fields["status"] = "reviewed"
        line = [_today()] + [f"{k.replace('_', ' ')} {v}" for k, v in given.items() if k != "profile_update"]
        for label, text in (("observed", observed), ("uncertainty", uncertainty)):
            if _line(text):
                line.append(f"{label}: {_line(text)}")
        blocks[at] = _decision_block(did, fields, reviews + [" | ".join(line)], extra)
        box["text"] = _decisions_text(name, blocks)
        return {"person": name, "decision_id": did, "status": fields.get("status"), "index": _decision_index(blocks)}
    return _write(mutate, failed, f"Coach decision review: {name}", "Saved to decisions.md. Read it back to check the index.",
                  **_text_io(_coach_path(name, "decisions.md")))

# Questions: data.json coachQuestions[person] = [{id, question, why, priority, decision, askedAt,
# nextFollowUp, reminders, answer, answeredAt, status, updatedAt, closedReason?}]. `updatedAt` is ms
# since the epoch, the same stamp the app writes, because the app merges each question by id and the
# newest stamp wins.
QUESTION_PRIORITIES = ("safety", "blocking", "routine", "optional")
MAX_ROUTINE_QUESTIONS = 3

def _now_ms():
    return int(time.time() * 1000)

def _normal(text):
    return re.sub(r"\W+", " ", str(text)).strip().lower()

def get_coach_questions(data, person, status="open"):
    name = _person_named(data, person)
    if not name:
        return _unknown_person(data, person)
    if status not in ("open", "answered", "closed", "all"):
        return {"ok": False, "error": "status must be open, answered, closed or all."}
    today = _today()
    rows = [dict(q, due=q.get("status") == "open" and bool(q.get("nextFollowUp")) and q["nextFollowUp"] <= today)
            for q in (data.get("coachQuestions") or {}).get(name) or []
            if isinstance(q, dict) and status in ("all", q.get("status"))]
    return {"person": name, "status": status, "questions": rows}

def _question_edit(person, question_id, change, commit, message, statuses=("open", "answered"), asks=False):
    """Apply `change(q, failed)` to one open or answered question of the person, stamping updatedAt.
    `asks` is for a change that puts the question in front of them again, which the switch refuses."""
    failed = {}
    def mutate(data):
        name = _person_named(data, person)
        if not name:
            failed.update(_unknown_person(data, person))
            return None
        if asks and not progression.coach_on(data, name):
            failed["error"] = _coach_off(name)
            return None
        q = next((x for x in (data.get("coachQuestions") or {}).get(name) or []
                  if isinstance(x, dict) and x.get("id") == question_id), None)
        if q is None:
            failed["error"] = f"{name} has no question {question_id!r}."
            return None
        if q.get("status") not in statuses:
            failed["error"] = f"{question_id} is {q.get('status')}, so this does not apply."
            return None
        change(q, failed)
        if failed:
            return None
        q["updatedAt"] = _now_ms()
        return {"person": name, "question": dict(q)}
    return _write(mutate, failed, commit.format(person=person), message)

def add_question(person, question, why, priority="routine", decision="", next_follow_up="", question_id=""):
    question, why = _line(question), _line(why)
    if not question or not why:
        return {"ok": False, "error": "A question needs its text and why the answer matters."}
    if priority not in QUESTION_PRIORITIES:
        return {"ok": False, "error": f"priority must be one of {', '.join(QUESTION_PRIORITIES)}."}
    if next_follow_up and not _valid_date(next_follow_up):
        return {"ok": False, "error": "next_follow_up must be a date like 2026-11-09."}
    failed = {}
    def mutate(data):
        name = _person_named(data, person)
        if not name:
            failed.update(_unknown_person(data, person))
            return None
        if not progression.coach_on(data, name):
            failed["error"] = _coach_off(name)
            return None
        mine = (data.get("coachQuestions") or {}).get(name) or []
        mine = [q for q in mine if isinstance(q, dict)]
        same = next((q for q in mine if q.get("status") != "closed" and _normal(q.get("question")) == _normal(question)), None)
        if same:
            failed["error"] = f"Already asked as {same['id']} ({same['status']}). Remind or close it instead."
            return None
        new_id = question_id or _numbered_id("Q-" + _today().replace("-", ""), {q.get("id") for q in mine})
        if any(q.get("id") == new_id for q in mine):
            failed["error"] = f"{new_id} already exists."
            return None
        rec = {"id": new_id, "question": question, "why": why, "priority": priority, "decision": _line(decision),
               "askedAt": _today(), "nextFollowUp": next_follow_up or _in_days(7), "reminders": 0, "answer": "",
               "answeredAt": "", "status": "open", "updatedAt": _now_ms()}
        data.setdefault("coachQuestions", {}).setdefault(name, []).append(rec)
        routine = [q for q in mine + [rec] if q.get("status") == "open" and q.get("priority") in ("routine", "optional")]
        out = {"person": name, "question": rec}
        if len(routine) > MAX_ROUTINE_QUESTIONS:
            out["warning"] = f"{len(routine)} routine or optional questions are open. Ask at most {MAX_ROUTINE_QUESTIONS} in one review."
        return out
    return _write(mutate, failed, f"Coach question for {person}", "Saved. It shows on their Home tab after Sync now.")

def remind_question(person, question_id, next_follow_up=""):
    if next_follow_up and not _valid_date(next_follow_up):
        return {"ok": False, "error": "next_follow_up must be a date like 2026-11-09."}
    def change(q, failed):
        q["reminders"] = int(q.get("reminders") or 0) + 1
        q["nextFollowUp"] = next_follow_up or _in_days(7)
    return _question_edit(person, question_id, change, "Coach question reminder: {person}",
                          "Saved. The reminder count went up by one.", statuses=("open",), asks=True)

def close_question(person, question_id, reason):
    reason = _line(reason)
    if not reason:
        return {"ok": False, "error": "Say why it is closed: answered and acted on, declined, duplicate, superseded or no longer relevant."}
    def change(q, failed):
        q["status"], q["closedReason"] = "closed", reason
    return _question_edit(person, question_id, change, "Coach question closed: {person}",
                          "Saved. It no longer shows in the app.")

# ---------------------------------------------------------------- MCP wiring
def _register(mcp):
    @mcp.tool()
    def people() -> str:
        """List both people with their goals, latest bodyweight and session count, and `coach_on`:
        false when they turned Garmin and coach off in the app, in which case write nothing for
        them (notes, targets, questions) - the write tools refuse."""
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
    def measurements(person: str) -> str:
        """A person's tape measurements over time (date, cm per site: neck, shoulders, chest,
        waist, hips, and armL/armR, forearmL/forearmR, thighL/thighR, calfL/calfR). Taken
        about every 4 weeks; a site left out on a date was not measured."""
        return json.dumps(get_measurements(load_data(), person), indent=2)

    @mcp.tool()
    def nutrition(person: str, days: int = 14) -> str:
        """A person's food for the last `days` days (default 14), from the meals the Home Hub
        captures: per day kcal, protein, carbs, fat and fibre (grams), meal count and how many
        were `estimated` (a free-text guess, less reliable than a barcode). A day with
        `logged: false` had nothing captured, which is not the same as eating nothing. Fibre
        is null on a day with none recorded (meals before 26 Oct 2026 have none), and meals
        deleted in the hub are left out. The summary gives averages over logged days against
        the person's kcal and protein targets."""
        return json.dumps(get_nutrition(load_data(), person, days), indent=2)

    @mcp.tool()
    def progress(person: str, exercise: str) -> str:
        """Top-set weight over time for one exercise, for tracking progression."""
        return json.dumps(get_progress(load_data(), person, exercise), indent=2)

    @mcp.tool()
    def suggestions(include_done: bool = False, include_proposed: bool = False) -> str:
        """In-app improvement suggestions / bug reports the athletes logged. Each has id,
        person, date, text, status. Use for the app's dev backlog.

        Coach-raised items (`source: "coach"`) start as `status: "proposed"` and are NOT
        returned unless you pass include_proposed - the owner approves them in the app first,
        and approval is what turns one into work. `status: "declined"` means the owner said no:
        don't re-raise it and don't build it."""
        return json.dumps(get_suggestions(load_data(), include_done, include_proposed), indent=2)

    @mcp.tool()
    def propose_suggestion_tool(text: str, why: str = "", about: str = "") -> str:
        """Raise an improvement to the APP for the owner to approve - use this whenever a
        coaching note ends up mentioning something the tracker itself should do
        differently, so the idea reaches the dev chat instead of being buried in a note
        he has to remember. Training advice is not this: that goes in write_coaching.

        `text` is the change, phrased as the thing to do. `why` is the evidence from the
        data that prompted it. `about` optionally names the person or session it concerns.
        It lands as `proposed`, visible to the owner in the app's gear menu, and the dev chat
        cannot see it until it is approved. Identical text is not added twice, so re-running
        is safe and a declined idea won't come back."""
        return json.dumps(propose_suggestion(text, why, about), indent=2)

    @mcp.tool()
    def resolve_suggestion_tool(suggestion_id: str) -> str:
        """Mark a suggestion done (by id) once handled, so it drops off the app's pending list."""
        return json.dumps(resolve_suggestion(suggestion_id), indent=2)

    @mcp.tool()
    def coaching_history(person: str, limit: int = 10) -> str:
        """Past coaching you've written for a person (newest first) - each entry has a date
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
        """What the athletes SAY is holding each session back, in their own words.
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
    def program_changes(include_done: bool = False) -> str:
        """Program changes you have proposed and what became of them - `pending` is
        still waiting on a tick, `applied` was accepted, `declined` was refused. Check
        before proposing so you don't raise the same thing twice, and read a `declined`
        as a decision: don't work around it."""
        return json.dumps(get_program_changes(load_data(), include_done), indent=2)

    @mcp.tool()
    def write_program_change(session: str, exercise: str, why: str, sets: int | None = None,
                             target: str | None = None, add: dict | None = None,
                             remove: bool = False, after: str = "",
                             warmup: str | None = None,
                             move_after: str | None = None, rest_sec: int | None = None) -> str:
        """Propose ONE change to the program. It appears on that exercise in their
        Program tab with the reason and a tick, and the APP applies it when they accept
        - you are not waiting on a developer, and neither are they. This is how a set
        count or a target actually changes; a coaching note asking them to do 3 sets
        instead of 4 does not change what the app prescribes next week.

        `session` and `exercise` must be EXACT names. `why` is required and is shown on
        the card - they are being asked to accept a change to their training, so the
        reason has to stand on its own.

        Three kinds:
        * change numbers - pass `sets` and/or `target` ("Bench press", sets=3,
          target="3x5-8"). This is the common one.
        * add an exercise - pass `add` as the definition
          {"target": "3x8-10", "sets": 3, "cols": ["Weight (kg)", "Reps"],
           "load": "assist"} and optionally `after` to place it after a
          named exercise. Place work that matters EARLY: the deadlift sat last in
          Lower 1 and went unlogged for months.
        * remove an exercise - pass remove=True. Their past logs of it are kept; it
          just stops being prescribed. Use sparingly, and say what replaces it.

        Keep an exercise NAME identical to one already used if you want its history to
        continue - records, the Last column and the progress chart all key on the name.
        That is what makes the same movement in two sessions one trend rather than two.

        Refuses a duplicate of a change already waiting, and refuses to edit or remove
        something that isn't in that session. One change per call."""
        return json.dumps(propose_program_change(session, exercise, why, sets, target,
                                                 add, remove, after, warmup,
                                                 move_after, rest_sec), indent=2)

    @mcp.tool()
    def write_log_entry(session_id: str, exercise: str, rows: list, why: str = "") -> str:
        """Correct the rows of one exercise on one already-logged session - use it when
        the Garmin sync filled a run entry with the wrong thing, not to tidy numbers a
        person typed.

        `session_id` is the log's id (from recent_sessions), `exercise` its EXACT name,
        `rows` the full replacement list, each row matching that entry's columns - for a
        run that is [distance_km, "m:ss", "m:ss pace", avg_hr]. Read the session first.

        The case it exists for: a Garmin activity holds more than the session it was
        matched to, so the automatic fill describes the wrong work. A run entry once
        filled from three treadmill laps, one of which was an incline WALK, made the app
        report a far slower running pace and use it for the best pace and the Last column. The sync now prefers per-rep detail where it exists, but
        when it still gets it wrong, fix it here.

        Say what you changed and why in `why` - it is kept on the session alongside the
        previous rows, which also come back in the response so a bad edit can be undone.
        A corrected entry is never silently overwritten by a later sync.

        A session a person has edited in the app carries `editedAt` (ms, null once they undid
        it). Its sets were changed by the person, so read them as typed, not as a sync's guess."""
        return json.dumps(set_log_entry(session_id, exercise, rows, why), indent=2)

    @mcp.tool()
    def session_notes(session: str = "") -> str:
        """The 🎛 treadmill program, ⌚ recording, 🔥 warm-up and 🧊 cool-down notes on each
        session of the program, as they currently read. Omit `session` for all of them. ALWAYS call this before
        write_session_notes: the notes are long, hand-written mobility blocks and a write
        replaces them by default."""
        return json.dumps(get_session_notes(load_data(), session), indent=2)

    @mcp.tool()
    def write_session_notes(session: str, warmup: str | None = None,
                            cooldown: str | None = None, append: bool = False,
                            recording: str | None = None, setup: str | None = None,
                            garmin: str | None = None) -> str:
        """Rewrite a session's warm-up and/or cool-down note - use this when the fix is a
        change to what they do either side of the exercises, e.g. adding calf and ankle work
        to a cardio warm-up because someone's shins keep flaring, or dropping a stretch that
        aggravates a hip. `session` must be an EXACT session name.

        Unlike everything else you write, this is NOT per person: the note lives on the
        program and BOTH of them see the same text. So a note addressed to one of them does
        NOT belong here - put it in write_coaching(by_session=...), which is per person.
        The rule: no person-specific lines in a warm-up or
        cool-down. See docs/methods/coaching-method.md, Part 3, "Writing warm-ups and cool-downs" -
        it also settles what a cool-down is (stretches and breathing, never strength work),
        that decision rules and traffic lights do not go in a warm-up, and that a stated
        duration is computed from the list rather than guessed. Read it before writing one,
        and do not write back anything that section says was removed.

        KEEP THE REST OF THE SESSION IN STEP. `garmin`, `setup`, `recording`, `warmup` and
        `cooldown` describe one session between them, so changing any of them can leave the
        others lying. If the block count or the structure moves, walk all five and fix every
        reference: block numbers, lap counts, totals, "blocks 1-5", "when block 21 finishes".
        A recording note pointing at a block that no longer exists is worse than no note,
        because it is followed. This is how a recording note ended up telling someone to
        end at a block that did not exist in the session.

        Call `session_notes(session)` FIRST and work from what's there. These notes are long
        and hand-written, and passing `warmup` REPLACES the whole thing - months of mobility
        work included. For adding a line, pass `append=True` and just the new paragraph.
        Omit a field to leave it untouched; pass "" to clear it. The previous text comes back
        in the response, so a bad write can be undone by writing it back.

        `garmin` is the watch workout - the session built once on Garmin Connect and sent to
        the watch, which is how it gets programmed outdoors. `setup` is the treadmill program,
        the indoor fallback, as numbered time + speed blocks to key in before starting. `recording` is how to record the session on a Garmin (start,
        laps, end, what to report back). Keep it out of `warmup` - it is its own collapsed block
        above the warm-up, so that the warm-up isn't buried and so either can be rewritten
        without disturbing the other. For a person's OWN run session, use write_run instead.

        It reaches both phones on their next Sync now (a phone mid-workout takes it after).
        Program STRUCTURE - sets, reps, targets, which exercises - is not yours to change,
        with ONE exception: each person's own run session, which is yours (see write_run).
        Everywhere else, raise it with propose_suggestion_tool for the owner to approve."""
        return json.dumps(set_session_notes(session, warmup, cooldown, append, recording,
                                           setup, garmin), indent=2)

    @mcp.tool()
    def create_session(name: str, day: str = "Optional", exercises: list | None = None,
                       person: str = "", warmup: str = "", cooldown: str = "",
                       setup: str = "", recording: str = "", garmin: str = "") -> str:
        """Add a NEW session to the program - a whole training day that does not exist yet.

        Use it when the work genuinely does not belong in any current session: a mobility
        day, an assessment, a second cardio slot. To change a session that already exists,
        use write_session_notes for the notes and write_program_change for the exercises;
        this refuses a duplicate name.

        `name` must be unique and is how everything finds the session afterwards - logs are
        stored by session name, the next-cardio card matches by name, and every lookup
        resolves by name. `day` is a weekday or "Optional" (which is right whenever it has
        no fixed slot yet). `person` scopes it to one of them, the way each run session is;
        leave it empty and both see it.

        `exercises` is the list, in order, each
          {"name": str, "target": str, "sets": int, "cols": [2 or 3 column names],
           "warmup": optional str - the warm-up SETS for this lift}
        No `notes`: machine settings belong to each person and you cannot write them.
        Columns decide how the app treats it. A Distance + Time pair makes it a run. Two
        free-text columns like ["Min", "Notes"] make it a plain timed block. A first column
        of "cm" makes it a flexibility test: it charts in Progress as a ladder rung and
        stays out of records, volume and the Lifts chart. Add "betterWhen": "higher" on a
        test where a bigger number is the better one, like ankle range.

        Reuse an exercise NAME that already exists if you want its history to continue -
        records, the Last column and the progress chart all key on the name.

        The notes follow the same rules as write_session_notes: no person-specific lines
        (those go in write_coaching), no decision rules in a warm-up, and a cool-down is
        stretches and breathing rather than strength work. See docs/methods/coaching-method.md,
        Part 3. Adding a session is structural, so unless the owner has asked for it directly,
        raise it with propose_suggestion_tool first rather than creating it unannounced."""
        return json.dumps(add_session(name, day, exercises, person, warmup,
                                      cooldown, setup, recording, garmin), indent=2)

    @mcp.tool()
    def run_session(person: str, which: str = "") -> str:
        """`person`'s own run session as it currently stands - every exercise, target, set
        count, column and note, exactly as their phone will draw it. ALWAYS call this before
        write_run: a write replaces the exercise list outright.

        `which` picks between run sessions when a person owns more than one - they each have
        an easy run and a quality run. It matches the session key, its DAY, or any distinctive
        part of the name, case-insensitively, so "tuesday", "easy" or "quality" all work. Day
        is the most stable handle, since a session gets renamed when its content changes shape.
        Omit it and the error lists what they own."""
        return json.dumps(get_run(load_data(), person, which), indent=2)

    @mcp.tool()
    def withdraw_program_change(change_id: str) -> str:
        """Take back a PENDING program change you got wrong, before anyone acts on it.

        Use it when you proposed the wrong thing, or want to replace a proposal:
        propose_program_change refuses a duplicate on (session, exercise, op) while one
        is pending, so a bad one has to be withdrawn before a corrected one can be
        raised. Only `pending` can be withdrawn - once they have ticked or declined it,
        the decision is theirs."""
        return json.dumps(withdraw_program_change_tool(change_id), indent=2)

    @mcp.tool()
    def program_session(name: str = "") -> str:
        """One PROGRAMMED session in full - every exercise in order with its target, sets,
        columns, warm-up ramp (`warmup`) and load type, each person's machine settings
        (`machine_settings`, read-only), plus the
        session's day, who owns it and its four note fields.

        **Call this before proposing any program change.** It is what is PRESCRIBED, where
        `session(session_id)` is what was LOGGED and `run_session` only covers the run
        sessions. Without it there is no way to see a lifting session's exercises, and
        changing one blind is how you retire the wrong row and leave a session with no row
        at all.

        `name` matches the session's name, its key or its day, case-insensitively, and falls
        back to a distinctive fragment. Omit it and the error lists every session."""
        return json.dumps(get_program_session(load_data(), name), indent=2)

    @mcp.tool()
    def write_run(person: str, exercises: list | None = None, why: str = "",
                  name: str | None = None, day: str | None = None,
                  warmup: str | None = None, cooldown: str | None = None,
                  recording: str | None = None, setup: str | None = None,
                  which: str = "", garmin: str | None = None) -> str:
        """Re-prescribe ONE of `person`'s run sessions. This session is yours: the explicit
        instruction is that the coach decides the optimal run each week from
        the data, and is NOT restricted to the formats used so far. Rep sessions, tempo,
        progression runs, fartlek, hills, a straight easy run, run-walk, a compromised
        run off a lifting station - if the data says it, prescribe it. Design it properly
        from the evidence rather than nudging last week's numbers.

        `which` says WHICH of their run sessions to write, because they each own two - an
        easy run and a quality run, on different days. It matches the session key, its DAY, or
        any distinctive part of the name, case-insensitively ("tuesday", "easy", "quality").
        Prefer the day: it survives a rename, and renaming a run session is normal when its
        content changes shape. It is required whenever more than one session belongs to them,
        and the write replaces only that one.
        The two are prescribed separately and should not be made the same shape: with two runs
        a week the second one is the EASY one, not a second quality session.

        Read FIRST, every time: `run_session(person, which)` (what's there now), `running_form(person)`
        (every logged run, rep by rep off the watch - fade, drift, HR recovery, time in zone),
        `limiters(person)` (their own account of what's holding the session back - it wins over
        your reading of the numbers), `goals(person)`, and `wellness`/`recent_sessions` for what
        else is in the week. The stated main goal is the one in `goals(person)`, so a repeat is
        usually the right unit when it asks for race-style fitness.

        `exercises` REPLACES the whole list, so pass every exercise you want them to do,
        in order. Each is
          {"name": str, "target": str, "sets": int, "cols": [2 or 3 column names],
           "garminRun": optional bool,
           "warmup": optional str - the warm-up SETS for this lift,
           "groupId": optional str to circuit two together}
        Columns decide how the app treats it: a Distance + Time pair (e.g.
        ["Distance (km)", "Time (mm:ss)", "Pace"]) makes it a run - pace computes itself,
        `sets` draws a row per rep, and Garmin fills blank rows with the real splits. Two
        free-text columns like ["Min", "Notes"] make it a plain timed block. Anything else
        the watch records but that isn't distance+time (a speed-based interval, say) should
        set garminRun=true so heart rate still attaches.

        `move_after` REORDERS an existing exercise: pass the name of the one it should
        follow, or "" to move it to the front. Order is why work gets missed - an
        exercise at the end of a session goes unlogged review after review, and the same
        is true of anything behind a session that overruns. Place
        what matters early. A move changes nothing else, so it is safe to raise
        alongside the real content decision rather than instead of it.

        `rest_sec` sets the suggested rest between sets, in seconds (150 = 2:30). The app
        shows it on the exercise and the rest bar counts against it, changing colour when
        it is reached; they approve it like any other change (14 Oct). Typical: 150-180 on
        the main lifts, 60-90 on accessories.

        `warmup` can be changed on an EXISTING exercise from 6 Oct - before that `edit`
        carried only `sets` and `target`, which made restoring a ramp impossible rather
        than merely undone. Machine settings (`notes`) cannot be changed by you at all:
        since 13 Oct they are each person's own, edited only by them in the app. Deliberately not
        "any field": `cols` decides how an exercise is scored and drawn, and changing it
        under a logged history is a different and worse thing. Call `program_session` first
        to see what is actually there.

        **`warmup` is the warm-up sets, and it understands percentages.** Write it
        like "bar x8, 50%x5, 75%x3" and the app resolves each % against that person's
        top set, rounded to 2.5kg - from what they have already typed into the exercise
        today, falling back to their last session. It is per exercise and separate from
        the session's warmupNote, which is mobility work.

        **It is silently dropped if you leave it out.** Passing `exercises` REPLACES the
        list, and an exercise with no `warmup` is written with an empty one - which is
        how every exercise ended up with none and why bench
        stopped suggesting warm-up weights. The feature was never broken; the data was
        overwritten by a rebuild. Read the session first and carry `warmup` through.

        **Which exercises get one: the main lifts, normally the first two of a session**
        A ramp earns its place on the heavy compound you build up to -
        bench, squat, deadlift, the shoulder press - and is noise on a lateral raise or a
        face pull. The warm-ups are currently MISSING across the whole program; putting
        them back on the first two exercises of each session is outstanding work.

        **Machine settings are not yours to write.** Since 13 Oct each person keeps their
        own (seat height, pins, cable height), by exercise name, and only they edit them in
        the app - `program_session` shows them read-only as `machine_settings`. Every cue,
        how-to and reason goes in `write_coaching`'s by_exercise note, which the app shows
        under the exercise. Some of those notes start with a "How to:" paragraph that was
        moved there from the old settings box on 13 Oct - the drill instructions and the
        assessment test protocols. KEEP that paragraph when you rewrite the note; it is the
        only copy, and the re-test in 6-8 weeks depends on it.

        Keep an exercise NAME stable if you want its trend: records, the Last column and the
        progress chart all key on the name, so a rep block called "Run reps" every week
        trends, while renaming it to "4x800m" starts a new and empty history. Put the
        prescription in `target` instead - that's what it's for.

        `garmin` and `setup` are the two ways the session gets PROGRAMMED before they start,
        so nothing has to be adjusted mid-run - which is the whole reason it is programmed
        rather than run to a card. They are separate fields and separate folded panels on
        the phone, because outdoors is the default and correcting a heart-rate band must not
        mean re-sending the belt program. Write BOTH.

        `garmin` is THE WATCH WORKOUT, and it is the one they will actually use. Garmin Connect
        -> Training & Planning -> Workouts -> Create a Workout -> Run (or Walk), written as a
        table of step / type / duration / target, then Send to Watch, then how to start it on
        the day. A structured workout laps automatically at every step change, which replaces
        hand-lapping entirely and is the fix both for reps that stretch and for laps that get
        forgotten. Use a Heart Rate target where HR is the point of the session; leave it at
        No Target where it is not, and say why. Warn about HR lag on short reps - the watch
        tells you to speed up for the first 45-60s of a rep when you are already running
        correctly, and chasing that arrow turns a threshold session into a 5k by rep three.

        `setup` is THE TREADMILL FALLBACK, for a morning too cold, wet or dark: the session as
        a numbered list of time + speed (+ incline where it matters) blocks. Their treadmills
        take time and speed only, in 5-second steps, with no distance target, so express every
        block that way rather than in metres, and say what to do if the belt runs out of its
        20 stages.

        Both cover the warm-up, the reps AND their recoveries, and the cool-down: each is the
        session end to end, and each says its own total. Rewrite whichever the change touches -
        a stale program is worse than none, because it is keyed in before anyone reads the rest.

        `recording` is how to record THIS session on the watch, and it is its own field
        on purpose - it is NOT warm-up content and must not be put in `warmup`. It shows as
        a separate collapsed block above the warm-up on their phone. Write it whenever you
        change the session's structure, because the lap points are meaningless against a
        different structure, and it is the only way you can read a mixed activity back: a
        warm-up, a time trial and an easy jog all sit in ONE Garmin recording, so the
        activity-level averages are worthless without knowing which lap holds which piece.
        Cover, in this order: whether it is one activity or several; whether they are running
        the Garmin workout from `garmin` (in which case the laps are automatic and pressing Lap
        by hand SPLITS a step and corrupts the read) or freestyle; where to press Start, each
        Lap, and End; what each lap will hold, written for whoever reads it back later;
        anything to TYPE in as well (typed data is never overwritten by the sync, so a
        treadmill-belt number beats a wrist estimate); and anything to report back, like a
        treadmill-vs-watch distance check. Because it is separate, rewriting it never
        touches the hand-written mobility work in `warmup`, and vice versa.

        KEEP ALL FIVE SHORT (the notes were slimmed and the run notes cut to match). Instructions only: steps and belt blocks as "- " lines, never a
        table aligned with spaces; a lap map as "- Lap 1 - ..." lines; one report-back line.
        No dated stories ("on 26 August..."), no "why" paragraphs - that reasoning goes in
        `why` or the summary. docs/methods/coaching-method.md Part 3 lists what was cut.

        `why` is the reason, in two to four short sentences, and you should always pass it: it becomes
        the coach note on that session, so they read it while they train, and it lands in
        the coaching history so the two of you can see whether the call worked.

        WHEN THE SESSION CHANGES, WALK ALL FIVE FIELDS BEFORE YOU FINISH. `garmin`, `setup`,
        `recording`, `warmup` and `cooldown` describe one session between them, and a change
        to the structure invalidates references scattered across the other four. Check every
        block number, lap count and total in each: "blocks 1-5", "when block 21 finishes",
        "that is 9 lap presses", "the whole session is 44:40 on the belt". Rewriting one of the
        two programs and leaving the rest is the standard failure - it is how a person ended up with a
        recording note telling them to end at a block past the end of the session, and a warm-up
        pointing at belt blocks that had moved to the bike. A stale note is worse than a
        missing one, because it gets followed.

        Guard rails: you can only write a session that BELONGS to that person, so you cannot
        touch the other one's run or any shared session. The original `Cardio: Endurance +
        Core` is kept as an always-available backup - never delete or repurpose it, it is
        what they fall back to. The full previous session comes back in the response; keep it
        if you might want to put it back. Reaches their phone on the next Sync now, never
        mid-workout."""
        return json.dumps(set_run(person, exercises, why, name, day, warmup, cooldown,
                                  recording, setup, which, garmin), indent=2)

    @mcp.tool()
    def progression(person: str) -> str:
        """What the progression rule says for each of `person`'s weight x reps exercises, from
        their logs. Read it before writing by_exercise notes or targets.

        Per exercise: `status` is progress (every working set hit the top of the rep range, so
        the target is one step up, or down for assisted), hold (same weight again), unsure (due
        to progress but the step is unknown, so the target stays and the app says "up one step"),
        zero (assisted at 0 assist, ready for load), none (nothing logged with a weight yet) or
        off (the rule does not cover it: timed, fixed reps, bodyweight at 0). `w` is the working
        weight of the latest session and `target` the weight the rule suggests next. `step` is
        the jump and `source` where it came from: line (a Step line in a session's setupNote),
        barbell or dumbbell (by exercise name), or ladder (learned from the weights both people
        logged). `streak` is the number of latest sessions at the same weight. `stalled` is true
        after three sessions at one weight with no rep gain. `coach` is your target for the
        exercise while it still applies (until the person logs it again).

        A stall is your call: the rule only flags it. Check sleep and food before a deload.
        `steps_to_confirm` lists exercises that apply but have no known step. Write one with
        write_machine_step when you are sure, and list the rest for the owner to confirm.
        A target that differs from `target` goes in write_coaching(targets=...) with a why.
        `coach_off` is present when the person turned Garmin and coach off in the app: write no
        target for them, and `coach` stays empty."""
        return json.dumps(get_progression(load_data(), person), indent=2)

    @mcp.tool()
    def write_machine_step(exercise: str, step: float | None, session: str | None = None) -> str:
        """Set the progression step for an exercise: the smallest weight jump the machine or
        dumbbell rack allows, in kg. It is written as one line, "Step: Seated row = 2.5", in a
        session's setupNote and touches no other text. Both people share it. Pass step null (or
        0) to remove the line.

        `exercise` must be an exact exercise name in the program. Without `session` every
        existing line for it is replaced and a missing one is added to the first session that has
        the exercise. With `session` only that session's note changes. Only write a step you
        are sure of (the owner said it, or the weights logged show it). When unsure, leave it and
        list the exercise under "Machine steps to confirm" in your summary. The previous note
        text comes back in the response."""
        return json.dumps(set_machine_step(exercise, step, session), indent=2)

    @mcp.tool()
    def write_coaching(person: str, overall: str = "", by_exercise: dict | None = None,
                       by_session: dict | None = None, five_k: dict | None = None,
                       next_cardio: dict | None = None,
                       session_swap: dict | None = None,
                       lowest_rung: dict | None = None,
                       targets: dict | None = None) -> str:
        """Push coaching to a person so it shows in their app (Home + Log) during workouts.
        `by_session` = {exact session name: focus note} shown on that session (Home shows
        today's; Log shows the open session's). Prefer this for session-level guidance.
        `by_exercise` = {exact exercise name: the next step on that exercise} shown on that
        exercise while they train. Give one per exercise you have advice on.
        **Keep every card to two to four SHORT sentences, one paragraph** (long cards
        bloated the session screen). The number, the reason from the last
        log, and what to do if it goes wrong - e.g. "102.5kg for 5x5 - last week's 100 moved
        well. If set 4 grinds, stop and repeat 102.5 next week." No recaps of older sessions,
        no app news, no reasoning essays; safety lines stay, one sentence each. A "How to:"
        paragraph is the only thing allowed beyond that.
        `overall` = an optional general note shown on every session, two sentences at most.
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
        name a session you actually want them doing. It is per person, so the two of them can get different numbers for the same session - read limiters(person)
        first, because the two of them are usually limited by different things. The card
        marks itself done once they log a cardio session, and the app returns to
        alternating on its own until you write a new one.
        `session_swap` = put a DIFFERENT session on one weekday, for one week, as
        {"session": "Mobility assessment", "day": "Wednesday",
         "why": "one line of reasoning"}. `session` must be an EXACT session name and
        `day` a weekday name. Built for the Mobility assessment: it has
        no day of its own so it never turns up unasked, and this is what puts it on a
        Wednesday when a re-test is due, in place of that person's usual mobility
        session. It works for any session, including an Optional one - that is the point,
        since a session with no day cannot be reached by the automatic alternation.
        Per person, so you can re-test one of them without disturbing the other. It is
        SPENT as soon as they log that session, and the weekday goes back to normal on
        its own - so write it the week you want it, not in advance.
        `lowest_rung` = which flexibility test is the CURRENT lowest rung, per skill, as
        {"Side split": {"test": "Pancake hip tilt", "why": "one line of reasoning"},
         "Deep squat": {"test": "Deep squat hold - heels on a wedge", "why": "..."}}.
        The skill is free text (the skill that person is training toward); `test` must
        be the EXACT exercise name of a flexibility test they have logged, because the
        app tags that row of the Progress > Flex ladder with it. This is a judgement,
        not a number: centimetres on different tests are not comparable, so decide it
        from the assessment per docs/methods/flexibility-method.md (the test that is the
        hard stop for the skill, e.g. a wedge that buys squat depth means the ankle is
        the stop). Merged per skill - pass only the skills you are changing. Pass
        {"Skill": null} to clear one once that rung is fixed and the re-test has not
        yet shown the next. Re-write it after every Mobility assessment re-test.
        `targets` = your weight for the next session, per exercise, as
        {"Bench press": {"kg": 60, "reps": 8, "why": "one line of reasoning"}} (None clears one).
        Read progression(person) first: it says what the rule suggests. A kg that equals
        the rule's `target` needs no why. Any other kg is refused without one. It applies until
        the person logs that exercise again, then the rule takes over, so write it the
        week you want it. `reps` is optional.
        All merge into existing coaching. They see it after tapping Sync now.
        Refused for a person who turned Garmin and coach off in the app (see people())."""
        return json.dumps(set_coaching(person, overall, by_exercise or {}, by_session or {},
                                       five_k or None, next_cardio or None,
                                       session_swap or None, lowest_rung or None, targets or None), indent=2)

    @mcp.tool()
    def coach_profile(person: str) -> str:
        """The coach's memory file for `person`: coach/<person>/profile.md, their current truth
        (goals, authority, dated and sourced safety notes, active program, preferences, response
        patterns, checkpoint). Read it, and the decisions index, before advising anyone. Method:
        docs/methods/coaching-behaviour-method.md."""
        return json.dumps(get_coach_profile(load_data(), person), indent=2)

    @mcp.tool()
    def write_coach_profile(person: str, text: str) -> str:
        """Replace coach/<person>/profile.md with `text` (Markdown). It is a WHOLE-FILE write, so
        read coach_profile first and carry forward everything still true, especially safety notes,
        approvals and the checkpoint. Every fact carries its date and origin (athlete report,
        training log, clinician instruction, coach hypothesis). Read it back afterwards."""
        return json.dumps(set_coach_profile(person, text), indent=2)

    @mcp.tool()
    def coach_decisions(person: str) -> str:
        """coach/<person>/decisions.md: the append-only decision log, with `index` listing the
        active decisions and those due for review. Read it before deciding anything, review what
        is due, and link a replacement to the decision it supersedes."""
        return json.dumps(get_coach_decisions(load_data(), person), indent=2)

    @mcp.tool()
    def add_coach_decision(person: str, scope: str, before: str, after: str, reason: str, expected: str,
                           review_due: str, authority: str = "", status: str = "applied", rule: str = "",
                           watch: str = "", exposure_needed: str = "", agreement: str = "no_response",
                           implementation: str = "not_due", satisfaction: str = "not_asked",
                           response_quote: str = "", supersedes: str = "",
                           linked_questions: list[str] | None = None, profile_update: str = "",
                           decision_id: str = "") -> str:
        """Append one decision to coach/<person>/decisions.md and rebuild its index. `before` and
        `after` are the exact old and new prescription. `reason` separates what was observed from
        what is thought to explain it. `expected` is an observable result with a time horizon, and
        `watch` the downside to look for. `review_due` is a date (2026-11-16) and `exposure_needed`
        what a fair review needs. `rule` cites the method rule, for example P4. `status` is one of
        proposed, approved, applied, declined, superseded, reviewed. Agreement, implementation and
        satisfaction are kept apart: agreement agreed, agreed_with_changes, pushed_back, declined,
        no_response. Implementation not_due, completed, partly_completed, not_completed, unknown.
        Satisfaction liked, disliked, mixed, neutral, not_asked. Silence is no_response, never
        agreed. `supersedes` is the id of an older decision, which is then marked superseded.
        `decision_id` is optional (D-YYYYMMDD-NN is generated). Never invent a response."""
        return json.dumps(add_decision(person, scope, before, after, reason, expected, review_due, authority,
                                       status, rule, watch, exposure_needed, agreement, implementation,
                                       satisfaction, response_quote, supersedes, linked_questions,
                                       profile_update, decision_id), indent=2)

    @mcp.tool()
    def review_coach_decision(person: str, decision_id: str, implementation: str | None = None,
                              agreement: str | None = None, satisfaction: str | None = None,
                              response_quote: str | None = None, status: str | None = None,
                              outcome: str | None = None, observed: str = "", next_action: str | None = None,
                              next_review: str | None = None, uncertainty: str = "",
                              profile_update: str | None = None) -> str:
        """Record the response and the review on an existing decision, add a dated review line and
        rebuild the index. The change, reason and expected result are never edited. Pass only what
        you know: `outcome` is helpful, unhelpful, mixed, uncertain, not_yet_evaluable or pending
        (use not_yet_evaluable when the change was not tried). `next_action` starts with keep, revise,
        revert, stop or defer. Setting an outcome marks an active decision reviewed, unless you pass
        `next_review` (a date), which keeps it active and moves its review date."""
        return json.dumps(review_decision(person, decision_id, implementation, agreement, satisfaction,
                                          response_quote, status, outcome, observed, next_action,
                                          next_review, uncertainty, profile_update), indent=2)

    @mcp.tool()
    def coach_questions(person: str, status: str = "open") -> str:
        """The questions put to `person` (status open, answered, closed or all). An `answered` one has
        their `answer` and `answeredAt` and is waiting for you to act on it and then close it. `due`
        is true on an open one whose nextFollowUp has passed. Read these before asking anything, so
        nothing is asked twice."""
        return json.dumps(get_coach_questions(load_data(), person, status), indent=2)

    @mcp.tool()
    def add_coach_question(person: str, question: str, why: str, priority: str = "routine",
                           decision: str = "", next_follow_up: str = "", question_id: str = "") -> str:
        """Ask `person` a question. It shows on their Home tab with its `why`, and they answer there.
        Ask only what could change a decision, clear up safety or respect a preference. `priority`
        is safety, blocking, routine or optional. `decision` links a decision id. `next_follow_up`
        is a date and defaults to a week. No more than three routine questions per review. A
        question already open is refused, and so is any question for a person who turned Garmin
        and coach off in the app. Whoever reads the answer is you, on the next review."""
        return json.dumps(add_question(person, question, why, priority, decision, next_follow_up, question_id), indent=2)

    @mcp.tool()
    def remind_coach_question(person: str, question_id: str, next_follow_up: str = "") -> str:
        """Count one reminder on an open question and move its follow-up date (default a week).
        For a non-essential question, remind once, then close it after two reviews."""
        return json.dumps(remind_question(person, question_id, next_follow_up), indent=2)

    @mcp.tool()
    def close_coach_question(person: str, question_id: str, reason: str) -> str:
        """Close a question so it leaves the app: answered and acted on, declined, duplicate,
        superseded or no longer relevant. `reason` is required. An unresolved safety question stays
        open."""
        return json.dumps(close_question(person, question_id, reason), indent=2)

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
