# -*- coding: utf-8 -*-
"""Draft trimmed session notes, 16 Oct 2026. Data only - review before writing.

Daniel slimmed the four lifting warm-ups/cool-downs himself on 16 Oct and asked for
the rest to follow. Rules agreed: durations computed from the list, the "5 breaths"
line out of the lifting cool-downs, run/mobility notes cut to the instructions (no
dated stories, no rationale essays), every block, lap map and report-back item kept.

    python scratchpad/trim_oct16_drafts.py      # prints durations + long lines
"""
D = {}

# ---------------------------------------------------------------- lifting
UPPER_COOL = """COOL-DOWN - {m} min, stretches and breathing only.

- Easy walk - 3 min, nasal breathing
- Doorway or cable pec stretch - 40s each side, across the chest, not in the shoulder joint
- Overhead lat stretch on a rack - 40s each side, hips back and down
- Thoracic extension over a bench - 45s"""

LOWER_COOL = """COOL-DOWN - {m} min, stretches and breathing only.

- Easy treadmill walk - 3 min
- 90/90 stretch, leaning forward - 40s each side
- Hip flexor stretch, glute squeezed - 40s each side, gentle
- Calf stretch, knee straight then bent - 30s each way, each side"""

D["Upper A"] = dict(warmup="""WARM-UP - {m} min.

- Easy cardio, any machine - 5 min
- Band complex - 15 reps
- Cable external rotation - 15 each arm
- Thoracic extension over a bench or roller - 45s, exhale as you extend. Not the lower back.""",
    cooldown=UPPER_COOL)

D["Upper B"] = dict(warmup="""WARM-UP - {m} min.

- Easy cardio, any machine - 5 min
- Band complex - 10 reps
- Cable external rotation - 15 each arm, elbow pinned to your side
- Scapular pull-ups - 5-8, straight arms, blades down and together, pause at the top
- Dead hang - 20s, shoulders active, not shrugged""",
    cooldown=UPPER_COOL)

D["Lower A"] = dict(warmup="""WARM-UP - {m} min, active. No long static holds before lifting.

- Treadmill walk, 4-6% incline - 5 min
- Hip CARs - 3 each side, about 10s a circle
- 90/90 switches - 8 each side, sit tall, controlled
- Adductor rock-back - 8 each side
- Glute bridge - 10, 2s squeeze, ribs down
- Side-lying abduction - 12 each side, toe DOWN, heel leading, slow
- Adductor isometric - 5 x 20s at 70%
- Hip flexor isometric - 3 x 20s each side
- BW squat 10 slow, split squat 6 each leg
- Band complex - 10 reps
- Thoracic extension, roller under the mid-back - 45s""",
    cooldown=LOWER_COOL)

D["Lower B"] = dict(warmup="""WARM-UP - {m} min, active. No long static holds before lifting.

- Treadmill walk, 4-6% incline - 5 min, build until warm
- Hip CARs - 3 each side, slow
- 90/90 switches - 8 each side
- Adductor rock-back - 8 each side
- Glute bridge - 10, 2s squeeze at the top
- Side-lying abduction - 12 each side, toe DOWN, heel leading, slow
- Adductor isometric, ball or towel between the knees - 5 x 20s at 70%
- Hip flexor isometric, knee into a band or wall - 3 x 20s each side
- BW squat 10 slow""",
    cooldown=LOWER_COOL)

# ---------------------------------------------------------------- runs
RUN_COOL = """COOL-DOWN - {m} min.

- Walk at {w} until your breathing settles. HR down before you stretch anything.
- Calf stretch on a step or the belt frame, knee straight then bent - 30s each way, each side
- Quad stretch, standing - 40s each side
- Figure-4 glute stretch - 40s each side
- Hamstring stretch - 40s each side, slight knee bend, hinge from the hip"""

D["Zone 2: Daniel"] = dict(person="Daniel", which="thursday",
    garmin="""BUILD IT ONCE in Garmin Connect: Training & Planning -> Workouts -> Create a Workout
-> Run. Name it "Zone 2 - easy run".

- Step 1 Warm Up - 10:00, no target
- Step 2 Run - 30:00, Heart Rate custom 120-139
- Step 3 Cool Down - 5:00, no target

Save, Send to Watch. As the ladder climbs, edit only step 2's time and re-send.

ON THE DAY: get the belt program ready, then on the watch Run -> hold MENU -> Training ->
Workouts -> "Zone 2 - easy run" -> Do Workout, as an INDOOR run. Start the watch and the
belt at the same moment.

Arrow up? Drop the belt 0.2 and wait 30s - HR lags about a minute. Don't chase it.

THURSDAY TRAIN (12:45): be on the belt by 11:00, or 10:30 once the run is past 50 min.
Running late? Take a later train rather than cutting the run.""",
    setup="""\U0001f39b TREADMILL PROGRAM - 4 blocks, 45:00, then stretches off the belt.

1. 5:00 at 5.5 - walk
2. 5:00 at 8.0 - easy jog build
3. 30:00 at 9.0 - THE RUN, continuous
4. 5:00 at 5.5 - cool-down walk

Only block 3 changes as the ladder climbs. Blocks 1 and 2 match the watch's 10:00
warm-up, so keep them together at 10:00.

Over 140? DROP THE SPEED, NOT THE TIME, and log the speed you ended on.
Outdoors: skip the table and just run the watch workout.""",
    recording="""⌚ RECORDING - one INDOOR RUN, warm-up included. Start the watch and the belt
together, then press nothing. DO NOT PRESS LAP - it splits the run in two.

- Lap 1 - warm-up (blocks 1 and 2)
- Lap 2 - THE RUN (block 3), the lap that counts
- Lap 3 - cool-down (block 4)

At the end: yes to CALIBRATE & SAVE with the belt's total distance, and type the belt
distance into the app as well.
Outdoors: record an outdoor run. Nothing to calibrate.

REPORT BACK in Notes: the belt speed that held you in 120-139, whether lap 2 was unbroken
(if not, where you walked and for how long), and lap 2's average HR.""",
    warmup="""WARM-UP - 10 min, on the belt (blocks 1 and 2). Nothing static.

- Walk at 5.5 - 3 min
- Ankle circles - 10 each way, off the belt
- Leg swings, front to back - 10 each leg, off the belt
- Easy jog build at 8.0 - 5 min, finishing at the pace you'll start on""",
    cooldown=RUN_COOL, w="5.5")

D["Quality run: Daniel"] = dict(person="Daniel", which="monday",
    garmin="""BUILD IT ONCE in Garmin Connect: Training & Planning -> Workouts -> Create a Workout
-> Run. Name it "Threshold reps".

- Step 1 Warm Up - Lap Button Press, no target
- Step 2 Repeat 4x: Run 4:00, Heart Rate custom 165-173 / Recover 2:00, no target
- Step 3 Cool Down - 5:00, no target

Save, Send to Watch. More reps later: change the Repeat count and re-send.

ON THE DAY: load "Threshold reps" -> Do Workout, as an INDOOR run. Warm up and do the
strides by hand, program the belt, then PRESS LAP AS YOU START THE BELT PROGRAM. That is
the only press.

HR lags 45-60s, so ignore the speed-up arrow for the first minute of each rep.""",
    setup="""\U0001f39b TREADMILL PROGRAM - warm-up and strides by hand first, then 9 blocks, 29:00.

- Blocks 1, 3, 5, 7 - 4:00 at 11.0, REPS
- Blocks 2, 4, 6, 8 - 2:00 at 7.5, float
- Block 9 - 5:00 at 5.5, cool-down walk

11.0 is a starting point. The reps are there to find where it puts your HR.
Outdoors: run the watch workout, strides at 20s instead of 30s.""",
    recording="""⌚ RECORDING - one INDOOR RUN. One Lap press, as the belt program starts.

- Lap 1 - warm-up and strides
- Laps 2-9 - reps and floats. THE EVEN LAPS ARE THE REPS.
- Lap 10 - cool-down walk

At the end: yes to CALIBRATE & SAVE with the belt's total distance, and type each rep into
the app as well.
Outdoors: record an outdoor run, and turn the 1 km auto-lap off if you're not using the
workout.

REPORT BACK in Notes: the belt speed, each rep's average HR, whether rep 4 felt like rep 1,
and whether you worked the weekend (and when Sunday's shift finished).""",
    warmup="""WARM-UP - {m} min, on the belt, all by hand. Nothing static.

- Walk at 5.5 - 3 min
- Ankle circles - 10 each way, off the belt
- Leg swings, front to back - 10 each leg, off the belt
- Easy jog at 8.0 - 4 min
- Strides - 4 x 30s at about 13.0, 60s at 5.5 between
- Easy jog at 7.5 - 1 min""",
    cooldown=RUN_COOL, w="5.5")

D["Quality run: Cerys"] = dict(person="Cerys", which="monday",
    garmin="""BUILD IT ONCE in Garmin Connect: Training & Planning -> Workouts -> Create a Workout
-> Run. Name it "Run walk reps".

- Step 1 Warm Up - Lap Button Press, no target
- Step 2 Repeat 8x: Run 1:00 / Recover 2:00, both no target
- Step 3 Cool Down - 5:00, no target

Save, Send to Watch. No HR target on purpose: the watch is the clock. It buzzes at 60s and
you walk. More reps later: change the Repeat count and re-send.

ON THE DAY: load "Run walk reps" -> Do Workout, as an INDOOR run. Warm up by hand, program
the belt, then press Start on the belt and Lap on the watch together. That is the only press.""",
    setup="""\U0001f39b TREADMILL PROGRAM - warm-up by hand first, then 16 blocks, 24:00, no incline.

- Odd blocks, 1 to 15 - 1:00 at 10.0, REPS
- Even blocks, 2 to 16 - 2:00 at 5.5, walk

Cool-down walk by hand afterwards. 10.0 is fixed: the reps grow, the speed doesn't.
Outdoors: run the watch workout on flat ground, and say so in the log.""",
    recording="""⌚ RECORDING - one INDOOR RUN. One Lap press, as the belt program starts.

- Lap 1 - warm-up
- Laps 2-17 - reps and walks. THE EVEN LAPS ARE THE REPS.
- Lap 18 - cool-down walk

At the end: yes to CALIBRATE & SAVE with the belt's total distance, and type each rep in
yourself.
Outdoors: record an outdoor run, 1 km auto-lap off, and say so in the log.

REPORT BACK in Notes:
- any rep you eased off - which rep, and WHICH SHIN
- whether all eight were a full minute at 10.0
- how the shins felt afterwards
- whether you worked the weekend, and how long you were on your feet
- on Tuesday, how the shins feel going into the sled (write it in Tuesday's session)""",
    warmup="""WARM-UP - {m} min, on the belt, all by hand. Nothing static.

- Walk at 5.5 - 3 min
- Ankle circles - 10 each way, off the belt
- Leg swings, front to back - 10 each leg, off the belt
- Easy jog at 8.0 - 4 min
- Easy jog at 10.0 - 20s, to meet the rep speed once
- Walk at 5.5 - 1 min""",
    cooldown=RUN_COOL, w="5.0")

D["Zone 2: Cerys"] = dict(person="Cerys", which="thursday",
    garmin="""BUILD IT ONCE in Garmin Connect: Training & Planning -> Workouts -> Create a Workout
-> Walk. Name it "Zone 2 - walk".

- Step 1 Warm Up - 5:00, no target
- Step 2 Walk - 20:00, Heart Rate custom 119-138
- Step 3 Cool Down - 5:00, no target

Save, Send to Watch. When 20:00 becomes 25:00, edit step 2 and re-send.

ON THE DAY: get the belt program ready, then on the watch Walk -> hold MENU -> Training ->
Workouts -> "Zone 2 - walk" -> Do Workout, as an INDOOR walk. Start the watch and the belt
at the same moment.

Arrow up? EASE THE GRADIENT BEFORE THE SPEED, then wait 30s - HR lags about a minute.""",
    setup="""\U0001f39b TREADMILL PROGRAM - 3 blocks, 30:00, then stretches off the belt.

1. 5:00 at 5.0, flat - warm-up walk
2. 20:00 at 5.0, 6% - THE SESSION, HR 119-138
3. 5:00 at 4.0, flat - cool-down walk

Adjust to the watch, not to these numbers.

PROGRESSION - gradient first, then time:
- never buzzed in the 20 min - add 1% next time
- buzzed now and then and you eased it - same gradient
- buzzed constantly - drop 1%, or the speed to 4.5
- three clean weeks at one gradient - 20:00 becomes 25:00

Outdoors: any steady hill, 20 min brisk, and say it was outdoors.""",
    recording="""⌚ RECORDING - one INDOOR WALK. Start the watch and the belt together, then press
nothing.

- Lap 1 - warm-up
- Lap 2 - THE SESSION, the lap that counts
- Lap 3 - cool-down

No need to calibrate on a walk.
Outdoors: record an outdoor walk and say so - there's no gradient number that week.

REPORT BACK in Notes: the gradient AND speed that held you in 119-138, whether the watch
buzzed high and how often, and anything the shins said (which one).""",
    warmup="""WARM-UP - {m} min. No jog, nothing static.

- Easy walk at 5.0, flat - 3 min
- Ankle circles - 10 each way, off the belt
- Leg swings, front to back - 10 each leg, off the belt""",
    cooldown="""COOL-DOWN - {m} min.

- Walk at 4.0 until your breathing settles. HR down before you stretch anything.
- Calf stretch on a step or the belt frame, knee straight then bent - 30s each way, each
  side, extra time on the left
- Quad stretch, standing - 40s each side
- Figure-4 glute stretch - 40s each side
- Hamstring stretch - 40s each side, slight knee bend, hinge from the hip""")

# ---------------------------------------------------------------- mobility
MOB_COOL = """COOL-DOWN - 3 min. Breathing only.

- 8 breaths, 4s in / 6s out, lying on your back with the knees bent"""

D["Mobility: Daniel"] = dict(
    setup="""WHAT YOU NEED: a wall, a bench or box, two yoga blocks or books, a rack or TRX to hold.
No loading.

SKILLS: pike and deep squat. Both stop at your hip (pancake 42cm, Tailor's 35/29cm), not
your ankle, so one list serves both.

ORDER: small and isolated first, compound last. Don't reorder.
NO PUSHING. First firm stop. Pain means back off.""",
    warmup="""WARM-UP - {m} min. Nothing static.

- Easy bike or brisk walk - 5 min
- Hip CARs - 3 each side, slow, about 10s a circle
- Ankle circles - 10 each way
- Bodyweight squat - 10 slow, only as deep as is comfortable""",
    cooldown=MOB_COOL)

D["Mobility: Cerys"] = dict(
    setup="""WHAT YOU NEED: a wall, a step or low box, a 5cm plate or wedge, two yoga blocks or
books, something to hold. No loading.

SKILLS: side split and deep squat. Built on your two lowest rungs: pancake hip tilt (50cm)
and the left ankle (8cm against 11.5cm on the right). No hamstring work - your hamstrings
aren't what stops you.

ORDER: small and isolated first, compound last.
ALWAYS START ON THE LEFT, and give the left any extra round.
NO PUSHING. First firm stop. If the shins complain, stop that exercise and note which shin.""",
    warmup="""WARM-UP - {m} min. Nothing static.

- Easy bike or brisk flat walk - 5 min
- Ankle circles - 10 each way
- Hip CARs - 3 each side, slow
- Bodyweight squat - 10 slow, heels on a plate if that's more comfortable""",
    cooldown=MOB_COOL)

D["Mobility assessment"] = dict(
    warmup="""MEASURE COLD - on a day you haven't trained, Wednesday evening, same time of day
every time.

- Same conditions: cold, barefoot, same floor, same wall, same wedge height
- Same landmark - write anything ambiguous in Notes
- No pushing - first firm stop
- Straight-leg raises: log a heel height in cm as well as the degrees

A RE-TEST every 6-8 weeks, in place of that week's Mobility session. Tap each test's setup
line for how to do it.""",
    cooldown="""Nothing to cool down from. Check Progress > Flex before the next block is written:
the lowest rung is what the training is built on.""")


def render():
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    import note_times as nt
    out = {}
    for name, f in D.items():
        r = {}
        for field in ("garmin", "setup", "recording", "warmup", "cooldown"):
            t = f.get(field)
            if t is None:
                continue
            if "{m}" in t or "{w}" in t:
                body = t.replace("{w}", f.get("w", ""))
                t = body.replace("{m}", str(max(1, nt.minutes(body.replace("{m}", "0")))))
            r[field] = t
        out[name] = r
    return out


if __name__ == "__main__":
    for name, r in render().items():
        for field, t in r.items():
            head = t.split("\n")[0]
            long = [l for l in t.split("\n") if len(l) > 95]
            print(f"{name:22} {field:9} {len(t):5} chars | {head[:60]}" + (f"  LONG:{long}" if long else ""))
