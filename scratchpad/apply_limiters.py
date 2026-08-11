"""Record what Daniel says is holding each cardio session back - his words.

From Daniel, 11 Aug 2026, when asked explicitly rather than inferred from the
numbers. This matters because the two of them produce superficially similar
traces for opposite reasons, and the right advice is opposite too:

  Speed + Core
    Daniel  hasn't found his top working speed yet - building up deliberately
            rather than overshooting. So the limiter is CALIBRATION, not
            capacity. (Consistent with 29 Jul: 13 km/h reps peaked at 157 of a
            200 max, never above Zone 3.)
    Cerys   top speed already found. Her limiter is NOT speed - she is at her
            ceiling, so progression has to come from rep length, rep count or
            recovery. (29 Jul: 396s in Zone 4 and 228s in Zone 5 at 11 km/h.)

  Endurance + Core
    Daniel  the length/time of the run.
    Cerys   Zone 2 is a WALK for her, not a run. Prescribing "easy run" to her
            is prescribing a walk. (1 Aug: 0.75 km at 14:16/km, 299s in Z1 and
            225s in Z3 - she cannot run slowly enough to sit in Zone 2.)

Stored as limiters[person][exact session name]; the coach reads it with the
limiters() MCP tool before interpreting anything, and the app shows it on the
session. Idempotent; backs data.json up first.

    python scratchpad/apply_limiters.py            # dry run
    python scratchpad/apply_limiters.py --apply    # push
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

LIMITERS = {
    "Daniel": {
        "Cardio: Speed + Core":
            "Haven't found my top working speed yet - building up to it rather than "
            "overshooting. Progress the speed in small steps.",
        "Cardio: Endurance + Core":
            "The length/time of the run is what limits this one.",
    },
    "Cerys": {
        "Cardio: Speed + Core":
            "Top speed already found - this is as fast as I go. Progress has to come "
            "from something other than the speed.",
        "Cardio: Endurance + Core":
            "Zone 2 is a walk for me, not a run - I can't run slowly enough to stay in it.",
    },
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
        "User-Agent": "tt-apply-limiters",
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

    people = data.get("people") or []
    names = {s.get("name") for s in (data.get("program", {}).get("sessions") or {}).values()}

    lim = data.get("limiters") or {}
    changed = False

    for person, bysess in LIMITERS.items():
        if person not in people:
            raise SystemExit("!! %r is not one of the accounts: %s" % (person, people))
        entry = dict(lim.get(person) or {})
        for session, text in bysess.items():
            if session not in names:
                raise SystemExit("!! %r is not a session in the program: %s" % (session, sorted(names)))
            if entry.get(session) == text:
                print("  [already] %-7s %s" % (person, session))
                continue
            if entry.get(session):
                print("  [replace] %-7s %s" % (person, session))
                print("            was: %s" % entry[session])
            else:
                print("  [add]     %-7s %s" % (person, session))
            print("            now: %s" % text)
            entry[session] = text
            changed = True
        lim[person] = entry

    if not changed:
        print("\nNothing to change - already applied.")
        return

    data["limiters"] = lim

    if dry:
        print("\nDry run. Re-run with --apply to push.")
        return

    body = json.dumps({
        "message": "Record the stated limiters for both cardio sessions",
        "content": base64.b64encode(json.dumps(data).encode("utf-8")).decode("ascii"),
        "sha": meta["sha"],
    }).encode("utf-8")
    api(url, token, data=body, method="PUT")
    print("\nPushed.")


if __name__ == "__main__":
    main()
