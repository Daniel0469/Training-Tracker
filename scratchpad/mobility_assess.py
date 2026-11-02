# -*- coding: utf-8 -*-
"""The Mobility assessment session, plus the rewritten Lower 1 notes.

Program data only - no app code. `apply_to_program(program)` mutates in place and
returns a list of what it changed, so proto_mobility.py can print it.

The tests come from the flexibility-ladder method: you assess individual tissues
in isolation to find the one rung that is actually limiting the skill, rather
than stretching whatever feels tight. Every test is a distance in centimetres so
it charts, and every test is floor- or wall-referenced so it repeats: a tape
measure and a flat floor, no equipment and no judgement call.

Day is deliberately "Optional" - unassigned until the uni timetable lands.
"""

KEY = "mobilityAssess"

# cols[0] == "cm" is what makes these flexibility tests to the app (isFlexTest).
# betterWhen:"higher" flags the two where a bigger number is the better one.
COLS = ["cm", "Notes"]


def _reflow(text):
    """Hard-wrapped source -> wrapping prose.

    Exercise notes render as ordinary wrapping text (see the Run reps and Dead
    bug notes in the real program), so a hard break mid-sentence double-wraps on
    a phone and reads ragged. The literals below stay wrapped for readability
    here; this joins each paragraph back into one line on the way out. Blank
    lines survive as paragraph breaks.
    """
    paras = [" ".join(l.strip() for l in p.split("\n") if l.strip())
             for p in text.split("\n\n")]
    return "\n\n".join(p for p in paras if p)


def _ex(name, target, notes, sets=1, higher=False):
    ex = {"name": name, "warmup": "", "notes": _reflow(notes), "target": target,
          "sets": sets, "cols": list(COLS)}
    if higher:
        ex["betterWhen"] = "higher"
    return ex


EXERCISES = [
    # ---- Pike / forward fold ------------------------------------------------
    _ex(
        "Standing fold",
        "Fingertips to floor - knees locked",
        "Feet together, knees locked straight, fold forward and let your arms hang.\n"
        "Measure from the tip of your middle finger to the floor.\n"
        "If you reach past the floor, log 0 and note how flat your hands go.\n\n"
        "What it tests: the whole pike chain at once - hamstrings, calves, and how\n"
        "much stretch your nervous system will let you into standing. This is the\n"
        "headline number, not a diagnosis: the two raises below say WHY it is\n"
        "where it is.",
    ),
    _ex(
        "Straight-leg raise - passive",
        "Heel height off the floor - hands pulling",
        "Lie on your back. Other leg flat on the floor, knee straight - if it lifts,\n"
        "the number is wrong. Raise one leg, knee locked, and pull it toward you\n"
        "with your hands or a strap until it stops.\n"
        "Measure from your heel straight down to the floor.\n"
        "Row 1 = left leg, row 2 = right leg. Note which in the Notes column.\n\n"
        "What it tests: your total hamstring range with something else doing the\n"
        "pulling. Higher is better.",
        sets=2, higher=True,
    ),
    _ex(
        "Straight-leg raise - active",
        "Heel height off the floor - no hands",
        "Exactly the same position, but no hands and no strap. Lift the leg using\n"
        "only your own hip flexors and hold it there long enough to measure.\n"
        "Row 1 = left leg, row 2 = right leg.\n\n"
        "What it tests: how much of that range you can actually USE. The gap\n"
        "between this and the passive raise is the single most useful number in\n"
        "the assessment - a big gap means you need strength into the range you\n"
        "already own, a small gap means you need more total range. They call for\n"
        "opposite training. Higher is better.",
        sets=2, higher=True,
    ),
    # ---- The shared rung ----------------------------------------------------
    _ex(
        "Pancake hip tilt",
        "Forehead to floor - legs wide, back rounded",
        "Sit with your legs as wide as they go, then bring them in a little so you\n"
        "are not fighting the end range. Round your back and reach your head down\n"
        "toward the floor. Measure forehead to floor.\n\n"
        "What it tests: whether you can tilt your pelvis forward under load. This\n"
        "is the rung pike and deep squat share - without it, the squat runs into\n"
        "bone at the hip and the fold happens entirely in your spine. If this one\n"
        "is low, it is very likely the first thing to train.",
    ),
    # ---- Deep squat ---------------------------------------------------------
    _ex(
        "Tailor's pose (wall)",
        "Outer knee to floor - back against the wall",
        "Sit with your back flat against a wall, soles of the feet together and\n"
        "pulled in close. Let the knees drop - no hands, no pushing.\n"
        "Measure from the outside of the knee down to the floor.\n"
        "Row 1 = left, row 2 = right. Sides are often very different here.\n\n"
        "What it tests: the short adductors and hip rotators with the knee bent,\n"
        "which is the shape a deep squat actually asks for. Straight-leg adductor\n"
        "stretches do not tell you this.",
        sets=2,
    ),
    _ex(
        "Knee to wall (ankle)",
        "Toe distance from the wall - heel stays down",
        "Face a wall in a half-kneeling lunge, front foot pointing straight at it.\n"
        "Drive the knee forward over the toes to touch the wall, heel flat on the\n"
        "floor. Slide the foot back until the knee only just touches with the heel\n"
        "still down. Measure from the tip of your big toe to the wall.\n"
        "Row 1 = left, row 2 = right.\n\n"
        "What it tests: ankle dorsiflexion, the most common hard stop on squat\n"
        "depth and the one people almost never test. Higher is better. Under about\n"
        "10cm and your ankles are limiting your squat, whatever your hips do.",
        sets=2, higher=True,
    ),
    _ex(
        "Deep squat - heel lift",
        "Heel to floor at the bottom - feet flat, no shoes",
        "Barefoot, feet about shoulder width, squat as deep as you can and hold it.\n"
        "Measure the gap under whichever heel comes up more.\n"
        "0 means both heels stay down - log 0 and note how the position felt.\n\n"
        "What it tests: the skill itself, as one movement. Read it against the two\n"
        "tests above: heels up with a poor knee-to-wall is an ankle problem, heels\n"
        "up with a good one is a hip problem.",
    ),
    # ---- Shoulders (next block, but cheap to baseline now) ------------------
    _ex(
        "Supine overhead reach",
        "Wrists to floor - low back pressed flat",
        "Lie on your back, knees bent, feet flat. Press your lower back into the\n"
        "floor and keep it there - this is the whole test, and it is easy to cheat\n"
        "by arching. Reach both straight arms overhead toward the floor.\n"
        "Measure from the back of your wrists to the floor.\n\n"
        "What it tests: shoulder flexion, with the lower back taken out of it. The\n"
        "lats are usually what stops you.",
    ),
    _ex(
        "Shoulder external rotation",
        "Back of hand to floor - elbow at 90, out to the side",
        "Lie on your back. Take one arm out to the side at shoulder height, elbow\n"
        "bent to 90 so the forearm points at the ceiling. Keep the shoulder and\n"
        "the opposite ribs down. Let the hand rotate back toward the floor above\n"
        "your head. Measure back of hand to floor.\n"
        "Row 1 = left, row 2 = right.\n\n"
        "What it tests: subscapularis and teres major, isolated by the rotation.\n"
        "These are the ones that quietly limit an overhead position when the lats\n"
        "test fine.",
        sets=2,
    ),
]


WARMUP = u"""MEASURE COLD. Do this before anything else, on a day you have not trained.

Stretching warms tissue up and buys you a few centimetres that wear off within
hours - useful before a session, useless as a measurement. If you warm up first
you will measure the warm-up, not your flexibility, and next time's number will
depend on how hard you warmed up rather than on whether you improved.

Three rules that matter more than the numbers themselves:

- Same conditions every time. Cold, same time of day, barefoot, same floor.
- Measure to the same landmark every time. Write down anything ambiguous in the
  Notes column so the next reading matches this one.
- No pushing. Go to the first firm stop, not to the deepest you can force. A
  forced number is not repeatable and it is not what you train against.

This is not a workout and there is nothing to beat. Tap the 🔧 setup line on each
test for exactly how to set it up and what it is telling you."""


COOLDOWN = u"""Nothing to cool down from - you have not trained.

Once both of you have logged a set of numbers, the Flexibility ladder in Progress
shows every rung side by side. The lowest one is what we build the first block
around."""


# ---- The rewritten Lower 1 notes -------------------------------------------
# Same content, different shape. Three changes: the traffic light moves to the
# top because it is a decision you make BEFORE you warm up, not an item in the
# warm-up; each block opens with a line saying what it is for; and the cool-down
# stops calling four sets of core and glute work "the passive half".
LOWER1_WARMUP = u"""FIRST - adductor squeeze. Your traffic light for today.

GREEN, no pain
  Train as normal.
AMBER, 1-3/10
  Train, hold loads, don't progress the lunge step.
RED, sharp or 4+/10
  Lunge back a step, skip hip adduction. Isometrics and glutes only.

Get it assessed if the hip wakes either of you at night, locks or gives way, radiates down
the leg, or a flare hasn't settled in 48 hours.

WARM-UP - 12 min, active. No long static holds before lifting.

This is preparation for today's session and nothing more. The range it gives you is temporary
and gone within hours, which is exactly what a warm-up is for - lasting flexibility is built
in its own session, not here.

- Treadmill walk, 4-6% incline - 5 min, build until warm
- Hip CARs - 3 each side, slow
- 90/90 switches - 8 each side
- Adductor rock-back - 8 each side
- Glute bridge - 10, 2s squeeze at the top
- Side-lying abduction - 12 each side, toe DOWN, heel leading, slow
    Cerys: the clicky hip. Shorten the range until it goes quiet and slow it right down. A
    painless click is common and fine; pain, or a weak-feeling leg, drop it and tell me.
- Adductor isometric, ball or towel between the knees - 5 x 20s at 70%
- Hip flexor isometric, knee into a band or wall - 3 x 20s each side
- BW squat 10 slow, split squat 6 each leg, calf raise 15
- Ramp leg press - light x8, 50% x5, 75% x3

Shoulders, only if you're squatting or pressing overhead later in the week:
- Band pull-aparts - 20, straight arms, thumbs turning back
- Thoracic extension over a bench or roller - 45s, exhale at the bottom"""

LOWER1_COOLDOWN = u"""COOL-DOWN - 13 min, in two halves that do different jobs.

CORE + GLUTES. This half is training, not cooling down - work at it.
- Copenhagen plank - 3 x 15s each side (short lever: knee on the bench)
- Side plank, top-leg lift - 3 x 8 each side
- Dead bug, unilateral isometric hold - 3 x 15s each side
- Single-leg glute bridge - 3 x 10 each side

COMING DOWN. Breathing and blood flow. Easy, no forcing, nothing held hard.
- Easy treadmill walk - 3 min, nasal breathing only
- 90/90 stretch, leaning forward over the front shin - 40s each side
- Hip flexor stretch, glute squeezed, ribs down - 40s each side, gentle
    Cerys: skip entirely if it reproduces the front-hip pain
- Hamstring stretch - 40s each side
- Adductor rock-back, held - 40s each side
- Calf stretch on a step, knee straight then bent - 30s each way, each side
- On your back, knees bent - 5 breaths, 4s in / 6s out"""


def apply_to_program(program):
    changed = []
    sessions = program["sessions"]

    sessions[KEY] = {
        "name": "Mobility assessment",
        "day": "Optional",
        "warmupNote": WARMUP,
        "cooldownNote": COOLDOWN,
        "exercises": [dict(e) for e in EXERCISES],
    }
    if KEY not in program["order"]:
        program["order"].append(KEY)
    changed.append("added session '%s' (%d tests, %d measurements, day=Optional)"
                   % (sessions[KEY]["name"], len(EXERCISES),
                      sum(e["sets"] for e in EXERCISES)))

    l1 = sessions["lower1"]
    l1["warmupNote"] = LOWER1_WARMUP
    l1["cooldownNote"] = LOWER1_COOLDOWN
    changed.append("rewrote Lower 1 warm-up + cool-down (form only, same content)")

    return changed
