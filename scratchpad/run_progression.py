#!/usr/bin/env python3
"""Run the progression tools of mcp-coach/server.py from a FRESH process against a COPY of the
store, so it shows what the current file does rather than what a long-running MCP server loaded
at startup. GitHub is stubbed with the in-memory hub from check_servers.py: nothing leaves the
machine and the shared store is never opened.

    python scratchpad/run_progression.py            # newest scratchpad/data-backup-*.json
    python scratchpad/run_progression.py --writes   # also try write_coaching targets and write_machine_step
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
print("store copy:", os.path.basename(path))
hub = FakeHub({"data.json": store_text})
tools = FakeMCP()
S._register(tools)
call = lambda name, **kw: json.loads(tools.tools[name](**kw))


def show(person):
    out = call("progression", person=person)
    print("\n%s" % person)
    for r in out["exercises"]:
        step = "step %g (%s)" % (r["step"], r["source"]) if r.get("step") is not None else "step unknown"
        line = "  %-32s %-8s w=%s target=%s  %s  streak %s" % (
            r["exercise"][:32], r["status"], r.get("w"), r.get("target"), step, r.get("streak"))
        line += "  " + " ".join(x for x in (r.get("flag"), r.get("why"), r.get("coach") and "coach target") if x)
        print(line.rstrip())
    print("  steps to confirm:", ", ".join(out["steps_to_confirm"]) or "none")


with patched(S, hub):
    for person in json.loads(store_text)["people"]:
        show(person)
    if "--writes" in sys.argv:
        print("\n-- write_coaching targets")
        bench = {"Bench press": {"kg": 60, "why": "keeps the bar speed"}}
        print("differs, no why:", call("write_coaching", person="Daniel", targets={"Bench press": {"kg": 60}}))
        print("unknown exercise:", call("write_coaching", person="Daniel", targets={"Nope": {"kg": 1, "why": "x"}}))
        print("with why:", call("write_coaching", person="Daniel", targets=bench))
        after = json.loads(hub.files["data.json"])["coaching"]["Daniel"]["targets"]
        print("stored:", json.dumps(after))
        print("active in progression:", [r["exercise"] for r in call("progression", person="Daniel")["exercises"] if r.get("coach")])
        print("clear:", call("write_coaching", person="Daniel", targets={"Bench press": None}).get("ok"))
        print("\n-- write_machine_step")
        for label, kw in (("add", dict(exercise="Seated row", step=2.5)),
                          ("replace", dict(exercise="Seated row", step=5)),
                          ("same again", dict(exercise="Seated row", step=5)),
                          ("unknown", dict(exercise="Nope", step=5)),
                          ("remove", dict(exercise="Seated row", step=None))):
            r = call("write_machine_step", **kw)
            notes = {s["name"]: s.get("setupNote", "") for s in json.loads(hub.files["data.json"])["program"]["sessions"].values()
                     if "Step:" in s.get("setupNote", "")}
            print("%-10s ok=%s %s notes=%s" % (label, r.get("ok"), r.get("error", r.get("sessions", "")), json.dumps(notes)))
