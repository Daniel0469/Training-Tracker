#!/usr/bin/env python3
"""Retire the Seated cable row slot in Upper A and put Seated row in its place.

Daniel asked for this on 28 September: make the plate-loaded `Seated row` permanent
and retire the cable slot. The coach could not do it - it had no way to read a
lifting session's exercise list, so it could not tell whether `Seated row` was in
the program at all, and removing the wrong one leaves Upper A with no row. Both are
in it: the cable row at position 3 and `Seated row` tacked on at position 8, last.

So this is two edits, not one. Removing the cable row alone would leave the real row
at the end of the session, which is where work goes to die - the same reason the
farmers carry has gone unlogged four reviews running.

Logged history is NOT touched. The 15 `Seated cable row` logs keep their own name:
a cable stack and a plate-loaded row are not the same load, and merging them would
splice two lifts into one trend and one PR. Same reasoning that keeps
`Flat press (DB)` out of `Bench press`. Daniel's call, 6 Oct.

Idempotent, dry-run by default, backs the store up first, and refuses rather than
guesses if Upper A does not look the way it did when this was written.

    python scratchpad/apply_rowslot.py training-tracker [--commit]
"""
import sys, os, json, datetime, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(g); g.loader.exec_module(G)
G._load_server_env(sys.argv[1] if len(sys.argv) > 1 else "training-tracker")
c = importlib.util.spec_from_file_location("ttc", os.path.join(ROOT, "mcp-coach", "server.py"))
C = importlib.util.module_from_spec(c); c.loader.exec_module(C)

COMMIT = "--commit" in sys.argv
SESSION, DROP, KEEP = "Upper A", "Seated cable row", "Seated row"

data, *_ = C._github_read_with_sha()
sessions = ((data.get("program") or {}).get("sessions") or {})
key = next((k for k, s in sessions.items() if (s or {}).get("name") == SESSION), None)
if key is None:
    raise SystemExit("!! no session called %r - stopping rather than guessing." % SESSION)
exs = sessions[key].get("exercises") or []
names = [e.get("name") for e in exs]

print("%s, before:" % SESSION)
for i, n in enumerate(names):
    print("   %d %s%s" % (i, n, "   <-- drop" if n == DROP else ("   <-- keep" if n == KEEP else "")))

if DROP not in names and KEEP in names:
    print("\nAlready applied - %r is gone and %r is at position %d." % (DROP, KEEP, names.index(KEEP)))
    sys.exit(0)
if DROP not in names or KEEP not in names:
    raise SystemExit("\n!! expected both %r and %r in %s; found %s. Stopping."
                     % (DROP, KEEP, SESSION, names))

slot = names.index(DROP)
print("\nafter: %r removed, %r moved from %d to %d" % (DROP, KEEP, names.index(KEEP), slot))
kept = [n for n in names if n != DROP]
kept.remove(KEEP)
kept.insert(slot, KEEP)
for i, n in enumerate(kept):
    print("   %d %s" % (i, n))

logs = sum(1 for l in data.get("logs", []) for e in (l.get("entries") or [])
           if e.get("name") == DROP)
print("\n%d logged %r entries keep their own name and are not touched." % (logs, DROP))

if not COMMIT:
    print("\nDRY RUN - nothing written. Re-run with --commit.")
    sys.exit(0)

stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = os.path.join(ROOT, "scratchpad", "data-backup-%s.json" % stamp)
json.dump(data, open(backup, "w", encoding="utf-8"), indent=1)
print("\nbacked up -> %s" % os.path.basename(backup))

def mutate(d):
    s = ((d.get("program") or {}).get("sessions") or {}).get(key) or {}
    lst = s.get("exercises") or []
    cur = [e.get("name") for e in lst]
    if DROP not in cur:
        return None
    pos = cur.index(DROP)
    lst[:] = [e for e in lst if e.get("name") != DROP]
    held = next((e for e in lst if e.get("name") == KEEP), None)
    if held is not None:
        lst.remove(held)
        lst.insert(pos, held)
    now = datetime.datetime.now(datetime.timezone.utc)
    # JS toISOString exactly: mergeInData compares these stamps as STRINGS, and
    # Python's "+00:00" sorts below "Z", so a naive stamp reads as older than the
    # phones' copy and the change silently never arrives.
    d["program"]["updatedAt"] = now.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (now.microsecond // 1000)
    return [e.get("name") for e in lst]

out = C._github_update(mutate, "Upper A: retire the cable row slot, promote Seated row")
print("now:", out)
print("backup is %s if it needs putting back" % os.path.basename(backup))
