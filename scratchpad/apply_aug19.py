"""The five approved coach suggestions from 19 Aug 2026 - the four that are
program data (the fifth, the sticky person selector, is app code).

Each is a coach proposal Daniel approved in the app's gear menu, so the text is
his decision, not the coach's. Where a proposal left a fork, he answered it:

 1. Calf raise moves off the shoulder-pad machine onto the leg press, in BOTH
    Lower 1 and Lower 2. Daniel & Cerys flagged it independently on 18 Aug - the
    pads hurt before the calves are worked, both stuck at 70kg.
    It is RENAMED to "Leg press calf raise" rather than kept. Records, the Last
    column and the progress chart all key on the exercise NAME, and 70kg on a
    pad machine is not the same load as a leg press, so keeping the name would
    splice two different movements into one trend and one PR. The five logged
    sessions each (both people, 25 Jun - 18 Aug) stay under the old name, which
    is what the app does with any rename. Same call, same reason, as keeping
    "Flat press (DB)" out of "Bench press".
    Lower 2's machine-setting note "5/3/3" is dropped with it: those are the old
    machine's pin settings and would be actively wrong on the leg press.

 2. Goblet squat added to Lower 2, 3x8-10. Cerys asked for it to reach depth her
    back squat can't (the front-loaded counterbalance lets the torso stay
    upright); Daniel logged the mirror problem on 11 Aug. Placed LAST on his
    instruction - the alternative offered was straight after Squat, since Lower 2
    already overruns and the last exercise is the one that gets dropped.

 3. Lower 2 reordered: the lunges move to after the seated leg curl. Daniel's
    ask - lunges need floor space, which is what disappears when a class is on,
    so mid-session forces a live reshuffle. The leg curl is a machine and is
    always free.

 4. Bench press (Upper 1) goes 4 sets -> 3, target with it. Daniel asked twice,
    on 12 and 19 Aug; both 4-set sessions overran and ended early, and his 19 Aug
    3-set run took 66 min with every lift holding or improving (bench 50kg 3x8 at
    RPE 6, down from RPE 8 at the same weight on 4 sets).
    NOT applied to Upper 2's pull-ups, though the proposal allowed it and they do
    read 4: "unassisted pull up" is one of Cerys's two stated goals and the
    overrun evidence was about Upper 1, not that lift. Daniel's call.
    Lower 2's squat already reads 3, so that part of the proposal is a no-op.
    Also tidied while in there, on his instruction: Lower 1's deadlift had sets=3
    against a target of "4x5-8", so the form drew 3 rows under a target asking
    for 4. Target now matches the sets.

Idempotent: re-running changes nothing. Writes a timestamped backup of data.json
next to this script before pushing, and refuses to run if the program has moved
underneath it.

    python scratchpad/apply_aug19.py            # dry run
    python scratchpad/apply_aug19.py --apply    # push
"""
import base64, io, json, os, sys, urllib.request
from datetime import datetime, timezone

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
OLD_CALF, NEW_CALF = "Standing calf raise", "Leg press calf raise"
CALF_NOTES = ("Feet on the bottom edge of the leg press platform, press through the balls of "
              "the feet. Nothing on the shoulders.")
GOBLET = {
    "name": "Goblet squat",
    "warmup": "",
    "notes": "Light DB or kettlebell held at the chest - the counterbalance is what lets you sit "
             "lower, so go for depth rather than load.",
    "target": "3x8-10",
    "sets": 3,
    "cols": ["Weight (kg)", "Reps"],
    "muscles": ["quads", "glutes"],
}


def cfg():
    p = r"C:\Users\danie\Documents\TrainingTracker\.mcp.json"
    env = json.load(io.open(p, encoding="utf-8"))["mcpServers"]["training-tracker"]["env"]
    return env["TT_GITHUB_REPO"], env["TT_GITHUB_TOKEN"], env["TT_GITHUB_PATH"]


def api(url, token, data=None, method=None):
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "tt-apply-aug19",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def find(exs, name):
    for i, e in enumerate(exs):
        if e.get("name") == name:
            return i
    return -1


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
    expected = ["lower2", "upper1", "cardioSpeed", "cardioEndurance", "upper2", "lower1", "weekendRun"]
    unknown = [k for k in data["program"].get("order", []) if k not in expected]
    if unknown:
        raise SystemExit("!! program.order has sessions this script doesn't know about: %s" % unknown)
    changed = []

    # -- 1. calf raise -> leg press, both lower days ------------------------
    for key in ("lower1", "lower2"):
        exs = sessions[key]["exercises"]
        i = find(exs, OLD_CALF)
        if i < 0:
            if find(exs, NEW_CALF) >= 0:
                print("  [already] %s: calf raise already renamed" % key)
            else:
                raise SystemExit("!! %s: no calf raise found under either name" % key)
            continue
        exs[i]["name"] = NEW_CALF
        old_note = exs[i].get("notes", "")
        exs[i]["notes"] = CALF_NOTES
        changed.append("%s: %r -> %r%s" % (key, OLD_CALF, NEW_CALF,
                       " (dropped stale machine setting %r)" % old_note if old_note else ""))

    # -- 2. goblet squat, last in Lower 2 -----------------------------------
    exs = sessions["lower2"]["exercises"]
    if find(exs, GOBLET["name"]) >= 0:
        print("  [already] lower2: goblet squat present")
    else:
        exs.append(dict(GOBLET))
        changed.append("lower2: + %s (%s), last" % (GOBLET["name"], GOBLET["target"]))

    # -- 3. Lower 2 order: lunges after the seated leg curl ------------------
    exs = sessions["lower2"]["exercises"]
    li, ci = find(exs, "Walking/sandbag lunges"), find(exs, "Seated leg curl")
    if li < 0 or ci < 0:
        raise SystemExit("!! lower2: lunges or seated leg curl missing")
    if li < ci:
        exs.insert(ci, exs.pop(li))      # pop first: ci is then the slot after the curl
        changed.append("lower2: lunges moved after the seated leg curl")
    else:
        print("  [already] lower2: lunges already after the seated leg curl")

    # -- 4. bench 4 -> 3 sets, and the deadlift target/sets mismatch ---------
    exs = sessions["upper1"]["exercises"]
    i = find(exs, "Bench press")
    if i < 0:
        raise SystemExit("!! upper1: no bench press")
    if exs[i].get("sets") == 4 or exs[i].get("target") == "4x5-8":
        exs[i]["sets"], exs[i]["target"] = 3, "3x5-8"
        changed.append("upper1: bench press 4 sets -> 3 (target 4x5-8 -> 3x5-8)")
    else:
        print("  [already] upper1: bench press reads %s sets / %r"
              % (exs[i].get("sets"), exs[i].get("target")))

    exs = sessions["lower1"]["exercises"]
    i = find(exs, "Deadlift")
    if i >= 0 and exs[i].get("sets") == 3 and exs[i].get("target") == "4x5-8":
        exs[i]["target"] = "3x5-8"
        changed.append("lower1: deadlift target 4x5-8 -> 3x5-8 (sets already 3)")
    else:
        print("  [already] lower1: deadlift reads %s sets / %r"
              % (exs[i].get("sets"), exs[i].get("target")))

    # Pull-ups deliberately untouched - see the module docstring.
    pux = sessions["upper2"]["exercises"]
    pu = pux[find(pux, "Pull-ups (assisted to weighted)")]
    print("  [skip]    upper2: pull-ups left at %s sets (Cerys's goal lift)" % pu.get("sets"))

    if not changed:
        print("\nNothing to do - the store already matches.")
        return

    print("\nchanges:")
    for c in changed:
        print("  *", c)
    print("\nLower 2 is now:")
    for i, e in enumerate(sessions["lower2"]["exercises"]):
        print("   %d. %-28s sets=%s target=%s" % (i, e["name"], e.get("sets"), e.get("target")))

    if dry:
        print("\n(dry run - nothing pushed. Re-run with --apply)")
        return

    # The phones adopt the program only when its stamp is NEWER than theirs, and
    # they compare it as a plain string - so it has to be JS's toISOString shape.
    now = datetime.now(timezone.utc)
    data["program"]["updatedAt"] = now.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (now.microsecond // 1000)
    body = json.dumps({
        "message": "Program: calf raise to leg press, goblet squat, Lower 2 order, bench 3 sets",
        "content": base64.b64encode(json.dumps(data, indent=2).encode("utf-8")).decode("ascii"),
        "sha": meta["sha"],
    }).encode("utf-8")
    api(url, token, body, "PUT")
    print("\npushed. program.updatedAt =", data["program"]["updatedAt"])
    print("Both phones pick it up on their next Sync now (not mid-workout).")


main()
