"""Add Back extension to the end of Lower B (Daniel, 17 Oct), copied from Lower A so the
name, target and columns match and its history lines up. Backs up first.
    python -X utf8 scratchpad/apply_backext_lowerb.py"""
import os, json, copy, datetime, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(g); g.loader.exec_module(G); G._load_server_env("training-tracker")
c = importlib.util.spec_from_file_location("ttc", os.path.join(ROOT, "mcp-coach", "server.py"))
C = importlib.util.module_from_spec(c); c.loader.exec_module(C)
live, *_ = C._github_read_with_sha()
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
json.dump(live, open(os.path.join(ROOT, "scratchpad", "data-backup-%s.json" % stamp), "w", encoding="utf-8"), indent=1)
print("backed up -> data-backup-%s.json" % stamp)
def mutate(data):
    S = data["program"]["sessions"]
    if any(e["name"] == "Back extension" for e in S["lower1"]["exercises"]):
        print("Lower B already has Back extension - nothing written"); return None
    src = next(e for e in S["lower2"]["exercises"] if e["name"] == "Back extension")
    S["lower1"]["exercises"].append(copy.deepcopy(src))
    data["program"]["updatedAt"] = C._now_iso()
    return True
C._github_update(mutate, "Lower B: add Back extension (Daniel, 17 Oct)")
d, *_ = C._github_read_with_sha()
for k in ("lower2", "lower1"):
    s = d["program"]["sessions"][k]
    print(s["name"], "|", ", ".join("%s %s" % (e["name"], e["sets"]) for e in s["exercises"]))
print("Lower B back extension:", [e for e in d["program"]["sessions"]["lower1"]["exercises"] if e["name"] == "Back extension"])
