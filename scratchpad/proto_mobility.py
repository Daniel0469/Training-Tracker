# -*- coding: utf-8 -*-
"""Build a LOCAL prototype state for the Mobility assessment. Pushes nothing.

Reads the most recent data-backup-*.json (so the prototype carries the real
history), applies the proposed program change in memory, seeds two dated sets of
assessment numbers so the ladder and the chart have something to draw, and writes
scratchpad/proto-mobility-state.json for the browser to load into localStorage.
The shared store is never opened.

    python scratchpad/proto_mobility.py
"""
import glob, io, json, os, uuid

import mobility_assess
import roll_notes

HERE = os.path.dirname(os.path.abspath(__file__))

backups = sorted(glob.glob(os.path.join(HERE, "data-backup-*.json")))
if not backups:
    raise SystemExit("!! no data-backup-*.json here")
src = backups[-1]
data = json.load(io.open(src, encoding="utf-8"))
print("source:", os.path.basename(src))

changed = mobility_assess.apply_to_program(data["program"])

# Must run second: it rewrites every note, Lower 1 and the assessment's own
# included, so it has the last word on wording.
data.setdefault("coaching", {})
rolled, moved, removed = roll_notes.apply_to_program(data["program"], data["coaching"])

# Two fake baselines per person, six weeks apart, so the ladder shows a Change
# column and the chart has a line rather than a dot. Prototype only - these never
# go near the real store.
SEED = {
    # test name: (Daniel wk0, Daniel wk6, Cerys wk0, Cerys wk6)
    "Standing fold":               ([14.0], [10.5], [6.0], [4.0]),
    "Straight-leg raise - passive": ([58, 55], [64, 61], [76, 74], [78, 77]),
    "Straight-leg raise - active":  ([31, 29], [38, 36], [52, 50], [55, 54]),
    "Pancake hip tilt":            ([34.0], [27.0], [19.0], [15.0]),
    "Tailor's pose (wall)":        ([21, 17], [17, 14], [11, 9], [9, 8]),
    "Knee to wall (ankle)":        ([7.5, 6.0], [9.0, 8.0], [11.0, 10.5], [11.5, 11.0]),
    "Deep squat - heel lift":      ([4.5], [2.0], [0.0], [0.0]),
    "Supine overhead reach":       ([9.0], [6.5], [3.0], [2.0]),
    "Shoulder external rotation":  ([8.0, 11.0], [6.0, 9.0], [2.0, 3.0], [1.0, 2.0]),
}
SIDES = ["left", "right"]


def entry(ex, vals):
    # Mirrors what saveSession writes, betterWhen included - otherwise the seeded
    # history would exercise a code path the real app never produces.
    en = {"name": ex["name"], "cols": list(ex["cols"]),
          "rows": [[str(v), (SIDES[i] if len(vals) > 1 else "")]
                   for i, v in enumerate(vals)]}
    if ex.get("betterWhen"):
        en["betterWhen"] = ex["betterWhen"]
    return en


exs = mobility_assess.EXERCISES
for person, i0, i1 in (("Daniel", 0, 1), ("Cerys", 2, 3)):
    for date, idx in (("2026-07-19", i0), ("2026-08-30", i1)):
        data["logs"].append({
            "id": str(uuid.uuid4()),
            "person": person,
            "date": date,
            "sessionKey": mobility_assess.KEY,
            "sessionName": "Mobility assessment",
            "entries": [entry(e, SEED[e["name"]][idx]) for e in exs],
        })
changed.append("seeded 2 dated assessments per person (PROTOTYPE ONLY)")

data["activePerson"] = 0
data["theme"] = data.get("theme") or "light"

out = os.path.join(HERE, "proto-mobility-state.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(data, indent=1))

for c in changed:
    print("  *", c)
print("\nNotes rewritten:")
for c in rolled:
    print("   ", c)
print("\nMoved into coaching:")
for c in moved:
    print("   ", c)
print("\nRemoved from notes entirely:")
for key, where, what in removed:
    print("    %-16s %-10s %s" % (key, where, what))
print("\nwrote", os.path.basename(out), "- nothing pushed, shared store untouched")
