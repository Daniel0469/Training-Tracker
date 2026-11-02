"""Build a LOCAL prototype state for the progression targets. Pushes nothing.

Newest data-backup-*.json in, scratchpad/proto-progression-state.json out. Adds logs dated
after the real ones so Upper A shows every case:

  Daniel  Bench press, all sets at the top of the range: progress, 62.5 kg
          Incline DB press, short of the top: hold at 22 kg
          Pallof press, all sets at the top and no known step: "Up one step"
          Face pull, all sets at the top with a Step line in the setup note: 22.8 kg
          Triceps pushdown, due, but switched off for Daniel: plain boxes
  Cerys   Bench press, three sessions at 35 kg and no rep gain: "Stalled"
          Incline DB press, a coach target (14 kg, 10 reps, with a why) over the rule's 12 kg

The shared store is never opened.

    python scratchpad/proto_progression.py
"""
import glob, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "mcp-coach"))
import progression

src = sorted(glob.glob(os.path.join(HERE, "data-backup-2*.json")))[-1]
data = json.load(io.open(src, encoding="utf-8"))
print("source:", os.path.basename(src))

upper = data["program"]["sessions"]["upper1"]
cols = {e["name"]: e["cols"] for e in upper["exercises"]}
next_id = [1793100000000]


def log(person, date, work):
    """work: exercise name -> (weight, [reps per set])."""
    entries = []
    for name, (kg, reps) in work.items():
        entries.append({"name": name, "cols": cols[name], "rows": [[str(kg), str(r)] for r in reps],
                        "done": list(range(len(reps)))})
    next_id[0] += 1
    data["logs"].append({"id": next_id[0], "updatedAt": next_id[0], "date": date, "person": person,
                         "sessionKey": "upper1", "sessionName": upper["name"], "entries": entries,
                         "feedback": "", "difficulty": None, "volume": 0, "durationSec": 3000})


log("Daniel", "2026-11-01", {
    "Bench press": (60, [8, 8, 8]),
    "Incline DB press": (22, [10, 9, 8]),
    "Pallof press": (6.8, [12, 12]),
    "Face pull": (20.3, [15, 15]),
    "Triceps pushdown": (20.3, [12, 12]),
})
for date, reps in (("2026-10-28", [6, 6, 6]), ("2026-10-30", [6, 6, 6]), ("2026-11-01", [6, 5, 6])):
    log("Cerys", date, {"Bench press": (35, reps)})

upper["setupNote"] = "Step: Face pull = 2.5"

incline = next(e for e in upper["exercises"] if e["name"] == "Incline DB press")
rule = progression.progression_for(data, "Cerys", incline)
cerys = data["coaching"]["Cerys"]
cerys["targets"] = {"Incline DB press": {
    "kg": 14, "reps": 10,
    "why": "Three sessions at 12 kg and the last set looked easy. Try 14 kg for 10.",
    "rule": rule["target"], "asOfLog": progression.latest_log_id(data, "Cerys", "Incline DB press"),
    "updated": "2026-11-02"}}

data["progression"] = {"Daniel": {"ex": {"Triceps pushdown": {"off": True, "updatedAt": 1793100000000}}}}

prog = data["program"]
prog["order"] = [k for k in prog["order"] if k in prog["sessions"]]  # live store has orphan keys (2 Nov)
data["activePerson"] = 0
data["theme"] = "light"
out = os.path.join(HERE, "proto-progression-state.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(data, indent=1))
print("wrote", os.path.basename(out), "- load it in the browser, nothing pushed")
for person in data["people"]:
    print(person)
    for r in progression.report(data, person)["exercises"]:
        if r["session"] == upper["name"]:
            print("  %-34s %-8s %s -> %s  step %s  flag %s  coach %s" % (
                r["exercise"], r["status"], r.get("w"), r.get("target"), r.get("step"), r.get("flag"),
                (r.get("coach") or {}).get("kg")))
