#!/usr/bin/env python3
"""Run the coach memory tools of mcp-coach/server.py from a FRESH process against a COPY of the
store, so it shows what the current file does rather than what a long-running MCP server loaded
at startup. GitHub is stubbed with the in-memory hub from check_servers.py: nothing leaves the
machine and the shared store and the Training-Data repo are never opened.

    python scratchpad/run_coach_memory.py            # newest scratchpad/data-backup-*.json

Exercises coach_profile, write_coach_profile, coach_decisions, add_coach_decision,
review_coach_decision, coach_questions, add_coach_question, remind_coach_question and
close_coach_question, prints each result and ends with a pass/fail list.
"""
import glob, importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scratchpad"))
from check_servers import FakeHub, FakeMCP, patched

spec = importlib.util.spec_from_file_location("ttc", os.path.join(ROOT, "mcp-coach", "server.py"))
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

path = sorted(glob.glob(os.path.join(ROOT, "scratchpad", "data-backup-*.json")))[-1]
store_text = open(path, encoding="utf-8").read()
store = json.loads(store_text)
A, B = store["people"][:2]
print("store copy:", os.path.basename(path), "people:", A, B)

tools = FakeMCP()
S._register(tools)
results = []


def call(name, **kw):
    return json.loads(tools.tools[name](**kw))


def show(label, out):
    text = json.dumps(out)
    print("%-34s %s" % (label, text if len(text) < 230 else text[:227] + "..."))
    return out


def check(label, ok):
    results.append((label, bool(ok)))


def data_json(hub):
    return json.loads(hub.files["data.json"])


DECISION = dict(scope="Weekly run", before="20 minutes easy", after="15 minutes easy this week",
                reason="Observed: busy work week, no shin symptoms reported. Thought: a shorter run is easier to start.",
                expected="One manageable run with no symptom worse", review_due="2026-11-09",
                authority="run, delegated", rule="P14", exposure_needed="1 run", watch="shin pain during the run")

hub = FakeHub({"data.json": store_text})
with patched(S, hub):
    print("\n-- profile")
    out = show("read, none yet", call("coach_profile", person=A))
    check("profile starts empty", out["exists"] is False)
    show("unknown person", call("coach_profile", person="Nobody"))
    show("too short", call("write_coach_profile", person=A, text="x"))
    out = show("write", call("write_coach_profile", person=A, text="# Profile: %s\n\nGoals: made-up example, 2026-11-02, athlete report.\n" % A))
    check("profile written under coach/<name>/", "coach/%s/profile.md" % A in hub.files)
    out = show("write again", call("write_coach_profile", person=A.lower(), text="# Profile: %s\n\nGoals: second version.\n" % A))
    check("whole file replaced, name matched ignoring case", out["replaced"] and "second version" in hub.files["coach/%s/profile.md" % A])
    out = show("read back", call("coach_profile", person=A))
    check("read back equals written", out["text"] == hub.files["coach/%s/profile.md" % A])
    show("other person untouched", call("coach_profile", person=B))

    print("\n-- decisions")
    show("missing field", call("add_coach_decision", person=A, **dict(DECISION, expected="")))
    show("bad agreement", call("add_coach_decision", person=A, agreement="yes", **DECISION))
    show("bad date", call("add_coach_decision", person=A, **dict(DECISION, review_due="soon")))
    show("bad person", call("add_coach_decision", person="Nobody", **DECISION))
    first = show("add", call("add_coach_decision", person=A, **DECISION))
    second = show("add, same day", call("add_coach_decision", person=A, **dict(
        DECISION, scope="Bench press", before="60 kg 3x8", after="62.5 kg 3x8", rule="P4", review_due="2026-11-02")))
    check("ids count up", (first["decision_id"], second["decision_id"]) == ("D-20261102-01", "D-20261102-02"))
    check("due decision in the index", any("D-20261102-02" in r for r in second["index"]["due"]))
    show("supersede a missing one", call("add_coach_decision", person=A, supersedes="D-1", **DECISION))
    third = show("supersede the first", call("add_coach_decision", person=A, supersedes="D-20261102-01",
                                             decision_id="D-20261102-09", **dict(DECISION, after="10 minutes easy")))
    text = hub.files["coach/%s/decisions.md" % A]
    check("old decision marked superseded", "superseded_by: D-20261102-09" in text)
    check("original rationale kept on the superseded entry", text.count("Observed: busy work week") == 3)
    show("duplicate id", call("add_coach_decision", person=A, decision_id="D-20261102-09", **DECISION))
    show("review: not found", call("review_coach_decision", person=A, decision_id="D-1", outcome="helpful"))
    show("review: nothing given", call("review_coach_decision", person=A, decision_id="D-20261102-02"))
    show("review: bad outcome", call("review_coach_decision", person=A, decision_id="D-20261102-02", outcome="great"))
    out = show("review: not tried", call("review_coach_decision", person=A, decision_id="D-20261102-02",
                                         implementation="not_completed", outcome="not_yet_evaluable",
                                         observed="Bench was not logged this week.", next_action="defer",
                                         uncertainty="Reason unknown."))
    check("outcome marks it reviewed", out["status"] == "reviewed")
    out = show("review: keep watching", call("review_coach_decision", person=A, decision_id="D-20261102-09",
                                             agreement="agreed", response_quote="Fine by me.", outcome="uncertain",
                                             next_review="2026-11-16", next_action="keep"))
    check("next_review keeps it active", out["status"] == "applied" and any("2026-11-16" in r for r in out["index"]["active"]))
    out = show("read decisions", {k: v for k, v in call("coach_decisions", person=A).items() if k != "text"})
    text = call("coach_decisions", person=A)["text"]
    print(text)
    check("index sits above the entries", text.index("## Index") < text.index("## Entries"))
    check("no entry text lost on review", "Observed: busy work week" in text and "Bench was not logged" in text)
    check("other person has no decisions", call("coach_decisions", person=B)["exists"] is False)
    check("data.json untouched by the file tools", data_json(hub) == store)

    print("\n-- questions")
    show("missing why", call("add_coach_question", person=A, question="Which day?", why=""))
    show("bad priority", call("add_coach_question", person=A, question="Which day?", why="x", priority="urgent"))
    q1 = show("add", call("add_coach_question", person=A, question="Did the shorter run feel manageable?",
                          why="Decides whether the run stays at 15 minutes.", priority="blocking",
                          decision="D-20261102-01"))
    show("add duplicate", call("add_coach_question", person=A, question="did the SHORTER run feel manageable", why="x"))
    q2 = show("add, other person", call("add_coach_question", person=B, question="Any shin soreness the morning after?",
                                        why="Needed before the run changes.", priority="safety"))
    for text_ in ("Prefer mornings?", "Prefer cables?", "Prefer dumbbells?", "Prefer barbells?"):
        last = call("add_coach_question", person=A, question=text_, why="x", priority="routine")
    show("fourth routine question", last)
    check("warns over three routine questions", "warning" in last)
    show("list open", call("coach_questions", person=A))
    check("people kept apart", all(q["question"] != q2["question"]["question"] for q in call("coach_questions", person=A)["questions"]))
    show("list other person", call("coach_questions", person=B))

    qid = q1["question"]["id"]
    d = data_json(hub)
    mine = next(q for q in d["coachQuestions"][A] if q["id"] == qid)
    mine.update(status="answered", answer="Yes, it felt fine.", answeredAt="2026-11-03", updatedAt=S._now_ms() + 1000)
    hub.files["data.json"] = json.dumps(d, indent=2)
    out = show("list answered (as the app wrote)", call("coach_questions", person=A, status="answered"))
    check("answer visible to the coach", out["questions"][0]["answer"] == "Yes, it felt fine.")
    show("remind an answered one", call("remind_coach_question", person=A, question_id=qid))
    other = call("coach_questions", person=A)["questions"][1]["id"]
    out = show("remind an open one", call("remind_coach_question", person=A, question_id=other, next_follow_up="2026-11-16"))
    check("reminder counted", out["question"]["reminders"] == 1 and out["question"]["nextFollowUp"] == "2026-11-16")
    show("close without a reason", call("close_coach_question", person=A, question_id=qid, reason=""))
    out = show("close", call("close_coach_question", person=A, question_id=qid, reason="Answered and acted on."))
    check("closed and stamped", out["question"]["status"] == "closed" and out["question"]["updatedAt"] == S._now_ms())
    show("close again", call("close_coach_question", person=A, question_id=qid, reason="again"))
    show("wrong person's id", call("close_coach_question", person=B, question_id=other, reason="x"))
    check("closed one leaves the open list", all(q["id"] != qid for q in call("coach_questions", person=A)["questions"]))
    show("list all", call("coach_questions", person=A, status="all"))
    check("other person's question untouched", data_json(hub)["coachQuestions"][B] == [q2["question"]])
    after = data_json(hub)
    check("only coachQuestions changed in data.json", {k: v for k, v in after.items() if k != "coachQuestions"} == store)

    print("\n-- conflicts")
    hub.fail_puts = [["decisions.md", 409]]
    out = show("decision write, one 409", call("add_coach_decision", person=B, **DECISION))
    check("409 retried", out.get("ok") is True)
    hub.fail_puts = [["profile.md", 422]]
    out = show("profile create, one 422", call("write_coach_profile", person=B, text="# Profile: %s\n\nMade-up example.\n" % B))
    check("422 on create retried", out.get("ok") is True)
    hub.fail_puts = [["data.json", 409]]
    out = show("question write, one 409", call("add_coach_question", person=B, question="Another one?", why="x"))
    check("409 retried on data.json", out.get("ok") is True)
    hub.files["coach/%s/decisions.md" % B] = "free text with no entries heading\n"
    out = show("decisions file not in format", call("add_coach_decision", person=B, **DECISION))
    check("refuses to rewrite a file it cannot parse", out.get("ok") is False and "format" in out["error"])
    check("only the stub was called", all("api.github.com/repos/owner/store/contents/" in r["url"] for r in hub.log))

hub = FakeHub({"sub/data.json": store_text})
with patched(S, hub):
    os.environ["TT_GITHUB_PATH"] = "sub/data.json"
    print("\n-- paths follow the store path")
    call("write_coach_profile", person=A, text="# Profile: %s\n\nMade-up example.\n" % A)
    print(sorted(hub.files))
    check("memory sits next to the store file", "sub/coach/%s/profile.md" % A in hub.files)
    os.environ["TT_GITHUB_LOG_PATH"] = "elsewhere/log.json"
    call("write_coach_profile", person=B, text="# Profile: %s\n\nMade-up example.\n" % B)
    check("the log path sets the folder", "elsewhere/coach/%s/profile.md" % B in hub.files)
    os.environ.pop("TT_GITHUB_PATH")
    os.environ.pop("TT_GITHUB_LOG_PATH")

print("\n-- results")
for label, ok in results:
    print("%-4s %s" % ("PASS" if ok else "FAIL", label))
failed = [label for label, ok in results if not ok]
print("%d checks, %d failed" % (len(results), len(failed)))
sys.exit(1 if failed else 0)
