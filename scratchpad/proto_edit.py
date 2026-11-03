"""Build a LOCAL prototype state for editing saved sessions. Pushes nothing.

Newest data-backup-*.json in, scratchpad/proto-edit-state.json out, plus scratchpad/proto-edit-scenes.json,
the sessions each scene of scratchpad/review/edit-stage.html works on. The shared store is never opened,
and the logs are the store copy's own, none added:

  raise     the person's first Bench press (20 kg) goes up, so the later sessions that were records stop being one
  lower     one Bench press goes down, so the session after it becomes a record
  addremove a Bench press with a done list: remove a set, mark a warm-up, add a set
  run       a run whose rows the watch sync wrote (rows_from "reps ..."): a time is edited and the pace follows

It also prints how many stored pr flags a full recompute would flip with no edit at all, using the app's
own functions (scratchpad/review/edit-cases.js --dryrun, run under VS Code's Electron as node).

    python scratchpad/proto_edit.py
"""
import glob, io, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
src = sorted(glob.glob(os.path.join(HERE, "data-backup-2*.json")))[-1]
data = json.load(io.open(src, encoding="utf-8"))
print("source:", os.path.basename(src))


def find(person, date, key, name):
    for l in data["logs"]:
        if l["person"] == person and l["date"] == date and l["sessionKey"] == key \
                and any(e["name"] == name for e in l["entries"]):
            return l
    sys.exit("not in the store copy: %s %s %s %s" % (person, date, key, name))


# Daniel: 20 kg on 23 Jul, records at 50 (12 Aug) and 70 (21 Sep), a 50 kg tie on 19 Aug.
# Cerys: 20 kg on 23 Jul, records at 25 (12 Aug), 30 (21 Sep) and 40 (26 Oct), a 30 kg tie on 28 Sep.
scenes = {
    "Daniel": {
        "raise": {"id": find("Daniel", "2026-07-23", "upper1", "Bench press")["id"], "to": "75"},
        "lower": {"id": find("Daniel", "2026-08-12", "upper1", "Bench press")["id"], "to": "45"},
        "addremove": {"id": find("Daniel", "2026-10-19", "upper1", "Bench press")["id"]},
        "run": {"id": find("Daniel", "2026-08-13", "cardioEndurance", "Easy run (Zone 2)")["id"]},
    },
    "Cerys": {
        "raise": {"id": find("Cerys", "2026-07-23", "upper1", "Bench press")["id"], "to": "32"},
        "lower": {"id": find("Cerys", "2026-09-21", "upper1", "Bench press")["id"], "to": "28"},
        "addremove": {"id": find("Cerys", "2026-10-26", "upper1", "Bench press")["id"]},
        "run": {"id": find("Cerys", "2026-08-13", "cardioEndurance", "Easy run (Zone 2)")["id"]},
    },
}
data["activePerson"] = 0
data["theme"] = "light"
prog = data["program"]
prog["order"] = [k for k in prog["order"] if k in prog["sessions"]]  # live store has orphan keys (2 Nov)

state_path = os.path.join(HERE, "proto-edit-state.json")
io.open(state_path, "w", encoding="utf-8").write(json.dumps(data, indent=1))
io.open(os.path.join(HERE, "proto-edit-scenes.json"), "w", encoding="utf-8").write(json.dumps(scenes, indent=1))
print("wrote proto-edit-state.json and proto-edit-scenes.json - load them in the browser, nothing pushed")

code = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Microsoft VS Code", "Code.exe")
cases = os.path.join(HERE, "review", "edit-cases.js")
if os.path.exists(code):
    env = dict(os.environ, ELECTRON_RUN_AS_NODE="1")
    out = subprocess.run([code, cases, "--dryrun", state_path], env=env, capture_output=True, text=True, check=True).stdout
    dry = json.loads(out)
    print("a full recompute with no edit would flip %d stored pr flags, on %d of %d sessions (value-only moves: %d)"
          % (dry["flagFlips"], dry["logs"], len(data["logs"]), dry["valueOnly"]))
    for line in dry["detail"]:
        print("  " + line)
else:
    print("VS Code not found at", code, "- skipped the dry run")
