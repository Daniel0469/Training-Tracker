"""Rewrite all 14 session warm-up / cool-down notes in the tighter gym format.

Daniel, 20 Aug 2026: these notes are what he reads between sets and they had
grown too wordy. Agreed shape:

  * one line per move - name, dose, then a cue only where the move is easy to
    get wrong (heel-leading on the abduction, elbows down on the rack holds).
    Paragraphs of prose technique are gone.
  * the per-person coaching asides and the safety text STAY, compressed to an
    indented line or two under the move they belong to. Nothing is dropped:
    Cerys's hip click, the PAILs/RAILs hold-off, the shin/calf note, the
    adductor traffic light and the red flags all survive.
  * housekeeping lines that were never instructions come out: the paragraph on
    both Wednesday sessions explaining how the app picks your cardio (that
    belongs in the Guide), and "Calf raise is out of this warm-up, as you asked"
    (an acknowledgement of a change already made).

The only other losses are two bits of rationale for the coach's own past edits -
why PAILs/RAILs stayed on the list, and the fuller account of what moved out of
the Wednesday endurance cool-down. Both explained a decision rather than telling
you how to train. Every dose, time and cue is intact.

No app code changes, so no CACHE_NAME bump: these are program data and reach the
phones through Sync like any other program edit.

Idempotent, and paranoid: each note must currently hash to the text this script
was written against, or already equal the new text. Anything else and it stops
without touching the store.

    python scratchpad/apply_note_trim.py            # dry run
    python scratchpad/apply_note_trim.py --apply    # push
"""
import base64, hashlib, io, json, os, sys, urllib.request
from datetime import datetime, timezone

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))

# sha1 of each note as it stood on 20 Aug 2026, before this rewrite.
OLD = {
    ("lower2", "warmupNote"): "1af95dfb7bd84d191c44c66294c4fd708856ac2d",
    ("lower2", "cooldownNote"): "39b0f703e254f185706ce915c8d2332fc466cfce",
    ("upper1", "warmupNote"): "1ab1427a3b360008516823701c2987267d55370d",
    ("upper1", "cooldownNote"): "626c0597c6d4e1140eb12e93a2563d34e5a6fd96",
    ("cardioSpeed", "warmupNote"): "2a92ca7cb4377f5dbf5227bb4ff38ac14022d37b",
    ("cardioSpeed", "cooldownNote"): "39a98374ea564d3e7bccd39b334401d7ea99ff9d",
    ("cardioEndurance", "warmupNote"): "04e7ed351e433caff125428df218056888f106f3",
    ("cardioEndurance", "cooldownNote"): "5917192284339e6c16ac36c78eba303b206db3a3",
    ("upper2", "warmupNote"): "d3b0abfb7bfa9659fbf9ea2d848cebb8df1e65da",
    ("upper2", "cooldownNote"): "0b9b515a7adfc45fea9e73c52df409668ff972fe",
    ("lower1", "warmupNote"): "9841e7fafb8e555e0fa59ec91fbf6f0091e9e9f8",
    ("lower1", "cooldownNote"): "79870068f8e85132a552949f96568537413f7bbb",
    ("weekendRun", "warmupNote"): "e7d4c60e6621d94e2daa1f8866fecc88f7ceeab0",
    ("weekendRun", "cooldownNote"): "026d07aff4502eb70c28f2d73e5b3c266803e8d2",
}

NEW = {}

NEW[("lower2", "warmupNote")] = """13 min, active - no long static stretches before lifting.

- Treadmill walk, 4-6% incline - 5 min
- Hip CARs - 3 each side, about 10s a circle
- 90/90 switches - 8 each side, sit tall, controlled
- Adductor rock-back - 8 each side
- Glute bridge - 10, 2s squeeze, ribs down
- Side-lying abduction - 12 each side, toe DOWN, heel leading, slow
    Cerys: the clicky hip. Shorten the range until it goes quiet and slow it right down. A
    painless click is common and fine; pain, or a weak-feeling leg, drop it and tell me.
- Adductor isometric - 5 x 20s at 70%
- Hip flexor isometric - 3 x 20s each side

Shoulders, BEFORE the bar goes on your back - on squats it's the rack position that bites.
- Band pull-aparts - 20, light band, straight arms, thumbs turning back, blades doing it
- Thoracic extension, roller under the mid-back - 45s, hands behind your head, exhale as you
  extend. Not the lower back.
- Bar-only rack holds - 3 x 15s in your squat grip. WIDER than feels natural, elbows DOWN
  not flared back. Still pinches? Wider again. Sort it here, not under 80kg.

- BW squat 10 slow, split squat 6 each leg
- Ramp squat - bar x8, 50% x5, 75% x3 (of working weight: at 80kg, 40kg x8 then 60kg x3)

Adductor squeeze is your daily traffic light - judge it here:
  green, no pain - train as normal
  amber, 1-3/10 - train, hold loads, don't progress the lunge step
  red, sharp or 4+/10 - lunge back a step, skip hip adduction, isometrics and glutes only
Get it assessed if the hip wakes either of you at night, locks or gives way, radiates down
the leg, or a flare hasn't settled in 48 hours."""

NEW[("lower2", "cooldownNote")] = """13 min - the passive half.

- Copenhagen plank - 3 x 15s each side
- Side plank, top-leg lift - 3 x 8 each side
- Seated march, light resistance - 3 x 10 each side
- Single-leg glute bridge - 3 x 10 each side
- Easy treadmill walk - 3 min
- 90/90 stretch, leaning forward - 40s each side
- Hip flexor stretch, glute squeezed - 40s each side, gentle, don't force it
    Cerys: skip entirely if it reproduces the front-hip pain
- Hamstring stretch - 40s each side
- Adductor rock-back, held - 40s each side
- Calf stretch, knee straight then bent - 30s each way, each side
- 5 breaths, 4s in / 6s out"""

NEW[("upper1", "warmupNote")] = """8 min. Shoulders and mid-back, not hips.

- Easy cardio, any machine - 5 min
- Band pull-aparts - 20, straight arms, thumbs turning back at the end
- Band external rotation - 15 each arm, elbow pinned to your side, no shrug
- Thoracic extension over a bench or roller - 45s, exhale as you extend. Not the lower back.
- Ramp the flat press - 50% x8, 75% x5 (at 52.5kg: 26kg, then 40kg)

Cerys: your shoulder popped on the pushdown on 19 Aug, so do the two band moves properly
rather than fast. Hip CARs live in the Lower warm-ups now - add 3 each side here if this is
your only session of the day."""

NEW[("upper1", "cooldownNote")] = """6 min.

- Easy walk - 3 min, nasal breathing
- Doorway or cable pec stretch - 40s each side, across the chest not inside the shoulder
  joint. If it's in the joint, drop the elbow lower.
- Overhead lat stretch on a rack - 40s each side, hips back and down
- Thoracic extension over a bench - 45s
- Child's pose with side reach - 40s each side"""

NEW[("cardioSpeed", "warmupNote")] = """10 min, active.

- Easy cardio - 5 min
- Hip CARs - 5 each side
- 90/90 switches - 10 each side
- Glute bridge - 10
- Side-lying abduction - 12 each side
- Hip flexor isometric - 3 x 20s each side
- Ankle circles - 10 each way
- Leg swings, front to back - 10 each leg
- Pigeon pose - 40s each side"""

NEW[("cardioSpeed", "cooldownNote")] = """6 min - stretches, plus two bits of hip work Cerys asked to keep.

- Hip hike - 2 x 10 each side    [Cerys only. Daniel: skip to the stretches]
- Side-lying clam - 10 slow each side    [Cerys only. Daniel: skip]
- Calf stretch on a step, knee straight then bent - 30s each way, each side
    Cerys: this one matters most to you - shin insurance after hard running
- Quad stretch, standing or seated, whichever you prefer - 40s each side
- Figure-4 glute stretch - 40s each side. On your back, ankle across the opposite thigh,
  pull the far knee towards your chest. Felt in the BACK of the hip, not the front.
- Hamstring stretch - 40s each side, slight knee bend, hinge from the hip, back flat"""

NEW[("cardioEndurance", "warmupNote")] = """9 min, active.

- Brisk walk - 4 min
- Hip CARs - 3 each side
- 90/90 switches - 8 each side
- Glute bridge - 10
- Side-lying abduction - 12 each side
- Ankle circles - 10 each way
- Leg swings, front to back - 10 each leg
- Easy jog build - 3 min"""

NEW[("cardioEndurance", "cooldownNote")] = """12 min, stretches only - the strength work that used to sit here (Copenhagen, hip hike, dead
bug) lives in the two Lower sessions now.

- Walk - 3 min, nasal breathing only. HR down before you stretch anything.
- PAILs/RAILs in 90/90 - 2-3 cycles each side:
    settle in, hold 90s to 2 min
    PAIL: push the shin down into the floor, ramp 20% to 100% over 10s
    RAIL: try to lift the shin off the floor, ramp to 100% over 10s
    relax, pull slightly deeper, repeat
    Cerys: skip until two clear pain-free weeks or a physio says otherwise - 90/90 is deep
    hip flexion, which a front-of-hip problem dislikes. The rest of the list is fine, and
    do the CARs daily.
- Calf stretch on a step, knee straight then bent - 30s each way, each side
    Cerys: don't skip. Your shins were quiet on 13 Aug for the first time since July, and
    calf length is part of why.
- Standing quad stretch - 40s each side, knee at the floor, glute squeezed, ribs down. Lie
  on your side if your balance goes.
- Figure-4 glute stretch - 40s each side, ankle across the opposite thigh, pull the far knee
  in. Back of the hip, not the front.
- Hamstring stretch - 40s each side, slight knee bend, hinge from the hip, back flat
- 5 breaths, 4s in / 6s out"""

NEW[("upper2", "warmupNote")] = """8 min. This is the pull-up session, so the scap work is the part that counts.

- Easy cardio, any machine - 5 min
- Band pull-aparts - 20, straight arms, thumbs turning back at the end
- Band external rotation - 15 each arm, elbow pinned to your side
- Scapular pull-ups - 5-8. Hang straight-armed, pull the blades down and together to lift an
  inch or two without bending the elbows. Pause at the top.
- Dead hang - 20s, shoulders active, not shrugged up round your ears
    Cerys: log the time - grip usually runs out before the back does
- Ramp the first lift - 50% x8, 75% x5"""

NEW[("upper2", "cooldownNote")] = """6 min.

- Easy walk - 3 min, nasal breathing
- Overhead lat stretch - 40s each side, worth an extra 20s today, you've just pulled
- Doorway or cable pec stretch - 40s each side, across the chest not inside the joint
- Thoracic extension over a bench - 45s
- Child's pose with side reach - 40s each side"""

NEW[("lower1", "warmupNote")] = """12 min, active - no long static stretches before lifting.

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

Shoulders, if you're squatting or pressing overhead later in the week:
- Band pull-aparts - 20, straight arms, thumbs turning back
- Thoracic extension over a bench or roller - 45s, exhale at the bottom

Adductor squeeze is your daily traffic light - judge it here:
  green, no pain - train as normal
  amber, 1-3/10 - train, hold loads, don't progress the lunge step
  red, sharp or 4+/10 - lunge back a step, skip hip adduction, isometrics and glutes only
Get it assessed if the hip wakes either of you at night, locks or gives way, radiates down
the leg, or a flare hasn't settled in 48 hours."""

NEW[("lower1", "cooldownNote")] = """13 min - the passive half.

- Copenhagen plank - 3 x 15s each side (short lever: knee on the bench)
- Side plank, top-leg lift - 3 x 8 each side
- Dead bug, unilateral isometric hold - 3 x 15s each side
- Single-leg glute bridge - 3 x 10 each side
- Easy treadmill walk - 3 min, nasal breathing only
- 90/90 stretch, leaning forward over the front shin - 40s each side
- Hip flexor stretch, glute squeezed, ribs down - 40s each side, gentle, don't force it
    Cerys: skip entirely if it reproduces the front-hip pain
- Hamstring stretch - 40s each side
- Adductor rock-back, held - 40s each side
- Calf stretch on a step, knee straight then bent - 30s each way, each side
- On your back, knees bent - 5 breaths, 4s in / 6s out"""

NEW[("weekendRun", "warmupNote")] = """Optional - a bonus, not a box to tick. No target and no progression: go by feel, easy enough
to hold a conversation, walk whenever you want. Skip it and nothing is behind.

- Easy walk a few minutes, then run when you feel like running."""

NEW[("weekendRun", "cooldownNote")] = """Walk until your breathing settles, then whatever stretches you fancy - the Wednesday
cool-down list is there if you want it."""


def cfg():
    p = r"C:\Users\danie\Documents\TrainingTracker\.mcp.json"
    env = json.load(io.open(p, encoding="utf-8"))["mcpServers"]["training-tracker"]["env"]
    return env["TT_GITHUB_REPO"], env["TT_GITHUB_TOKEN"], env["TT_GITHUB_PATH"]


def api(url, token, data=None, method=None):
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "tt-note-trim",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def sha1(s):
    return hashlib.sha1((s or "").encode("utf-8")).hexdigest()


def main():
    dry = "--apply" not in sys.argv
    repo, token, path = cfg()
    url = "https://api.github.com/repos/%s/contents/%s" % (repo, path)
    meta = api(url, token)
    data = json.loads(base64.b64decode(meta["content"]).decode("utf-8"))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = os.path.join(HERE, "data-backup-%s.json" % stamp)
    io.open(backup, "w", encoding="utf-8").write(json.dumps(data, indent=1))
    print("backup written:", backup)

    sessions = data["program"]["sessions"]
    known = set(k for k, _ in OLD)
    if set(sessions) != known:
        raise SystemExit("!! the store's sessions don't match this script: only-store=%s only-script=%s"
                         % (sorted(set(sessions) - known), sorted(known - set(sessions))))

    changed, before, after = [], 0, 0
    for (key, field), old_hash in OLD.items():
        cur = sessions[key].get(field) or ""
        new = NEW[(key, field)]
        before += len(cur)
        after += len(new)
        if cur == new:
            print("  [already] %s.%s" % (key, field))
            continue
        if sha1(cur) != old_hash:
            raise SystemExit(
                "!! %s.%s has been edited since this script was written (hash %s, expected %s).\n"
                "   Nothing pushed. Re-read the note and update the script."
                % (key, field, sha1(cur), old_hash))
        sessions[key][field] = new
        changed.append("%-16s %-13s %5d -> %4d chars  (-%d%%)"
                       % (key, field, len(cur), len(new), round(100 * (1 - len(new) / len(cur)))))

    if not changed:
        print("\nNothing to do - the store already matches.")
        return

    print("\nchanges:")
    for c in changed:
        print("  *", c)
    print("\ntotal: %d -> %d chars (-%d%%)" % (before, after, round(100 * (1 - after / before))))

    if dry:
        print("\n(dry run - nothing pushed. Re-run with --apply)")
        return

    # The phones adopt the program only when its stamp is NEWER than theirs, and
    # they compare it as a plain string - so it has to be JS's toISOString shape.
    now = datetime.now(timezone.utc)
    data["program"]["updatedAt"] = now.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (now.microsecond // 1000)
    body = json.dumps({
        "message": "Program: warm-up and cool-down notes trimmed to the gym-readable format",
        "content": base64.b64encode(json.dumps(data, indent=2).encode("utf-8")).decode("ascii"),
        "sha": meta["sha"],
    }).encode("utf-8")
    api(url, token, body, "PUT")
    print("\npushed. program.updatedAt =", data["program"]["updatedAt"])
    print("Both phones pick it up on their next Sync (not mid-workout).")


main()
