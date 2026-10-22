"""Local prototype state for the 22 Oct app changes. Pushes nothing, never opens the store.
Newest data-backup-*.json in, with a fake "(preview)" pending coach change on Upper A so the
change dialog has something to show; writes scratchpad/proto-oct22-state.json.
    python -X utf8 scratchpad/proto_oct22.py"""
import glob, io, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
src = max(glob.glob(os.path.join(HERE, "data-backup-2*Z.json")), key=os.path.getmtime)
data = json.load(io.open(src, encoding="utf-8"))
print("source:", os.path.basename(src))
pcs = data.setdefault("programChanges", [])
pcs.append({"id": 1, "at": "2026-10-22T12:00:00.000Z", "status": "pending", "session": "Upper A",
            "exercise": "Preview curl", "op": "add",
            "fields": {"target": "2x12", "sets": 2, "cols": ["Weight (kg)", "Reps"]},
            "why": "(preview only - not a real change)"})
data["activePerson"] = 0
json.dump(data, io.open(os.path.join(HERE, "proto-oct22-state.json"), "w", encoding="utf-8"))
print("wrote proto-oct22-state.json")
