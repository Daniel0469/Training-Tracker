#!/usr/bin/env python3
"""End-to-end check of the rewritten speed-trace segmentation, against a COPY of
the store. Reads Garmin, writes only to scratchpad/proto-refresh26.json - the
shared store is never opened.

    python scratchpad/test_refresh26.py training-garmin 2026-08-26 Daniel
"""
import sys, os, json, copy, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
G._load_server_env(sys.argv[1]); G._ensure_ca_bundle()

date, person = sys.argv[2], sys.argv[3]
store = json.load(open(os.path.join(ROOT, "scratchpad", "store.json"), encoding="utf-8"))
program = store.get("program") or {}
log = next(l for l in store["logs"] if l.get("date") == date and l.get("person") == person)
before = copy.deepcopy(log)

aid = log["garminActivityId"]
a, splits = G.fetch_activity(aid)
extras = G.fetch_activity_extras(aid)
G.enrich_log(log, a, splits, program=program, extras=extras)

run = next(e for e in log["entries"] if G._is_run_entry(e))
old = next(e for e in before["entries"] if G._is_run_entry(e))
print("run entry cols: %s" % run["cols"])
print("\nrows BEFORE (what the old detector wrote):")
for r in old["rows"]:
    print("   %s" % r)
print("\nrows AFTER:")
for r in run["rows"]:
    print("   %s" % r)
print("\nrows_from: %s" % (log.get("garmin") or {}).get("rows_from"))

reps = (log.get("garmin") or {}).get("reps") or {}
print("\nreps: count=%s" % reps.get("count"))
print("derived: %s" % json.dumps(reps.get("derived")))
print("\nsetup_match: %s" % reps.get("setup_match"))
print("note: %s" % reps.get("note"))

out = os.path.join(ROOT, "scratchpad", "proto-refresh26.json")
json.dump(store, open(out, "w", encoding="utf-8"), indent=1)
print("\nwrote %s (a copy - the shared store was never opened)" % out)
