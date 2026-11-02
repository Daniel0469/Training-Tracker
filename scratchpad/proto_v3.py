"""Build a LOCAL prototype state for the design-v3 restyle. Pushes nothing.

Copies the most recent data-backup-*.json (real history, so every card has
something to draw), forces dark (design v3 is dark-first) and writes
scratchpad/proto-v3-state.json for the browser to load into localStorage. The
shared store is never opened.

    python scratchpad/proto_v3.py
"""
import glob, io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
backups = sorted(glob.glob(os.path.join(HERE, "data-backup-*.json")))
if not backups:
    raise SystemExit("!! no data-backup-*.json here")
src = backups[-1]
data = json.load(io.open(src, encoding="utf-8"))
data["activePerson"] = 0
data["theme"] = "dark"
out = os.path.join(HERE, "proto-v3-state.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(data))
print("source:", os.path.basename(src), "| people:", data.get("people"), "| colors:", data.get("colors"))
print("wrote", os.path.basename(out), "- load it in the browser, nothing pushed")
