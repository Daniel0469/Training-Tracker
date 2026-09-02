# -*- coding: utf-8 -*-
"""Estimate how long a warm-up / cool-down list actually takes.

The stated durations had drifted from the lists (Lower 1's cool-down still said
13 min after four sets of core work came out of it). Rather than invent a new
number per session, this reads each line and adds it up, so the arithmetic is
auditable and any single line can be argued with.

Deliberately rough. Rest between isometric sets is assumed at 10s, a rep at 3s,
and 8s of transition per item for walking to the next thing.
"""
import re

REST = 10.0      # between sets of an isometric hold
REP = 3.0        # one rep of anything counted in reps
MOVE = 8.0       # getting from one item to the next


def _line_seconds(line):
    t = line.strip().lstrip("-").strip()
    if not t:
        return 0.0

    # "10 rounds of 3 moves, one rep of each in turn" - a circuit, so the detail
    # sits on indented lines this never reads. The header has to carry the maths.
    m = re.search(r"(\d+)\s*rounds?\s*of\s*(\d+)", t)
    if m:
        return float(m.group(1)) * float(m.group(2)) * REP

    # "2 cycles each side, about 2 min a cycle" - must beat the plain "N min"
    # rule below, which would otherwise price the whole item at one cycle.
    m = re.search(r"(\d+)(?:\s*-\s*(\d+))?\s*cycles?\s*each side.*?(\d+)\s*min", t)
    if m:
        n = float(m.group(2) or m.group(1))
        return n * 2 * float(m.group(3)) * 60

    # "5 min", "3 min"
    m = re.search(r"(\d+)\s*min\b", t)
    if m:
        return float(m.group(1)) * 60

    # "5 breaths, 4s in / 6s out"
    m = re.search(r"(\d+)\s*breaths?.*?(\d+)s\s*in.*?(\d+)s\s*out", t)
    if m:
        return float(m.group(1)) * (float(m.group(2)) + float(m.group(3)))

    # "3 x 15s each side" -> both sides, with a rest after each hold
    m = re.search(r"(\d+)\s*x\s*(\d+)\s*s\b.*?each (?:side|leg|arm)", t)
    if m:
        n, s = float(m.group(1)), float(m.group(2))
        return n * 2 * (s + REST)

    # "5 x 20s at 70%"
    m = re.search(r"(\d+)\s*x\s*(\d+)\s*s\b", t)
    if m:
        n, s = float(m.group(1)), float(m.group(2))
        return n * (s + REST)

    # "30s each way, each side" -> four holds
    m = re.search(r"(\d+)\s*s\b.*?each way,?\s*each side", t)
    if m:
        return float(m.group(1)) * 4

    # "40s each side"
    m = re.search(r"(\d+)\s*s\b.*?each (?:side|leg|arm)", t)
    if m:
        return float(m.group(1)) * 2

    # "3 x 10 each side" (reps, not seconds)
    m = re.search(r"(\d+)\s*x\s*(\d+)\b(?!\s*s).*?each (?:side|leg|arm)", t)
    if m:
        return float(m.group(1)) * float(m.group(2)) * 2 * REP

    # "Glute bridge - 10, 2s squeeze at the top" - the leading number is reps and
    # the seconds are a per-rep tempo cue, not the duration of the whole item.
    m = re.search(r"^[^0-9]*?(\d+)\s*,\s*(\d+)\s*s\b", t)
    if m:
        return float(m.group(1)) * (REP + float(m.group(2)))

    # "45s", "20s"
    m = re.search(r"(\d+)\s*s\b", t)
    if m:
        return float(m.group(1))

    # "12 each side", "5-8 each side", "3 each side, slow"
    m = re.search(r"(\d+)(?:\s*-\s*(\d+))?\s*(?:slow\s*)?each (?:side|leg|arm|way)", t)
    if m:
        n = float(m.group(2) or m.group(1))
        return n * 2 * REP

    # "Band pull-aparts - 20, straight arms..."  leading rep count
    m = re.search(r"^[^0-9]*?(\d+)(?:\s*-\s*(\d+))?\b", t)
    if m:
        n = float(m.group(2) or m.group(1))
        if n <= 60:
            return n * REP

    return 20.0  # something happens, we just can't read how much


def minutes(body, verbose=False):
    """Whole minutes for every '- ' item in a note body."""
    total = 0.0
    for line in body.split("\n"):
        s = line.strip()
        if not s.startswith("- "):
            continue
        secs = _line_seconds(s) + MOVE
        total += secs
        if verbose:
            print("      %5.1fs  %s" % (secs, s[2:72]))
    return int(round(total / 60.0))
