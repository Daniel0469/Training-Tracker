"""Read-only: print every exercise `notes` (machine settings) in the live store,
grouped by exercise name, so they can be sorted into settings vs reasoning.
Writes nothing to the store; saves a timestamped local backup copy.

    python scratchpad/list_notes.py
"""
import base64, io, json, os
from datetime import datetime, timezone
from apply_recording_split import api, cfg

HERE = os.path.dirname(os.path.abspath(__file__))
repo, token, path = cfg()
meta = api("https://api.github.com/repos/%s/contents/%s" % (repo, path), token)
data = json.loads(base64.b64decode(meta["content"]).decode("utf-8"))
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
io.open(os.path.join(HERE, "data-backup-%s.json" % stamp), "w", encoding="utf-8").write(json.dumps(data, indent=1))

by = {}
prog = data.get("program") or {}
for k in prog.get("order") or []:
    s = (prog.get("sessions") or {}).get(k) or {}
    for e in s.get("exercises") or []:
        n = (e.get("notes") or "").strip()
        if n:
            by.setdefault(e["name"], []).append((s.get("name"), n))
print("store sha:", meta["sha"][:10], "| program updatedAt:", prog.get("updatedAt"), "| machineSettings present:", "machineSettings" in data)
for i, (name, rows) in enumerate(sorted(by.items()), 1):
    texts = sorted(set(t for _, t in rows))
    print("\n[%d] %s  (in: %s)%s" % (i, name, ", ".join(sorted(set(s for s, _ in rows))), "  ** DIFFERENT TEXT PER SESSION **" if len(texts) > 1 else ""))
    for t in texts:
        print("    ---\n    " + t.replace("\n", "\n    "))
