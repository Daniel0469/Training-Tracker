#!/usr/bin/env python3
"""Third pass: is Garmin's run/walk split detection a better interval source than our
speed-trace heuristic? And does this person wear the watch outside workouts?

    python scratchpad/probe_garmin3.py training-garmin [activity_id ...]
"""
import sys, os, json, datetime, collections, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("ttgarmin", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)

G._load_server_env(sys.argv[1] if len(sys.argv) > 1 else "training-garmin")
G._ensure_ca_bundle()
g = G.garmin_client()
today = datetime.date.today()
d = lambda n: (today - datetime.timedelta(days=n)).isoformat()
print("PERSON:", os.environ.get("TT_PERSON"))
print("DEVICES:", [x.get("productDisplayName") for x in (g.get_devices() or [])])

print("\n### wear-time check: does the watch see anything outside workouts?")
for n in range(1, 11):
    st = g.get_stats(d(n)) or {}
    sl = ((g.get_sleep_data(d(n)) or {}).get("dailySleepDTO") or {})
    print("  %s steps=%-6s sleep=%-7s rhr=%-4s bb_diff=%s" % (
        d(n), st.get("totalSteps"), sl.get("sleepTimeSeconds"),
        st.get("restingHeartRate"), st.get("bodyBatteryChargedValue")))

ids = sys.argv[2:]
if not ids:
    ids = [str(a.get("activityId")) for a in (g.get_activities(0, 30) or []) if G.is_run(a)][:3]

for aid in ids:
    a = g.get_activity(aid)
    print("\n" + "=" * 68)
    print("ACTIVITY %s  %s  %s  (%s)" % (aid, a.get("activityName"), G.activity_type(a),
                                         (G._field(a, "startTimeLocal") or "")[:10]))
    print("=" * 68)
    try:
        sp = (g.get_activity_typed_splits(aid) or {}).get("splits") or []
    except Exception as e:
        print("typed_splits ERROR", e); continue
    print("split types:", dict(collections.Counter(s.get("type") or s.get("splitType") or "?" for s in sp)))
    for want in ("RWD_RUN", "INTERVAL_ACTIVE", "RWD_WALK"):
        rows = [s for s in sp if (s.get("type") or "") == want]
        if not rows:
            continue
        print("\n  %s x%d" % (want, len(rows)))
        for i, s in enumerate(rows, 1):
            dist = s.get("distance") or 0
            dur = s.get("duration") or 0
            kmh = (dist / dur * 3.6) if dur else 0
            print("    %2d  %5.0fm  %6.1fs  %5.2f km/h  pace %-5s  HR %s/%s  cad %s  pwr %s" % (
                i, dist, dur, kmh, G._pace(dist / 1000, dur) or "-",
                s.get("averageHR"), s.get("maxHR"),
                round(s.get("averageRunCadence") or 0), s.get("averagePower")))
    # what our own heuristic says, for comparison
    iv = G.detect_intervals(G.fetch_detail_series(aid))
    print("\n  detect_intervals() ->", json.dumps(iv) if iv else "None")
