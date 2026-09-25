#!/usr/bin/env python3
"""Mark the cardio sessions, and free the Upper B logs stuck awaiting a run.

Daniel's rule, 25 Sep: "garmin sync should be for cardio sessions". It used to be
inferred from an exercise carrying garminRun, so Upper B - a lifting day with a
ski erg in it - was tagged "awaiting run" on every save and could never clear,
because the matcher only ever accepts activities whose type contains "run". Two
sessions were stuck that way on 24 Sep.

Idempotent and dry-run by default. Backs data.json up next to this script first.

    python scratchpad/apply_cardio_flag.py training-tracker [--commit]
"""
import sys, os, json, datetime, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(g); g.loader.exec_module(G)
G._load_server_env(sys.argv[1] if len(sys.argv) > 1 else "training-tracker")
c = importlib.util.spec_from_file_location("ttc", os.path.join(ROOT, "mcp-coach", "server.py"))
C = importlib.util.module_from_spec(c); c.loader.exec_module(C)

COMMIT = "--commit" in sys.argv

# The cardio sessions, by key. Listed explicitly rather than derived: "has a cardio
# exercise in it" is the rule that broke, and "leads with one" would break the first
# time a session is reordered, which is already on the backlog.
CARDIO = {"cardioEndurance", "easyCerys", "runDaniel", "runCerys", "weekendRun"}

data, sha, url, token = C._github_read_with_sha()
prog = (data.get("program") or {}).get("sessions") or {}

print("sessions:")
for k in (data.get("program") or {}).get("order") or []:
    s = prog.get(k) or {}
    want = k in CARDIO
    now = s.get("cardio") is True
    mark = "   " if want == now else ("  +" if want else "  -")
    print("%s %-18s %-24s cardio: %s -> %s" % (mark, k, s.get("name"), now, want))

stuck = [l for l in data.get("logs", []) if l.get("garminWanted") and not l.get("garminActivityId")]
print("\nlogs stuck 'awaiting run' with nothing linkable:")
for l in stuck:
    keep = l.get("sessionKey") in CARDIO
    print("   %s %-8s %-22s %s" % (l.get("date"), l.get("person"), l.get("sessionName"),
                                   "keep waiting (is cardio)" if keep else "CLEAR"))

if not COMMIT:
    print("\nDRY RUN - nothing written. Re-run with --commit.")
    sys.exit(0)

stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = os.path.join(ROOT, "scratchpad", "data-backup-%s.json" % stamp)
json.dump(data, open(backup, "w", encoding="utf-8"), indent=1)
print("\nbacked up -> %s" % os.path.basename(backup))

def mutate(d):
    changed = []
    sessions = ((d.get("program") or {}).get("sessions") or {})
    for k, s in sessions.items():
        want = k in CARDIO
        if want and s.get("cardio") is not True:
            s["cardio"] = True; changed.append("cardio+ " + k)
        elif not want and "cardio" in s:
            s.pop("cardio"); changed.append("cardio- " + k)
    for l in d.get("logs", []):
        if l.get("garminWanted") and not l.get("garminActivityId") \
                and l.get("sessionKey") not in CARDIO:
            l["garminWanted"] = False
            changed.append("unstuck %s %s %s" % (l.get("date"), l.get("person"), l.get("sessionName")))
    if not changed:
        return None
    # The program is adopted by the phones only when its stamp is NEWER than theirs,
    # and mergeInData compares these as plain strings - so it has to be JS's exact
    # toISOString format, not Python's default +00:00, which sorts below "Z".
    d.setdefault("program", {})["updatedAt"] = (
        datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") +
        "%03dZ" % (datetime.datetime.now(datetime.timezone.utc).microsecond // 1000))
    return changed

changed = C._github_update(mutate, "Mark cardio sessions; free the stuck Upper B logs")
if changed is None:
    print("nothing to change - already applied")
else:
    for ch in changed:
        print("  *", ch)
print("\nbackup is %s if any of that needs putting back" % os.path.basename(backup))
