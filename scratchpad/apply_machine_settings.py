"""Move the program's shared exercise `notes` into per-person machine settings.

Daniel, 13 Oct 2026: the settings box is his and Cerys's own, the coach must not
write it, and the coaching prose that had built up in it goes. Every note in the
store was read and sorted three ways (the table below):

  SETTINGS  real machine settings -> data.machineSettings[person][exercise], for
            each person who does that exercise
  HOWTO     drill / test instructions -> appended to that person's coach note for
            the exercise (coaching[person].byExercise) as a "How to:" paragraph
  dropped   reasoning, history, plans - everything not listed below

Then `notes` is removed from every program exercise and program.updatedAt is
bumped, so both phones adopt the cleaned program on their next sync.

Idempotent: an existing machineSettings entry is left alone, and a coach note that
already has a "How to:" paragraph is not appended to twice.

    python scratchpad/apply_machine_settings.py              # dry run: the review list
    python scratchpad/apply_machine_settings.py --proto      # apply to the newest local
                                                             # backup -> proto-ms-state.json
    python scratchpad/apply_machine_settings.py --apply      # backup, then push to the store
"""
import base64, copy, glob, io, json, os, sys, time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))

SETTINGS = {
    "Back extension": "3",
    "Seated row": "7",
    "Cable crossover": "Cable height shoulder height or just above, both sides matched. Log the weight of ONE side.",
    "Leg press calf raise": "Feet on the bottom edge of the leg press platform, press through the balls of the feet. Nothing on the shoulders.",
    "Incline DB press": "Log the weight of ONE dumbbell.",
    "Single-leg seated leg curl": "Log the weight per leg.",
}

# name -> text for everyone who does it, or {person: text} where the old notes
# differed per session.
HOWTO = {
    "Adductor rock-back - isometric reps":
        "Half-kneeling. One knee down, the other leg straight out to the side with the foot flat and the toes pointing forward. Sit the hips back toward the down heel until you feel the inside of the straight leg, stop at the first firm stop, hold 3 seconds, come out. That is one rep. Eight reps, short rest, next side. Do not turn it into a hold. Left gets an extra round.",
    "Back squat (technique)":
        "Empty bar to about 40%. Rack position: wider grip, elbows down.",
    "Bulgarian split squat":
        "Rear foot on a bench, weight through the front heel.",
    "Deep squat - depth test":
        "Two measurements of the same squat.\nRow 1: barefoot on a flat floor. Squat as deep as you can control, hold it, and measure from the crease of your hip straight down to the floor.\nRow 2: exactly the same squat, both heels on a 5cm plate or wedge.\nMeasure cold, before anything else.",
    "Deep squat - heel lift":
        "Barefoot, feet about shoulder width, squat as deep as you can and hold it. Measure the gap under whichever heel comes up more. 0 means both heels stay down - log 0 and note how the position felt.",
    "Deep squat hold - assisted":
        "Hold a rack upright or a TRX at arm's length, feet about shoulder width, and sink to the bottom of a squat. Use your arms to take enough weight that the heels stay flat and the chest stays up.\nAt the bottom: elbows inside the knees, pry the knees outward, and spend the 45 seconds trying to bring the chest up rather than sinking further.\nFour rounds, 45 seconds, 30 seconds rest. Progress by taking weight off your hands, not by going deeper.",
    "Deep squat hold - heels on a wedge":
        "Heels on a 5cm plate or wedge, feet about shoulder width, holding something at arm's length. Sink to the bottom and hold 45 seconds. Four rounds, 30 seconds rest.\nAt the bottom: elbows inside the knees, pry the knees outward, chest up.\nProgress by lowering the wedge, not by holding longer: 5cm now, 2.5cm when four clean rounds feel easy. Record the wedge height every week in the second column.",
    "Farmers carry":
        "Stay tall, shoulders down, do not run.",
    "Frog - contract and relax":
        "On your forearms, knees wide, shins out in line with the thighs, ankles flexed so the inside of the foot is on the floor. Rock the hips back to the first firm stop and settle.\nEach round: squeeze your knees INTO the floor as if trying to drag them together, about 70 percent effort, for 5 seconds. Then let go completely and rock a little further back for 10 seconds. That is one round. Five rounds.",
    "Hip abduction":
        "Light - quality of the movement over the number on the stack. Slow out, slower back.",
    "Hip adduction":
        "Light, same as the abduction machine.",
    "Knee to wall (ankle)":
        "Face a wall in a half-kneeling lunge, front foot pointing straight at it. Drive the knee forward over the toes to touch the wall, heel flat on the floor. Slide the foot back until the knee only just touches with the heel still down. Measure from the tip of your big toe to the wall. Row 1 = left, row 2 = right.",
    "Knee to wall - isometric reps":
        "Half-kneeling facing a wall, front foot pointing straight at it, heel FLAT and staying flat. Drive the knee forward over the toes towards the wall, hold 3 seconds at the first firm stop, come back. That is one rep. Ten reps, short rest, next side.\nThe heel lifting is the end of the set.\nLeft gets an extra round, and start every set on the left. Write your best toe-to-wall distance for each side in the Notes.",
    "Loaded soleus stretch - knee bent":
        "Ball of one foot on a step, heel hanging off the back. Bend that knee and push it forward over the toes while letting the heel sink - bent knee is the whole instruction.\n45 seconds each side, three rounds, left first. Hold the wall or a rail for balance and let your bodyweight do the work. If the shins ache during it, ease off rather than pushing.",
    "Modified Thomas test (hip extension)":
        "Sit on the very end of a bench, lie back, and hug ONE knee to your chest hard enough to flatten your lower back onto the bench. Let the other leg hang off the end. Measure from the back of that hanging thigh straight down to the level of the bench top. Row 1 = LEFT leg hanging, row 2 = right leg hanging. If the thigh rests level with the bench or below it, log 0 and say so in the Notes.\nThe hug is the whole test: if the lower back lifts off the bench you are measuring an arch instead of a hip.",
    "Pancake fold hold":
        "Same wide-leg seated position. Let go, round the back, and let your bodyweight take you forward onto two yoga blocks or a stack of books under your forearms or forehead.\nHold 45 seconds, breathing out slowly and letting a little more go on each exhale. Four rounds, resting 30 seconds between.\nLower the blocks as the weeks go on, and write the block height in the Notes.",
    "Pancake hip tilt":
        "Sit with your legs as wide as they go, then bring them in a little so you are not fighting the end range. Round your back and reach your head down toward the floor. Measure forehead to floor.",
    "Romanian deadlift":
        "Hinge, not a squat. Bar close, soft knees, stop where the hamstrings stop you - the back rounding is the end of the set.",
    "Seated pancake tilt - active lift":
        "Sit with the legs as wide as they go, then bring them in slightly so you are not fighting end range. Knees pointing at the ceiling, toes up. Hands off the floor, arms out in front.\nDrive the pelvis forward into an anterior tilt - point your tailbone backwards and your belt buckle down - and lift the chest forward and up over the floor. Back STRAIGHT, not rounded. Hold 3 seconds, sit back up. Eight reps. If your back rounds, you have gone too far forward: come back until it is straight.",
    "Shoulder press":
        "Machine if your gym has one, dumbbells if not. Start light and add slowly.",
    "Ski erg / row":
        "Alternate: ski 250, row 250, ski 250, row 250. Log the metres and the time for each round.",
    "Sled push + pull":
        "One round = push it down, pull it back. Technique at a light load: finish each round breathing hard but able to talk. Build the load slowly.",
    "Standing fold":
        "Feet together, knees locked straight, fold forward and let your arms hang. Measure from the tip of your middle finger to the floor. If you reach past the floor, log 0 and note how flat your hands go.",
    "Straight-leg raise - active":
        "Exactly the same position as the passive raise, but no hands and no strap. Lift the leg using only your own hip flexors and hold it there long enough to measure. Row 1 = left leg, row 2 = right leg.",
    "Straight-leg raise - passive":
        "Lie on your back. Other leg flat on the floor, knee straight - if it lifts, the number is wrong. Raise one leg, knee locked, and pull it toward you with your hands or a strap until it stops. Measure from your heel straight down to the floor. Row 1 = left leg, row 2 = right leg. Note which in the Notes column.",
    "Supine overhead reach":
        "Lie on your back, knees bent, feet flat. Press your lower back into the floor and keep it there - it is easy to cheat by arching. Reach both straight arms overhead toward the floor. Measure from the back of your wrists to the floor.",
    "Supported side split - contract and relax":
        "Facing a wall, hands on it for support, feet wide and toes pointing FORWARD rather than out. Slide the feet apart until you feel the inside of the thighs, and stop at the first firm stop.\nEach round: squeeze your feet inward against the floor as if trying to drag them back together, about 70 percent, for 5 seconds. Then release completely and let the feet slide a little wider for 10 seconds. Five rounds.\nAs you go wider, tip the pelvis forward rather than letting the hips tuck under. Socks on a smooth floor, or feet on towels, makes the slide work.",
    "Tailor's pose (wall)":
        "Sit with your back flat against a wall, soles of the feet together and pulled in close. Let the knees drop - no hands, no pushing. Measure from the outside of the knee down to the floor. Row 1 = left, row 2 = right.",
}


def persons_for(data, name):
    """Who does this exercise: each session that has it, scoped to its owner if any."""
    who = []
    people = [p for p in (data.get("people") or []) if p]
    for s in ((data.get("program") or {}).get("sessions") or {}).values():
        if any(e.get("name") == name for e in (s or {}).get("exercises") or []):
            for p in ([s["person"]] if s.get("person") else people):
                if p not in who:
                    who.append(p)
    return who


def transform(data):
    """Mutate `data` in place. Returns the review list."""
    report = []
    now = int(time.time() * 1000)
    ms = data.setdefault("machineSettings", {})
    coaching = data.setdefault("coaching", {})
    seen = {}
    for s in ((data.get("program") or {}).get("sessions") or {}).values():
        for e in (s or {}).get("exercises") or []:
            n = (e.get("notes") or "").strip()
            if n:
                seen.setdefault(e["name"], set()).add(n)
            e.pop("notes", None)
    for name in sorted(seen):
        who = persons_for(data, name)
        line = {"exercise": name, "people": who, "old": sorted(seen[name]), "setting": None, "howto": None}
        if name in SETTINGS:
            line["setting"] = SETTINGS[name]
            for p in who:
                by = ms.setdefault(p, {})
                if name not in by:
                    by[name] = {"text": SETTINGS[name], "updatedAt": now}
        if name in HOWTO:
            line["howto"] = HOWTO[name]
            for p in who:
                entry = coaching.setdefault(p, {})
                bx = entry.setdefault("byExercise", {})
                cur = (bx.get(name) or "").strip()
                if "How to:" in cur:
                    continue
                bx[name] = (cur + "\n\n" if cur else "") + "How to: " + HOWTO[name]
        report.append(line)
    prog = data.setdefault("program", {})
    prog["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (now % 1000)
    return report


def print_report(report):
    keep = [r for r in report if r["setting"]]
    move = [r for r in report if r["howto"]]
    drop = [r for r in report if not r["setting"] and not r["howto"]]
    print("== KEPT AS MACHINE SETTINGS (%d) - copied to each person who does it" % len(keep))
    for r in keep:
        print("  - %s (%s): %s" % (r["exercise"], ", ".join(r["people"]), r["setting"]))
    print("\n== HOW-TO MOVED INTO THE COACH NOTE (%d) - the rest of the old text is dropped" % len(move))
    for r in move:
        print("  - %s (%s)" % (r["exercise"], ", ".join(r["people"])))
    print("\n== DROPPED ENTIRELY (%d) - reasoning, history, plans" % len(drop))
    for r in drop:
        first = r["old"][0].split("\n")[0]
        print("  - %s: \"%s%s\"" % (r["exercise"], first[:90], "..." if len(first) > 90 or len(r["old"][0]) > len(first) else ""))


def main():
    if "--proto" in sys.argv:
        src = sorted(glob.glob(os.path.join(HERE, "data-backup-*.json")))[-1]
        data = json.load(io.open(src, encoding="utf-8"))
        rep = transform(data)
        data["activePerson"] = 0
        data["theme"] = "dark"
        io.open(os.path.join(HERE, "proto-ms-state.json"), "w", encoding="utf-8").write(json.dumps(data))
        io.open(os.path.join(HERE, "proto-ms-report.json"), "w", encoding="utf-8").write(json.dumps(rep, indent=1))
        print("source:", os.path.basename(src), "-> proto-ms-state.json (nothing pushed)\n")
        print_report(rep)
        return
    from apply_recording_split import api, cfg
    repo, token, path = cfg()
    url = "https://api.github.com/repos/%s/contents/%s" % (repo, path)
    meta = api(url, token)
    data = json.loads(base64.b64decode(meta["content"]).decode("utf-8"))
    before = copy.deepcopy(data)
    rep = transform(data)
    print_report(rep)
    if "--apply" not in sys.argv:
        print("\n(dry run - nothing written)")
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    io.open(os.path.join(HERE, "data-backup-%s.json" % stamp), "w", encoding="utf-8").write(json.dumps(before, indent=1))
    body = {"message": "Machine settings: per person, coaching prose sorted out (Daniel, 13 Oct)",
            "content": base64.b64encode(json.dumps(data, indent=2).encode("utf-8")).decode("ascii"),
            "sha": meta["sha"]}
    api(url, token, json.dumps(body).encode("utf-8"), "PUT")
    print("\npushed; backup data-backup-%s.json" % stamp)


if __name__ == "__main__":
    main()
