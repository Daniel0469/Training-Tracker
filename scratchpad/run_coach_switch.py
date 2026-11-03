#!/usr/bin/env python3
"""Run the coach tools of mcp-coach/server.py from a FRESH process against a COPY of the store
with one person's Garmin and coach switch off, to show what the current file does rather than what
a long-running MCP server loaded at startup. GitHub is stubbed with the in-memory hub from
check_servers.py: nothing leaves the machine and the shared store is never opened.

    python scratchpad/run_coach_switch.py            # newest scratchpad/data-backup-*.json

The second person has features[name].garmin.on = false. Shows people (coach_on), write_coaching,
add_coach_question and remind_coach_question refused for her and unchanged for the first person,
progression marking coach_off with her target hidden, write_run keeping the session change but
skipping the note, and ends with a pass/fail list.
"""
import glob, importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scratchpad"))
sys.path.insert(0, os.path.join(ROOT, "mcp-coach"))
from check_servers import FakeHub, FakeMCP, patched
import progression

spec = importlib.util.spec_from_file_location("ttc", os.path.join(ROOT, "mcp-coach", "server.py"))
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

path = sorted(glob.glob(os.path.join(ROOT, "scratchpad", "data-backup-*.json")))[-1]
store = json.loads(open(path, encoding="utf-8").read())
A, B = store["people"][:2]
print("store copy:", os.path.basename(path), "- switch off for", B)

incline = next(e for e in store["program"]["sessions"]["upper1"]["exercises"] if e["name"] == "Incline DB press")
rule = progression.progression_for(store, B, incline)
store["coaching"][B]["targets"] = {"Incline DB press": {
    "kg": 14, "reps": 10, "why": "Made-up example.", "rule": rule["target"],
    "asOfLog": progression.latest_log_id(store, B, "Incline DB press"), "updated": "2026-11-02"}}
store["features"] = {B: {"garmin": {"on": False, "updatedAt": 1793100000000}}}
store_text = json.dumps(store, indent=2)

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


hub = FakeHub({"data.json": store_text})
with patched(S, hub):
    out = show("people", call("people"))
    check("people say who has the coach on", [p["coach_on"] for p in out] == [True, False])

    before = hub.files["data.json"]
    out = show("write_coaching, switched off", call("write_coaching", person=B, overall="Made-up note.",
                                                    by_session={"Upper A": "Made-up note."}))
    check("coaching write refused", out["ok"] is False and "switched off" in out["error"])
    out = show("add question, switched off", call("add_coach_question", person=B, question="Any soreness?", why="x"))
    check("question refused", out["ok"] is False and "switched off" in out["error"])
    check("nothing written by the refusals", hub.files["data.json"] == before)

    out = show("write_coaching, switched on", call("write_coaching", person=A, overall="Made-up note."))
    check("first person still coached", out["ok"] is True)
    out = show("add question, switched on", call("add_coach_question", person=A, question="Any soreness?", why="x"))
    check("first person still asked", out["ok"] is True)

    d = json.loads(hub.files["data.json"])
    d["coachQuestions"] = {B: [{"id": "Q-1", "question": "Old one?", "why": "x", "priority": "routine", "status": "open",
                                "reminders": 0, "nextFollowUp": "2026-11-09", "updatedAt": 1}]}
    hub.files["data.json"] = json.dumps(d, indent=2)
    out = show("remind, switched off", call("remind_coach_question", person=B, question_id="Q-1"))
    check("reminder refused", out["ok"] is False and "switched off" in out["error"])
    out = show("close, switched off", call("close_coach_question", person=B, question_id="Q-1", reason="Switched off."))
    check("closing still allowed", out["ok"] is True)

    out = show("progression, switched off", {k: v for k, v in call("progression", person=B).items() if k != "exercises"})
    check("progression marks coach_off", "coach_off" in out)
    rows = call("progression", person=B)["exercises"]
    check("coach target hidden", all("coach" not in r for r in rows))
    check("rule target still shown", any(r["exercise"] == "Incline DB press" and r.get("target") is not None for r in rows))
    check("first person has no coach_off mark", "coach_off" not in call("progression", person=A))

    out = show("write_run, switched off", call("write_run", person=B, which="Quality run", why="Made-up reason.", warmup="Made-up warm-up."))
    check("session change kept", out["ok"] is True and "warmupNote" in out["changed"])
    check("note skipped", "note_skipped" in out)
    after = json.loads(hub.files["data.json"])
    check("no coach note written for her", "Made-up reason." not in json.dumps(after["coaching"][B]))

print("\n-- results")
for label, ok in results:
    print("%-4s %s" % ("PASS" if ok else "FAIL", label))
failed = [label for label, ok in results if not ok]
print("%d checks, %d failed" % (len(results), len(failed)))
sys.exit(1 if failed else 0)
