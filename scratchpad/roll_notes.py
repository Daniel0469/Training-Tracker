# -*- coding: utf-8 -*-
"""Roll Daniel's Lower 1 shape across every session's warm-up and cool-down.

Four rules, all his:

  1. Cool-downs are stretches and breathing. No strength work.
  2. No traffic lights or decision rules in a warm-up.
  3. Person-specific notes live in coaching, not in warm-up/cool-down text.
  4. Stated durations get recalculated from the list (see note_times.py).

Plus one that fell out of his own edit: a ramp already stored on the exercise
card is not repeated in the note, because it renders twice on the same screen.

`apply_to_program(program, coaching)` mutates in place and returns (changes,
moved_to_coaching, removed) so proto_mobility.py can print all three.
"""
import note_times

# {MIN} is filled from the list itself. The two run warm-ups have no placeholder:
# their "8 minutes" is the treadmill program's block time, not the sum of items.
NOTES = {
    "lower1": {
        "warmupNote": u"""WARM-UP - {MIN} min, active. No long static holds before lifting.

- Treadmill walk, 4-6% incline - 5 min, build until warm
- Hip CARs - 3 each side, slow
- 90/90 switches - 8 each side
- Adductor rock-back - 8 each side
- Glute bridge - 10, 2s squeeze at the top
- Side-lying abduction - 12 each side, toe DOWN, heel leading, slow
- Adductor isometric, ball or towel between the knees - 5 x 20s at 70%
- Hip flexor isometric, knee into a band or wall - 3 x 20s each side
- BW squat 10 slow
- Band circuit - 10 rounds of 3 moves, one rep of each in turn:
    Band pull-aparts - straight arms, thumbs turning back
    Banded press - straight out from the chest, blades wide at the end of the rep
    Banded shoulder dislocations - slow, wide grip on the band
- Band external rotation - 15 each arm, elbow pinned to your side, no shrug
- Thoracic extension over a bench or roller - 45s, exhale at the bottom""",
        "cooldownNote": u"""COOL-DOWN - {MIN} min, stretches and breathing only.

- Easy treadmill walk - 3 min, nasal breathing only
- 90/90 stretch, leaning forward over the front shin - 40s each side
- Hip flexor stretch, glute squeezed, ribs down - 40s each side, gentle
- Hamstring stretch - 40s each side
- Adductor rock-back, held - 40s each side
- Calf stretch on a step, knee straight then bent - 30s each way, each side
- On your back, knees bent - 5 breaths, 4s in / 6s out""",
    },
    "lower2": {
        "warmupNote": u"""WARM-UP - {MIN} min, active. No long static holds before lifting.

- Treadmill walk, 4-6% incline - 5 min
- Hip CARs - 3 each side, about 10s a circle
- 90/90 switches - 8 each side, sit tall, controlled
- Adductor rock-back - 8 each side
- Glute bridge - 10, 2s squeeze, ribs down
- Side-lying abduction - 12 each side, toe DOWN, heel leading, slow
- Adductor isometric - 5 x 20s at 70%
- Hip flexor isometric - 3 x 20s each side
- BW squat 10 slow, split squat 6 each leg

Shoulders, BEFORE the bar goes on your back - on squats it's the rack position that bites.
- Band pull-aparts - 20, light band, straight arms, thumbs turning back, blades doing it
- Thoracic extension, roller under the mid-back - 45s, hands behind your head, exhale as you
  extend. Not the lower back.
- Bar-only rack holds - 3 x 15s in your squat grip. WIDER than feels natural, elbows DOWN
  not flared back. Still pinches? Wider again. Sort it here, not under 80kg.""",
        "cooldownNote": u"""COOL-DOWN - {MIN} min, stretches and breathing only.

- Easy treadmill walk - 3 min
- 90/90 stretch, leaning forward - 40s each side
- Hip flexor stretch, glute squeezed - 40s each side, gentle, don't force it
- Hamstring stretch - 40s each side
- Adductor rock-back, held - 40s each side
- Calf stretch, knee straight then bent - 30s each way, each side
- 5 breaths, 4s in / 6s out""",
    },
    "upper1": {
        "warmupNote": u"""WARM-UP - {MIN} min. Shoulders and mid-back, not hips.

- Easy cardio, any machine - 5 min
- Band pull-aparts - 20, straight arms, thumbs turning back at the end
- Band external rotation - 15 each arm, elbow pinned to your side, no shrug
- Thoracic extension over a bench or roller - 45s, exhale as you extend. Not the lower back.""",
        "cooldownNote": u"""COOL-DOWN - {MIN} min, stretches and breathing only.

- Easy walk - 3 min, nasal breathing
- Doorway or cable pec stretch - 40s each side, across the chest not inside the shoulder
  joint. If it's in the joint, drop the elbow lower.
- Overhead lat stretch on a rack - 40s each side, hips back and down
- Thoracic extension over a bench - 45s
- Child's pose with side reach - 40s each side""",
    },
    "upper2": {
        "warmupNote": u"""WARM-UP - {MIN} min. This is the pull-up session, so the scap and shoulder work is
the part that counts.

- Easy cardio, any machine - 5 min
- Band pull-aparts - 20, straight arms, thumbs turning back at the end
- Banded press - 15, straight out from the chest, blades wide at the end of the rep
    Pairs with the pull-aparts: one opens the front, one closes the back.
- Banded shoulder dislocations - 10, slow, wide grip on the band
    Go as wide as you need to get all the way over without shrugging or arching. Narrow
    the grip over the weeks as the range improves.
- Band external rotation - 15 each arm, elbow pinned to your side
- Scapular pull-ups - 5-8. Hang straight-armed, pull the blades down and together to lift an
  inch or two without bending the elbows. Pause at the top.
- Dead hang - 20s, shoulders active, not shrugged up round your ears
- Ramp the first lift - a set of 5 at about 50% is right for pull-ups""",
        "cooldownNote": u"""COOL-DOWN - {MIN} min, stretches and breathing only.

- Easy walk - 3 min, nasal breathing
- Overhead lat stretch - 40s each side, worth an extra 20s today, you've just pulled
- Doorway or cable pec stretch - 40s each side, across the chest not inside the joint
- Thoracic extension over a bench - 45s
- Child's pose with side reach - 40s each side""",
    },
    "cardioEndurance": {
        "warmupNote": u"""WARM-UP - {MIN} min, active.

- Brisk walk - 4 min
- Hip CARs - 3 each side
- 90/90 switches - 8 each side
- Glute bridge - 10
- Side-lying abduction - 12 each side
- Ankle circles - 10 each way
- Leg swings, front to back - 10 each leg
- Easy jog build - 3 min""",
        "cooldownNote": u"""COOL-DOWN - {MIN} min, stretches and breathing only.

- Walk - 3 min, nasal breathing only. HR down before you stretch anything.
- Calf stretch on a step, knee straight then bent - 30s each way, each side
- Standing quad stretch - 40s each side, knee at the floor, glute squeezed, ribs down. Lie
  on your side if your balance goes.
- Figure-4 glute stretch - 40s each side, ankle across the opposite thigh, pull the far knee
  in. Back of the hip, not the front.
- Hamstring stretch - 40s each side, slight knee bend, hinge from the hip, back flat
- 5 breaths, 4s in / 6s out""",
    },
    "runDaniel": {
        # The walk is block 13 of the treadmill program, so it is counted in the
        # belt time, not here - same reasoning as Cerys's 8-minute warm-up.
        "cooldownNote": u"""COOL-DOWN - {MIN} min after the belt stops. Block 13's 5 min walk at 5.5 is the
first part - let your breathing settle on it.

- Calf stretch on a step, knee straight then bent - 30s each way, each side
- Quad stretch, standing or seated - 40s each side
- Figure-4 glute stretch - 40s each side
- Hamstring stretch - 40s each side, slight knee bend, hinge from the hip""",
    },
    "runCerys": {
        # No {MIN}: the 8 minutes is blocks 1-5 of the treadmill program.
        "warmupNote": u"""WARM-UP - blocks 1 to 5, 8 minutes. The bike is fine for block 1.

- Ankle circles - 10 each way
- Leg swings, front to back - 10 each leg
- Calf raises - 15 slow, both legs""",
        "cooldownNote": u"""COOL-DOWN - {MIN} min, stretches and breathing only.

- Calf stretch on a step, knee straight then bent - 30s each way, each side
- Quad stretch, standing or seated - 40s each side
- Figure-4 glute stretch - 40s each side. Felt in the BACK of the hip, not the front.
- Hamstring stretch - 40s each side, slight knee bend, hinge from the hip""",
    },
    "mobilityAssess": {
        "warmupNote": u"""MEASURE COLD - before training, on a day you have not trained.

Warming up buys a few centimetres that wear off within hours, so a warm measurement tells you
how hard you warmed up rather than whether you improved.

- Same conditions every time: cold, same time of day, barefoot, same floor
- Same landmark every time - write anything ambiguous in the Notes column
- No pushing. First firm stop, not the deepest you can force

Tap the setup line on each test for how to set it up and what it is telling you.""",
    },
}

# Rule 3: what comes out of the notes and goes into coaching, keyed by person and
# session NAME (which is how coaching.bySession is keyed).
TO_COACHING = {
    "Cerys": {
        "Lower 1": u"Side-lying abduction, the clicky hip: shorten the range until it goes quiet "
                   u"and slow it right down. A painless click is common and fine; pain, or a "
                   u"weak-feeling leg, drop it and tell me. Hip flexor stretch: skip entirely if "
                   u"it reproduces the front-hip pain.",
        "Lower 2": u"Side-lying abduction, the clicky hip: shorten the range until it goes quiet "
                   u"and slow it right down. A painless click is common and fine; pain, or a "
                   u"weak-feeling leg, drop it and tell me. Hip flexor stretch: skip entirely if "
                   u"it reproduces the front-hip pain.",
        "Upper 1": u"Your shoulder popped on the pushdown on 19 Aug, so do the two band moves "
                   u"properly rather than fast. Hip CARs live in the Lower warm-ups now - add 3 "
                   u"each side here if this is your only session of the day.",
        "Upper 2": u"Banded shoulder dislocations matter most to you - take them slowly and stop "
                   u"short of anything that pinches. On the dead hang, log the time: grip usually "
                   u"runs out before the back does.",
        "Cardio: Endurance + Core":
                   u"Skip the 90/90 PAILs/RAILs until two clear pain-free weeks or a physio says "
                   u"otherwise - 90/90 is deep hip flexion, which a front-of-hip problem dislikes. "
                   u"The rest of the cool-down is fine, and do the CARs daily. Don't skip the calf "
                   u"stretch: your shins were quiet on 13 Aug for the first time since July, and "
                   u"calf length is part of why.",
        "Run: Cerys":
                   u"Blocks 2 and 4, the two 20-second jogs, are a test rather than a formality. "
                   u"Shins and left hip both get a say: if either speaks up there, skip the reps "
                   u"and do the incline walk on its own. That is not failing the session. The calf "
                   u"stretch in the cool-down is the most important line in it - calf length is "
                   u"shin insurance.",
    },
}

# The adductor red flags are safety guidance rather than a decision rule, so they
# move to coaching for both of you rather than being dropped with the traffic light.
RED_FLAGS = (u"Adductor red flags, either of you: get the hip assessed if it wakes you at night, "
             u"locks or gives way, radiates down the leg, or a flare hasn't settled in 48 hours.")

REMOVED = [
    ("lower1", "cool-down", "Copenhagen plank, side plank, dead bug, single-leg glute bridge"),
    ("lower2", "cool-down", "Copenhagen plank, side plank, seated march, single-leg glute bridge"),
    ("runCerys", "cool-down", "Hip hike, side-lying clam"),
    ("cardioEndurance", "cool-down", "PAILs/RAILs in 90/90 - the last flexibility training "
                                     "left in a cool-down"),
    ("lower1", "warm-up", "adductor traffic light (green/amber/red)"),
    ("lower2", "warm-up", "adductor traffic light (green/amber/red)"),
    ("lower1", "warm-up", "Ramp leg press - already on the Leg press card"),
    ("lower2", "warm-up", "Ramp squat - already on the Squat card"),
    ("upper1", "warm-up", "Ramp the flat press - already on the Bench press card"),
]


def apply_to_program(program, coaching):
    changes, moved = [], []
    sessions = program["sessions"]

    for key, fields in NOTES.items():
        if key not in sessions:
            continue
        for field, body in fields.items():
            if "{MIN}" in body:
                body = body.replace("{MIN}", str(note_times.minutes(body)))
            was = sessions[key].get(field, "")
            sessions[key][field] = body
            label = "warm-up" if field == "warmupNote" else "cool-down"
            changes.append("%-16s %-10s %d -> %d lines"
                           % (sessions[key]["name"], label,
                              len(was.split("\n")), len(body.split("\n"))))

    for person, bysess in TO_COACHING.items():
        slot = coaching.setdefault(person, {}).setdefault("bySession", {})
        for sess_name, text in bysess.items():
            existing = slot.get(sess_name, "")
            if text in existing:
                continue
            slot[sess_name] = (existing + "\n\n" + text).strip() if existing else text
            moved.append("%s / %s" % (person, sess_name))

    for person in ("Daniel", "Cerys"):
        slot = coaching.setdefault(person, {}).setdefault("bySession", {})
        for sess_name in ("Lower 1", "Lower 2"):
            existing = slot.get(sess_name, "")
            if RED_FLAGS in existing:
                continue
            slot[sess_name] = (existing + "\n\n" + RED_FLAGS).strip() if existing else RED_FLAGS
            moved.append("%s / %s (red flags)" % (person, sess_name))

    return changes, moved, REMOVED
