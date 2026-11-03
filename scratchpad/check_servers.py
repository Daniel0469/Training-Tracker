"""Behaviour diff for mcp-coach/server.py and mcp-garmin/server.py (issue #55).

Loads the base revision of each server (git show) and the current file, runs the same
calls against an in-memory GitHub store built from the newest scratchpad/data-backup-*.json
and a stubbed Garmin client, and prints only the keys whose results differ.

    python scratchpad/check_servers.py            # base revision vs working tree
    python scratchpad/check_servers.py --self     # base vs base (must show zero diffs)
    python scratchpad/check_servers.py --base REV # compare another revision

No network: urllib.request.urlopen, time and datetime are replaced while a scenario runs.
"""
import argparse, base64, contextlib, copy, datetime as real_dt, difflib, glob, hashlib, importlib.util
import io, json, os, random, re, subprocess, sys, tempfile, time, types, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN = real_dt.datetime(2026, 11, 2, 12, 0, 0, 123456, tzinfo=real_dt.timezone.utc).timestamp()
SERVERS = {"coach": "mcp-coach/server.py", "garmin": "mcp-garmin/server.py"}


# ---------------------------------------------------------------- loading
def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def base_source(rev, rel, tmp):
    text = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=ROOT, capture_output=True,
                          check=True).stdout
    out = os.path.join(tmp, "base_" + rel.replace("/", "_"))
    with open(out, "wb") as f:
        f.write(text)
    if rel.startswith("mcp-coach"):      # the server imports progression.py from its own folder
        with open(os.path.join(tmp, "progression.py"), "wb") as f:
            f.write(subprocess.run(["git", "show", f"{rev}:mcp-coach/progression.py"], cwd=ROOT,
                                   capture_output=True, check=True).stdout)
    return out


# ---------------------------------------------------------------- frozen clock
class _Date(real_dt.date):
    @classmethod
    def today(cls):
        return cls(2026, 11, 2)


class _DateTime(real_dt.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 11, 2, 12, 0, 0, 123456, tzinfo=tz)


FAKE_DT = types.SimpleNamespace(date=_Date, datetime=_DateTime, timezone=real_dt.timezone,
                                timedelta=real_dt.timedelta)


# ---------------------------------------------------------------- fake GitHub
class Resp(io.BytesIO):
    pass


def _sha(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


class FakeHub:
    """Serves GET/PUT on /contents/<path> from memory and records every request."""

    def __init__(self, files, fail_puts=()):
        self.files = dict(files)
        self.fail_puts = [list(f) for f in fail_puts]
        self.log = []

    def urlopen(self, req, timeout=None):
        url, method = req.full_url, req.get_method()
        path = url.split("/contents/", 1)[1]
        body = json.loads(req.data) if req.data else None
        shown = None
        if body is not None:
            shown = dict(body)
            shown["content"] = base64.b64decode(body["content"]).decode("utf-8")
        self.log.append({"method": method, "url": url, "headers": dict(sorted(req.header_items())),
                         "body": shown, "timeout": timeout})
        if method == "GET":
            if path not in self.files:
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, io.BytesIO(b""))
            text = self.files[path]
            return Resp(json.dumps({"content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
                                    "sha": _sha(text)}).encode("utf-8"))
        for i, (substr, code) in enumerate(self.fail_puts):
            if substr in path:
                del self.fail_puts[i]
                raise urllib.error.HTTPError(url, code, "conflict", {}, io.BytesIO(b""))
        if path in self.files and body.get("sha") != _sha(self.files[path]):
            raise urllib.error.HTTPError(url, 409, "sha mismatch", {}, io.BytesIO(b""))
        self.files[path] = shown["content"]
        return Resp(json.dumps({"content": {"sha": _sha(shown["content"])}}).encode("utf-8"))


@contextlib.contextmanager
def patched(mod, hub):
    saved = (urllib.request.urlopen, time.time, time.sleep, mod.datetime)
    urllib.request.urlopen, time.time, time.sleep, mod.datetime = (
        hub.urlopen, lambda: FROZEN, lambda s: None, FAKE_DT)
    env = {k: os.environ.pop(k, None) for k in ("TT_GITHUB_PATH", "TT_GITHUB_LOG_PATH", "TT_DATA_FILE",
                                                "TT_PERSON")}
    os.environ["TT_GITHUB_REPO"], os.environ["TT_GITHUB_TOKEN"] = "owner/store", "token-for-tests"
    try:
        yield
    finally:
        urllib.request.urlopen, time.time, time.sleep, mod.datetime = saved
        for k, v in env.items():
            if v is not None:
                os.environ[k] = v


class FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def deco(fn):
            self.tools[fn.__name__] = fn
            return fn
        return deco


def canon(v):
    return json.dumps(v, indent=1, sort_keys=True, default=str)


def attempt(fn, *a, **kw):
    try:
        out = fn(*a, **kw)
    except SystemExit as e:
        return {"SystemExit": str(e.code)}
    except Exception as e:
        return {"EXC": f"{type(e).__name__}: {e}"}
    if isinstance(out, str):
        try:
            return json.loads(out)
        except ValueError:
            return out
    return out


def run_steps(mod, tools, name, steps, files, fail_puts=(), out=None):
    """steps: (label, 'tool'|'fn:name', kwargs). Results, requests and files land in `out`."""
    hub = FakeHub(files, fail_puts)
    with patched(mod, hub):
        for label, target, kw in steps:
            fn = getattr(mod, target[3:]) if target.startswith("fn:") else tools[target]
            out[f"{name}/{label}"] = canon(attempt(fn, **kw))
    out[f"{name}/#requests"] = canon(hub.log)
    for path, text in sorted(hub.files.items()):
        out[f"{name}/#file {path}"] = text


# ---------------------------------------------------------------- context from the store
def derive(store):
    people = store["people"]
    sessions = store["program"]["sessions"]
    lift_key = next(k for k, s in sessions.items() if not s.get("person") and len(s["exercises"]) >= 3)
    lift = sessions[lift_key]
    is_run = lambda e: (any("dist" in str(c).lower() for c in e.get("cols") or [])
                        and any("time" in str(c).lower() for c in e.get("cols") or []))
    ctx = {"people": people, "lift_key": lift_key, "lift": lift["name"],
           "ex": [e["name"] for e in lift["exercises"]],
           "all_ex": sorted({e["name"] for l in store["logs"] for e in l.get("entries") or []}),
           "sess_names": [s["name"] for s in sessions.values()], "sess_keys": list(sessions),
           "log_ids": [l["id"] for l in store["logs"]], "run_which": {}, "ladder": {}, "run_log": {},
           "lift_log": {}, "pending": [c["id"] for c in store.get("programChanges") or []
                                       if c.get("status") == "pending"],
           "done": [c["id"] for c in store.get("programChanges") or [] if c.get("status") != "pending"],
           "sugg": [s["id"] for s in store.get("suggestions") or []],
           "sugg_text": next((s["text"] for s in store.get("suggestions") or [] if s.get("text")), "x")}
    for p in people:
        owned = [(k, s) for k, s in sessions.items() if s.get("person") == p]
        runs = [k for k, s in owned if any(is_run(e) for e in s.get("exercises") or [])]
        ctx["run_which"][p] = (runs or [k for k, _ in owned] or [""])[0]
        ctx["ladder"][p] = next((e["name"] for l in store["logs"] if l.get("person") == p
                                 for e in l.get("entries") or []
                                 if str((e.get("cols") or [""])[0]).strip().lower() == "cm"), "Test")
        ctx["run_log"][p] = next(((l["id"], e["name"]) for l in store["logs"] if l.get("person") == p
                                  for e in l.get("entries") or [] if is_run(e) and e.get("rows")),
                                 (None, None))
        ctx["lift_log"][p] = next(((l["id"], e["name"]) for l in store["logs"] if l.get("person") == p
                                   for e in l.get("entries") or [] if e.get("rows")), (None, None))
    return ctx


# ---------------------------------------------------------------- coach scenarios
def coach_scenarios(ctx):
    P, lift, ex = ctx["people"], ctx["lift"], ctx["ex"]
    sc = []

    def add(name, steps, files=(), fail=()):
        sc.append((name, steps, dict(files), list(fail)))

    reads = [("people", "people", {}), ("program_changes", "program_changes", {}),
             ("program_changes_all", "program_changes", {"include_done": True}),
             ("suggestions", "suggestions", {}),
             ("suggestions_all", "suggestions", {"include_done": True, "include_proposed": True}),
             ("limiters_all", "limiters", {}), ("session_notes", "session_notes", {}),
             ("program_session_none", "program_session", {}),
             ("session_missing", "session", {"session_id": "0"}),
             ("coaching_history_x", "coaching_history", {"person": "Nobody"})]
    reads += [(f"session_notes {n}", "session_notes", {"session": n}) for n in ctx["sess_names"] + ["zzz"]]
    reads += [(f"program_session {n}", "program_session", {"name": n})
              for n in ctx["sess_names"] + ctx["sess_keys"] + ["zzz", "Tuesday", "run", "mobility", "a"]]
    reads += [(f"session {i}", "session", {"session_id": str(i)}) for i in ctx["log_ids"]]
    reads += [("goals Nobody", "goals", {"person": "Nobody"})]
    for p in P:
        reads += [(f"goals {p}", "goals", {"person": p}), (f"recent {p}", "recent_sessions", {"person": p}),
                  (f"recent100 {p}", "recent_sessions", {"person": p, "limit": 100}),
                  (f"prs {p}", "prs", {"person": p}), (f"bodyweight {p}", "bodyweight", {"person": p}),
                  (f"measurements {p}", "measurements", {"person": p}),
                  (f"nutrition {p}", "nutrition", {"person": p}),
                  (f"nutrition3 {p}", "nutrition", {"person": p, "days": 3}),
                  (f"coaching_history {p}", "coaching_history", {"person": p}),
                  (f"coaching_history1 {p}", "coaching_history", {"person": p, "limit": 1}),
                  (f"running_form {p}", "running_form", {"person": p}),
                  (f"limiters {p}", "limiters", {"person": p})]
        reads += [(f"progress {p} {n}", "progress", {"person": p, "exercise": n}) for n in ctx["all_ex"]]
        for w in dict.fromkeys(["", "run", "quality", "mobility", "tuesday", "wednesday",
                                ctx["run_which"][p], "zzz"]):
            reads.append((f"run_session {p} {w!r}", "run_session", {"person": p, "which": w}))
    add("reads", reads)
    add("reads_with_log", reads[:0] + [(f"coaching_history {p}", "coaching_history", {"person": p})
                                       for p in P] + [("limit", "coaching_history", {"person": P[0], "limit": 1})],
        files={"coaching-log.json": json.dumps(
            [{"id": 5, "date": "2026-10-01", "person": P[0], "overall": "a"},
             {"id": 6, "date": "2026-10-02", "person": P[1], "overall": "b"},
             {"id": 7, "date": "2026-10-03", "person": P[0], "overall": "c"}], indent=1)})

    for p in P:
        lad = ctx["ladder"][p]
        full = dict(person=p, overall="Overall note", by_session={lift: "Session focus"},
                    by_exercise={ex[0]: "Exercise step"},
                    five_k={"time": "25:00", "pace": "5:00", "basis": "b", "confidence": "low"},
                    next_cardio={"session": ctx["sess_names"][0], "focus": "f", "why": "w"},
                    session_swap={"session": ctx["sess_names"][-1], "day": "Wednesday", "why": "w"},
                    lowest_rung={"Skill A": {"test": lad, "why": "w"},
                                 "Skill B": {"test": "Not a logged test", "why": "w"}, "Skill C": None})
        add(f"coaching {p}", [("full", "write_coaching", full),
                              ("again", "write_coaching", {"person": p, "overall": "Second"}),
                              ("empty", "write_coaching", {"person": p}),
                              ("clear", "write_coaching", {"person": p, "lowest_rung": {"Skill A": None}}),
                              ("blank test", "write_coaching",
                               {"person": p, "lowest_rung": {"Skill D": {"test": "  "}}}),
                              ("history", "coaching_history", {"person": p})])
        add(f"coaching conflict {p}", [("full", "write_coaching", full), ("history", "coaching_history", {"person": p})],
            fail=[("data.json", 409)])
        add(f"coaching conflicts exhausted {p}", [("full", "write_coaching", full)],
            fail=[("data.json", 409)] * 3)
        add(f"coaching log conflict {p}", [("full", "write_coaching", full)],
            files={"coaching-log.json": "[]"}, fail=[("coaching-log", 409)])
        add(f"coaching log error {p}", [("full", "write_coaching", full)], fail=[("coaching-log", 500)])
        add(f"limiter {p}", [("set", "write_limiter", {"person": p, "session": lift, "text": " tight hips "}),
                             ("clear", "write_limiter", {"person": p, "session": lift, "text": ""}),
                             ("read", "limiters", {"person": p})])

        owned = ctx["run_which"][p]
        run_ex = [{"name": "Run reps", "target": "6 x 1 min", "sets": 6, "garminRun": True,
                   "cols": ["Distance (km)", "Time (mm:ss)", "Pace"], "restSec": "90", "betterWhen": "Higher",
                   "load": "bw", "muscles": ["legs"], "notes": "dropped", "warmup": "bar x8"},
                  {"name": "Plank", "target": "3 x 40s", "sets": 3, "cols": ["Min", "Notes"]}]
        run_steps = [("read", "run_session", {"person": p, "which": owned})]
        for w in dict.fromkeys(["", "run", "quality", "mobility", "tuesday", "wednesday", owned, "zzz"]):
            run_steps.append((f"which {w!r}", "write_run",
                              {"person": p, "which": w, "setup": f"setup for {w}", "why": "because"}))
        run_steps += [
            ("exercises", "write_run", {"person": p, "which": owned, "exercises": run_ex, "why": "new shape"}),
            ("exercises same", "write_run", {"person": p, "which": owned, "exercises": run_ex}),
            ("exercises empty", "write_run", {"person": p, "which": owned, "exercises": []}),
            ("exercises bad", "write_run", {"person": p, "which": owned, "exercises": ["x"]}),
            ("exercises noname", "write_run", {"person": p, "which": owned, "exercises": [{"cols": ["a", "b"]}]}),
            ("exercises cols", "write_run", {"person": p, "which": owned, "exercises": [{"name": "n", "cols": ["a"]}]}),
            ("exercises sets", "write_run", {"person": p, "which": owned,
                                             "exercises": [{"name": "n", "cols": ["a", "b"], "sets": "x"}]}),
            ("exercises sets range", "write_run", {"person": p, "which": owned,
                                                   "exercises": [{"name": "n", "cols": ["a", "b"], "sets": 31}]}),
            ("exercises restSec", "write_run", {"person": p, "which": owned,
                                                "exercises": [{"name": "n", "cols": ["a", "b"], "restSec": "x"}]}),
            ("rename", "write_run", {"person": p, "which": owned, "name": "Renamed run", "day": "Saturday"}),
            ("rename clash", "write_run", {"person": p, "which": owned, "name": ctx["lift"].upper()}),
            ("notes", "write_run", {"person": p, "which": owned, "warmup": "w", "cooldown": "c",
                                    "recording": "r", "setup": "s", "garmin": "g", "why": "reason"}),
            ("notes clear", "write_run", {"person": p, "which": owned, "warmup": "", "garmin": ""}),
            ("nothing", "write_run", {"person": p, "which": owned}),
            ("bad person", "write_run", {"person": "Nobody", "setup": "s"}),
            ("read", "run_session", {"person": p, "which": owned})]
        add(f"write_run {p}", run_steps)
        add(f"write_run conflict {p}", [("w", "write_run", {"person": p, "which": owned, "setup": "s", "why": "y"})],
            fail=[("data.json", 412)])

        rid, rname = ctx["run_log"][p]
        lid, lname = ctx["lift_log"][p]
        add(f"log_entry {p}", [
            ("run", "write_log_entry", {"session_id": str(rid), "exercise": rname,
                                        "rows": [[1.0, "5:00", "5:00", 150], [None, "x"]], "why": "fix"}),
            ("same", "write_log_entry", {"session_id": str(rid), "exercise": rname,
                                         "rows": [[1.0, "5:00", "5:00", 150], ["", "x"]]}),
            ("lower", "write_log_entry", {"session_id": str(lid), "exercise": str(lname).upper(),
                                          "rows": [[50, 5]]}),
            ("bad exercise", "write_log_entry", {"session_id": str(lid), "exercise": "zzz", "rows": [[1]]}),
            ("bad rows", "write_log_entry", {"session_id": str(lid), "exercise": lname, "rows": []}),
            ("bad id", "write_log_entry", {"session_id": "0", "exercise": lname, "rows": [[1]]}),
            ("read", "session", {"session_id": str(rid)})])

    # session notes (shared)
    sn = [("read", "session_notes", {"session": lift})]
    for label, kw in (("warmup", {"warmup": "New warm-up"}), ("append", {"warmup": "Extra", "append": True}),
                      ("append empty", {"cooldown": "Cool", "append": True}),
                      ("cooldown clear", {"cooldown": ""}),
                      ("recording+setup", {"recording": "rec", "setup": "set"}),
                      ("same", {"setup": "set"}), ("nothing", {}),
                      ("garmin", {"garmin": "watch"}),
                      ("all", {"warmup": " a ", "cooldown": "b", "recording": "c", "setup": "d", "garmin": "e"})):
        sn.append((label, "write_session_notes", dict(session=lift, **kw)))
    sn += [("lowercase", "write_session_notes", {"session": lift.lower(), "warmup": "lc"}),
           ("by key", "write_session_notes", {"session": ctx["lift_key"], "warmup": "key"}),
           ("missing", "write_session_notes", {"session": "zzz", "warmup": "x"}),
           ("blank", "write_session_notes", {"session": "", "warmup": "x"}),
           ("read after", "session_notes", {"session": lift})]
    add("session_notes", sn)

    cs = [("full", "create_session", {"name": "New day", "day": "Friday", "person": P[0],
                                      "exercises": [{"name": "Squat", "sets": 3, "cols": ["Weight (kg)", "Reps"],
                                                     "load": "bw", "timed": True, "bwPct": 50, "groupId": "g1"}],
                                      "warmup": "w", "cooldown": "c", "setup": "s", "recording": "r",
                                      "garmin": "g"}),
          ("dup", "create_session", {"name": " new DAY "}),
          ("bare", "create_session", {"name": "Another one"}),
          ("bare key", "create_session", {"name": "Another-one"}),
          ("key clash", "create_session", {"name": ctx["lift"] + " "}),
          ("blank", "create_session", {"name": "  "}),
          ("bad person", "create_session", {"name": "Q", "person": "Nobody"}),
          ("bad exercise", "create_session", {"name": "Q2", "exercises": [{"name": "x", "cols": ["a"]}]}),
          ("read", "program_session", {"name": "New day"})]
    add("create_session", cs)

    pc = [("edit", "write_program_change", {"session": lift, "exercise": ex[0], "why": "w", "sets": 4,
                                            "target": "4x6", "warmup": "bar x8", "rest_sec": 150}),
          ("edit dup", "write_program_change", {"session": lift, "exercise": ex[0], "why": "w", "sets": 3}),
          ("edit nothing", "write_program_change", {"session": lift, "exercise": ex[1], "why": "w"}),
          ("edit missing ex", "write_program_change", {"session": lift, "exercise": "zzz", "why": "w", "sets": 3}),
          ("remove", "write_program_change", {"session": lift, "exercise": ex[1], "why": "w", "remove": True}),
          ("remove missing", "write_program_change", {"session": lift, "exercise": "zzz", "why": "w", "remove": True}),
          ("add", "write_program_change", {"session": lift, "exercise": "Brand new", "why": "w", "after": ex[0],
                                           "add": {"target": "3x8", "sets": 3, "cols": ["Weight (kg)", "Reps"],
                                                   "name": "ignored", "notes": "ignored"}}),
          ("add exists", "write_program_change", {"session": lift, "exercise": ex[0], "why": "w", "add": {}}),
          ("move front", "write_program_change", {"session": lift, "exercise": ex[2], "why": "w", "move_after": ""}),
          ("move after", "write_program_change", {"session": lift, "exercise": ex[0], "why": "w",
                                                  "move_after": ex[2]}),
          ("move self", "write_program_change", {"session": lift, "exercise": ex[0], "why": "w",
                                                 "move_after": ex[0]}),
          ("move bad dest", "write_program_change", {"session": lift, "exercise": ex[0], "why": "w",
                                                     "move_after": "zzz"}),
          ("bad session", "write_program_change", {"session": "zzz", "exercise": ex[0], "why": "w", "sets": 1}),
          ("list", "program_changes", {})]
    pw = [("withdraw", "withdraw_program_change", {"change_id": str(i)}) for i in ctx["pending"][:2]]
    pw += [("withdraw done", "withdraw_program_change", {"change_id": str(i)}) for i in ctx["done"][:1]]
    pw += [("withdraw missing", "withdraw_program_change", {"change_id": "0"})]
    add("program_change", pc)
    add("program_change_withdraw", pc[:1] + pw + [("list", "program_changes", {"include_done": True})])

    su = [("new", "propose_suggestion_tool", {"text": "  Add a thing  ", "why": " because ", "about": " Run "}),
          ("dup", "propose_suggestion_tool", {"text": "add   a THING"}),
          ("dup existing", "propose_suggestion_tool", {"text": ctx["sugg_text"]}),
          ("empty", "propose_suggestion_tool", {"text": " "}),
          ("resolve", "resolve_suggestion_tool", {"suggestion_id": str(ctx["sugg"][0])}),
          ("resolve missing", "resolve_suggestion_tool", {"suggestion_id": "0"}),
          ("list", "suggestions", {"include_done": True, "include_proposed": True})]
    add("suggestions", su)

    p0 = P[0]
    add("direct", [("nutrition today", "fn:get_nutrition", {"data": None, "person": p0}),
                   ("nutrition fixed", "fn:get_nutrition", {"data": None, "person": p0, "days": 30,
                                                           "today": real_dt.date(2026, 10, 30)})])
    return sc


def run_coach(mod, store_text, ctx):
    out = {}
    mcp = FakeMCP()
    mod._register(mcp)
    for name, steps, files, fail in coach_scenarios(ctx):
        files = {"data.json": store_text, **files}
        fixed = []
        for label, target, kw in steps:
            if target.startswith("fn:") and kw.get("data", 1) is None:
                kw = dict(kw)
                kw["data"] = json.loads(store_text)
            fixed.append((label, target, kw))
        run_steps(mod, mcp.tools, "coach/" + name, fixed, files, fail, out)
    run_load_data(mod, store_text, out)
    return out


def run_load_data(mod, store_text, out):
    hub = FakeHub({"data.json": store_text})
    with patched(mod, hub):
        out["coach/load_data"] = canon(attempt(lambda: mod.load_data() == json.loads(store_text)))
        os.environ["TT_GITHUB_PATH"] = "sub/other.json"
        out["coach/load_data other path"] = canon(attempt(mod.load_data))
        del os.environ["TT_GITHUB_PATH"]
        del os.environ["TT_GITHUB_TOKEN"]
        path = os.path.join(tempfile.gettempdir(), "tt_check_data.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(store_text)
        os.environ["TT_DATA_FILE"] = path
        out["coach/load_data file"] = canon(attempt(lambda: mod.load_data() == json.loads(store_text)))
        os.environ.pop("TT_DATA_FILE")
        out["coach/load_data none"] = canon(attempt(mod.load_data))
        os.remove(path)
    out["coach/load_data #requests"] = canon(hub.log)


# ---------------------------------------------------------------- garmin fixtures
GMT0 = "2026-10-20T06:30:00.0"


def mk_activity(kind, aid=1, date="2026-10-20"):
    flat = {"activityId": aid, "activityName": f"Run {kind}", "activityType": {"typeKey": "treadmill_running"},
            "startTimeLocal": f"{date} 07:30:00", "startTimeGMT": f"{date} 06:30:00", "distance": 5120.5,
            "duration": 1810.4, "movingDuration": 1750.2, "averageHR": 151.4, "maxHR": 181, "minHR": 90,
            "averageRunningCadenceInStepsPerMinute": 168.2, "maxRunCadence": 190, "elevationGain": 12.3,
            "calories": 402, "aerobicTrainingEffect": 3.44, "anaerobicTrainingEffect": 1.1,
            "activityTrainingLoad": 88.84, "trainingEffectLabel": "AEROBIC_BASE", "steps": 5100,
            "moderateIntensityMinutes": 10, "vigorousIntensityMinutes": 12, "waterEstimated": 410,
            "groundContactTime": 251.6, "verticalOscillation": 8.46, "verticalRatio": 8.14,
            "strideLength": 101.7, "averagePower": 241.5, "maxPower": 410, "normalizedPower": 255,
            "directWorkoutRpe": 60, "directWorkoutFeel": 75, "vO2MaxValue": 48.2}
    if kind == "flat":
        return flat
    if kind == "nested":
        head = {k: flat[k] for k in ("activityId", "activityName", "activityType")}
        head["summaryDTO"] = {k: v for k, v in flat.items() if k not in head}
        return head
    if kind == "dto":
        return {"activityId": aid, "activityTypeDTO": {"typeKey": "cycling"}, "summaryDTO": {
            "startTimeLocal": f"{date}T18:00:00.0", "distance": 0, "duration": 0}}
    if kind == "sparse":
        return {"activityId": aid, "activityType": {"typeKey": "running"}, "startTimeLocal": f"{date} 09:15",
                "distance": 3000, "duration": 1200, "directWorkoutFeel": 60, "directWorkoutRpe": 0}
    return {}


def mk_laps(kind):
    if kind == "none":
        return {}
    laps = [{"distance": 1000, "duration": 330.2, "averageHR": 140, "maxHR": 150, "averageRunCadence": 160},
            {"distance": 0, "duration": 4},
            {"distance": 1000.4, "duration": 300, "averageHR": 155.5, "maxHR": 168},
            {"distance": 812, "duration": 270.7, "averageHR": None},
            {"distance": 20, "duration": 0}]
    if kind == "nohr":
        laps = [{k: v for k, v in l.items() if "HR" not in k} for l in laps]
    return {"lapDTOs": laps}


def _gmt(sec):
    t = real_dt.datetime(2026, 10, 20, 6, 30, 0) + real_dt.timedelta(seconds=sec)
    return t.strftime("%Y-%m-%dT%H:%M:%S.0")


def mk_blocks(kind):
    """[(type, seconds, km/h)] for a recording."""
    if kind == "walk_rec":
        b = [("RWD_WALK", 300, 5.0)]
        for _ in range(6):
            b += [("RWD_RUN", 60, 13.0), ("RWD_WALK", 90, 5.0)]
        return b + [("RWD_WALK", 200, 4.5)]
    if kind == "jog_rec":
        b = [("RWD_RUN", 200, 8.0)]
        for _ in range(4):
            b += [("RWD_RUN", 360, 11.0), ("RWD_RUN", 90, 7.5)]
        return b
    if kind == "mixed":
        return [("RWD_RUN", 40, 12.5), ("RWD_WALK", 60, 5.0), ("RWD_RUN", 42, 12.5), ("RWD_WALK", 60, 5.0),
                ("RWD_RUN", 41, 12.5), ("RWD_WALK", 120, 5.0), ("RWD_RUN", 583, 12.0), ("RWD_RUN", 300, 7.0)]
    if kind == "zone2":
        return [("RWD_RUN", 314, 8.0), ("RWD_WALK", 80, 5.0), ("RWD_RUN", 247, 8.0), ("RWD_WALK", 60, 5.0),
                ("RWD_RUN", 428, 8.0), ("RWD_WALK", 50, 5.0), ("RWD_RUN", 207, 8.0)]
    if kind == "stand":
        return [("RWD_RUN", 338, 8.0), ("RWD_STAND", 60, 0.8), ("RWD_RUN", 358, 8.0), ("RWD_STAND", 80, 0.8),
                ("RWD_RUN", 300, 8.0)]
    if kind == "adjacent":
        return [("RWD_WALK", 120, 5.0), ("RWD_RUN", 428, 11.0), ("RWD_RUN", 207, 11.0), ("RWD_WALK", 100, 5.0)]
    if kind == "single":
        return [("RWD_WALK", 200, 5.0), ("RWD_RUN", 900, 11.0), ("RWD_WALK", 100, 5.0)]
    if kind == "fade":
        b = []
        for sp in (13.5, 12.5, 14.1, 13.1, 10.2):
            b += [("RWD_RUN", 60, sp), ("RWD_WALK", 120, 4.0)]
        return b
    return [("RWD_RUN", 1800, 10.0)]


def mk_typed(kind, rng):
    out, t = [], 0
    for typ, sec, kmh in mk_blocks(kind):
        out.append({"type": typ, "startTimeGMT": _gmt(t), "duration": sec + rng.random(),
                    "distance": kmh / 3.6 * sec, "averageHR": 120 + rng.randrange(60),
                    "maxHR": 150 + rng.randrange(40), "averageRunCadence": 150 + rng.randrange(30),
                    "averagePower": (200 + rng.randrange(80)) if typ == "RWD_RUN" else None})
        t += sec
    return out


def mk_series(kind, rng, step=1):
    pts, t = [], 0.0
    for typ, sec, kmh in mk_blocks(kind):
        end = t + sec
        while t < end:
            sp = max(0.0, kmh + rng.gauss(0, 0.04 * kmh + 0.2))
            hr = None if rng.random() < 0.03 else 110 + 0.02 * t + rng.gauss(0, 3) + (sp * 2)
            cad = None if rng.random() < 0.05 else 150 + rng.gauss(0, 6)
            pts.append((t, sp, hr, cad))
            t += step
    return pts


def run_garmin_pure(mod, store, out):
    rng = random.Random(7)
    program = copy.deepcopy(store["program"])
    program["sessions"]["intv"] = {
        "name": "Intervals", "exercises": [
            {"name": "Warm", "cols": ["Min", "Notes"], "sets": 1},
            {"name": "Speed reps", "cols": ["Hard (km/h)", "Easy (km/h)"], "sets": 6, "garminRun": True},
            {"name": "Run", "cols": ["Distance (km)", "Time", "Pace"], "sets": 1}],
        "setupNote": "1  5:00  5.0  warm-up\n2  1:00  13.0  REP run\n3  1:30  5.0  recover\n"
                     "4  1:00  13.0  rep run\nnot a row"}
    program["sessions"]["cardio"] = {"name": "Cardio", "exercises": [
        {"name": "Bike", "cols": ["Min", "Notes"]}, {"name": "Run", "cols": ["Distance (km)", "Time", "Pace"], "sets": 4},
        {"name": "Plank", "cols": ["Weight (kg)", "Reps"]}]}

    def rec(key, fn, *a, **kw):
        out[f"garmin/{key}"] = canon(attempt(fn, *copy.deepcopy(a), **copy.deepcopy(kw)))

    with patched(mod, FakeHub({})):
        for x in (0, 59.6, 61, 3599.5, None, 7384):
            rec(f"_mmss {x}", mod._mmss, x)
        for km, sec in ((1, 300), (0, 10), (None, 5), (5.12, 1810), (0.5, 1), (1.0, 359.99), (2, -1)):
            rec(f"_pace {km} {sec}", mod._pace, km, sec)
        for v in (None, "", " 3.5 ", "x", 7, True):
            rec(f"_num {v!r}", mod._num, v)
        for kind in ("flat", "nested", "dto", "sparse", "empty"):
            a = mk_activity(kind)
            for fn in ("summarize_activity", "activity_metrics", "activity_type", "is_run"):
                rec(f"{fn} {kind}", getattr(mod, fn), a)
            for lk in ("full", "nohr", "none"):
                sp = mk_laps(lk)
                rec(f"activity_to_log {kind} {lk}", mod.activity_to_log, a, sp, "P")
                rec(f"splits_to_rows_hr {kind} {lk}", mod.splits_to_rows_hr, sp, a)
        for lk in ("full", "nohr", "none"):
            sp = mk_laps(lk)
            for fn in ("splits_to_rows", "splits_detail"):
                rec(f"{fn} {lk}", getattr(mod, fn), sp)
            rec(f"splits_to_rows_hr {lk} no a", mod.splits_to_rows_hr, sp)
        rec("splits None", mod.splits_to_rows, None)
        rec("splits_detail None", mod.splits_detail, None)

        shapes = ("walk_rec", "jog_rec", "mixed", "zone2", "stand", "adjacent", "single", "fade", "steady")
        for kind in shapes:
            for step in (1, 7):
                typed, series = mk_typed(kind, random.Random(kind)), mk_series(kind, random.Random(kind + "s"), step)
                a = mk_activity("flat")
                tag = f"{kind} step{step}"
                rec(f"detect_intervals {tag}", mod.detect_intervals, series)
                rec(f"detect_intervals tight {tag}", mod.detect_intervals, series, 40, 5)
                rec(f"reps_from_typed_splits {tag}", mod.reps_from_typed_splits, typed, a, series)
                rec(f"reps_from_typed_splits noseries {tag}", mod.reps_from_typed_splits, typed, a)
                for exp, setup in ((None, None), (6, None), (3, mod._prescribed_blocks(
                        {"sessionKey": "intv"}, program)), (6, [{"sec": 360, "kmh": 11.0}])):
                    rec(f"reps_from_speed_trace {tag} {exp} {bool(setup)}", mod.reps_from_speed_trace,
                        series, expected=exp, setup=setup)
                rec(f"reps_from_speed_trace minrep {tag}", mod.reps_from_speed_trace, series, None, 60)
                rec(f"effort_drift {tag}", mod.effort_drift, typed, a, series)
                rec(f"effort_drift noseries {tag}", mod.effort_drift, typed, a, [])
                for bw in (None, 70):
                    rec(f"activity_efficiency {tag} {bw}", mod.activity_efficiency, a, typed, bw)
                rec(f"activity_efficiency none {tag}", mod.activity_efficiency, mk_activity("sparse"), None, 60)
                reps = attempt(mod.reps_from_typed_splits, typed, a, series)
                trace = attempt(mod.reps_from_speed_trace, series)
                for nm, r in (("typed", reps), ("trace", trace)):
                    if isinstance(r, dict) and r.get("reps"):
                        rec(f"rep_derived {nm} {tag}", mod.rep_derived, r["reps"])
                        rec(f"rows_from_reps {nm} {tag}", mod.rows_from_reps, r)
                        rec(f"rows_from_reps nohr {nm} {tag}", mod.rows_from_reps,
                            {"reps": [{k: v for k, v in x.items() if k != "avg_hr"} for x in r["reps"][:2]] + r["reps"][2:]})
                pts = [(t, k) for t, k, _h, _c in series]
                if len(pts) >= 30:
                    rec(f"_speed_levels {tag}", mod._speed_levels, [k for _t, k in pts])
                    rec(f"_levels_from_trace {tag}", mod._levels_from_trace, pts, 15)
                    blocks = attempt(mod._levels_from_trace, pts, 15)
                    rec(f"_same_length_runs {tag}", mod._same_length_runs, blocks)
                    rec(f"_between_speed {tag}", mod._between_speed, pts, blocks)
                    rec(f"_not_a_rep_set {tag}", mod._not_a_rep_set, [{"sec": b["sec"]} for b in blocks] or [{"sec": 0}])
        rec("rows_from_reps none", mod.rows_from_reps, None)
        rec("rep_derived empty", mod.rep_derived, [])
        rec("reps_from_typed_splits empty", mod.reps_from_typed_splits, [], mk_activity("flat"))
        rec("reps_from_typed_splits no start", mod.reps_from_typed_splits, mk_typed("fade", rng), {})
        rec("detect_intervals short", mod.detect_intervals, [(i, 5.0, None, None) for i in range(10)])
        rec("reps_from_speed_trace short", mod.reps_from_speed_trace, [(i, 5.0, None, None) for i in range(10)])
        rec("_setup_miss", mod._setup_miss, [{"sec": 60}], [60, 70])
        rec("_setup_miss none", mod._setup_miss, None, [1])
        for key in ("intv", "cardio", "lower1", "missing"):
            log = {"sessionKey": key, "entries": [{"name": "Warm"}, {"name": "Bike"}]}
            rec(f"_prescribed_blocks {key}", mod._prescribed_blocks, log, program)
            rec(f"_prescribed_reps {key}", mod._prescribed_reps, log, program)
            rec(f"_program_run_slot {key}", mod._program_run_slot, program, key, log)
            rec(f"_interval_entry {key}", mod._interval_entry,
                {"sessionKey": key, "entries": [{"name": "Speed reps", "rows": []}]}, program)
        rec("_program_run_slot None", mod._program_run_slot, None, "k", {})
        for rows in ([], [[1, "a", "b"]], [[1, "a", "b", ""]], [[1, "a", "b", 150]]):
            rec(f"_run_cols {rows}", mod._run_cols, rows)

        # real logs from the store: entries, reps, bodyweights
        for l in store["logs"]:
            i = l["id"]
            for e in l.get("entries") or []:
                rec(f"_is_run_entry {i} {e.get('name')}", mod._is_run_entry, e)
                rec(f"_entry_has_rows {i} {e.get('name')}", mod._entry_has_rows, e)
            rec(f"_program_run_slot log {i}", mod._program_run_slot, store["program"], l.get("sessionKey"), l)
            rec(f"_prescribed log {i}", lambda lg, pr: [mod._prescribed_blocks(lg, pr), mod._prescribed_reps(lg, pr)],
                l, store["program"])
            rec(f"bodyweight_on {i}", mod.bodyweight_on, store, l.get("person"), l.get("date"))
            reps = (l.get("garmin") or {}).get("reps")
            if reps and reps.get("reps"):
                rec(f"rep_derived store {i}", mod.rep_derived, reps["reps"])
                rec(f"rows_from_reps store {i}", mod.rows_from_reps, reps)
        for p in store["people"] + ["Nobody"]:
            rec(f"_person_bodyweights {p}", mod._person_bodyweights, store, p)
            for d in ("2000-01-01", "2026-10-15", "2099-01-01", None):
                rec(f"bodyweight_on {p} {d}", mod.bodyweight_on, store, p, d)

        # match_run
        runs = [mk_activity("flat", 11, "2026-10-20"), mk_activity("sparse", 12, "2026-10-20"),
                mk_activity("flat", 13, "2026-10-21"), mk_activity("empty", 14), mk_activity("dto", 15, "2026-10-20")]
        runs[2]["duration"] = 99999
        for date in ("2026-10-20", "2026-10-21", "2026-10-22", "bad", None):
            for used in (set(), {11}, {11, 12}):
                rec(f"match_run {date} {sorted(used)}", mod.match_run, runs, date, used)

        # enrich_log combinations
        lap_rows = mod.splits_to_rows_hr(mk_laps("full"), mk_activity("flat"))
        logs = {
            "empty run": {"id": 1, "date": "2026-10-20", "person": "P", "sessionKey": "intv", "garminWanted": True,
                          "entries": [{"name": "Run", "cols": ["Distance (km)", "Time", "Pace"], "rows": []}]},
            "no run entry": {"id": 2, "date": "2026-10-20", "person": "P", "sessionKey": "cardio",
                             "entries": [{"name": "Bike", "rows": [["5"]]}]},
            "no run entry no slot": {"id": 3, "date": "2026-10-20", "person": "P", "sessionKey": "zzz", "entries": []},
            "lap rows": {"id": 4, "date": "2026-10-20", "person": "P", "sessionKey": "intv",
                         "entries": [{"name": "Run", "cols": ["Distance (km)", "Time", "Pace", "HR"],
                                      "rows": copy.deepcopy(lap_rows)}]},
            "typed rows": {"id": 5, "date": "2026-10-20", "person": "P", "sessionKey": "intv", "durationSec": 99,
                           "entries": [{"name": "Run", "cols": ["Distance (km)", "Time", "Pace"],
                                        "rows": [[5, "30:00", "6:00"]]}]},
            "stamped rows": {"id": 6, "date": "2026-10-20", "person": "P", "sessionKey": "intv",
                             "garmin": {"rows_from": "laps"},
                             "entries": [{"name": "Run", "cols": ["Distance (km)", "Time", "Pace"],
                                          "rows": [[5, "30:00", "6:00"]]}]},
            "interval blank": {"id": 7, "date": "2026-10-20", "person": "P", "sessionKey": "intv",
                               "entries": [{"name": "Speed reps", "cols": ["Hard (km/h)", "Easy (km/h)"], "rows": []}]},
            "interval mph": {"id": 8, "date": "2026-10-20", "person": "P", "sessionKey": "intv",
                             "entries": [{"name": "Speed reps", "cols": ["Hard (mph)", "Easy (mph)"], "rows": []}]},
            "interval typed": {"id": 9, "date": "2026-10-20", "person": "P", "sessionKey": "intv",
                               "entries": [{"name": "Speed reps", "cols": ["Hard (km/h)", "Easy (km/h)"],
                                            "rows": [["12", ""]]}]},
            "no entries key": {"id": 10, "person": "P", "sessionKey": "intv"},
        }
        for lname, log in logs.items():
            for shape in shapes:
                for zones in (None, [1, 2, 3, 4, 5]):
                    typed = mk_typed(shape, random.Random(shape))
                    series = mk_series(shape, random.Random(shape + "s"), 2)
                    for extras in (None, {"typed_splits": typed, "series": series, "power_zone_secs": [1, 2, 3, 4, 5],
                                          "bodyweight_kg": 70}, {"typed_splits": [], "series": series}):
                        for lk in ("full", "none"):
                            rec(f"enrich_log {lname} {shape} {bool(zones)} {extras is not None and len(extras)} {lk}",
                                mod.enrich_log, log, mk_activity("flat"), mk_laps(lk), zones, program, extras)
            rec(f"enrich_log {lname} bare", mod.enrich_log, log, mk_activity("empty"), {}, None, None, None)
            rec(f"enrich_log {lname} sparse", mod.enrich_log, log, mk_activity("sparse"), mk_laps("nohr"))
        # a few more cases for segmentation paths through enrich_log
        for shape in shapes:
            for step in (1, 7):
                extras = {"typed_splits": [], "series": mk_series(shape, random.Random(shape + "x"), step)}
                rec(f"enrich_log trace only {shape} {step}", mod.enrich_log, logs["empty run"],
                    mk_activity("flat"), mk_laps("full"), None, program, extras)
                rec(f"enrich_log trace only interval {shape} {step}", mod.enrich_log, logs["interval blank"],
                    mk_activity("flat"), mk_laps("full"), None, program, extras)
        rec("_touch", lambda: mod._touch({}) or None)
        log = {}
        mod._touch(log)
        out["garmin/_touch value"] = canon(log)


class FakeClient:
    """A deterministic stand-in for garminconnect.Garmin: results depend on the id only."""

    def __init__(self, acts=(), dates=None):
        self.acts, self.dates = list(acts), dates or {}

    def _kind(self, aid):
        return ("walk_rec", "jog_rec", "mixed", "zone2", "stand", "adjacent", "single", "fade", "steady")[aid % 9]

    def get_activities(self, start, limit):
        return self.acts[:limit]

    def get_activity(self, aid):
        aid = int(aid)
        a = mk_activity(("flat", "nested", "sparse")[aid % 3], aid, self.dates.get(aid, "2026-10-%02d" % (1 + aid % 28)))
        if aid % 11 == 0:
            raise RuntimeError("no activity")
        return a

    def get_activity_splits(self, aid):
        aid = int(aid)
        if aid % 5 == 0:
            raise RuntimeError("no splits")
        return mk_laps(("full", "nohr", "none")[aid % 3])

    def get_activity_details(self, aid, maxchart=None, maxpoly=None):
        aid = int(aid)
        if aid % 7 == 0:
            raise RuntimeError("no details")
        series = mk_series(self._kind(aid), random.Random(aid), 3)
        return {"metricDescriptors": [{"key": "sumElapsedDuration", "metricsIndex": 0},
                                      {"key": "directSpeed", "metricsIndex": 1},
                                      {"key": "directHeartRate", "metricsIndex": 2},
                                      {"key": "directRunCadence", "metricsIndex": 3}],
                "activityDetailMetrics": [{"metrics": [t, k / 3.6, h, c]} for t, k, h, c in series]}

    def get_activity_typed_splits(self, aid):
        aid = int(aid)
        if aid % 13 == 0:
            raise RuntimeError("no typed splits")
        return {"splits": mk_typed(self._kind(aid), random.Random(aid))}

    def get_activity_hr_in_timezones(self, aid):
        aid = int(aid)
        if aid % 4 == 0:
            return []
        if aid % 6 == 0:
            raise RuntimeError("no hr zones")
        return [{"zoneNumber": i, "secsInZone": 100.4 * i * (aid % 3)} for i in range(1, 6)] + [{"secsInZone": 5}]

    def get_activity_power_in_timezones(self, aid):
        aid = int(aid)
        if aid % 2:
            return []
        return [{"zoneNumber": i, "secsInZone": 30.5 * i} for i in range(1, 6)]

    def connectapi(self, path):
        return [{"sport": "RUNNING", "zone1Floor": 1}, {"sport": "default", "zone1Floor": 100, "zone2Floor": 120,
                "zone3Floor": 140, "zone4Floor": 160, "zone5Floor": 175, "maxHeartRateUsed": 190,
                "restingHeartRateUsed": 50, "lactateThresholdHeartRateUsed": 168, "trainingMethod": "HR_MAX"}]

    def get_race_predictions(self):
        return {"time5K": 1500.4, "time10K": 3200, "timeHalfMarathon": 7000, "timeMarathon": 15000,
                "calendarDate": "2026-11-01"}

    def get_sleep_data(self, d):
        n = int(d[-2:])
        if n % 3 == 0:
            raise RuntimeError("no sleep")
        if n % 3 == 1:
            return {}
        return {"dailySleepDTO": {"sleepTimeSeconds": 27000 + n, "deepSleepSeconds": 5000, "lightSleepSeconds": 15000,
                                  "remSleepSeconds": 6000, "awakeSleepSeconds": 500, "avgHeartRate": 52.4,
                                  "avgSleepStress": 14.2, "averageRespirationValue": 14.66,
                                  "sleepScores": {"overall": {"value": 81}, "totalDuration": {"qualifierKey": "GOOD_ENOUGH"}}},
                "avgOvernightHrv": 61.2 if n % 2 else None, "hrvStatus": "BALANCED" if n % 4 else "NONE",
                "restingHeartRate": 51 if n % 2 else None}

    def get_hrv_data(self, d):
        return {"hrvSummary": {"lastNightAvg": 58.5, "status": "LOW"}}

    def get_stats(self, d):
        return {"restingHeartRate": 53}

    def get_training_readiness(self, d):
        return [{"score": 72, "level": "HIGH"}] if int(d[-2:]) % 2 else {"score": None}


def run_garmin_flows(mod, store, ctx, store_text, out):
    P = store["people"]
    mcp = FakeMCP()
    mod._register(mcp)

    def flow(name, steps, store_edit=None, acts=(), fail=(), dates=None):
        data = copy.deepcopy(store)
        if store_edit:
            store_edit(data)
        mod._client = FakeClient(acts, dates)
        text = json.dumps(data, indent=2)
        run_steps(mod, mcp.tools, "garmin/" + name, steps, {"data.json": text}, fail, out)
        mod._client = None

    flow("tools-read", [("recent_runs", "garmin_recent_runs", {"limit": 3}),
                        ("recent_acts", "garmin_recent_activities", {"limit": 3}),
                        ("activity", "garmin_activity", {"activity_id": "101"}),
                        ("activity2", "garmin_activity", {"activity_id": "102"})],
         acts=[mk_activity("flat", 1), mk_activity("dto", 2), mk_activity("sparse", 3)] * 4)
    flow("import", [("run", "garmin_import_run", {"activity_id": "101", "person": P[0]}),
                    ("again", "garmin_import_run", {"activity_id": "101", "person": P[0]}),
                    ("dto", "garmin_import_run", {"activity_id": "103", "person": P[1]}),
                    ("bad", "garmin_import_run", {"activity_id": "110", "person": P[1]})])
    flow("import conflict", [("run", "garmin_import_run", {"activity_id": "104", "person": P[0]})],
         fail=[("data.json", 409), ("data.json", 409)])
    flow("import exhausted", [("run", "garmin_import_run", {"activity_id": "104", "person": P[0]})],
         fail=[("data.json", 409)] * 3)
    flow("import error", [("run", "garmin_import_run", {"activity_id": "104", "person": P[0]})],
         fail=[("data.json", 500)])

    def wanted(person, n=4):
        pend = {}

        def edit(data):
            picks = [l for l in data["logs"] if l.get("person") == person and
                     any("dist" in str(c).lower() for e in l.get("entries") or [] for c in e.get("cols") or [])][:n]
            for i, l in enumerate(picks):
                l["garminWanted"] = True
                l.pop("garminActivityId", None)
                l.pop("garmin", None)
                pend[l["id"]] = (9000 + i, l["date"])
        return pend, edit

    for p in P:
        pend, edit = wanted(p)
        edit(copy.deepcopy(store))      # dry run to learn ids/dates
        edit_dates = {aid: d for aid, d in pend.values()}
        acts = [dict(mk_activity("flat", aid, d), startTimeLocal=f"{d} 0{aid % 9}:00:00") for aid, d in pend.values()]
        acts.insert(0, mk_activity("dto", 8999, "2026-10-01"))
        flow(f"fill_pending {p}", [("fill", "garmin_fill_pending", {"person": p}),
                                   ("again", "garmin_fill_pending", {"person": p})],
             store_edit=edit, acts=acts, dates=edit_dates)
        flow(f"fill_pending none {p}", [("fill", "garmin_fill_pending", {"person": p})])
        flow(f"fill_pending conflict {p}", [("fill", "garmin_fill_pending", {"person": p})],
             store_edit=edit, acts=acts, dates=edit_dates, fail=[("data.json", 409)])
        flow(f"refresh {p}", [("refresh", "garmin_refresh_metrics", {"person": p})])
        flow(f"hr_zones {p}", [("zones", "garmin_hr_zones", {"person": p}),
                               ("again", "garmin_hr_zones", {"person": p})])
        flow(f"wellness {p}", [("wellness", "garmin_wellness", {"person": p, "days": 6}),
                               ("again", "garmin_wellness", {"person": p, "days": 6}),
                               ("zero", "garmin_wellness", {"person": p, "days": 0})])
        flow(f"wellness conflict {p}", [("wellness", "garmin_wellness", {"person": p, "days": 4})],
             fail=[("data.json", 412)])
        lid = next(l["id"] for l in store["logs"] if l.get("person") == p)
        edit_link = lambda data, lid=lid: [l.pop("garminActivityId", None) for l in data["logs"] if l["id"] == lid]
        flow(f"enrich {p}", [("link", "garmin_enrich_session",
                              {"session_id": str(lid), "activity_id": "201", "person": p}),
                             ("again", "garmin_enrich_session",
                              {"session_id": str(lid), "activity_id": "201", "person": p}),
                             ("missing", "garmin_enrich_session",
                              {"session_id": "0", "activity_id": "201", "person": p}),
                             ("nonrun", "garmin_enrich_session",
                              {"session_id": str(lid), "activity_id": "210", "person": p})],
             store_edit=edit_link)

    # direct calls to the pieces the tools wrap
    steps = [("hr_zone_times", "fn:fetch_hr_zone_times", {"activity_id": i}) for i in range(1, 9)]
    steps += [("power_zone_times", "fn:fetch_power_zone_times", {"activity_id": i}) for i in range(1, 9)]
    steps += [("extras", "fn:fetch_activity_extras", {"activity_id": i}) for i in range(1, 15)]
    steps += [("series", "fn:fetch_detail_series", {"activity_id": i}) for i in (1, 7, 8)]
    steps += [("typed", "fn:fetch_typed_splits", {"activity_id": i}) for i in (1, 13)]
    steps += [("hr_zones", "fn:fetch_hr_zones", {}), ("race", "fn:fetch_race_predictions", {})]
    steps += [("wellness_day", "fn:fetch_wellness_day", {"date": "2026-10-%02d" % d}) for d in range(1, 9)]
    steps += [("backfill_zones", "fn:backfill_hr_zone_times", {"person": P[0]}),
              ("backfill_zones limit", "fn:backfill_hr_zone_times", {"person": P[1], "limit": 2}),
              ("backfill_entries", "fn:backfill_run_entries", {"person": P[0]}),
              ("backfill_entries 2", "fn:backfill_run_entries", {"person": P[1], "limit": 3}),
              ("race_sync", "fn:sync_race_predictions", {"person": P[0]}),
              ("race_sync again", "fn:sync_race_predictions", {"person": P[0]}),
              ("hrz_sync", "fn:sync_hr_zones", {"person": P[1]}),
              ("hrz_sync again", "fn:sync_hr_zones", {"person": P[1]})]

    def strip_run_entries(data):
        for l in data["logs"][:12]:
            l["entries"] = [e for e in l.get("entries") or [] if "dist" not in " ".join(map(str, e.get("cols") or [])).lower()]
            l.get("garmin", {}).pop("hr_zone_secs", None)
    flow("direct", steps, store_edit=strip_run_entries)

    # CLI entry points: env check and printed output
    def cli(args_by_fn):
        res = {}
        for fn, argv in args_by_fn:
            for person in (None, P[0]):
                buf = io.StringIO()
                if person:
                    os.environ["TT_PERSON"] = person
                else:
                    os.environ.pop("TT_PERSON", None)
                with contextlib.redirect_stdout(buf):
                    r = attempt(getattr(mod, fn), list(argv))
                res[f"{fn} {argv} {person}"] = {"ret": r, "stdout": buf.getvalue()}
        os.environ.pop("TT_PERSON", None)
        return res
    steps = [(k, "fn:_noop", {}) for k in ()]
    mod._client = FakeClient()
    hub = FakeHub({"data.json": store_text})
    with patched(mod, hub):
        for k, v in cli([("_sync", []), ("_hrzones", []), ("_refresh", []), ("_wellness", []),
                         ("_wellness", ["3"])]).items():
            out[f"garmin/cli {k}"] = canon(v)
    out["garmin/cli #requests"] = canon(hub.log)
    mod._client = None


# ---------------------------------------------------------------- selftests
def run_selftest(path, argv, key, out, cwd):
    r = subprocess.run([sys.executable, path] + argv, capture_output=True, text=True, cwd=cwd,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    stdout = re.sub(r'"updatedAt": \d+', '"updatedAt": 0', r.stdout)
    out[key] = canon({"rc": r.returncode, "stdout": stdout, "stderr": r.stderr[-300:]})


# ---------------------------------------------------------------- main
def collect(rel, srcpath, store, store_text, ctx, tag):
    out = {}
    mod = load_module(srcpath, f"{tag}_{rel.split('/')[0]}")
    if rel.startswith("mcp-coach"):
        out.update(run_coach(mod, store_text, ctx))
        run_selftest(srcpath, ["--selftest", DATA_FILE], "coach/--selftest", out, tempfile.gettempdir())
    else:
        run_garmin_pure(mod, store, out)
        run_garmin_flows(mod, store, ctx, store_text, out)
        sample = os.path.join(ROOT, "mcp-garmin", "sample-activity.json")
        run_selftest(srcpath, ["--selftest", sample], "garmin/--selftest", out, tempfile.gettempdir())
    return out


def report(old, new, label):
    keys = sorted(set(old) | set(new))
    bad = [k for k in keys if old.get(k) != new.get(k)]
    print(f"{label}: {len(keys)} keys compared, {len(bad)} differ")
    for k in bad:
        a, b = old.get(k), new.get(k)
        if a is None or b is None:
            print(f"  {k}: only in {'new' if a is None else 'old'}")
            continue
        diff = [l for l in difflib.unified_diff(a.splitlines(), b.splitlines(), "old", "new", lineterm="", n=0)
                if not l.startswith(("---", "+++", "@@"))]
        print(f"  {k}: {len(diff)} changed lines")
        for l in diff[:6]:
            print("     " + (l if len(l) < 220 else l[:217] + "..."))
    return len(bad)


def main():
    global DATA_FILE
    ap = argparse.ArgumentParser()
    ap.add_argument("--self", action="store_true", help="compare the base revision with itself")
    ap.add_argument("--base", default="5bd76a3")
    ap.add_argument("--only", choices=list(SERVERS))
    ap.add_argument("--dump", help="print the base results whose key contains this text")
    ap.add_argument("--errors", action="store_true", help="list base results that raised")
    args = ap.parse_args()
    DATA_FILE = sorted(glob.glob(os.path.join(ROOT, "scratchpad", "data-backup-*.json")))[-1]
    with open(DATA_FILE, encoding="utf-8") as f:
        store = json.load(f)
    store_text = json.dumps(store, indent=2)
    ctx = derive(store)
    total = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, rel in SERVERS.items():
            if args.only and args.only != name:
                continue
            old_path = base_source(args.base, rel, tmp)
            new_path = old_path if args.self else os.path.join(ROOT, rel)
            old = collect(rel, old_path, store, store_text, ctx, "old")
            new = collect(rel, new_path, store, store_text, ctx, "new")
            for k in sorted(old):
                if args.dump and args.dump in k:
                    print(k, "=>", old[k][:400])
                if args.errors and '"EXC"' in old[k][:12] + old[k][:40]:
                    print("raised:", k, old[k].replace(chr(10), " ")[:160])
            total += report(old, new, name)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
