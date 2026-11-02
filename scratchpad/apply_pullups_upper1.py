"""Add pull-ups to Upper 1, so they are trained twice a week rather than once.

Coach-raised, approved by Daniel on 26 Aug 2026. His own numbers are the argument:
on 21 Aug he did one set of 5 completely unassisted and needed 4.5kg of help for
the next three, which is exactly the threshold where frequency, not load, is what
turns one unassisted set into four. For Cerys it is the only strength goal she has
written down and it went 39 days untrained (13 Jul - 21 Aug) purely because the
session did not come round.

Three decisions worth keeping:

* The name is IDENTICAL to Upper 2's - "Pull-ups (assisted to weighted)". Records,
  the Last column and the progress chart all key on the name, so sharing it is what
  makes this one movement trained twice a week rather than two separate exercises
  with two half-histories. Same reason `load: "assist"` and the Assist (kg) / Reps
  columns are copied exactly: setLoad has to score both slots the same way, or
  Cerys's assistance coming down would read as her getting weaker in one session
  and stronger in the other.

* SECOND in the session, straight after the bench press. The coach said 3-4 sets
  and "early"; the deadlift is the standing lesson here - it sat last in Lower 1
  and went unlogged for months, so a movement that matters does not go at the end.

* THREE sets, not four. Upper 1 already runs 66-79 minutes and Daniel cut the
  bench to 3 sets on 19 Aug specifically to shorten it; adding a fourth set of a
  slow movement would hand back what that bought. 3 is inside the range the coach
  gave.

Cerys's shoulder is handled with a NOTE rather than by leaving the exercise out:
it popped on 19 Aug and ached after pull-ups on 21 Aug, so she holds off on the
second slot until it has been clear a couple of weeks. The coach asked for it this
way round on purpose - an exercise added and removed loses its place and its
history, a note does not.

Idempotent. Backs data.json up next to this script before pushing.

    python scratchpad/apply_pullups_upper1.py            # dry run
    python scratchpad/apply_pullups_upper1.py --apply    # push
"""
import base64, io, json, os, sys, urllib.request
from datetime import datetime, timezone

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "Pull-ups (assisted to weighted)"
NOTE = ("Cerys: skip this second slot until the right shoulder has been clear for a "
        "couple of weeks - Upper 2's set is enough for now. Daniel: this is the one "
        "to be fresh for, so it comes before the pulldown.")


def cfg():
    p = r"C:\Users\danie\Documents\TrainingTracker\.mcp.json"
    env = json.load(io.open(p, encoding="utf-8"))["mcpServers"]["training-tracker"]["env"]
    return env["TT_GITHUB_REPO"], env["TT_GITHUB_TOKEN"], env["TT_GITHUB_PATH"]


def api(url, token, data=None, method=None):
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "tt-apply-pullups-upper1",
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

    sessions = ((data.get("program") or {}).get("sessions")) or {}
    u1, u2 = sessions.get("upper1"), sessions.get("upper2")
    if not u1 or not u2:
        raise SystemExit("!! upper1 / upper2 not found")

    # Copy the shape from Upper 2 rather than restating it, so the two slots cannot
    # drift apart in columns or load type - which is what would break the scoring.
    src = next((e for e in u2["exercises"] if e.get("name") == NAME), None)
    if src is None:
        raise SystemExit("!! Upper 2 has no %r to copy the shape from" % NAME)

    if any(e.get("name") == NAME for e in u1["exercises"]):
        print("  [already] Upper 1 already has %r" % NAME)
        print("\nNothing to do.")
        return

    ex = {"name": NAME, "warmup": "", "notes": NOTE, "target": "3x4-10", "sets": 3,
          "cols": list(src.get("cols") or []), "muscles": list(src.get("muscles") or []),
          "load": src.get("load")}
    bench = next((i for i, e in enumerate(u1["exercises"]) if e.get("name") == "Bench press"), -1)
    at = bench + 1 if bench >= 0 else 0
    u1["exercises"].insert(at, ex)

    print("\n  [add] Upper 1 position %d: %s  %s sets, cols=%s load=%s"
          % (at, NAME, ex["sets"], ex["cols"], ex["load"]))
    print("\nUpper 1 is now:")
    for i, e in enumerate(u1["exercises"]):
        print("   %d. %-32s sets=%s" % (i, e["name"], e.get("sets")))
    print("\nShape matches Upper 2: cols=%s  load=%r  muscles=%s"
          % (ex["cols"] == list(src.get("cols") or []), ex["load"], ex["muscles"]))

    if dry:
        print("\n(dry run - nothing pushed. Re-run with --apply)")
        return

    now = datetime.now(timezone.utc)
    data["program"]["updatedAt"] = now.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (now.microsecond // 1000)
    body = json.dumps({
        "message": "Upper 1: pull-ups, so the movement is trained twice a week",
        "content": base64.b64encode(json.dumps(data, indent=2).encode("utf-8")).decode("ascii"),
        "sha": meta["sha"],
    }).encode("utf-8")
    api(url, token, body, "PUT")
    print("\npushed. program.updatedAt =", data["program"]["updatedAt"])
    print("Both phones pick it up on their next Sync now (not mid-workout).")


if __name__ == "__main__":
    main()
