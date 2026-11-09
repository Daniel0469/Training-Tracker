"""Build a LOCAL state for the Program tab review stage. Pushes nothing.

Newest data-backup-*.json in, scratchpad/proto-program-tab-state.json out. The state has three people:

  Daniel, Cerys  one shared program with sessions on several days, two auto-picks, three coach
                 changes waiting and one edit from Mum waiting
  Mum            her own small program, which Daniel can open and stage edits in

The shared store is never opened.

    python scratchpad/proto_program_tab.py
"""
import copy, glob, io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
src = sorted(glob.glob(os.path.join(HERE, "data-backup-2*.json")))[-1]
data = json.load(io.open(src, encoding="utf-8"))
print("source:", os.path.basename(src))


def lift(name, sets, reps, **extra):
    ex = {"name": name, "warmup": "", "target": "%dx%s" % (sets, reps), "sets": sets,
          "cols": ["Weight (kg)", "Reps"], "muscles": extra.pop("muscles", [])}
    ex.update(extra)
    return ex


def set_days(s, days, auto=None):
    s["days"] = days
    s["day"] = days[0] if days else "Optional"
    if auto:
        s["autoPick"] = {d: True for d in auto}


shared = data.pop("program")
shared["order"] = [k for k in shared["order"] if k in shared["sessions"]]
shared.update({"id": "p-daniel-cerys", "members": ["Daniel", "Cerys"], "version": 5,
               "updatedAt": "2026-11-09T08:00:00.000Z", "updatedBy": "Daniel"})
S = shared["sessions"]
set_days(S["upper1"], ["Tuesday"], ["Tuesday"])
set_days(S["upper2"], ["Friday"], ["Friday"])
set_days(S["lower2"], ["Monday"])
set_days(S["lower1"], ["Thursday"])
set_days(S["runDaniel"], ["Tuesday", "Saturday"])
set_days(S["runCerys"], ["Tuesday", "Saturday"])
set_days(S["mobilityDaniel"], ["Wednesday", "Sunday"], ["Wednesday"])
set_days(S["mobilityCerys"], ["Wednesday", "Sunday"], ["Wednesday"])
set_days(S["mobility-assessment"], [])
S["upper1"]["exercises"][3]["step"] = 2.5
S["upper1"]["exercises"][5]["groupId"] = "grp-demo"
S["upper1"]["exercises"][6]["groupId"] = "grp-demo"

coach = [
    {"id": "pc-coach-1", "at": "2026-11-08T09:00:00.000Z", "status": "pending", "session": "Upper A", "exercise": S["upper1"]["exercises"][3]["name"],
     "op": "edit", "fields": {"sets": 4}, "why": "Rows are lagging your presses. One more set.", "source": "coach"},
    {"id": "pc-coach-2", "at": "2026-11-08T09:01:00.000Z", "status": "pending", "session": "Upper A", "exercise": S["upper1"]["exercises"][-1]["name"],
     "op": "remove", "why": "The core work is covered elsewhere.", "source": "coach"},
    {"id": "pc-coach-3", "at": "2026-11-08T09:02:00.000Z", "status": "pending", "session": "Upper B", "exercise": "Face pull",
     "op": "add", "fields": {"target": "2x12-15", "sets": 2, "cols": ["Weight (kg)", "Reps"]}, "why": "Shoulder balance.", "source": "coach"}]

walk = {"name": "Walk and stretch", "exercises": [
    {"name": "Brisk walk", "warmup": "", "target": "30 min", "sets": 1, "cols": ["Distance (km)", "Time (mm:ss)", "Pace"], "muscles": []}]}
full_a = {"name": "Gentle full body", "exercises": [
    lift("Leg press", 2, "10-12", muscles=["quads", "glutes"]), lift("Seated cable row", 2, "10-12", muscles=["lats"]),
    lift("Chest press machine", 2, "10-12", muscles=["chest"])]}
set_days(full_a, ["Tuesday", "Friday"], ["Tuesday"])
set_days(walk, ["Saturday"])
mum = {"id": "p-mum", "members": ["Mum"], "version": 3, "updatedAt": "2026-11-01T09:00:00.000Z", "updatedBy": "Mum",
       "order": ["full-a", "walk"], "sessions": {"full-a": full_a, "walk": walk}}

base = copy.deepcopy(S["upper2"])
proposed = copy.deepcopy(base)
proposed["exercises"][0]["sets"] += 1
edits = [{"id": "pe-demo-1", "kind": "person", "programId": shared["id"], "from": "Mum", "baseVersion": 5,
          "base": {"sessions": {"upper2": base}}, "proposed": {"sessions": {"upper2": proposed}},
          "createdAt": "2026-11-09T07:30:00.000Z", "status": "pending"}]

data["programs"] = {shared["id"]: shared, mum["id"]: mum}
data["programIds"] = {"Daniel": {"id": shared["id"], "updatedAt": 0}, "Cerys": {"id": shared["id"], "updatedAt": 0},
                      "Mum": {"id": mum["id"], "updatedAt": 0}}
data["people"] = ["Daniel", "Cerys", "Mum"]
data["colors"] = ["navy", "purple", "teal"]
data["weights"] = data.get("weights", ["", ""]) + ["62"]
data["goals"] = data.get("goals", ["", ""]) + ["Stay strong and keep walking"]
data["programChanges"] = [c for c in data.get("programChanges", []) if c.get("status") != "pending"] + coach + edits
data["activePerson"] = 0
data["theme"] = "light"
out = os.path.join(HERE, "proto-program-tab-state.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(data, indent=1))
print("wrote", os.path.basename(out), "- load it in the browser, nothing pushed")
