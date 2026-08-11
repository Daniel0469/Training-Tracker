"""Add the optional weekend run to the program.

Agreed with Daniel (11 Aug 2026): the Mon-Fri week stays exactly as it is, with
its single Wednesday cardio slot. This is a *supplementary* run - done if you
fancy it on the day, tracked with Garmin, and deliberately carrying no target
and no progression, so skipping a weekend is not "falling behind".

    Weekend run (optional)   day = "Optional"

"Optional" is not a weekday, so the app's DOW lookup gives it 99 (sorts to the
bottom of every session list) and sessionForDate() can never match it - the
calendar never opens it and Home never calls it today's session. It is picked
by hand from the Log session dropdown. See the app-side commit "Sessions can sit
outside the week".

The exercise is deliberately NOT named "Easy run (Zone 2)", which is what the
Wednesday endurance session uses: records, the Last column and Home's run cards
key on the exercise NAME, so sharing it would fold the optional jog into the
structured Zone 2 progression. A separate name keeps them apart, which is the
point of "supplementary".

Distance + time columns mean isRunning() is true, so this session gets pace
auto-compute, a splits table, and - because saveSession() tags any session with
a running exercise as garminWanted - the hands-free Garmin auto-link for free.
No garminRun flag needed.

Idempotent: re-running makes no further change. Writes a timestamped backup of
data.json next to this script before pushing anything.

    python scratchpad/apply_weekendrun.py            # dry run
    python scratchpad/apply_weekendrun.py --apply    # push
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

KEY = "weekendRun"

SESSION = {
    "name": "Weekend run (optional)",
    "day": "Optional",
    "exercises": [
        {
            "name": "Weekend run",
            "warmup": "",
            "notes": "",
            "target": "",
            "sets": 1,
            "cols": ["Distance (km)", "Time (mm:ss)", "Pace"],
            "muscles": [],
        }
    ],
    "warmupNote": "Entirely optional - this one is a bonus, not a box to tick. No target and no "
                  "progression: go by feel, easy enough to hold a conversation, walk whenever you "
                  "want to. If you are not up for it, skip it and nothing is behind.\n\n"
                  "Few minutes of easy walking to start, then run when you feel like running.",
    "cooldownNote": "Walk until your breathing settles, then whatever stretches you fancy - the "
                    "Wednesday cool-down list is there if you want it.",
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
        "User-Agent": "tt-apply-weekendrun",
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

    prog = data["program"]
    sessions = prog["sessions"]
    order = prog.setdefault("order", [])

    # Refuse to run against a program that has moved underneath this script.
    expected = ["lower2", "upper1", "cardioSpeed", "cardioEndurance", "upper2", "lower1"]
    unknown = [k for k in order if k not in expected + [KEY]]
    if unknown:
        raise SystemExit("!! program.order has sessions this script doesn't know about: %s" % unknown)

    changed = False

    if KEY in sessions:
        if sessions[KEY] == SESSION:
            print("  [already] %s matches" % KEY)
        else:
            print("  [update]  %s differs from the intended definition" % KEY)
            print("            store name=%r day=%r exercises=%d"
                  % (sessions[KEY].get("name"), sessions[KEY].get("day"),
                     len(sessions[KEY].get("exercises") or [])))
            sessions[KEY] = SESSION
            changed = True
    else:
        print("  [add]     %s  %s (%s)" % (KEY, SESSION["name"], SESSION["day"]))
        sessions[KEY] = SESSION
        changed = True

    # Last in order. orderedKeys() re-sorts by weekday for display and "Optional"
    # falls to 99 regardless, so this only keeps the stored order tidy.
    if KEY not in order:
        order.append(KEY)
        print("  [order]   %s appended -> %s" % (KEY, order))
        changed = True
    elif order[-1] != KEY:
        order.remove(KEY)
        order.append(KEY)
        print("  [order]   %s moved to the end -> %s" % (KEY, order))
        changed = True
    else:
        print("  [already] order")

    if not changed:
        print("\nNothing to change - already applied.")
        return

    print("\n--- the week now reads ---")
    dow = {"Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4,
           "Friday": 5, "Saturday": 6, "Sunday": 7}
    for k in sorted(order, key=lambda k: (dow.get(sessions[k].get("day"), 99), order.index(k))):
        day = sessions[k].get("day")
        print("  %-10s %s%s" % (day, sessions[k].get("name"),
                                "   <- never auto-opened" if day == "Optional" else ""))
    print("  Sat/Sun    - off (the weekend run is opt-in, not scheduled)")

    if dry:
        print("\nDry run. Re-run with --apply to push.")
        return

    # Stamp the program so both phones adopt it on their next sync (mergeInData
    # only takes the store's copy when its updatedAt is newer than the device's).
    prog["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    body = json.dumps({
        "message": "Program: add the optional weekend run (day = Optional)",
        "content": base64.b64encode(json.dumps(data).encode("utf-8")).decode("ascii"),
        "sha": meta["sha"],
    }).encode("utf-8")
    api(url, token, data=body, method="PUT")
    print("\nPushed. program.updatedAt =", prog["updatedAt"])


if __name__ == "__main__":
    main()
