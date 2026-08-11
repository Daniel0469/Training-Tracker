"""Rewrite the alternation line at the top of both cardio warm-up notes.

The old line was written when the alternation was a convention you had to keep
in your own head:

    "Wednesday alternates: speed one week, Zone 2 the next. This is the speed
     week - for the other, pick ... Home's [zap] and [runner] cards show which
     you did last."

That is now wrong twice over. The app picks for you (11 Aug 2026): a live
"Next cardio" assignment from the coach wins, and with no assignment
sessionForDate() opens whichever of the two you did least recently, so a skipped
week no longer flips the rotation. And "this is the speed week" was never true of
a session - it is true of a given Wednesday - so whichever session you opened
always claimed to be the right one.

Only the first paragraph of each warmupNote changes. Everything below the blank
line - the actual mobility work - is untouched.

Idempotent, backs data.json up first.

    python scratchpad/apply_cardionotes.py            # dry run
    python scratchpad/apply_cardionotes.py --apply    # push
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

OLD = {
    "cardioSpeed":
        "Wednesday alternates: speed one week, Zone 2 the next. This is the speed week - "
        "for the other, pick Cardio: Endurance + Core from the session list. "
        "Home's \u26a1 and \U0001f3c3 cards show which you did last.",
    "cardioEndurance":
        "Wednesday alternates: Zone 2 one week, speed the next. This is the Zone 2 week - "
        "for the other, pick Cardio: Speed + Core from the session list. "
        "Home's \u26a1 and \U0001f3c3 cards show which you did last.",
}

NEW = {
    "cardioSpeed":
        "Wednesday's cardio, and you don't have to keep track of which one is due - the app "
        "opens it for you. If your coach has set a \u26a1 Next cardio card, that's the one; "
        "otherwise it's whichever of the two you did least recently. Fancy the other instead? "
        "Pick Cardio: Endurance + Core from the session list - nothing stops you.",
    "cardioEndurance":
        "Wednesday's cardio, and you don't have to keep track of which one is due - the app "
        "opens it for you. If your coach has set a \u26a1 Next cardio card, that's the one; "
        "otherwise it's whichever of the two you did least recently. Fancy the other instead? "
        "Pick Cardio: Speed + Core from the session list - nothing stops you.",
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
        "User-Agent": "tt-apply-cardionotes",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


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
    changed = False

    for key, old in OLD.items():
        if key not in sessions:
            raise SystemExit("!! %s is not in the program" % key)
        note = sessions[key].get("warmupNote", "")
        head, sep, rest = note.partition("\n\n")
        if head == NEW[key]:
            print("  [already] %s" % key)
            continue
        if head != old:
            raise SystemExit(
                "!! %s's first paragraph is not the one this script expects - it has been "
                "edited since. Check by hand.\n     found: %r" % (key, head))
        sessions[key]["warmupNote"] = NEW[key] + sep + rest
        print("  [rewrite] %s" % key)
        print("            was: %s" % old)
        print("            now: %s" % NEW[key])
        changed = True

    if not changed:
        print("\nNothing to change - already applied.")
        return

    if dry:
        print("\nDry run. Re-run with --apply to push.")
        return

    prog = data["program"]
    prog["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    body = json.dumps({
        "message": "Cardio warm-up notes: the app picks which Wednesday session is due",
        "content": base64.b64encode(json.dumps(data).encode("utf-8")).decode("ascii"),
        "sha": meta["sha"],
    }).encode("utf-8")
    api(url, token, data=body, method="PUT")
    print("\nPushed. program.updatedAt =", prog["updatedAt"])


if __name__ == "__main__":
    main()
