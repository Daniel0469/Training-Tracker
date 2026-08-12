#!/usr/bin/env python3
"""Dry run of the new extraction against real activities. Reads Garmin, writes nothing.

    python scratchpad/test_reps.py training-garmin 23781117926 23817366769
"""
import sys, os, json, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("ttgarmin", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)

G._load_server_env(sys.argv[1]); G._ensure_ca_bundle()
person = os.environ["TT_PERSON"]
store = json.load(open(os.path.join(ROOT, "scratchpad", "store.json"), encoding="utf-8"))
program = store.get("program")

for aid in sys.argv[2:]:
    a, splits = G.fetch_activity(aid)
    extras = G.fetch_activity_extras(aid)
    date = (G._field(a, "startTimeLocal") or "")[:10]
    extras["bodyweight_kg"] = G.bodyweight_on(store, person, date)
    print("=" * 72)
    print("%s  %s  %s  bodyweight=%s" % (person, date, a.get("activityName"),
                                         extras["bodyweight_kg"]))
    print("=" * 72)
    print("metrics:", json.dumps(G.activity_metrics(a), indent=1))
    print("efficiency:", json.dumps(
        G.activity_efficiency(a, extras["typed_splits"], extras["bodyweight_kg"]), indent=1))
    print("power zones:", extras["power_zone_secs"])
    reps = G.reps_from_typed_splits(extras["typed_splits"], a, extras["series"])
    print("reps:", json.dumps(reps, indent=1))

    # Simulate enriching the real logged session for that date, on a COPY.
    logs = [l for l in store.get("logs", [])
            if l and l.get("person") == person and l.get("date") == date]
    for l in logs:
        cp = json.loads(json.dumps(l))
        cp.pop("garmin", None); cp.pop("garminActivityId", None)
        before = json.loads(json.dumps(cp.get("entries") or []))
        G.enrich_log(cp, a, splits, G.fetch_hr_zone_times(aid), program, extras)
        print("\n--- session %s (%s) ---" % (cp.get("sessionName"), cp.get("id")))
        for i, e in enumerate(cp.get("entries") or []):
            same = i < len(before) and before[i].get("rows") == e.get("rows")
            print("   %-28s %s rows=%s%s" % (e.get("name"), e.get("cols"),
                                             e.get("rows"), "" if same else "   <-- CHANGED"))
        print("   garmin keys:", sorted((cp.get("garmin") or {}).keys()))
        print("   derived:", json.dumps((cp.get("garmin") or {}).get("reps", {}).get("derived")))
        print("   trace heuristic:", json.dumps((cp.get("garmin") or {}).get("intervals", {}).get("rep_secs")))
