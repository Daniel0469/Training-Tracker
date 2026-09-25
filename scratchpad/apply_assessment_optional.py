#!/usr/bin/env python3
"""Take the Mobility assessment off Wednesday.

Daniel, 23 Sep: "mobility assessment should not be assigned a day unless the coach
assigns it - should switch with the mobility session depending what the coach wants
that week". It sat on Wednesday alongside each person's own mobility session, so the
automatic alternation kept bringing it round - an assessment is a re-test, not a
weekly session.

Optional means it is never auto-opened, never "today's session" and sorts last. The
coach puts it on a Wednesday when a re-test is due, with write_coaching's
session_swap, which is spent as soon as it is logged.

Idempotent and dry-run by default; backs data.json up next to this script first.

    python scratchpad/apply_assessment_optional.py training-tracker [--commit]
"""
import sys, os, json, datetime, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(g); g.loader.exec_module(G)
G._load_server_env(sys.argv[1] if len(sys.argv) > 1 else "training-tracker")
c = importlib.util.spec_from_file_location("ttc", os.path.join(ROOT, "mcp-coach", "server.py"))
C = importlib.util.module_from_spec(c); c.loader.exec_module(C)

COMMIT = "--commit" in sys.argv
KEY, EXPECT = "mobility-assessment", "Wednesday"

data, *_ = C._github_read_with_sha()
sess = ((data.get("program") or {}).get("sessions") or {}).get(KEY)
if not sess:
    raise SystemExit("!! no session %r - has it been renamed? Stopping rather than guessing." % KEY)

print("%s (%s): day = %s" % (KEY, sess.get("name"), sess.get("day")))
if sess.get("day") == "Optional":
    print("Already Optional - nothing to do.")
    sys.exit(0)
if sess.get("day") != EXPECT:
    raise SystemExit("!! expected day %r, found %r - stopping rather than guessing." % (EXPECT, sess.get("day")))

print("\nWednesday, per person, after the change:")
for who in data.get("people") or []:
    if not who:
        continue
    keys = [k for k in (data["program"].get("order") or [])
            if (data["program"]["sessions"].get(k) or {}).get("day") == "Wednesday"
            and ((data["program"]["sessions"].get(k) or {}).get("person") in (None, "", who))
            and k != KEY]
    print("   %-8s %s" % (who, [data["program"]["sessions"][k]["name"] for k in keys] or "(nothing)"))

if not COMMIT:
    print("\nDRY RUN - nothing written. Re-run with --commit.")
    sys.exit(0)

stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = os.path.join(ROOT, "scratchpad", "data-backup-%s.json" % stamp)
json.dump(data, open(backup, "w", encoding="utf-8"), indent=1)
print("\nbacked up -> %s" % os.path.basename(backup))

def mutate(d):
    s = ((d.get("program") or {}).get("sessions") or {}).get(KEY)
    if not s or s.get("day") == "Optional":
        return None
    s["day"] = "Optional"
    now = datetime.datetime.now(datetime.timezone.utc)
    # JS toISOString exactly: mergeInData compares these as STRINGS and Python's
    # "+00:00" sorts below "Z", so a naive stamp reads as older than the phones'
    # copy and the change silently never arrives.
    d["program"]["updatedAt"] = now.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (now.microsecond // 1000)
    return True

print("changed:", C._github_update(mutate, "Mobility assessment has no day of its own"))
print("backup is %s if it needs putting back" % os.path.basename(backup))
