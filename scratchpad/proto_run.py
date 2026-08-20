"""Build a LOCAL prototype state for the two run sessions. Pushes nothing.

Reads the most recent data-backup-*.json (so the prototype carries the real
history, and the Last column shows something), applies the proposed program
change in memory, and writes scratchpad/proto-run-state.json for the browser to
load into localStorage. The shared store is never opened.

    python scratchpad/proto_run.py
"""
import glob, io, json, os

import run_sessions

HERE = os.path.dirname(os.path.abspath(__file__))

backups = sorted(glob.glob(os.path.join(HERE, "data-backup-*.json")))
if not backups:
    raise SystemExit("!! no data-backup-*.json here - run probe/apply once to get one")
src = backups[-1]
data = json.load(io.open(src, encoding="utf-8"))
print("source:", os.path.basename(src))

changed = run_sessions.apply_to_program(data["program"])
data["activePerson"] = 0
data["theme"] = data.get("theme") or "light"

out = os.path.join(HERE, "proto-run-state.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(data, indent=1))

for c in changed:
    print("  *", c)
print("\nWednesday now holds, per person:")
for k in data["program"]["order"]:
    s = data["program"]["sessions"][k]
    if str(s.get("day")).lower() in ("wednesday", "optional"):
        who = s.get("person") or "both"
        print("   %-22s %-10s %s" % (s["name"], s.get("day"), who))
        for e in s["exercises"]:
            print("        - %-20s %-32s sets=%s" % (e["name"], e.get("target"), e.get("sets")))
print("\nwrote", os.path.basename(out), "- load it in the browser, nothing pushed")
