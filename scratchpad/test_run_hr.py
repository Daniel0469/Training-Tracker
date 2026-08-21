#!/usr/bin/env python3
"""Dry run of the per-block HR work against real activities. Reads Garmin, writes
nothing - it enriches a COPY of the logged session in memory and prints what would
have been attached.

    python scratchpad/test_run_hr.py training-garmin 24053614591
    python scratchpad/test_run_hr.py training-garmin-cerys 24053658518
"""
import sys, os, json, copy, importlib.util

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

    print("=" * 74)
    print("%s  %s  %s" % (person, date, a.get("activityName")))
    print("   activity-level avg_hr = %s   max = %s   <- what the coach had before"
          % (G._field(a, "averageHR"), G._field(a, "maxHR")))

    print("\n-- (1) per-lap splits, as garmin_activity now returns them --")
    for r in G.splits_detail(splits):
        print("   lap %-2s %5.2fkm %7s  %8s  avg_hr=%-4s max_hr=%-4s %s kmh"
              % (r["lap"], r["km"], r["time"], r["pace"], r.get("avg_hr", "-"),
                 r.get("max_hr", "-"), r.get("avg_kmh", "-")))

    # Enrich a COPY of the real logged session, so the gate is exercised exactly as
    # the sync would exercise it - not a hand-made stand-in.
    log = next((l for l in store.get("logs", [])
                if str(l.get("garminActivityId")) == str(aid)), None)
    if log is None:
        print("\n   (no logged session links this activity - gate not exercised)")
        continue
    before = sorted((log.get("garmin") or {}).keys())
    out = G.enrich_log(copy.deepcopy(log), a, splits, program=program, extras=extras)
    g = out.get("garmin") or {}
    print("\n-- (2) per-rep, through the real enrich_log gate --")
    print("   garmin keys before: reps=%s effort_drift=%s"
          % ("reps" in before, "effort_drift" in before))
    reps = g.get("reps")
    if reps:
        print("   reps found: %d" % reps["count"])
        for r in reps["reps"]:
            print("      rep %-2s %4sm %3ss %5s kmh  avg_hr=%-4s max_hr=%-4s "
                  "rec=%-4ss rec_min_hr=%-4s drop=%s"
                  % (r["n"], r.get("dist_m"), r.get("sec"), r.get("kmh"),
                     r.get("avg_hr", "-"), r.get("max_hr", "-"),
                     r.get("recovery_sec", "-"), r.get("recovery_min_hr", "-"),
                     r.get("hr_drop", "-")))
        print("   derived: %s" % json.dumps(reps.get("derived")))
    else:
        print("   reps: None   skipped=%s" % g.get("reps_skipped"))
    if g.get("intervals"):
        print("   trace heuristic (intervals): %s reps" % g["intervals"].get("count"))
    print("\n-- (3) drift within one continuous effort --")
    print("   %s" % json.dumps(g.get("effort_drift"), indent=6))

    # What must NOT have happened.
    typed_rows = {e.get("name"): e.get("rows") for e in (log.get("entries") or [])}
    after_rows = {e.get("name"): e.get("rows") for e in (out.get("entries") or [])}
    changed = [n for n in typed_rows if typed_rows[n] != after_rows.get(n)]
    print("\n   entries whose rows changed: %s" % (changed or "none - typed data untouched"))
