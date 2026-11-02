"""The term routine - the rewritten program, agreed with Daniel on 2026-09-06.

Rewrites the four lifting sessions IN PLACE (same keys) so the Last column and
every log keep pointing at the right session, re-days the runs onto the two
mornings, and leaves the Mobility assessment to fill Wednesday for week 1.

Nothing here touches the shared store. `proto_term.py` applies it to a COPY.

The week
    Mon      Lower A   (hack squat led, sled push+pull)        evening 75-90
    Tue  AM  Easy run                                          outdoors ~40
         PM  Upper A   (bench led, farmers carry)              evening 75-90
    Wed      Mobility assessment, then mobility training       evening 60-75
    Thu  AM  Quality run                                       outdoors ~40
         PM  Upper B   (shoulder press led, ski/row)           evening 75-90
    Fri      Lower B   (deadlift led, sandbag lunges)          evening 75-90
    Sat/Sun  shifts. Optional easy run if you fancy it.
"""

KG = ["Weight (kg)", "Reps"]
ASSIST = ["Assist (kg)", "Reps"]
DIST = ["Weight (kg)", "Distance (m)"]
ROUNDS = ["Weight (kg)", "Rounds"]
ERG = ["Metres", "Time (mm:ss)"]
RUN = ["Distance (km)", "Time (mm:ss)", "Pace"]
MIN = ["Min", "Notes"]


def ex(name, target, sets, cols=None, notes="", muscles=None, **extra):
    e = {"name": name, "target": target, "sets": sets, "cols": cols or KG}
    if notes:
        e["notes"] = notes
    if muscles is not None:
        e["muscles"] = muscles
    e.update(extra)
    return e


# --------------------------------------------------------------- lifting days

LOWER_A = [
    ex("Back squat (technique)", "2x5 light", 2,
       notes="Not a working set and not a PR attempt - this is the pattern kept alive while the "
             "hack squat does the loading. Empty bar to about 40%. Rack position is the thing to "
             "fix here: wider grip, elbows down. Sort it at 20kg, not at 100.",
       muscles=["quads", "glutes"]),
    ex("Hack squat", "3x5-8", 3,
       notes="The working squat for this block. Fixed path, so Cerys can load it properly while "
             "the back squat rack position is still being sorted. Pick a weight inside the rep "
             "range and beat it next week - target and ceiling, you choose inside it.",
       muscles=["quads", "glutes"]),
    ex("Romanian deadlift", "3x8-12", 3,
       notes="Hinge, not a squat. Bar close, soft knees, stop where the hamstrings stop you - "
             "the back rounding is the end of the set. Serves the deadlift and hamstring "
             "durability for the running.",
       muscles=["hamstrings", "glutes"]),
    ex("Sled push + pull", "4 rounds - push a length, pull it back", 4, ROUNDS,
       notes="One round = push it down, pull it back. Two Hyrox stations in one exercise. "
             "Phase 0, so this is technique at a light load: you should finish each round "
             "breathing hard but able to talk. Build the load slowly - the sled is the one "
             "thing here that punishes the legs without wrecking them for Tuesday's run.",
       muscles=["quads", "glutes", "hamstrings", "traps"]),
    ex("Single-leg seated leg curl", "3x8-12 each leg", 3,
       notes="Your own fix from 27 Jul, finally in the program - the bilateral version was "
             "pulling your body instead of the weight. Log the weight per leg; the numbers "
             "are not comparable to the old two-leg entries, which is why the name changed.",
       muscles=["hamstrings"]),
    ex("Leg press calf raise", "3x12-15", 3,
       notes="Feet on the bottom edge of the leg press platform, press through the balls of the "
             "feet. Nothing on the shoulders.",
       muscles=["calves"]),
    ex("Hip abduction", "3x12-15", 3,
       notes="Light. Daniel asked for this to stay but at lower loads - quality of the movement "
             "over the number on the stack. Slow out, slower back.",
       muscles=["glutes"]),
    ex("Back extension", "3x10-15", 3, muscles=["lowerback"]),
]

UPPER_A = [
    ex("Bench press", "3x5-8", 3,
       notes="Long-term goal lift, held at maintenance this block. High intensity, low volume - "
             "that is what maintains strength while the running is the priority.",
       muscles=["chest"]),
    ex("Pull-ups (assisted to weighted)", "3x4-10", 3, ASSIST,
       notes="Cerys: skip this second slot until the right shoulder has been clear for a couple "
             "of weeks - Upper B's set is enough for now. Daniel: unassisted, chasing 3x8 at "
             "bodyweight before any load goes on.",
       muscles=["lats"], load="assist"),
    ex("Incline DB press", "3x8-12", 3,
       notes="Dumbbells, as you asked on 29 Aug. Log the weight of ONE dumbbell - same name in "
             "both places means one trend line rather than two half-empty ones.",
       muscles=["chest", "delts"]),
    ex("Seated cable row", "3x8-12", 3, muscles=["lats", "traps", "biceps"]),
    ex("Farmers carry", "3-4 lengths, heavy", 3, DIST,
       notes="Hyrox station. Grip is the point: sled pull and farmers carry sit six stations "
             "apart in a race and both need it. Stay tall, shoulders down, do not run.",
       muscles=["forearms", "traps", "abs"]),
    ex("Face pull", "3x12-15", 3,
       notes="Shoulder health, and the reason the overhead press on Thursday is safe to build.",
       muscles=["delts"]),
    ex("Triceps pushdown", "3x8-12", 3,
       notes="Left elbow flagged on 21 Aug (previous injury) and left as-is by your call on "
             "6 Sep. If it speaks up again, say so in the session note and we swap it.",
       muscles=["triceps"]),
    ex("Pallof press", "3x10-12 each side", 3,
       notes="In for the plank pull-through, which you asked to switch. Same job - resisting "
             "rotation - standing, on a cable. Directly useful for the carry and the sled, "
             "where staying square under a one-sided load is the whole skill.",
       muscles=["abs"]),
]

UPPER_B = [
    ex("Shoulder press", "3x5-8", 3,
       notes="Machine if your gym has one, dumbbells if not - both keep the shoulder on a path "
             "it likes, which matters for Cerys. This is the movement pattern the program has "
             "been missing entirely. Start light and add slowly.",
       muscles=["delts"]),
    ex("Pull-ups (assisted to weighted)", "4x4-10", 4, ASSIST,
       notes="The session that owns the pull-up. Cerys: this is your goal lift - reps at the "
             "current assistance before the assistance comes down.",
       muscles=["lats"], load="assist"),
    ex("Ski erg / row", "4 rounds x 250 m, alternating", 4, ERG,
       notes="They sit next to each other in your gym, so alternate: ski 250, row 250, ski 250, "
             "row 250. Two Hyrox stations covered in one block. Log the metres and the time for "
             "each round.",
       muscles=["lats", "traps", "abs"], garminRun=True),
    ex("Seated cable row", "3x8-12", 3, muscles=["lats", "traps", "biceps"]),
    ex("Lateral raise", "3x10-15", 3,
       notes="The one isolation slot that survived the cut - Upper A's was dropped.",
       muscles=["delts"]),
    ex("Triceps pushdown", "3x8-12", 3, muscles=["triceps"]),
    ex("Hammer curl", "3x8-12", 3,
       notes="Back in at Daniel's request on 6 Sep. Hammer grip rather than a straight-bar curl "
             "because it also loads the forearms, which sled pull and farmers carry both need.",
       muscles=["biceps", "forearms"]),
    ex("Russian twists", "3x10-15", 3, muscles=["abs"]),
]

LOWER_B = [
    ex("Deadlift", "3x5-8", 3,
       notes="The lift that went 39 days without happening. It now sits on its own day with "
             "nothing stacked on top of it and no run that morning. Find the working weight, "
             "then beat it - you have overtaken a prescribed progression three times running.",
       muscles=["glutes", "hamstrings", "lowerback"]),
    ex("Bulgarian split squat", "3x8-12 each leg", 3,
       notes="Single-leg strength, and the closest thing in the gym to the sandbag lunge that "
             "comes next. Rear foot on a bench, weight through the front heel.",
       muscles=["quads", "glutes"]),
    ex("Walking/sandbag lunges", "3 sets", 3, DIST,
       notes="Hyrox station. Moved here off Monday so the two lower days balance and Lower A "
             "stops running long.",
       muscles=["quads", "glutes"]),
    ex("Hip adduction", "3x12-15", 3,
       notes="Light, same as the abduction machine. This is the only direct adductor work in "
             "the week - it covers the one gap the coverage check found, and it serves the "
             "sled push and Cerys's hip.",
       muscles=["adductors"]),
    ex("Standing calf raise", "3x12-15", 3,
       notes="Second calf exposure of the week. Shins and calves are Cerys's governor, so this "
             "is load rather than impact - exactly the direction that helps.",
       muscles=["calves"]),
    ex("Dead bug", "3x8 each side", 3, muscles=["abs"]),
]


# ------------------------------------------------------------------ run days

EASY_D = [
    ex("Easy run", "30 min continuous, conversational", 1, RUN,
       notes="Week 1 of building toward the 8 km Phase 0 gate - your longest ever is 3.45 km, "
             "so this is a duration job, not a speed one. CONTINUOUS is the whole point: if you "
             "have to slow to a shuffle to keep running, slow to a shuffle. Conversational the "
             "whole way. One row for the total, or one per km if you want the splits."),
]

EASY_C = [
    ex("Run / walk reps", "8 x 1:00 run, 2:00 walk between", 8, RUN,
       notes="Outdoors on flat ground. Same eight reps you already do on the belt, off it. Run "
             "at whatever pace feels easy - your heart rate runs hot the moment you run and "
             "that is fine, the walks are what control the session, not the speed. Shins get a "
             "say: if they talk, stop and walk the rest. A short honest run beats a complete one "
             "you pushed through."),
    ex("Brisk walk", "10:00, find a hill if there is one", 1, MIN,
       notes="The outdoor stand-in for the incline walk. A gradient if you can find one, brisk "
             "and flat if you cannot."),
]

QUAL_D = [
    ex("Run reps", "4 x 4:00 hard, 2:00 easy jog between", 4, RUN,
       notes="Outdoor version of your treadmill reps. Run these by effort, not by pace: hard "
             "enough that talking is down to a few words, not a sprint. Your speed reserve is "
             "large - you have held 13 km/h at 79% of max HR - so the discipline here is "
             "starting the first rep no faster than you can hold the fourth.",
       garminRun=True),
]

QUAL_C = [
    ex("Run reps", "8 x 1:00 hard, 2:00 walk between", 8, RUN,
       notes="The quality version of the same eight reps: faster than Tuesday, same walks. Top "
             "speed is already found, so progress comes from holding it across all eight rather "
             "than from going faster. Ease off any rep the shins ask you to.",
       garminRun=True),
]

OPTIONAL_RUN = [
    ex("Easy run", "20-30 min, whenever you fancy it", 1, RUN,
       notes="The third run, and the one your goals actually need next - three sessions and "
             "15-20 km a week is the floor for real progression. It is optional on purpose: do "
             "it on a weekend morning if the shifts allow, skip it without anything being "
             "behind. Once it happens two weeks running, it earns a fixed day."),
]


# ------------------------------------------------------------ warm-up / notes

LOWER_A_WU = """WARM-UP - 20 min, active. No long static holds before lifting.

- Treadmill walk, 4-6% incline - 5 min
- Hip CARs - 3 each side, about 10s a circle
- 90/90 switches - 8 each side, sit tall, controlled
- Adductor rock-back - 8 each side
- Glute bridge - 10, 2s squeeze, ribs down
- Side-lying abduction - 12 each side, toe DOWN, heel leading, slow
- Adductor isometric - 5 x 20s at 70%
- Hip flexor isometric - 3 x 20s each side
- BW squat 10 slow, split squat 6 each leg

Shoulders, BEFORE the technique squats - on back squats it's the rack position that bites.
- Band pull-aparts - 20, light band, straight arms, thumbs turning back, blades doing it
- Thoracic extension, roller under the mid-back - 45s, hands behind your head, exhale as you
  extend. Not the lower back.
- Bar-only rack holds - 3 x 15s in your squat grip. WIDER than feels natural, elbows DOWN
  not flared back. Still pinches? Wider again. Sort it here, not under 80kg."""

LOWER_B_WU = """WARM-UP - 18 min, active. No long static holds before lifting.

- Treadmill walk, 4-6% incline - 5 min, build until warm
- Hip CARs - 3 each side, slow
- 90/90 switches - 8 each side
- Adductor rock-back - 8 each side
- Glute bridge - 10, 2s squeeze at the top
- Side-lying abduction - 12 each side, toe DOWN, heel leading, slow
- Adductor isometric, ball or towel between the knees - 5 x 20s at 70%
- Hip flexor isometric, knee into a band or wall - 3 x 20s each side
- BW squat 10 slow
- Bar-only hinges - 10, then ramp the deadlift in singles and triples. This is the lift that
  got rebuilt from scratch in August, so the ramp is part of the session, not a formality."""

LOWER_CD = """COOL-DOWN - 10 min, stretches and breathing only.

Short on purpose: the flexibility work now has its own Wednesday slot, so this is here to
bring you down, not to train range.

- Easy treadmill walk - 3 min
- 90/90 stretch, leaning forward - 40s each side
- Hip flexor stretch, glute squeezed - 40s each side, gentle
- Calf stretch, knee straight then bent - 30s each way, each side
- 5 breaths, 4s in / 6s out"""

UPPER_A_WU = """WARM-UP - 9 min. Shoulders and mid-back, not hips.

- Easy cardio, any machine - 5 min
- Band pull-aparts - 20, straight arms, thumbs turning back at the end
- Band external rotation - 15 each arm, elbow pinned to your side, no shrug
- Thoracic extension over a bench or roller - 45s, exhale as you extend. Not the lower back.
- Ramp the bench in - a set of 5 at about 50%"""

UPPER_B_WU = """WARM-UP - 10 min. This is the pull-up session, so the scap and shoulder work is
the part that counts.

- Easy cardio, any machine - 5 min
- Banded pull-apart, dislocation, press - 10 rounds of 3, one continuous motion
    Pull the band apart in front of you, take it up and over your head to behind and
    back again, then press it straight out from the chest. That is one rep.
    Go as wide on the band as you need to get all the way over without shrugging or
    arching. Narrow the grip over the weeks as the range improves.
- Band external rotation - 15 each arm, elbow pinned to your side
- Scapular pull-ups - 5-8. Hang straight-armed, pull the blades down and together to lift an
  inch or two without bending the elbows. Pause at the top.
- Dead hang - 20s, shoulders active, not shrugged up round your ears
- Ramp the first lift - a set of 5 at about 50% is right for pull-ups"""

UPPER_CD = """COOL-DOWN - 8 min, stretches and breathing only.

- Easy walk - 3 min, nasal breathing
- Doorway or cable pec stretch - 40s each side, across the chest not inside the shoulder
  joint. If it's in the joint, drop the elbow lower.
- Overhead lat stretch on a rack - 40s each side, hips back and down
- Thoracic extension over a bench - 45s"""

RUN_WU_OUT = """WARM-UP - 10 min, outdoors, before the session proper.

- Brisk walk - 3 min
- Ankle circles - 10 each way
- Leg swings, front to back - 10 each leg
- Easy jog build - 5 min, finishing at the pace you intend to start on

Cold, dark and outdoors, so the walk matters more than it does on a belt. Nothing static."""

RUN_CD_OUT = """COOL-DOWN - 7 min.

- Walk until your breathing settles. HR down before you stretch anything.
- Calf stretch on a step or kerb, knee straight then bent - 30s each way, each side
- Quad stretch, standing - 40s each side
- Figure-4 glute stretch - 40s each side
- Hamstring stretch - 40s each side, slight knee bend, hinge from the hip

Then shower at the gym or at home and get to the station. This is the part that decides
whether 06:00 actually works, so time it in week 1 and write down what it really took."""

EASY_D_SETUP = """IF IT IS TOO COLD, WET OR DARK - treadmill fallback. 6 blocks.

   #   time   speed   what
   1   5:00    5.5    walk, warm up
   2   3:00    8.0    easy jog build
   3  30:00    9.0    THE RUN - continuous, conversational
   4   5:00    5.5    cool-down walk

Total 43:00. Drop the speed rather than the time if 9.0 is not conversational - the duration
is the training, the pace is not.

Outdoors is the default. It saves the 20-30 min drive, which is what makes a 06:00 start
survivable, and continuous outdoor running is what the 8 km gate actually needs."""

QUAL_D_SETUP = """IF IT IS TOO COLD, WET OR DARK - treadmill fallback. 12 blocks, inside the
20-stage limit. Enter it all before you start.

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

Total 33:30 - 6:30 warming up, 16:00 hard, 6:00 of floats, 5:00 walking it off.

Shorter reps than the 5 x 6:00 you were doing, because the morning slot is 40 minutes, not
50. Same speed. Outdoors is the default."""

EASY_C_SETUP = """IF IT IS TOO COLD, WET OR DARK - treadmill fallback. 19 blocks, inside the
20-stage limit. Do the warm-up on the bike BEFORE you program anything.

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
  18   10:00     5.0      6%      incline walk

Total 32:20 on the belt, plus the bike warm-up. The incline walk is 10:00 rather than 15:00
because the morning slot is shorter than the old Wednesday one."""

RECORD_OUT = """OUTDOOR RUN - one activity for the whole thing, warm-up included.

  Start    as you begin the 10-minute warm-up walk/jog
  Lap      at the start of each rep and at the end of each rep
  End      when the cool-down walk finishes

Outdoors the watch measures the distance itself, so there is no treadmill total to calibrate
against and nothing to key in. Just start it and let it run.

Turn OFF the 1 km auto-lap. Outdoors it fires mid-rep and splits your laps the same way it
did on the belt. Activity Settings -> running -> Auto Lap.

ON THE TREADMILL INSTEAD? Then it is the old drill: one activity covering the whole belt run,
lap at every speed change, and say yes to "Calibrate & Save" at the end, entering the
treadmill's total distance."""

RECORD_OUT_EASY = """OUTDOOR RUN - one activity for the whole thing, warm-up included.

  Start    as you begin the 10-minute warm-up walk/jog
  Lap      once, as the continuous run starts
  End      when the cool-down walk finishes

Two lap presses, that is all - this is a continuous run, so there is nothing to split.

Outdoors the watch measures the distance itself. No calibration, nothing to key in.

ON THE TREADMILL INSTEAD? One activity covering the whole belt run, lap as the 30-minute
block starts, and say yes to "Calibrate & Save" at the end with the treadmill's total."""


SESSIONS = {
    "lower2": dict(name="Lower A", day="Monday", exercises=LOWER_A,
                   warmupNote=LOWER_A_WU, cooldownNote=LOWER_CD, setupNote="", recordingNote=""),
    "upper1": dict(name="Upper A", day="Tuesday", exercises=UPPER_A,
                   warmupNote=UPPER_A_WU, cooldownNote=UPPER_CD, setupNote="", recordingNote=""),
    "upper2": dict(name="Upper B", day="Thursday", exercises=UPPER_B,
                   warmupNote=UPPER_B_WU, cooldownNote=UPPER_CD, setupNote="", recordingNote=""),
    "lower1": dict(name="Lower B", day="Friday", exercises=LOWER_B,
                   warmupNote=LOWER_B_WU, cooldownNote=LOWER_CD, setupNote="", recordingNote=""),
    "cardioEndurance": dict(name="Easy run: Daniel", day="Tuesday", person="Daniel",
                            exercises=EASY_D, warmupNote=RUN_WU_OUT, cooldownNote=RUN_CD_OUT,
                            setupNote=EASY_D_SETUP, recordingNote=RECORD_OUT_EASY),
    "easyCerys": dict(name="Easy run: Cerys", day="Tuesday", person="Cerys",
                      exercises=EASY_C, warmupNote=RUN_WU_OUT, cooldownNote=RUN_CD_OUT,
                      setupNote=EASY_C_SETUP, recordingNote=RECORD_OUT),
    "runDaniel": dict(name="Quality run: Daniel", day="Thursday", person="Daniel",
                      exercises=QUAL_D, warmupNote=RUN_WU_OUT, cooldownNote=RUN_CD_OUT,
                      setupNote=QUAL_D_SETUP, recordingNote=RECORD_OUT),
    "runCerys": dict(name="Quality run: Cerys", day="Thursday", person="Cerys",
                     exercises=QUAL_C, warmupNote=RUN_WU_OUT, cooldownNote=RUN_CD_OUT,
                     setupNote=EASY_C_SETUP, recordingNote=RECORD_OUT),
    "weekendRun": dict(name="Optional easy run", day="Optional", exercises=OPTIONAL_RUN,
                       warmupNote="Optional - a bonus, not a box to tick. Easy walk a few "
                                  "minutes, then run when you feel like running.",
                       cooldownNote="Walk until your breathing settles, then whatever stretches "
                                    "you fancy.",
                       setupNote="", recordingNote=""),
}

ORDER = ["lower2", "cardioEndurance", "easyCerys", "upper1", "mobility-assessment",
         "runDaniel", "runCerys", "upper2", "lower1", "weekendRun"]

MOBILITY_WED_NOTE = """MEASURE COLD - before training, on a day you have not trained.

Wednesday evening is the slot for it: nothing else trains that day, so you arrive cold.
Measure at the SAME time of day every time - evening tissue reads a couple of centimetres
better than morning tissue, and a ladder that mixes the two is telling you about the clock.

- Same conditions every time: cold, same time of day, barefoot, same floor
- Same landmark every time - write anything ambiguous in the Notes column
- No pushing. First firm stop, not the deepest you can force

WEEK 1 ONLY. Once you have both logged a set of numbers, this session goes back to Optional
for re-tests and Wednesday becomes the mobility TRAINING session - 3 to 5 exercises stacked
on whichever rung turns out to be lowest. That cannot be written in advance, which is the
whole point of measuring first.

Tap the setup line on each test for how to set it up and what it is telling you."""


def apply_to_program(program):
    """Rewrite `program` in place. Returns a list of human-readable changes."""
    sessions = program["sessions"]
    changed = []

    for key, spec in SESSIONS.items():
        old = sessions.get(key)
        spec = dict(spec)
        exercises = spec.pop("exercises")
        if old is None:
            sessions[key] = {"name": spec["name"], "day": spec["day"], "exercises": exercises}
            changed.append("NEW  %-22s %s" % (spec["name"], spec["day"]))
        else:
            changed.append("%-22s -> %-22s %s" % (old.get("name"), spec["name"], spec["day"]))
            old["exercises"] = exercises
        s = sessions[key]
        for k, v in spec.items():
            s[k] = v
        if not spec.get("person"):
            s.pop("person", None)

    mob = sessions.get("mobility-assessment")
    if mob:
        mob["day"] = "Wednesday"
        mob["warmupNote"] = MOBILITY_WED_NOTE
        changed.append("%-22s -> %-22s Wednesday (week 1)" % ("Mobility assessment",
                                                             "Mobility assessment"))

    program["order"] = [k for k in ORDER if k in sessions] + \
                       [k for k in sessions if k not in ORDER]
    return changed
