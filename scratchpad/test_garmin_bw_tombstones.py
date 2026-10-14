#!/usr/bin/env python3
"""Check mcp-garmin ignores deleted weigh-ins (deletedBodyweights tombstones) when it
picks the bodyweight for watts/kg, on synthetic data in a fresh process - the running
MCP server is never trusted for this. Reads nothing remote, writes nothing.

    python scratchpad/test_garmin_bw_tombstones.py
"""
import os, sys, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("ttgarmin", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)

D = 1791900000000  # deletedAt used throughout
data = {
    "people": ["Daniel", "Cerys"],
    "bodyweights": [
        {"person": "Daniel", "date": "2026-07-26", "kg": 77.2},                      # live, unstamped
        {"person": "Daniel", "date": "2026-08-12", "kg": 74.6},                      # deleted (unstamped)
        {"person": "Daniel", "date": "2026-10-09", "kg": 74.8, "updatedAt": D},      # stamped AT deletedAt -> deleted
        {"person": "Daniel", "date": "2026-10-13", "kg": 74.5, "updatedAt": D + 1},  # re-weigh after delete -> used
        {"person": "Cerys",  "date": "2026-08-12", "kg": 79.8},                      # same date, other person -> live
    ],
    "deletedBodyweights": [
        {"person": "Daniel", "date": "2026-08-12", "deletedAt": D},
        {"person": "Daniel", "date": "2026-10-09", "deletedAt": D},
        {"person": "Daniel", "date": "2026-10-13", "deletedAt": D},
    ],
}

fails = 0
def ok(cond, msg):
    global fails
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: fails += 1

def wkg(store, date):
    bw = G.bodyweight_on(store, "Daniel", date)
    return bw, G.activity_efficiency({"averagePower": 300}, None, bw).get("watts_per_kg")

bw, w = wkg(data, "2026-08-20")
ok(bw == 77.2 and w == round(300 / 77.2, 2), "deleted 08-12 row skipped for watts/kg: bw=%s w/kg=%s" % (bw, w))
bw, w = wkg(data, "2026-10-10")
ok(bw == 77.2, "row stamped exactly at deletedAt is skipped: bw=%s" % bw)
bw, w = wkg(data, "2026-10-14")
ok(bw == 74.5 and w == round(300 / 74.5, 2), "re-weigh after a delete is used: bw=%s w/kg=%s" % (bw, w))
ok(G.bodyweight_on(data, "Cerys", "2026-08-20") == 79.8, "a tombstone only deletes its own person")

only_dead = {"bodyweights": [{"person": "Daniel", "date": "2026-08-12", "kg": 74.6}],
             "deletedBodyweights": [{"person": "Daniel", "date": "2026-08-12", "deletedAt": D}]}
bw, w = wkg(only_dead, "2026-08-20")
ok(bw is None and w is None, "all rows deleted -> no bodyweight, no watts/kg")

no_key = {k: v for k, v in data.items() if k != "deletedBodyweights"}
ok(G.bodyweight_on(no_key, "Daniel", "2026-08-20") == 74.6
   and G.bodyweight_on(no_key, "Daniel", "2026-10-10") == 74.8,
   "no tombstones = unchanged (74.6 on 08-20, 74.8 on 10-10)")

C_spec = importlib.util.spec_from_file_location("ttcoach", os.path.join(ROOT, "mcp-coach", "server.py"))
C = importlib.util.module_from_spec(C_spec); C_spec.loader.exec_module(C)
same = all(G._person_bodyweights(data, p) == C._person_bodyweights(data, p) for p in ("Daniel", "Cerys"))
ok(same, "garmin and coach helpers agree on the same store")

print("ALL PASS" if not fails else "FAILURES: %d" % fails)
sys.exit(1 if fails else 0)
