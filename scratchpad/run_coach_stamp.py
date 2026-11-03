#!/usr/bin/env python3
"""Run write_log_entry of mcp-coach/server.py from a FRESH process against a COPY of the store, to show
that a correction now stamps the log's updatedAt (the app settles a log edited on both sides by it).
GitHub is stubbed with the in-memory hub from check_servers.py: nothing leaves the machine and the
shared store is never opened.

    python scratchpad/run_coach_stamp.py            # newest scratchpad/data-backup-*.json
"""
import glob, importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scratchpad"))
sys.path.insert(0, os.path.join(ROOT, "mcp-coach"))
from check_servers import FakeHub, FakeMCP, patched

spec = importlib.util.spec_from_file_location("ttc", os.path.join(ROOT, "mcp-coach", "server.py"))
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

path = sorted(glob.glob(os.path.join(ROOT, "scratchpad", "data-backup-*.json")))[-1]
store = json.loads(open(path, encoding="utf-8").read())
print("store copy:", os.path.basename(path))

log = next(l for l in store["logs"] if l["date"] == "2026-08-13" and l["person"] == store["people"][0]
           and l["sessionKey"] == "cardioEndurance")
entry = next(e for e in log["entries"] if e["name"] == "Easy run (Zone 2)")
rows = [list(r) for r in entry["rows"]]
rows[0][0] = 0.8
print("log %s updatedAt before: %s" % (log["id"], log.get("updatedAt")))

tools = FakeMCP()
S._register(tools)
hub = FakeHub({"data.json": json.dumps(store, indent=2)})
with patched(S, hub):
    out = json.loads(tools.tools["write_log_entry"](session_id=str(log["id"]), exercise=entry["name"],
                                                    rows=rows, why="Made-up correction."))
    print("write_log_entry:", out.get("ok"), out.get("result", ""))
after = json.loads(hub.files["data.json"])
fixed = next(l for l in after["logs"] if l["id"] == log["id"])
print("log %s updatedAt after:  %s" % (log["id"], fixed.get("updatedAt")))
others = [l for l in after["logs"] if l["id"] != log["id"]]
same = all(a == b for a, b in zip(others, [l for l in store["logs"] if l["id"] != log["id"]]))
ok = fixed["updatedAt"] > (log.get("updatedAt") or 0) and fixed["entries"][0]["rows"] != entry["rows"] and same
print("PASS" if ok else "FAIL", "- stamped, rows corrected, no other log touched")
sys.exit(0 if ok else 1)
