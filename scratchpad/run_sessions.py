"""The two per-person run sessions - the single source of truth for their shape.

Imported by `proto_run.py` (writes a LOCAL prototype state, pushes nothing) and,
once Daniel has signed the prototype off, by the apply script that writes them to
the shared store.

Design, 20 Aug 2026, from the run history rather than from a template:

Daniel - the 29 Jul intervals peaked at 157 bpm against a 200 max and a 173
threshold, and he finished them faster than he started (fade -5.9%, drift 9 bpm).
1 min on / 2 min off never gets HR near where adaptation happens. His own
limiters say progress the speed in small steps, and that duration is what caps
the endurance run. Longer reps at a controlled speed with short recoveries fix
both at once. 11.0 km/h is his current estimated 5k pace (5:27/km), so 4x800m is
a real but honest step up from 6x1min, and it is the first evidence that would
move the 5k estimate off medium confidence.

Cerys - the same session read 13.5 / 12.5 / 14.1 / 13.1 / 10.2 km/h: a 28% fade
with ten minutes above Zone 4. Not a speed problem, a repeatability problem,
which is exactly what her limiter says. So the speed is FIXED at her own stated
11.0 km/h and the progression is reps, then recovery. Short reps with walk
recoveries also keep total continuous impact low, which is what her shins need -
they were quiet on 13 Aug for the first time since July.

Both - hyrox is the stated main goal, so the unit is a repeat, and the ladder
runs at the rep: 800m -> 1km for Daniel, 400m -> more reps -> less rest -> 500m
for Cerys, both heading for 8x1km. The rep exercise is called "Run reps" for BOTH
of them and that name must stay stable: records, the Last column and the progress
chart all key on the exercise name, so renaming it per week ("4x800m") would
shred the trend. The prescription lives in `target`, which is what the coach
rewrites each week.

Columns are Distance / Time / Pace rather than the old Hard/Easy speed pair, so
each rep is its own row: that is what makes the fade visible in History, and it
lets Garmin fill the reps in automatically.
"""

CORE = [
    {"name": "Plank pull through", "warmup": "", "notes": "", "target": "3x15-20",
     "sets": 3, "cols": ["Weight (kg)", "Reps"], "groupId": "grp-run-core"},
    {"name": "Russian twists", "warmup": "", "notes": "", "target": "3x10-15",
     "sets": 3, "cols": ["Weight (kg)", "Reps"], "groupId": "grp-run-core"},
]

WARMUP_COMMON = """- Easy cardio - 5 min
- Hip CARs - 5 each side
- 90/90 switches - 10 each side
- Glute bridge - 10
- Side-lying abduction - 12 each side
- Hip flexor isometric - 3 x 20s each side
- Ankle circles - 10 each way
- Leg swings, front to back - 10 each leg
- Build to rep speed - 2 x 20s at 11 km/h, walk between"""

DANIEL = {
    "name": "Run: Daniel",
    "day": "Wednesday",
    "person": "Daniel",
    "warmupNote": "10 min, active. The last line matters - don't let rep 1 be the warm-up.\n\n"
                  + WARMUP_COMMON,
    "cooldownNote": """6 min.

- Walk until your breathing settles - 3 min
- Calf stretch on a step, knee straight then bent - 30s each way, each side
- Quad stretch, standing or seated - 40s each side
- Figure-4 glute stretch - 40s each side. On your back, ankle across the opposite thigh,
  pull the far knee towards your chest. Felt in the BACK of the hip.
- Hamstring stretch - 40s each side, slight knee bend, hinge from the hip, back flat""",
    "exercises": [
        {"name": "Run reps", "warmup": "",
         "notes": "Treadmill 11.0 km/h. Walk the recovery, don't stand on the rails.",
         "target": "4 x 800m @ 11.0 km/h, 90s walk",
         "sets": 4, "cols": ["Distance (km)", "Time (mm:ss)", "Pace"], "garminRun": True},
        {"name": "Easy jog", "warmup": "", "notes": "Time on feet, not pace. Conversational.",
         "target": "10 min easy", "sets": 1,
         "cols": ["Distance (km)", "Time (mm:ss)", "Pace"], "garminRun": True},
    ] + CORE,
}

CERYS = {
    "name": "Run: Cerys",
    "day": "Wednesday",
    "person": "Cerys",
    "warmupNote": "10 min, active. Your shins decide this session: if they talk to you here, say\n"
                  "so and we drop reps, not speed.\n\n" + WARMUP_COMMON,
    "cooldownNote": """6 min - stretches, plus the two bits of hip work you asked to keep.

- Hip hike - 2 x 10 each side
- Side-lying clam - 10 slow each side
- Calf stretch on a step, knee straight then bent - 30s each way, each side
    The most important line here - it's shin insurance after running.
- Quad stretch, standing or seated - 40s each side
- Figure-4 glute stretch - 40s each side. On your back, ankle across the opposite thigh,
  pull the far knee towards your chest. Felt in the BACK of the hip, not the front.
- Hamstring stretch - 40s each side, slight knee bend, hinge from the hip, back flat""",
    "exercises": [
        {"name": "Run reps", "warmup": "",
         "notes": "Treadmill 11.0 km/h, every rep. Same speed on rep 6 as on rep 1 - that IS the "
                  "session. Walk the recovery.",
         "target": "6 x 400m @ 11.0 km/h, 90s walk",
         "sets": 6, "cols": ["Distance (km)", "Time (mm:ss)", "Pace"], "garminRun": True},
        {"name": "Incline walk", "warmup": "",
         "notes": "Your Zone 2. 13 Aug was 27 min at HR 139 and pain-free - this is that, kept.",
         "target": "10 min @ 4-6%", "sets": 1, "cols": ["Min", "Notes"]},
    ] + CORE,
}

RUN_KEYS = {"runDaniel": DANIEL, "runCerys": CERYS}
RETIRE = "Cardio: Speed + Core"      # removed from the program; its logs keep the name
OPTIONAL = "Cardio: Endurance + Core"  # day -> Optional, so it stays pickable but never auto-opens
# The kept-as-backup Zone 2 run gets a row per km of its 5km target. Blank rows
# are dropped when you save, so the "wear the watch, leave it empty, Garmin fills
# the splits" path is exactly as it was - the rows are there for the day you run
# without the watch and want to type your own splits, plus "+ set" for more.
ZONE2_EX, ZONE2_SETS = "Easy run (Zone 2)", 5


def apply_to_program(prog):
    """Mutate `prog` in place. Idempotent. Returns a list of what changed."""
    changed = []
    sessions, order = prog["sessions"], prog.setdefault("order", [])

    for key, sess in RUN_KEYS.items():
        if sessions.get(key) != sess:
            sessions[key] = {k: (v if not isinstance(v, list) else [dict(e) for e in v])
                             for k, v in sess.items()}
            changed.append(("added" if key not in order else "updated") + " " + sess["name"])
        if key not in order:
            order.append(key)

    for key, s in list(sessions.items()):
        if (s or {}).get("name") == RETIRE:
            del sessions[key]
            if key in order:
                order.remove(key)
            changed.append("retired " + RETIRE + " (its logged history keeps the name)")
        elif (s or {}).get("name") == OPTIONAL:
            if s.get("day") != "Optional":
                s["day"] = "Optional"
                changed.append(OPTIONAL + ": Wednesday -> Optional (pickable, never auto-opened)")
            for e in s.get("exercises") or []:
                if e.get("name") == ZONE2_EX and e.get("sets") != ZONE2_SETS:
                    e["sets"] = ZONE2_SETS
                    changed.append("%s: %s now draws %d rows, one per km"
                                   % (OPTIONAL, ZONE2_EX, ZONE2_SETS))

    return changed
