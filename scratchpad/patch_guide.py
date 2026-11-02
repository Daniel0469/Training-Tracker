# -*- coding: utf-8 -*-
"""Bring the in-app Guide up to date with the Flexibility pane.

CLAUDE.md: renderHelp has to reflect reality whenever a user-facing feature
changes. Two edits - the tab overview in section 1, and a new paragraph in
section 5 next to the Run and Time panes it sits beside.

    python scratchpad/patch_guide.py
"""
import io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "js", "app.js")
src = io.open(APP, encoding="utf-8").read()
orig = src


def sub(anchor, new, label):
    global src
    n = src.count(anchor)
    if n != 1:
        sys.exit("!! anchor matched %d times (%s)" % (n, label))
    src = src.replace(anchor, new)
    print("  *", label)


sub(
    u"(with <b>\U0001f3cb Lifts</b>, <b>\U0001f3c3 Run</b> once you\\'ve logged a run,"
    u" and <b>⚖ Body</b> side by side at the top) and <b>Program</b>.')",
    u"(with <b>\U0001f3cb Lifts</b>, <b>\U0001f3c3 Run</b> once you\\'ve logged a run,"
    u" <b>\U0001f938 Flexibility</b> once you\\'ve logged a mobility test,"
    u" and <b>⚖ Body</b> side by side at the top) and <b>Program</b>.')",
    "section 1 tab overview",
)

FLEX_PARA = (
    u"\n     +p('<b>\U0001f938 Flexibility</b> appears once you\\'ve logged a mobility test, and reads as a "
    u"<b>ladder</b>: every test you\\'ve measured, where it is now, and how far it has moved since the "
    u"first time you measured it. The idea is that one thing is <b>limiting</b> a position - an ankle, a "
    u"hamstring, the ability to tilt your pelvis - and that the limiting one is the only thing worth "
    u"training. So the table is there to make your <b>lowest rung</b> findable, not to admire the high "
    u"ones. Tests are measured in <b>centimetres</b>, so they stay out of Lifts, out of your records and "
    u"out of session volume. Most are a gap you want to <b>close</b>; the ones marked "
    u"<b>higher is better</b> (ankle range, active leg raise) improve by growing. A test you do on both "
    u"sides reports the <b>worse side</b>, since that is the one holding the movement back. Pick any test "
    u"underneath to chart it for both of you over time.')"
    u"\n     +p('The <b>Mobility assessment</b> session in Program is what fills it. It is a set of "
    u"measurements rather than a workout - a tape measure, a wall and a flat floor - and each test\\'s "
    u"\U0001f527 <b>setup</b> line says exactly how to set it up and what it is telling you. Measure "
    u"<b>cold</b>, before training: stretching buys you a few centimetres that wear off within hours, so "
    u"warming up first measures the warm-up rather than your flexibility. Same conditions, same landmark, "
    u"no forcing - a number you had to fight for won\\'t repeat next time.')"
)

sub(
    u"Each rep\\'s <b>speed is its average</b>, so it reads a little under the belt setting"
    u" - what you typed stays the record.'));",
    u"Each rep\\'s <b>speed is its average</b>, so it reads a little under the belt setting"
    u" - what you typed stays the record.')" + FLEX_PARA + u");",
    "section 5 Flexibility paragraphs",
)

if src == orig:
    sys.exit("!! nothing changed")
io.open(APP, "w", encoding="utf-8", newline="").write(src)
print("\nwrote js/app.js  (%+d chars)" % (len(src) - len(orig)))
