"""Fresh READ of the live store -> backup + local prototype state for the program trim.
Writes nothing to the store.   python -X utf8 scratchpad/proto_trim.py"""
import sys, os, json, datetime, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(g); g.loader.exec_module(G)
G._load_server_env("training-tracker")
c = importlib.util.spec_from_file_location("ttc", os.path.join(ROOT, "mcp-coach", "server.py"))
C = importlib.util.module_from_spec(c); c.loader.exec_module(C)
data, *_ = C._github_read_with_sha()
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
json.dump(data, open(os.path.join(ROOT, "scratchpad", "data-backup-%s.json" % stamp), "w", encoding="utf-8"), indent=1)
data["activePerson"] = 0
data["theme"] = data.get("theme") or "light"
json.dump(data, open(os.path.join(ROOT, "scratchpad", "proto-trim-state.json"), "w", encoding="utf-8"))
print("backup", stamp, "| logs", len(data["logs"]), "| newest", max(l["date"] for l in data["logs"]))
