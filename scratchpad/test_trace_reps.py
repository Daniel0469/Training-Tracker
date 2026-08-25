#!/usr/bin/env python3
"""Speed-trace rep segmentation, against real activities and a synthetic float.

Reads Garmin, writes nothing. The float case has no real activity yet - Daniel's
threshold session hasn't been run - so it is proved on a constructed trace and
must be re-checked against the real one afterwards.

    python scratchpad/test_trace_reps.py training-garmin 23781117926 24053614591 23817366769
    python scratchpad/test_trace_reps.py training-garmin-cerys 23781080809 24053658518
    python scratchpad/test_trace_reps.py --synthetic
"""
import sys, os, json, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)


def show(label, res, expected_note=""):
    print("\n-- %s %s" % (label, expected_note))
    if not res:
        print("   (no reps found)")
        return
    print("   count=%s  %s" % (res["count"], res.get("note", "")))
    for r in res["reps"]:
        print("      rep %-2s %4ss %5s kmh  avg_hr=%-4s max_hr=%-4s cad=%-4s "
              "rec=%-5ss rec_kmh=%-5s rec_min_hr=%s"
              % (r["n"], r.get("sec"), r.get("kmh"), r.get("avg_hr", "-"),
                 r.get("max_hr", "-"), r.get("cadence_spm", "-"),
                 r.get("recovery_sec", "-"), r.get("recovery_kmh", "-"),
                 r.get("recovery_min_hr", "-")))
    print("   derived: %s" % json.dumps(res.get("derived")))


def synthetic():
    """A treadmill session whose recovery is a JOG, not a walk - the case Garmin's
    run/walk detection cannot segment at all. Built with the same wrist-estimate
    noise the real traces show (reps read high and wander), not clean steps."""
    import random
    random.seed(7)
    series, t = [], 0.0
    def block(sec, kmh, hr0, hr1, cad):
        nonlocal t
        for i in range(int(sec)):
            frac = i / max(1.0, sec)
            noise = random.uniform(-0.9, 0.9)
            series.append((t, max(0.0, kmh + noise), hr0 + (hr1 - hr0) * frac,
                           cad + random.uniform(-3, 3)))
            t += 1.0
    block(300, 8.0, 95, 130, 158)            # warm-up jog
    block(30, 12.5, 130, 140, 170); block(60, 5.5, 140, 120, 130)   # build-up + walk
    block(30, 12.5, 120, 142, 170); block(60, 5.5, 142, 118, 130)   # build-up + walk
    for i in range(4):                        # 4 x 6:00 @ 11.0, 1:30 float @ 7.5
        block(360, 11.0, 135 + i * 6, 160 + i * 5, 168)
        if i < 3:
            block(90, 7.5, 160 + i * 5, 138 + i * 4, 152)
    block(300, 5.5, 150, 110, 125)           # cool-down walk
    return series


if "--synthetic" in sys.argv:
    s = synthetic()
    print("synthetic trace: %d samples, %.0fs" % (len(s), s[-1][0]))
    res = G.reps_from_speed_trace(s, expected=4)
    show("jog-float session (4 x 6:00 @ 11.0, float @ 7.5)", res, "-> must find 4")
    assert res and res["count"] == 4, "FAILED: the float case is the whole point"
    # Garmin's own method cannot do this one: there are no walk blocks between reps.
    print("\n   Garmin run/walk equivalent: needs RWD_WALK between reps, which a")
    print("   float session has none of - that is why this detector exists.")
    print("\nSYNTHETIC PASS")
    sys.exit(0)

G._load_server_env(sys.argv[1]); G._ensure_ca_bundle()
person = os.environ["TT_PERSON"]
store = json.load(open(os.path.join(ROOT, "scratchpad", "store.json"), encoding="utf-8"))

for aid in sys.argv[2:]:
    a, splits = G.fetch_activity(aid)
    extras = G.fetch_activity_extras(aid)
    series = extras.get("series") or []
    date = (G._field(a, "startTimeLocal") or "")[:10]
    log = next((l for l in store.get("logs", [])
                if str(l.get("garminActivityId")) == str(aid)), None)
    # What the coach prescribed, if this session still exists in the program.
    expected = None
    if log:
        sess = ((store.get("program") or {}).get("sessions") or {}).get(log.get("sessionKey")) or {}
        for e in sess.get("exercises") or []:
            if G._is_run_entry(e) or e.get("garminRun"):
                expected = e.get("sets")
                break
    print("=" * 76)
    print("%s  %s  %s   prescribed reps=%s" % (person, date, a.get("activityName"), expected))
    typed = G.reps_from_typed_splits(extras.get("typed_splits"), a, series)
    print("   Garmin run/walk says: %s" % (
        typed.get("count") if typed and typed.get("reps") else
        ("refused: " + typed["skipped"][:60]) if typed else "nothing"))
    show("speed trace", G.reps_from_speed_trace(series, expected=expected))
