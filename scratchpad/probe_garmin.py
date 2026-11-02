#!/usr/bin/env python3
"""One-off: find out which Garmin endpoints actually hold data for a person.

Read-only. Nothing is written to the store. Prints a compact yes/no/shape report so
we can decide what's worth pulling into the tracker.

    python scratchpad/probe_garmin.py training-garmin
"""
import sys, os, json, datetime, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("ttgarmin", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)

server = sys.argv[1] if len(sys.argv) > 1 else "training-garmin"
G._load_server_env(server)
G._ensure_ca_bundle()
g = G.garmin_client()

today = datetime.date.today()
d = lambda n: (today - datetime.timedelta(days=n)).isoformat()

def shape(v, depth=0):
    """Describe a response compactly: keys of dicts, length+first-item shape of lists."""
    if isinstance(v, dict):
        if depth >= 2:
            return "{%d keys}" % len(v)
        return {k: shape(x, depth + 1) for k, x in list(v.items())[:40]}
    if isinstance(v, list):
        return ["len=%d" % len(v)] + ([shape(v[0], depth + 1)] if v else [])
    if isinstance(v, str):
        return v[:40]
    return v

def probe(label, fn):
    try:
        v = fn()
    except Exception as e:
        print("\n--- %-28s ERROR %s" % (label, str(e)[:120]))
        return None
    empty = v is None or v == [] or v == {}
    print("\n--- %-28s %s" % (label, "EMPTY" if empty else "DATA"))
    if not empty:
        print(json.dumps(shape(v), indent=1, default=str)[:2200])
    return v

print("=" * 70)
print("person:", os.environ.get("TT_PERSON"), " probed:", today)
print("=" * 70)

probe("devices", lambda: [{"name": x.get("productDisplayName"), "id": x.get("deviceId")}
                          for x in (g.get_devices() or [])])

# --- daily / wellness (the hub side) -------------------------------------------
probe("sleep_data(yesterday)", lambda: g.get_sleep_data(d(1)))
probe("hrv_data(yesterday)", lambda: g.get_hrv_data(d(1)))
probe("training_readiness", lambda: g.get_training_readiness(d(1)))
probe("training_status", lambda: g.get_training_status(d(1)))
probe("body_battery", lambda: g.get_body_battery(d(3), d(1)))
probe("all_day_stress", lambda: g.get_all_day_stress(d(1)))
probe("stats(yesterday)", lambda: g.get_stats(d(1)))
probe("rhr_day", lambda: g.get_rhr_day(d(1)))
probe("respiration", lambda: g.get_respiration_data(d(1)))
probe("spo2", lambda: g.get_spo2_data(d(1)))
probe("intensity_minutes", lambda: g.get_intensity_minutes_data(d(1)))
probe("weekly_intensity_minutes", lambda: g.get_weekly_intensity_minutes(d(1), 4))
probe("daily_steps", lambda: g.get_daily_steps(d(7), d(1)))
probe("floors", lambda: g.get_floors(d(1)))
probe("morning_readiness", lambda: g.get_morning_training_readiness(d(1)))

# --- fitness / performance ------------------------------------------------------
probe("max_metrics (VO2max)", lambda: g.get_max_metrics(d(1)))
probe("endurance_score", lambda: g.get_endurance_score(d(30), d(1)))
probe("hill_score", lambda: g.get_hill_score(d(30), d(1)))
probe("running_tolerance", lambda: g.get_running_tolerance(d(1)))
probe("lactate_threshold", lambda: g.get_lactate_threshold(d(60), d(1)))
probe("fitnessage", lambda: g.get_fitnessage_data(d(1)))
probe("personal_record", lambda: g.get_personal_record())
probe("race_predictions", lambda: g.get_race_predictions())
probe("user_summary", lambda: g.get_user_summary(d(1)))

# --- body / nutrition -----------------------------------------------------------
probe("body_composition(90d)", lambda: g.get_body_composition(d(90), d(0)))
probe("weigh_ins(90d)", lambda: g.get_weigh_ins(d(90), d(0)))
probe("hydration", lambda: g.get_hydration_data(d(1)))
probe("nutrition_food_log", lambda: g.get_nutrition_daily_food_log(d(1)))

# --- per-activity extras --------------------------------------------------------
runs = [a for a in (g.get_activities(0, 30) or []) if G.is_run(a)]
print("\n\n" + "=" * 70)
print("recent runs:")
for a in runs[:12]:
    print("  %s  %-34s %s  id=%s" % ((G._field(a, "startTimeLocal") or "")[:16],
                                     (a.get("activityName") or "")[:34],
                                     G.activity_type(a), a.get("activityId")))
print("=" * 70)

if runs:
    aid = runs[0].get("activityId")
    print("\n### per-activity probes on the most recent run", aid)
    full = probe("get_activity (all keys)", lambda: g.get_activity(aid))
    probe("activity_weather", lambda: g.get_activity_weather(aid))
    probe("typed_splits", lambda: g.get_activity_typed_splits(aid))
    probe("split_summaries", lambda: g.get_activity_split_summaries(aid))
    probe("exercise_sets", lambda: g.get_activity_exercise_sets(aid))
    probe("power_in_timezones", lambda: g.get_activity_power_in_timezones(aid))
    det = probe("activity_details metric keys",
                lambda: sorted(m.get("key") for m in
                               (g.get_activity_details(aid, maxchart=2, maxpoly=0)
                                .get("metricDescriptors") or [])))
    if full:
        s = full.get("summaryDTO") or {}
        print("\n### summaryDTO full field list (the numbers we could be reading):")
        print(json.dumps({k: v for k, v in sorted(s.items())}, indent=1, default=str)[:4000])
