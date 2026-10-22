"""Daniel's 22 Oct answers: Lower A / Lower B warm-up headers to 15 / 13 min, and clear the
coach's session cards for retired session names (never shown). Backs up first.
    python -X utf8 scratchpad/apply_oct22.py"""
import os, json, datetime, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(g); g.loader.exec_module(G); G._load_server_env("training-tracker")
c = importlib.util.spec_from_file_location("ttc", os.path.join(ROOT, "mcp-coach", "server.py"))
C = importlib.util.module_from_spec(c); c.loader.exec_module(C)
live, *_ = C._github_read_with_sha()
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
json.dump(live, open(os.path.join(ROOT, "scratchpad", "data-backup-%s.json" % stamp), "w", encoding="utf-8"), indent=1)
print("backed up -> data-backup-%s.json" % stamp)
HEADERS = {"lower2": ("WARM-UP - 18 min,", "WARM-UP - 15 min,"), "lower1": ("WARM-UP - 16 min,", "WARM-UP - 13 min,")}
def mutate(data):
    S = data["program"]["sessions"]; changed = False
    for k, (old, new) in HEADERS.items():
        w = S[k].get("warmupNote") or ""
        if w.startswith(old):
            S[k]["warmupNote"] = new + w[len(old):]; changed = True
            print(S[k]["name"], "->", new)
    names = {s["name"] for s in S.values()}
    for p, entry in (data.get("coaching") or {}).items():
        bs = entry.get("bySession") or {}
        gone = [n for n in bs if n not in names]
        for n in gone: del bs[n]
        if gone: changed = True; print(p, "cleared:", ", ".join(gone))
    if not changed: print("nothing to change"); return None
    data["program"]["updatedAt"] = C._now_iso()
    return True
C._github_update(mutate, "Warm-up headers 15/13 min, retired session cards cleared (Daniel, 22 Oct)")
d, *_ = C._github_read_with_sha()
for k in HEADERS: print(d["program"]["sessions"][k]["name"], "|", d["program"]["sessions"][k]["warmupNote"].splitlines()[0])
for p, e in d["coaching"].items(): print(p, "bySession now:", list((e.get("bySession") or {}).keys()))
