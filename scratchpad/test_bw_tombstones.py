#!/usr/bin/env python3
"""Check the coach ignores deleted weigh-ins (deletedBodyweights tombstones), on
synthetic data in a fresh process - the running MCP server is never trusted for this.
Reads nothing remote, writes nothing.

    python scratchpad/test_bw_tombstones.py
"""
import os, sys, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("ttcoach", os.path.join(ROOT, "mcp-coach", "server.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

D = 1791900000000  # deletedAt used throughout
data = {
    "people": ["Daniel", "Cerys"], "weights": ["74.6", "79.8"], "goals": ["", ""], "logs": [],
    "bodyweights": [
        {"person": "Daniel", "date": "2026-07-26", "kg": 77.2},                      # live, unstamped
        {"person": "Daniel", "date": "2026-08-12", "kg": 74.6},                      # deleted (unstamped)
        {"person": "Daniel", "date": "2026-10-09", "kg": 74.8, "updatedAt": D},      # stamped AT deletedAt -> deleted
        {"person": "Daniel", "date": "2026-10-13", "kg": 74.5, "updatedAt": D + 1},  # re-weigh after delete -> stands
        {"person": "Cerys",  "date": "2026-08-12", "kg": 79.8},                      # same date, other person -> live
    ],
    "deletedBodyweights": [
        {"person": "Daniel", "date": "2026-08-12", "deletedAt": D},
        {"person": "Daniel", "date": "2026-10-09", "deletedAt": D},
        {"person": "Daniel", "date": "2026-10-13", "deletedAt": D},
        {"person": "Daniel", "date": "2026-08-12", "deletedAt": D - 5},   # duplicate, older: max wins
    ],
}

fails = 0
def ok(cond, msg):
    global fails
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: fails += 1

hist = C.get_bodyweight(data, "Daniel")
ok([h["date"] for h in hist] == ["2026-07-26", "2026-10-13"],
   "get_bodyweight drops deleted rows, keeps the re-weigh: %s" % [h["date"] for h in hist])
ok(C.get_bodyweight(data, "Cerys") == [{"date": "2026-08-12", "kg": 79.8}],
   "a tombstone only deletes its own person")

ppl = {p["person"]: p for p in C.list_people(data)}
ok(ppl["Daniel"]["latest_bodyweight_kg"] == 74.5, "list_people latest = the re-weigh (74.5)")

ok(C._bodyweight_on(data, "Daniel", "2026-08-20") == 77.2,
   "_bodyweight_on skips the deleted 08-12 row (77.2, not 74.6)")
ok(C._bodyweight_on(data, "Daniel", "2026-10-10") == 77.2,
   "_bodyweight_on skips a row stamped exactly at deletedAt")

only_dead = {"people": ["Daniel"], "logs": [], "bodyweights": [{"person": "Daniel", "date": "2026-08-12", "kg": 74.6}],
             "deletedBodyweights": [{"person": "Daniel", "date": "2026-08-12", "deletedAt": D}]}
ok(C.get_bodyweight(only_dead, "Daniel") == [] and C.list_people(only_dead)[0]["latest_bodyweight_kg"] is None,
   "all rows deleted -> empty history, no latest weight")

no_key = {k: v for k, v in data.items() if k != "deletedBodyweights"}
ok(len(C.get_bodyweight(no_key, "Daniel")) == 4, "a store without deletedBodyweights reads as before")

print("ALL PASS" if not fails else "FAILURES: %d" % fails)
sys.exit(1 if fails else 0)
