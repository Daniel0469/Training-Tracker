"""Build a LOCAL prototype state with the recording split applied. Pushes nothing.

Reads the most recent data-backup-*.json (so the prototype carries the real
sessions and history), applies the same split apply_recording_split.py would,
and writes scratchpad/proto-recording-state.json for the browser to load into
localStorage. The shared store is never opened.

    python scratchpad/proto_recording.py
"""
import glob, io, json, os

from apply_recording_split import split_note

HERE = os.path.dirname(os.path.abspath(__file__))

backups = sorted(glob.glob(os.path.join(HERE, "data-backup-*.json")))
if not backups:
    raise SystemExit("!! no data-backup-*.json here - run the probe or apply script once")
src = backups[-1]
data = json.load(io.open(src, encoding="utf-8"))
print("source:", os.path.basename(src))

for key, s in (data["program"]["sessions"]).items():
    if not s.get("person") or s.get("recordingNote"):
        continue
    got, why = split_note(s.get("warmupNote") or "")
    if not got:
        print("  !! %s: %s" % (s.get("name"), why))
        continue
    s["recordingNote"], s["warmupNote"] = got
    print("  * %-14s recording %4d chars, warm-up %4d chars"
          % (s.get("name"), len(got[0]), len(got[1])))

data["activePerson"] = 0
data["theme"] = data.get("theme") or "light"

out = os.path.join(HERE, "proto-recording-state.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(data, indent=1))
print("\nwrote", os.path.basename(out), "- load it in the browser, nothing pushed")
