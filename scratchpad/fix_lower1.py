# -*- coding: utf-8 -*-
"""Rewrite the Lower 1 note constants in mobility_assess.py.

Session notes render as pre-wrap, so a hard line break is kept AND the line is
wrapped again if it is too long for the screen. Two rules fall out of that, both
learned by looking at the real thing on a 375px phone:

  - Never align columns with spaces. A wrapped line loses its indent entirely and
    the table collapses into rubble. This is what my first traffic light did.
  - Wrap prose around 95 characters, matching the existing notes. The continuation
    lines then read as an ordinary paragraph. Wrapping at 72 leaves it ragged.

    python scratchpad/fix_lower1.py
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mobility_assess.py")
text = io.open(SRC, encoding="utf-8").read()

WARMUP = u'''FIRST - adductor squeeze. Your traffic light for today.

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
- Thoracic extension over a bench or roller - 45s, exhale at the bottom'''

COOLDOWN = u'''COOL-DOWN - 13 min, in two halves that do different jobs.

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
- On your back, knees bent - 5 breaths, 4s in / 6s out'''


def replace_const(name, value):
    global text
    pat = re.compile(r'(%s = u""")(.*?)(""")' % name, re.S)
    if not pat.search(text):
        sys.exit("!! could not find %s" % name)
    text = pat.sub(lambda m: m.group(1) + value + m.group(3), text, count=1)
    print("  *", name)


replace_const("LOWER1_WARMUP", WARMUP)
replace_const("LOWER1_COOLDOWN", COOLDOWN)

# Guard the rule this file exists to enforce.
for label, body in (("warm-up", WARMUP), ("cool-down", COOLDOWN)):
    for line in body.split("\n"):
        if len(line) > 95:
            sys.exit("!! %s line over 95 chars: %r" % (label, line[:60]))
        if re.search(r"\S {3,}\S", line):
            sys.exit("!! %s line uses space-aligned columns: %r" % (label, line[:60]))

io.open(SRC, "w", encoding="utf-8", newline="").write(text)
print("\nrewrote Lower 1 notes - no space-aligned columns, prose within 95 chars")
