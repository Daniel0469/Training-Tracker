"""Prototype the week-1 run prescriptions against a COPY of the store.

Reads the current program state, applies the four run sessions through the same
resolver the MCP tool uses (with the new `which` selector), writes the result to a
local state file, and prints a before/after. The shared store is never opened.
"""
import io, json, importlib.util, copy

SRC = 'scratchpad/proto-term-state.json'
OUT = 'scratchpad/proto-run-week1.json'

spec = importlib.util.spec_from_file_location("srv", "mcp-coach/server.py")
srv = importlib.util.module_from_spec(spec); spec.loader.exec_module(srv)

data = json.load(io.open(SRC, encoding='utf-8'))
before = copy.deepcopy(data)

RUN_COLS = ["Distance (km)", "Time (mm:ss)", "Pace"]

# ============================================================ Daniel, Tuesday
D_EASY_EX = [{
    "name": "Easy run",
    "target": "30 min continuous, HR under 140",
    "sets": 1,
    "cols": RUN_COLS,
    "notes": (
        "Correction first: your longest run is not 3.45 km any more. On 26 August you covered "
        "6.48 km on the watch - about 5.9 km once the belt over-read is taken off - with 6.17 km "
        "of it running. Your longest unbroken effort inside that was 13:44 at 4:59/km with 9 beats "
        "of drift. The card used to say 3.45 km and it was out of date.\n\n"
        "So 30 minutes continuous is not a distance problem. Under 140 bpm it comes out around "
        "3.8-4.0 km, well inside what you did a fortnight ago. What is new is that it is unbroken, "
        "and that it is genuinely easy - which nothing in your August log is.\n\n"
        "Every August run finished in Zone 3 or above: 13 Aug RPE 8, 20 Aug RPE 9, 26 Aug RPE 9 "
        "with the watch calling it weak. Your July runs were the easy ones, at 118-127 bpm. Going "
        "from one run a week to two, the second one is meant to be the easy one, and the standard "
        "way this goes wrong is that both end up hard.\n\n"
        "140 is your Zone 3 floor and it is a ceiling, not a target. Over it, slow down. If slowing "
        "down is not enough, walk until it drops and then run again - that still counts. The "
        "duration is the training; today it genuinely does not matter what the pace turns out to be.\n\n"
        "Build it on Garmin once (see the setup note) and the watch holds the zone for you, so you "
        "are not the one policing it mid-run."
    ),
}]

D_EASY_SETUP = """BUILD IT ON GARMIN CONNECT ONCE - then the watch runs the session and holds
the zone for you. This is the outdoor version of programming the belt.

  Garmin Connect app -> More -> Training & Planning -> Workouts -> Create a Workout -> Run
  Name it "Zone 2 - 30 min"

  step           type      duration   target
  1  Warm Up     Time       10:00     No Target
  2  Run         Time       30:00     Heart Rate -> Custom -> 120 to 139
  3  Cool Down   Time        5:00     No Target

  Save, then Send to Watch.

ON THE DAY: press Run, hold MENU -> Training -> Workouts -> "Zone 2 - 30 min" -> Do Workout.
The watch buzzes at every step change, laps by itself, and shows an arrow the moment you drift
out of 120-139. Follow the arrow. That is the entire session.

Only the 30-minute step carries a target, so warm up and cool down however you like.

End to end this is about 45 minutes plus stretching, against a 40-45 minute slot. Week 1 exists
to find out whether that actually fits before the train, so time it and write down what it took.

IF IT IS TOO COLD, WET OR DARK - treadmill fallback. 4 blocks.

   #   time   speed   what
   1   5:00    5.5    walk, warm up
   2   3:00    8.0    easy jog build
   3  30:00    9.0    THE RUN - continuous
   4   5:00    5.5    cool-down walk

Total 43:00. 9.0 should sit you around 130-135 - on 26 August 8.3 km/h had you at 124. If the
belt puts you over 140, drop the speed, not the time. The duration is the training."""

D_EASY_REC = """OUTDOOR RUN - one activity for the whole thing, warm-up included.

RUNNING THE GARMIN WORKOUT (the default): press Start as you begin the warm-up and End when the
cool-down finishes. Nothing in between. The workout laps automatically at each step change, so
lap 1 is the warm-up, lap 2 is the 30-minute run, lap 3 is the cool-down. Do NOT press Lap
yourself - it splits a step in two and the run stops reading as one continuous block, which is
the one thing this session is being measured on.

FREESTYLE INSTEAD? Start at the warm-up, one Lap press as the continuous run begins, End after
the cool-down. Two presses.

Outdoors the watch measures the distance itself. No calibration, nothing to key in.

ON THE TREADMILL INSTEAD? One activity covering the whole belt run, lap as the 30-minute block
starts, and say yes to "Calibrate & Save" at the end with the treadmill's total. Type the belt
distance in as well - typed data is never overwritten by the sync, and the belt number beats
the wrist estimate.

REPORT BACK: what pace 120-139 actually turned out to be. That number is the point of the
session and we have never had it outdoors."""

# =========================================================== Daniel, Thursday
D_QUAL_EX = [{
    "name": "Run reps",
    "target": "4 x 4:00 at threshold (HR 165-173), 2:00 easy jog between",
    "sets": 4,
    "cols": RUN_COLS,
    "garminRun": True,
    "notes": (
        "Threshold effort, not 5k effort. Four minutes is short enough that the method would "
        "normally say run it at goal pace, but goal pace is 4:00/km against a current 5:12 and "
        "that is not a real number yet. So these are your 6-minute reps with two minutes taken "
        "off, at the same intensity. Not a faster session, a shorter one.\n\n"
        "165-173 is the band, and it is exactly where 26 August landed: four reps averaging 149, "
        "161, 160, 163, with the ends touching 168, 171, 169 and finally 174 against a threshold "
        "of 173. That was a threshold session landing precisely where one should. This is the same "
        "session, outdoors.\n\n"
        "The real job this week is calibration. Every quality rep you have ever run was on a belt "
        "that chose the speed for you. Outdoors nothing chooses it, and eight self-paced kilometres "
        "is exactly what a Hyrox is. So run to the heart rate, look at the pace afterwards, and we "
        "will know what your threshold actually costs on the road.\n\n"
        "Start rep 1 no faster than you can hold rep 4. Your speed reserve is big enough that the "
        "first rep is the one that will lie to you.\n\n"
        "Losing the 5 x 6:00 is deliberate, not an oversight. Thirty minutes at threshold does not "
        "fit a 40-minute morning. The duration progression moves to Tuesday instead, which is the "
        "session that actually attacks the 8 km gate."
    ),
}]

D_QUAL_SETUP = """BUILD IT ON GARMIN CONNECT ONCE - then the watch times every rep and every
float for you, which is what the belt used to do.

  Garmin Connect app -> More -> Training & Planning -> Workouts -> Create a Workout -> Run
  Name it "4 x 4 threshold"

  step             type      duration   target
  1  Warm Up       Time       10:00     No Target
  2  Repeat 4x
       Run         Time        4:00     Heart Rate -> Custom -> 165 to 173
       Recover     Time        2:00     No Target
  3  Cool Down     Time        5:00     No Target

  Save, then Send to Watch.

ON THE DAY: press Run, hold MENU -> Training -> Workouts -> "4 x 4 threshold" -> Do Workout.

ONE THING TO KNOW BEFORE YOU START IT. Heart rate lags 45-60 seconds behind effort, so at the
start of every rep the watch will tell you to speed up when you are already running correctly.
Ignore it for the first minute of each rep. Settle into the effort and let the heart rate
arrive. Chasing that arrow off the line is how a threshold session becomes a 5k session by
rep three.

Total 37 minutes plus stretching.

IF IT IS TOO COLD, WET OR DARK - treadmill fallback. 11 blocks, inside the 20-stage limit.
Enter it all before you start.

   #   time    speed    what
   1   5:00     8.0     warm-up jog
   2   0:30    12.5     build-up
   3   1:00     5.5     walk
   4   4:00    11.0     REP 1
   5   2:00     7.5     float
   6   4:00    11.0     REP 2
   7   2:00     7.5     float
   8   4:00    11.0     REP 3
   9   2:00     7.5     float
  10   4:00    11.0     REP 4
  11   5:00     5.5     cool-down walk

Total 33:30 - 6:30 warming up, 16:00 hard, 6:00 of floats, 5:00 walking it off. Shorter reps
than the 5 x 6:00 you were doing, because the morning slot is 40 minutes, not 50. Same speed."""

D_QUAL_REC = """OUTDOOR RUN - one activity for the whole thing, warm-up included.

RUNNING THE GARMIN WORKOUT (the default): Start at the warm-up, End after the cool-down, and
press nothing in between. The workout laps at every step change on its own, so you get a clean
lap per rep and a lap per float - which is exactly what the rep-by-rep read needs, and what
hand-lapping has kept getting wrong.

You do NOT need to turn off the 1 km auto-lap for this. A structured workout overrides it.

FREESTYLE INSTEAD? Turn the 1 km auto-lap OFF first (Activity Settings -> running -> Auto Lap),
because outdoors it fires mid-rep. Then Lap at the start and the end of every rep: nine presses
across the session.

Outdoors the watch measures the distance itself, so there is nothing to calibrate or key in.

ON THE TREADMILL INSTEAD? One activity covering the whole belt run, lap at every speed change,
and say yes to "Calibrate & Save" at the end, entering the treadmill's total distance.

REPORT BACK: the pace of each rep. Four reps held at 165-173 outdoors is the first honest read
we will have of what your threshold costs off a belt, and every pace target after this one
comes from it."""

# ============================================================= Cerys, Tuesday
C_EASY_EX = [{
    "name": "Incline walk",
    "target": "20:00 held in Zone 2 (HR 119-138)",
    "sets": 1,
    "cols": ["Min", "Notes"],
    "garminRun": True,
    "notes": (
        "This session has changed shape. It was a second set of running reps; it is now your Zone 2 "
        "session, and Zone 2 for you is a walk, not a run. That is your own account of it and the "
        "data agrees - you are in Zone 4 within a minute of starting to run, even at an easy "
        "10 km/h.\n\n"
        "So the heart rate is the target and the walk is only how you get there. 119-138 is your "
        "Zone 2. Build it on Garmin once (see the setup note) and the watch runs it: if it tells "
        "you the rate is high, drop the GRADIENT before you drop the speed; if it never says "
        "anything at all for twenty minutes, add gradient next week. You spotted this yourself on "
        "26 August - the speed was too high for the incline and your heart rate was above where it "
        "should have been - and you finished on 4.5 at 6%, which was the right instinct.\n\n"
        "Why there is no running today: Monday evening is hack squat and sled push-pull, twelve "
        "hours before this. Sled push loads calves and shins hard, and the shins are governing "
        "everything. Thursday's run gets three clear days instead.\n\n"
        "This is not a consolation prize. The incline walking is where your aerobic base is "
        "actually being built, it is genuinely pain-free, and it costs your shins nothing. What it "
        "cannot do is prepare the tibia for running, which is what Thursday is for. Two different "
        "jobs and both need doing.\n\n"
        "20:00 is up from the 10-15 written before, because it is now the whole session rather "
        "than a tail on the end of one."
    ),
}]

C_EASY_SETUP = """BUILD IT ON GARMIN CONNECT ONCE - then the watch holds the zone for you and
you never have to look at the screen.

  Garmin Connect app -> More -> Training & Planning -> Workouts -> Create a Workout -> Walk
  Name it "Zone 2 - 20 min"

  step           type      duration   target
  1  Warm Up     Time        5:00     No Target
  2  Walk        Time       20:00     Heart Rate -> Custom -> 119 to 138
  3  Cool Down   Time        5:00     No Target

  Save, then Send to Watch.

ON THE DAY: press Walk, hold MENU -> Training -> Workouts -> "Zone 2 - 20 min" -> Do Workout.
The watch shows an arrow the moment you drift out of 119-138. Follow it: too high, ease the
GRADIENT before the speed; never buzzing at all across the whole 20 minutes, add gradient
next week.

Total 30 minutes plus stretching, so this one fits the morning comfortably.

IF IT IS TOO COLD, WET OR DARK - treadmill fallback. 3 blocks.

   #    time    speed   incline   what
   1    5:00     5.0      0       walk, warm up
   2   20:00     5.0      6%      THE SESSION - hold HR 119-138
   3    5:00     4.0      0       cool-down walk

5.0 at 6% is where 26 August put you around the right heart rate. Adjust to the WATCH, not to
the numbers written here.

OUTDOORS IS THE DEFAULT - a hill or any steady gradient, walked briskly for 20 minutes. Flat is
fine if there is nothing near you; you will just walk faster to reach the same zone."""

C_EASY_REC = """ZONE 2 WALK - one activity for the whole thing, warm-up included. Record it as a
WALK, not a run: the heart rate is the record here and the pace means nothing.

RUNNING THE GARMIN WORKOUT (the default): Start at the warm-up, End after the cool-down, press
nothing in between. It laps at each step by itself, so lap 2 is the 20 minutes that matter.

FREESTYLE INSTEAD? Start at the warm-up, one Lap press as the 20-minute block begins, End after
the cool-down. Two presses.

ON THE TREADMILL INSTEAD? Same thing, one activity, lap as the 20-minute block starts.

REPORT BACK, in the Notes column: the gradient and the speed that actually held you in 119-138.
That is the number this session exists to find, and next week's starts from it."""

C_EASY_WU = """WARM-UP - 5 min, before the session proper.

- Easy walk - 3 min, flat
- Ankle circles - 10 each way
- Leg swings, front to back - 10 each leg

No jog build - there is no running in this session. Nothing static."""

C_EASY_CD = """COOL-DOWN - 5 min walk, then stretches.

- Walk until your breathing settles. HR down before you stretch anything.
- Calf stretch on a step or kerb, knee straight then bent - 30s each way, each side
- Quad stretch, standing - 40s each side
- Figure-4 glute stretch - 40s each side
- Hamstring stretch - 40s each side, slight knee bend, hinge from the hip

The calf stretch is the one that matters most for you - calf length is shin insurance."""

# ============================================================ Cerys, Thursday
C_QUAL_EX = [{
    "name": "Run reps",
    "target": "8 x 1:00 run, 2:00 walk between - the minute stays a minute",
    "sets": 8,
    "cols": RUN_COLS,
    "garminRun": True,
    "notes": (
        "What you actually did on 26 August: ten reps, not eight, and five of them ran 72-81 "
        "seconds instead of sixty.\n\n"
        "And it was a good session. Your fastest rep was the last one - 13.6 km/h, after 13.5, "
        "13.2 and 13.1. On 29 July you faded 28% by rep five; this time there was no fade at all. "
        "Your cadence held between 136 and 151 the whole way to the end, where in July it fell "
        "from 151 to 140. Holding cadence late was the target and you hit it. Heart rate recovery "
        "averaged 34 beats between reps.\n\n"
        "You also typed the reps accurately, which matters more than it sounds - the watch and "
        "your rows agree almost exactly, so for the first time the record is the truth rather than "
        "a rounded guess.\n\n"
        "The one thing to change: rep length is the single variable the shin protocol says to hold "
        "constant while everything else grows, because it is what loads shins hardest. You "
        "stretched it, and your own note says the shins spoke on one rep and were exhausted "
        "afterwards. So eight reps, and a minute means a minute. Build it on Garmin (see the setup "
        "note) and the watch takes that decision away from you entirely.\n\n"
        "Why eight is not a step backwards. This is your first run off a treadmill in this block, "
        "and a belt absorbs about 71% more shock than pavement. The same rep on the road is more "
        "load than it was on the belt at identical speed. Holding at eight strict minutes on a new "
        "surface is the same step, not a smaller one. Once the surface is old news the reps grow "
        "again.\n\n"
        "Ease off any rep the shins ask you to, and stop at the first twinge rather than the "
        "second. One flare means we hold here another week, not that we go back."
    ),
}]

C_QUAL_SETUP = """BUILD IT ON GARMIN CONNECT ONCE - and this one matters more than usual,
because the watch timing the reps is what stops them stretching.

  Garmin Connect app -> More -> Training & Planning -> Workouts -> Create a Workout -> Run
  Name it "8 x 1 run walk"

  step             type      duration   target
  1  Warm Up       Time       10:00     No Target
  2  Repeat 8x
       Run         Time        1:00     No Target
       Recover     Time        2:00     No Target
  3  Cool Down     Time        5:00     No Target

  Save, then Send to Watch.

ON THE DAY: press Run, hold MENU -> Training -> Workouts -> "8 x 1 run walk" -> Do Workout.

NO HEART RATE TARGET ANYWHERE IN IT, on purpose. Your heart rate does what it does the moment
you start running, and giving the watch a rate to chase would just have it telling you to stop
mid-rep. The watch is here for the CLOCK. It buzzes at sixty seconds and you walk. On 26 August
five of your reps ran 72-81 seconds instead of sixty, and rep length is the one thing the shin
protocol says to hold still, so this is the single most useful thing the watch can do for you.

Total 39 minutes plus stretching.

IF IT IS TOO COLD, WET OR DARK - treadmill fallback. 18 blocks, inside the 20-stage limit.
Do the warm-up BEFORE you program anything.

   #    time    speed   incline   what
   1    0:20    10.0      0       jog test - shins and hip get a say here
   2    1:00     5.5      0       walk
   3    1:00    10.0      0       REP 1
   4    2:00     5.5      0       walk
   5    1:00    10.0      0       REP 2
   6    2:00     5.5      0       walk
   7    1:00    10.0      0       REP 3
   8    2:00     5.5      0       walk
   9    1:00    10.0      0       REP 4
  10    2:00     5.5      0       walk
  11    1:00    10.0      0       REP 5
  12    2:00     5.5      0       walk
  13    1:00    10.0      0       REP 6
  14    2:00     5.5      0       walk
  15    1:00    10.0      0       REP 7
  16    2:00     5.5      0       walk
  17    1:00    10.0      0       REP 8
  18    5:00     5.0      0       cool-down walk

Total 27:20 on the belt. The incline walk has moved to Tuesday, where it is now the whole
session, so this one is running only.

OUTDOORS IS THE DEFAULT - flat ground, and the walks are timed the same way."""

C_QUAL_REC = """OUTDOOR RUN - one activity for the whole thing, warm-up included.

RUNNING THE GARMIN WORKOUT (the default): Start at the warm-up, End after the cool-down, and
press nothing in between. Every rep and every walk gets its own lap automatically.

THIS FIXES THE 26 AUGUST PROBLEM. Your note said you forgot to lap after the warm-up, so the
warm-up and the first reps ran together in one block and the splits had to be rebuilt from the
speed trace afterwards. With the workout loaded there is no lap to forget.

You do NOT need to turn off the 1 km auto-lap for this - a structured workout overrides it.

FREESTYLE INSTEAD? Turn the 1 km auto-lap OFF first (Activity Settings -> running -> Auto Lap),
then Lap once as the warm-up finishes, and at the start and the end of every rep.

Outdoors the watch measures the distance itself, so there is nothing to calibrate or key in.

ON THE TREADMILL INSTEAD? One activity covering the whole belt run, lap at every speed change,
and say yes to "Calibrate & Save" at the end, entering the treadmill's total distance.

REPORT BACK: whether any rep had to be eased off, and which one. That is the shin signal and it
is what decides next week."""

# ================================================================== apply
PLAN = [
    ("Daniel", "Tuesday",  dict(exercises=D_EASY_EX, setup=D_EASY_SETUP, recording=D_EASY_REC,
                                name="Zone 2: Daniel")),
    ("Daniel", "Thursday", dict(exercises=D_QUAL_EX, setup=D_QUAL_SETUP, recording=D_QUAL_REC)),
    ("Cerys",  "Tuesday",  dict(exercises=C_EASY_EX, setup=C_EASY_SETUP, recording=C_EASY_REC,
                                warmup=C_EASY_WU, cooldown=C_EASY_CD, name="Zone 2: Cerys")),
    ("Cerys",  "Thursday", dict(exercises=C_QUAL_EX, setup=C_QUAL_SETUP, recording=C_QUAL_REC)),
]


def apply(data, person, which, exercises=None, name=None, day=None,
          warmup=None, cooldown=None, recording=None, setup=None):
    """The mutation half of set_run, against our copy - the real one writes to GitHub."""
    key, s = srv._find_run_session(data, person, which)
    if key is None:
        raise SystemExit(f"resolve failed for {person}/{which}: {s}")
    if exercises is not None:
        s["exercises"] = [srv._clean_exercise(e, i) for i, e in enumerate(exercises)]
    if name:
        s["name"] = name
    if day:
        s["day"] = day
    for field, text in (("setupNote", setup), ("recordingNote", recording),
                        ("warmupNote", warmup), ("cooldownNote", cooldown)):
        if text is not None:
            s[field] = text.strip()
    return key


for person, which, kw in PLAN:
    key = apply(data, person, which, **kw)
    print(f"applied {person}/{which} -> {key}")

data.setdefault("program", {})["updatedAt"] = srv._now_iso()
json.dump(data, io.open(OUT, 'w', encoding='utf-8'), indent=1)
print(f"\nwrote {OUT}")

print("\n" + "=" * 78)
for person, which, _ in PLAN:
    k, s = srv._find_run_session(data, person, which)
    _, b = srv._find_run_session(before, person, which)
    print(f"\n### {s['name']}  ({s['day']}, key={k})")
    if b.get("name") != s.get("name"):
        print(f"    RENAMED from {b['name']!r}")
    for e in s["exercises"]:
        print(f"    now: {e['name']} - {e['target']}")
    for e in b.get("exercises", []):
        print(f"    was: {e['name']} - {e.get('target')}")
