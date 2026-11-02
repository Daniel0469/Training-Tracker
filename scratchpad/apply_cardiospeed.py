"""Apply the 29 Jul Cardio: Speed + Core warm-up / cool-down edits to the live store.

Nine changes from Daniel's session feedback, all of them text edits to the
cardioSpeed session's warmupNote / cooldownNote (the mobility work lives in
those free-text blocks, not as program exercises). Scope confirmed with Daniel:
Cardio: Speed + Core only - the other five sessions keep their own numbers.

Idempotent: re-running makes no further change. Writes a timestamped backup of
data.json next to this script before pushing anything.
"""
import base64
import io
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))


def cfg():
    p = r"C:\Users\danie\Documents\TrainingTracker\.mcp.json"
    env = json.load(io.open(p, encoding="utf-8"))["mcpServers"]["training-tracker"]["env"]
    return env["TT_GITHUB_REPO"], env["TT_GITHUB_TOKEN"], env["TT_GITHUB_PATH"]


def api(url, token, data=None, method=None):
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "tt-apply-cardiospeed",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


# ---- the nine edits, as (description, old, new) on the note text -------------
# An empty `new` deletes the whole line.
WARMUP_EDITS = [
    ("hip CARs -> 5 each side",
     "- Standing hip CARs - 3 each side",
     "- Standing hip CARs - 5 each side"),
    ("90/90s -> 10 each side",
     "- 90/90 hip switches - 8 each side",
     "- 90/90 hip switches - 10 each side"),
    ("generic warm-up cardio (no named machine)",
     "- Easy jog, 5 min",
     "- Any easy cardio, 5 min"),
    ("remove strides",
     "- Strides - 3 x 20s, building to interval pace",
     ""),
    ("add pigeon pose",
     "- Leg swings, front to back - 10 each leg",
     "- Leg swings, front to back - 10 each leg\n- Pigeon pose - 40s each side"),
]

COOLDOWN_EDITS = [
    ("clams -> 10 slow reps each side",
     "- Isometric side-lying clam - 3 x 20s each side",
     "- Side-lying clam - 10 slow reps each side"),
    ("hip hikes -> 2 sets",
     "- Hip hike - 3 x 10 each side",
     "- Hip hike - 2 x 10 each side"),
    ("quad stretch: standing or seated",
     "- Standing quad stretch - 40s each side",
     "- Standing or seated quad stretch - 40s each side"),
    ("remove the cardio line",
     "- Easy jog 3 min, then walk 2 min - do not stop dead after the last interval",
     ""),
    ("remove breaths",
     "- 5 breaths, 4s in / 6s out",
     ""),
    # Consequence of the two removals above, not a separate request: dropping the
    # 3 min jog + 2 min walk takes ~5 min out of a block still labelled 10 min.
    ("cool-down duration now reflects what's left",
     "10 min - passive.",
     "5 min - passive."),
]


def apply(note, edits, label):
    out, applied, already = note, [], []
    for desc, old, new in edits:
        # Insert-after-anchor edits (new == old + extra line) keep matching their
        # own anchor once applied, so they'd duplicate the added line on a second
        # run. Check the finished state first for those.
        if new and new != old and new.startswith(old) and new in out:
            already.append(desc)
            continue
        if old in out:
            if new:
                out = out.replace(old, new, 1)
            else:
                # drop the line and its newline
                out = out.replace(old + "\n", "", 1).replace(old, "", 1)
            applied.append(desc)
        elif (new and new in out) or (not new and old not in out):
            already.append(desc)
        else:
            raise SystemExit("!! %s: could not find text for '%s'\n   %r" % (label, desc, old))
    return out.rstrip() + "\n" if out.endswith("\n") else out, applied, already


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

    sess = data["program"]["sessions"]["cardioSpeed"]
    wu, wa, wal = apply(sess["warmupNote"], WARMUP_EDITS, "warm-up")
    cd, ca, cal = apply(sess["cooldownNote"], COOLDOWN_EDITS, "cool-down")

    for lbl, ap, al in (("warm-up", wa, wal), ("cool-down", ca, cal)):
        for d in ap:
            print("  [apply] %s: %s" % (lbl, d))
        for d in al:
            print("  [already done] %s: %s" % (lbl, d))

    if wu == sess["warmupNote"] and cd == sess["cooldownNote"]:
        print("\nNothing to change - already applied.")
        return

    print("\n--- new warm-up ---\n" + wu)
    print("\n--- new cool-down ---\n" + cd)

    if dry:
        print("\nDry run. Re-run with --apply to push.")
        return

    sess["warmupNote"] = wu
    sess["cooldownNote"] = cd
    # Stamp the program so both phones adopt it on their next sync (mergeInData
    # only takes the store's copy when its updatedAt is newer than the device's).
    data["program"]["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    body = json.dumps({
        "message": "Cardio: Speed + Core warm-up/cool-down edits (29 Jul feedback)",
        "content": base64.b64encode(json.dumps(data).encode("utf-8")).decode("ascii"),
        "sha": meta["sha"],
    }).encode("utf-8")
    api(url, token, data=body, method="PUT")
    print("\nPushed. program.updatedAt =", data["program"]["updatedAt"])


if __name__ == "__main__":
    main()
