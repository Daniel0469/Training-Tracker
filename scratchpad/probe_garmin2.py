#!/usr/bin/env python3
"""Second pass: the fields the first probe truncated. Read-only.

    python scratchpad/probe_garmin2.py training-garmin [activity_id]
"""
import sys, os, json, datetime, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("ttgarmin", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)

server = sys.argv[1] if len(sys.argv) > 1 else "training-garmin"
G._load_server_env(server); G._ensure_ca_bundle()
g = G.garmin_client()
today = datetime.date.today()
d = lambda n: (today - datetime.timedelta(days=n)).isoformat()

def head(t): print("\n" + "=" * 68 + "\n" + t + "\n" + "=" * 68)

# --- the full detail-series metric list -----------------------------------------
runs = [a for a in (g.get_activities(0, 30) or []) if G.is_run(a)]
ids = sys.argv[2:] or [str(runs[0].get("activityId"))]
for aid in ids:
    a = g.get_activity(aid)
    head("ACTIVITY %s  %s  %s" % (aid, a.get("activityName"), G.activity_type(a)))
    try:
        det = g.get_activity_details(aid, maxchart=3, maxpoly=0)
        print("detail metric keys:")
        for m in (det.get("metricDescriptors") or []):
            print("   ", m.get("key"), "  unit:", (m.get("unit") or {}).get("key"))
    except Exception as e:
        print("details ERROR", e)
    try:
        ts = g.get_activity_typed_splits(aid)
        sp = ts.get("splits") or []
        print("\ntyped_splits: %d" % len(sp))
        for s in sp[:8]:
            print("   ", json.dumps({k: v for k, v in s.items()
                                     if v not in (None, 0, 0.0)}, default=str)[:400])
    except Exception as e:
        print("typed_splits ERROR", e)
    try:
        ss = g.get_activity_split_summaries(aid)
        print("\nsplit_summaries:")
        for s in (ss.get("splitSummaries") or []):
            print("   ", json.dumps({k: v for k, v in s.items()
                                     if v not in (None, 0, 0.0)}, default=str)[:400])
    except Exception as e:
        print("split_summaries ERROR", e)
    print("\nsummaryDTO:", json.dumps(dict(sorted((a.get("summaryDTO") or {}).items())),
                                      indent=1, default=str))
    print("\nHR zones:", g.get_activity_hr_in_timezones(aid))
    try:
        print("Power zones:", g.get_activity_power_in_timezones(aid))
    except Exception as e:
        print("Power zones ERROR", e)

# --- things the shape() collapsed ------------------------------------------------
head("PERSONAL RECORDS (Garmin's own)")
for r in (g.get_personal_record() or []):
    print("  typeId=%-3s value=%-12s %s  %s" % (r.get("typeId"), r.get("value"),
          (r.get("activityStartDateTimeLocalFormatted") or "")[:10], r.get("activityName")))

head("ENDURANCE SCORE groupMap")
print(json.dumps(g.get_endurance_score(d(30), d(1)), indent=1, default=str)[:2500])

head("TRAINING STATUS (unpacked)")
print(json.dumps(g.get_training_status(d(1)), indent=1, default=str)[:3500])

head("RHR / stats_and_body")
print(json.dumps(g.get_rhr_day(d(1)), indent=1, default=str)[:1200])

head("SLEEP - most recent 14 days, any data at all?")
for n in range(1, 15):
    try:
        s = (g.get_sleep_data(d(n)) or {}).get("dailySleepDTO") or {}
        print("  %s sleepTimeSeconds=%s deep=%s" % (d(n), s.get("sleepTimeSeconds"),
                                                    s.get("deepSleepSeconds")))
    except Exception as e:
        print("  %s ERROR %s" % (d(n), str(e)[:60]))

head("VO2MAX / max_metrics - look back for the last real value")
for n in (1, 3, 7, 14, 30, 60, 120, 400):
    try:
        m = g.get_max_metrics(d(n))
        gen = ((m or [{}])[0].get("generic") or {}) if m else {}
        print("  %s -> vo2 %s (%s)" % (d(n), gen.get("vo2MaxPreciseValue"), gen.get("calendarDate")))
    except Exception as e:
        print("  %s ERROR %s" % (d(n), str(e)[:60]))
