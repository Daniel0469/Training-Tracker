"""Build a LOCAL prototype state for the term routine. Pushes nothing.

Reads the most recent data-backup-*.json (so the prototype carries the real
history and the Last column shows something), applies the rewritten program in
memory, and writes scratchpad/proto-term-state.json for the browser to load
into localStorage. The shared store is never opened.

    python scratchpad/proto_term.py
"""
import glob, io, json, os

import term_sessions

HERE = os.path.dirname(os.path.abspath(__file__))

backups = sorted(glob.glob(os.path.join(HERE, "data-backup-*.json")))
if not backups:
    raise SystemExit("!! no data-backup-*.json here")
src = backups[-1]
data = json.load(io.open(src, encoding="utf-8"))
print("source:", os.path.basename(src))

changed = term_sessions.apply_to_program(data["program"])
data["activePerson"] = 0
data["theme"] = data.get("theme") or "light"

out = os.path.join(HERE, "proto-term-state.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(data, indent=1))

print("\nchanges")
for c in changed:
    print("  *", c)

DOW = {"monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4, "friday": 5,
       "saturday": 6, "sunday": 7, "optional": 9}
print("\nthe week")
keys = sorted(data["program"]["order"],
              key=lambda k: DOW.get(str(data["program"]["sessions"][k].get("day", "")).lower(), 8))
for k in keys:
    s = data["program"]["sessions"][k]
    who = s.get("person") or "both"
    print("  %-9s %-22s %-7s %2d exercises" % (s.get("day"), s["name"], who, len(s["exercises"])))

print("\nwrote", os.path.basename(out), "- load it in the browser, nothing pushed")
