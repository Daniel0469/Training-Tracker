"""Build a LOCAL prototype state for per-person programs. Pushes nothing.

Newest data-backup-*.json in, scratchpad/proto-programs-state.json out. The state has three people:

  Daniel, Cerys  one shared program (members both), as today
  Mum            her own small program, version 3

and two changes waiting on Mum, both from Daniel:

  a program change   Leg press 2 -> 3 sets, a new Glute bridge, and a new Stretch session
  a copy of Upper A  from Daniel's program

The shared store is never opened.

    python scratchpad/proto_programs.py
"""
import glob, io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
src = sorted(glob.glob(os.path.join(HERE, "data-backup-2*.json")))[-1]
data = json.load(io.open(src, encoding="utf-8"))
print("source:", os.path.basename(src))


def lift(name, sets, reps, **extra):
    ex = {"name": name, "warmup": "", "target": "%dx%s" % (sets, reps), "sets": sets,
          "cols": ["Weight (kg)", "Reps"], "muscles": extra.pop("muscles", [])}
    ex.update(extra)
    return ex


shared = data.pop("program")
shared["order"] = [k for k in shared["order"] if k in shared["sessions"]]  # live store has orphan keys (2 Nov)
shared.update({"id": "p-daniel-cerys", "members": ["Daniel", "Cerys"], "version": 5,
               "updatedAt": "2026-11-02T18:00:00.000Z", "updatedBy": "Daniel"})

full_a = {"name": "Gentle full body", "day": "Tuesday", "exercises": [
    lift("Leg press", 2, "10-12", muscles=["quads", "glutes"]),
    lift("Seated cable row", 2, "10-12", muscles=["lats"]),
    lift("Chest press machine", 2, "10-12", muscles=["chest"])]}
walk = {"name": "Walk and stretch", "day": "Friday", "cardio": True, "exercises": [
    {"name": "Brisk walk", "warmup": "", "target": "30 min", "sets": 1,
     "cols": ["Distance (km)", "Time (mm:ss)", "Pace"], "muscles": []}]}
mum = {"id": "p-mum", "members": ["Mum"], "version": 3, "updatedAt": "2026-11-01T09:00:00.000Z",
       "updatedBy": "Mum", "order": ["full-a", "walk"], "sessions": {"full-a": full_a, "walk": walk}}

data["programs"] = {shared["id"]: shared, mum["id"]: mum}
data["programIds"] = {"Daniel": {"id": shared["id"], "updatedAt": 0}, "Cerys": {"id": shared["id"], "updatedAt": 0},
                      "Mum": {"id": mum["id"], "updatedAt": 0}}

data["people"] = ["Daniel", "Cerys", "Mum"]
data["colors"] = ["navy", "purple", "teal"]
data["weights"] = data.get("weights", ["", ""]) + ["62"]
data["goals"] = data.get("goals", ["", ""]) + ["Stay strong and keep walking"]
data["bodyweights"].append({"person": "Mum", "date": "2026-11-01", "kg": 62, "updatedAt": 1793100000000})

proposed_a = json.loads(json.dumps(full_a))
proposed_a["exercises"][0].update({"sets": 3, "target": "3x10-12"})
proposed_a["exercises"].append(lift("Glute bridge", 2, "12-15", muscles=["glutes"]))
stretch = {"name": "Stretch", "day": "Sunday", "exercises": [
    {"name": "Hamstring stretch", "warmup": "", "target": "2 x 30 s", "sets": 2, "cols": ["Weight (kg)", "Reps"], "muscles": []}]}

data["programChanges"] = list(data.get("programChanges", [])) + [
    {"id": "pc-demo-1", "kind": "person", "programId": "p-mum", "from": "Daniel", "baseVersion": 3,
     "base": {"sessions": {"full-a": full_a}},
     "proposed": {"sessions": {"full-a": proposed_a, "stretch": stretch}, "order": ["full-a", "walk", "stretch"]},
     "createdAt": "2026-11-03T08:30:00.000Z", "status": "pending"},
    {"id": "pc-demo-2", "kind": "copy", "programId": "p-mum", "from": "Daniel", "baseVersion": 3,
     "base": {"sessions": {}},
     "proposed": {"sessions": {"upper1": shared["sessions"]["upper1"]}},
     "createdAt": "2026-11-03T08:31:00.000Z", "status": "pending"}]

data["activePerson"] = 0
data["theme"] = "light"
out = os.path.join(HERE, "proto-programs-state.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(data, indent=1))
print("wrote", os.path.basename(out), "- load it in the browser, nothing pushed")
