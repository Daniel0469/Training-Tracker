"""Run the coach and Garmin server scenarios of check_servers.py twice, on the GitHub store and on
the Supabase store (fake_postgrest.py), and compare what each tool returns and what each store
holds afterwards.

    python scratchpad/run_supabase_servers.py

The scenarios, the stubbed Garmin client and the frozen clock are check_servers.py's. Only the
store behind the servers changes: FakeHub and patched() in that module are swapped for versions
that serve the same files from a fake PostgREST. No network, and the newest scratchpad
data-backup-*.json is the only data read. Exit status 1 when anything differs.
"""
import contextlib, copy, difflib, json, os, sys, time, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, "mcp-coach")]
import check_servers as cs
import tt_records
from fake_postgrest import FakePostgrest
from test_records import canon as canon_data, latest_store

URL, SECRET = "https://fake.test", "sb-secret-for-tests"
KINDS = {"data.json": set(tt_records.KNOWN_KINDS), "coaching-log": {"coach_log"}, "coach/": {"coach_file"}}


class SbHub:
    """cs.FakeHub's interface over a fake PostgREST: files in, requests logged, files out."""

    def __init__(self, files, fail_puts=()):
        self.fake = FakePostgrest(URL, SECRET)
        coach = {k[len("coach/"):]: v for k, v in files.items() if k.startswith("coach/")}
        self.fake.seed(tt_records.to_records(json.loads(files["data.json"]), now=1, coach_files=coach,
                                             coaching_log=json.loads(files.get("coaching-log.json", "[]"))))
        for substr, code in fail_puts:
            self.fake.fail_posts.append((code, next(k for name, k in KINDS.items() if name in substr)))

    def urlopen(self, req, timeout=None):
        return self.fake.urlopen(req, timeout)

    @property
    def log(self):
        return self.fake.log

    @property
    def files(self):
        rows = list(self.fake.rows.values())
        files = {"data.json": json.dumps(tt_records.from_records(rows), indent=2)}
        coach, log = tt_records.coach_parts(rows)
        if log:
            files["coaching-log.json"] = json.dumps(log, indent=1)
        files.update({"coach/" + k: v for k, v in coach.items()})
        return files


@contextlib.contextmanager
def ticking(mod, hub):
    """check_servers freezes time.time, so every id the servers make from it is the same one.
    Here it moves on a millisecond per call, which gives each record its own id as in real use."""
    with ORIGINAL_PATCHED(mod, hub):
        ticks = iter(range(10 ** 9))
        time.time = lambda: cs.FROZEN + next(ticks) / 1000
        yield


@contextlib.contextmanager
def patched_sb(mod, hub):
    saved = {k: os.environ.pop(k, None) for k in ("TT_SUPABASE_URL", "TT_SUPABASE_SECRET_KEY")}
    os.environ["TT_SUPABASE_URL"], os.environ["TT_SUPABASE_SECRET_KEY"] = URL, SECRET
    try:
        with ticking(mod, hub):
            yield
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


ORIGINAL_PATCHED, ORIGINAL_HUB = cs.patched, cs.FakeHub


@contextlib.contextmanager
def patched_gh(mod, hub):
    with ORIGINAL_PATCHED(mod, hub):
        yield


def memory_flow(mod, store, store_text, out):
    """The coach memory tools: profile and decision files, and questions in data.json."""
    mcp = cs.FakeMCP()
    mod._register(mcp)
    a, b = store["people"][:2]
    decision = dict(scope="Weekly run", before="20 minutes easy", after="15 minutes easy this week",
                    reason="Observed: busy work week, no shin symptoms reported.", expected="One manageable run",
                    review_due="2026-11-09", authority="run, delegated", rule="P14", watch="shin pain")
    steps = [("profile none", "coach_profile", {"person": a}),
             ("profile write", "write_coach_profile", {"person": a, "text": f"# Profile: {a}\n\nGoals: example.\n"}),
             ("profile again", "write_coach_profile", {"person": a.lower(), "text": f"# Profile: {a}\n\nSecond version.\n"}),
             ("profile read", "coach_profile", {"person": a}),
             ("profile other", "coach_profile", {"person": b}),
             ("decision add", "add_coach_decision", {"person": a, **decision}),
             ("decision second", "add_coach_decision", {"person": a, **dict(decision, scope="Bench", review_due="2026-11-02")}),
             ("decision review", "review_coach_decision", {"person": a, "decision_id": "D-20261102-02",
                                                           "implementation": "not_completed", "outcome": "not_yet_evaluable",
                                                           "observed": "Not logged.", "next_action": "defer"}),
             ("decisions read", "coach_decisions", {"person": a}),
             ("question add", "add_coach_question", {"person": a, "question": "Did it feel fine?", "why": "Sets the run length.",
                                                     "question_id": "Q-1"}),
             ("question add other", "add_coach_question", {"person": b, "question": "Any soreness?", "why": "Safety.",
                                                           "priority": "safety", "question_id": "Q-1"}),
             ("question remind", "remind_coach_question", {"person": a, "question_id": "Q-1", "next_follow_up": "2026-11-16"}),
             ("question list", "coach_questions", {"person": a}),
             ("question close", "close_coach_question", {"person": a, "question_id": "Q-1", "reason": "Done."}),
             ("question list again", "coach_questions", {"person": a, "status": "all"}),
             ("question list other", "coach_questions", {"person": b})]
    cs.run_steps(mod, mcp.tools, "memory", steps, {"data.json": store_text}, (), out)


def collect(use_supabase, store, store_text, ctx):
    cs.patched, cs.FakeHub = (patched_sb, SbHub) if use_supabase else (ticking, ORIGINAL_HUB)
    out = {}
    coach = cs.load_module(os.path.join(ROOT, "mcp-coach", "server.py"), "coach_" + str(use_supabase))
    out.update(cs.run_coach(coach, store_text, ctx))
    memory_flow(coach, store, store_text, out)
    garmin = cs.load_module(os.path.join(ROOT, "mcp-garmin", "server.py"), "garmin_" + str(use_supabase))
    cs.run_garmin_flows(garmin, store, ctx, store_text, out)
    return out


def unordered(value):
    """Lists in a tool's reply compared as sets: the table keeps no row order."""
    if isinstance(value, dict):
        return {k: unordered(v) for k, v in value.items()}
    if isinstance(value, list):
        return sorted((unordered(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
    return value


def comparable(key, text):
    """Files compare by meaning (list order and exportedAt are not stored). Requests differ by design."""
    if key.endswith("#requests") or "/load_data" in key:
        return None
    if "#file data.json" in key:
        data = json.loads(text)
        for extra in ("programs", "programIds"):        # the Supabase store always has the app's new shape
            data.pop(extra, None)
        data["program"] = {k: v for k, v in data.get("program", {}).items() if k not in ("id", "members", "version")}
        return json.dumps(canon_data(data), sort_keys=True, indent=1)
    if "#file coaching-log.json" in key:
        return json.dumps(sorted(json.loads(text), key=lambda e: e["id"]), sort_keys=True, indent=1)
    try:
        return json.dumps(unordered(json.loads(text)), sort_keys=True, indent=1)
    except ValueError:
        return text


def compare(gh, sb):
    keys = sorted(set(gh) | set(sb))
    bad = compared = 0
    for k in keys:
        a, b = comparable(k, gh.get(k, "")), comparable(k, sb.get(k, ""))
        compared += a is not None
        if a is None or a == b:
            continue
        bad += 1
        diff = [l for l in difflib.unified_diff(a.splitlines(), b.splitlines(), "github", "supabase", lineterm="", n=0)
                if not l.startswith(("---", "+++", "@@"))]
        print(f"  {k}: {len(diff)} changed lines")
        for l in diff[:6]:
            print("     " + (l if len(l) < 200 else l[:197] + "..."))
    print(f"scenarios and files compared: {compared}, differing: {bad}")
    return bad


def extra_checks(store, store_text):
    """What the scenarios cannot show: only changed rows are sent, a moved row is retried, a wrong key is refused."""
    cs.patched, cs.FakeHub = patched_sb, SbHub
    mod = cs.load_module(os.path.join(ROOT, "mcp-coach", "server.py"), "coach_extra")
    failures = []

    def check(name, ok, note=""):
        print(("ok   " if ok else "FAIL ") + name + (f"  ({note})" if note else ""))
        if not ok:
            failures.append(name)
    hub = SbHub({"data.json": store_text})
    log_id = store["logs"][0]["id"]
    with cs.patched(mod, hub):
        check("load_data returns the stored data", canon_data(mod.load_data()) == canon_data(store))

        def tag_one_log(data):
            next(l for l in data["logs"] if l["id"] == log_id)["feedback"] = "from the coach"
            return {"done": True}
        check("_prog_of finds each person's program", all(mod._prog_of(mod.load_data(), p)["sessions"] == store["program"]["sessions"]
                                                         for p in store["people"]))
        mod._github_update(tag_one_log, "tag")
        posts = [r for r in hub.log if r["method"] == "POST"]
        check("a one-log edit sends one row", len(posts) == 1 and len(posts[0]["body"]) == 1,
              f"{[len(p['body']) for p in posts]} rows")
        check("the row is that log, stamped by the coach", posts[0]["body"][0]["key"] == str(log_id)
              and posts[0]["body"][0]["by"] == "coach")

        calls = []

        def tag_again(data):
            calls.append(1)
            if len(calls) == 1:
                hub.fake.touch("log", str(log_id))          # a phone writes the same record meanwhile
            next(l for l in data["logs"] if l["id"] == log_id)["difficulty"] = 4
            return {"done": True}
        mod._github_update(tag_again, "tag again")
        check("a moved row is read again and the change redone", len(calls) == 2)
        row = hub.fake.rows[("log", str(log_id))]
        check("both coach edits are kept", row["body"].get("feedback") == "from the coach" and row["body"].get("difficulty") == 4)

        before = len(hub.log)
        mod._github_update(lambda data: {"nothing": True}, "no change")
        check("an unchanged store sends no write", all(r["method"] == "GET" for r in hub.log[before:]))

        def drop_one(data):
            data["logs"] = [l for l in data["logs"] if l["id"] != log_id]
            return {"done": True}
        mod._github_update(drop_one, "drop")
        gone = hub.fake.rows[("log", str(log_id))]
        check("removing a log soft-deletes it and keeps its body", gone["deleted_at"] and gone["body"].get("feedback"))
        check("it no longer reads back", all(l["id"] != log_id for l in mod.load_data()["logs"]))

        def drop_key(data):
            del data["coaching"][store["people"][0]]["overall"]
            return {"done": True}
        mod._github_update(drop_key, "drop key")
        key = ("person_data:coaching", store["people"][0])
        check("a removed key stays removed", "overall" not in hub.fake.rows[key]["body"]
              and "overall" not in mod.load_data()["coaching"][store["people"][0]])

        os.environ["TT_SUPABASE_SECRET_KEY"] = "wrong"
        try:
            mod.load_data()
            check("a wrong key is refused", False)
        except urllib.error.HTTPError as e:
            check("a wrong key is refused", e.code == 401)
        os.environ["TT_SUPABASE_SECRET_KEY"] = SECRET
    return failures


def main():
    with open(latest_store(), encoding="utf-8") as f:
        store = json.loads(f.read())
    # The table keeps no list order, so both runs start from the order it would hand back.
    store = tt_records.from_records(tt_records.to_records(store, now=1))
    store_text = json.dumps(store, indent=2)
    ctx = cs.derive(store)
    cs.DATA_FILE = latest_store()
    print("GitHub store:")
    gh = collect(False, store, store_text, ctx)
    print("Supabase store:")
    sb = collect(True, store, store_text, ctx)
    bad = compare(gh, sb)
    print("extra checks:")
    bad += len(extra_checks(store, store_text))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
