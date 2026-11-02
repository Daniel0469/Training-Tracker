"""Build a LOCAL prototype state for timed exercises. Pushes nothing.

Newest data-backup-*.json in, scratchpad/proto-timed-state.json out. Adds a timed
"Dead hang" to Upper A and one earlier hang per person, so the stopwatch and the
hold PR have something to show. The shared store is never opened.

    python scratchpad/proto_timed.py
"""
import glob, io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
src = sorted(glob.glob(os.path.join(HERE, "data-backup-2*.json")))[-1]
data = json.load(io.open(src, encoding="utf-8"))
print("source:", os.path.basename(src))

hang = {"name": "Dead hang", "warmup": "", "target": "3 x 30-45s", "sets": 3,
        "cols": ["Weight (kg)", "Time (s)"], "restSec": 90,
        "timed": {"holdSec": 45, "graceSec": 5, "autoFill": True}}
data["program"]["sessions"]["upper1"]["exercises"].append(hang)
for i, p in enumerate(data["people"]):
    data["logs"].append({"id": 1790000000000 + i, "date": "2026-10-27", "person": p,
        "sessionKey": "upper1", "sessionName": "Upper A",
        "entries": [{"name": "Dead hang", "cols": hang["cols"], "timed": True,
                     "rows": [["", "30"], ["", "32"], ["", "28"]]}],
        "feedback": "", "volume": 0})
prog = data["program"]
prog["order"] = [k for k in prog["order"] if k in prog["sessions"]]  # live store has orphan keys (2 Nov)
data["activePerson"] = 0
data["theme"] = "light"
out = os.path.join(HERE, "proto-timed-state.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(data, indent=1))
print("wrote", os.path.basename(out), "- load it in the browser, nothing pushed")
