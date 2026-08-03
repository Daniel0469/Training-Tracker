"""Move the program to a Mon-Fri week, Saturday and Sunday off.

Legs / Upper / Cardio / Upper / Legs, agreed with Daniel:

    Mon  Lower 2                  (was Friday)   - squats come off two rest days
    Tue  Upper 1                  (was Thursday)
    Wed  Cardio: Speed + Core     (unchanged)    ) alternate week to week; Speed
    Wed  Cardio: Endurance + Core (was Saturday) ) is the one the app auto-opens
    Thu  Upper 2                  (was Sunday)
    Fri  Lower 1                  (was Monday)
    Sat/Sun - off

Six sessions into five slots, so both cardio sessions share Wednesday.
sessionForDate() takes the first Wednesday session in program.order, so
cardioSpeed leads and Endurance is one tap away in the Log session dropdown.
A line at the top of each cardio warm-up note says so.

Days only. No exercise, target, set or note content changes beyond that line,
and nothing touches logged history - entries carry their own sessionKey and
sessionName, so past sessions keep the day they were actually done on.

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
        "User-Agent": "tt-apply-weekdays",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


# key -> (expected current day, new day). The expected day is checked, so this
# refuses to run against a program that has already moved on underneath it.
DAYS = {
    "lower2":          ("Friday",    "Monday"),
    "upper1":          ("Thursday",  "Tuesday"),
    "cardioSpeed":     ("Wednesday", "Wednesday"),
    "cardioEndurance": ("Saturday",  "Wednesday"),
    "upper2":          ("Sunday",    "Thursday"),
    "lower1":          ("Monday",    "Friday"),
}

# Monday-first, and cardioSpeed ahead of cardioEndurance so it's the Wednesday
# the app opens on. orderedKeys() re-sorts by weekday for display anyway; this
# order is what breaks the Wednesday tie.
ORDER = ["lower2", "upper1", "cardioSpeed", "cardioEndurance", "upper2", "lower1"]

# Prepended to each cardio warm-up note (the 🔥 card at the top of the Log form),
# so it's obvious on the day that the two share Wednesday.
ALT_NOTE = {
    "cardioSpeed": "Wednesday alternates: speed one week, Zone 2 the next. This is the speed week - "
                   "for the other, pick Cardio: Endurance + Core from the session list. "
                   "Home's \u26a1 and \U0001f3c3 cards show which you did last.",
    "cardioEndurance": "Wednesday alternates: Zone 2 one week, speed the next. This is the Zone 2 week - "
                       "for the other, pick Cardio: Speed + Core from the session list. "
                       "Home's \u26a1 and \U0001f3c3 cards show which you did last.",
}


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

    missing = [k for k in DAYS if k not in sessions]
    if missing:
        raise SystemExit("!! sessions missing from the store: %s" % missing)
    unknown = [k for k in sessions if k not in DAYS]
    if unknown:
        raise SystemExit("!! store has sessions this script doesn't know about: %s" % unknown)

    changed = False

    for key, (was, now) in DAYS.items():
        cur = sessions[key].get("day")
        if cur == now:
            print("  [already] %-16s %s" % (key, now))
            continue
        if cur != was:
            raise SystemExit("!! %s is on %r, expected %r or %r - program has moved, "
                             "re-check before running" % (key, cur, was, now))
        print("  [move]    %-16s %s -> %s" % (key, cur, now))
        sessions[key]["day"] = now
        changed = True

    if prog.get("order") != ORDER:
        if sorted(prog.get("order", [])) != sorted(ORDER):
            raise SystemExit("!! program.order holds different keys than expected: %s" % prog.get("order"))
        print("  [order]   %s -> %s" % (prog.get("order"), ORDER))
        prog["order"] = ORDER
        changed = True
    else:
        print("  [already] order")

    for key, line in ALT_NOTE.items():
        note = sessions[key].get("warmupNote", "")
        if note.startswith(line):
            print("  [already] %-16s alternation note" % key)
            continue
        if "Wednesday alternates:" in note:
            raise SystemExit("!! %s already has a different alternation note - check by hand" % key)
        sessions[key]["warmupNote"] = line + "\n\n" + note
        print("  [note]    %-16s alternation line added" % key)
        changed = True

    if not changed:
        print("\nNothing to change - already applied.")
        return

    print("\n--- the week now reads ---")
    dow = {"Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4,
           "Friday": 5, "Saturday": 6, "Sunday": 7}
    for k in sorted(prog["order"], key=lambda k: (dow.get(sessions[k].get("day"), 99),
                                                  prog["order"].index(k))):
        print("  %-10s %s" % (sessions[k].get("day"), sessions[k].get("name")))
    print("  Sat/Sun    - off")

    if dry:
        print("\nDry run. Re-run with --apply to push.")
        return

    # Stamp the program so both phones adopt it on their next sync (mergeInData
    # only takes the store's copy when its updatedAt is newer than the device's).
    prog["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    body = json.dumps({
        "message": "Program: Mon-Fri week (legs/upper/cardio/upper/legs), Sat+Sun off",
        "content": base64.b64encode(json.dumps(data).encode("utf-8")).decode("ascii"),
        "sha": meta["sha"],
    }).encode("utf-8")
    api(url, token, data=body, method="PUT")
    print("\nPushed. program.updatedAt =", prog["updatedAt"])


if __name__ == "__main__":
    main()
