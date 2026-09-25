#!/usr/bin/env python3
"""Swap the banded external rotation for a cable one, in both warm-ups.

Daniel, 25 Sep: "swap banded rotation for cables". The line appears in Upper A and
Upper B, worded slightly differently in each, so this matches the exercise name
rather than the whole line and leaves every cue after it intact.

Idempotent and dry-run by default; backs data.json up next to this script first.
Refuses rather than guesses if a note no longer contains the line it expects.

    python scratchpad/apply_cable_rotation.py training-tracker [--commit]
"""
import sys, os, json, re, datetime, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(g); g.loader.exec_module(G)
G._load_server_env(sys.argv[1] if len(sys.argv) > 1 else "training-tracker")
c = importlib.util.spec_from_file_location("ttc", os.path.join(ROOT, "mcp-coach", "server.py"))
C = importlib.util.module_from_spec(c); c.loader.exec_module(C)

COMMIT = "--commit" in sys.argv
TARGETS = ["upper1", "upper2"]
# "Band external rotation" / "Banded external rotation" -> "Cable external rotation"
PAT = re.compile(r"\bBand(?:ed)? external rotation\b")
NEW = "Cable external rotation"

data, *_ = C._github_read_with_sha()
prog = (data.get("program") or {}).get("sessions") or {}

hits = 0
for k in TARGETS:
    s = prog.get(k) or {}
    note = s.get("warmupNote") or ""
    found = [ln.strip() for ln in note.splitlines() if PAT.search(ln)]
    already = [ln.strip() for ln in note.splitlines() if NEW.lower() in ln.lower()]
    print("== %s (%s)" % (k, s.get("name")))
    for ln in found:
        hits += 1
        print("   -  %s" % ln[:110])
        print("   +  %s" % PAT.sub(NEW, ln)[:110])
    for ln in already:
        print("   ok already cable: %s" % ln[:100])
    if not found and not already:
        print("   !! no external-rotation line found - nothing to do here")

if not hits:
    print("\nNothing to change (already applied, or the wording moved).")
    sys.exit(0)
if not COMMIT:
    print("\nDRY RUN - nothing written. Re-run with --commit.")
    sys.exit(0)

stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = os.path.join(ROOT, "scratchpad", "data-backup-%s.json" % stamp)
json.dump(data, open(backup, "w", encoding="utf-8"), indent=1)
print("\nbacked up -> %s" % os.path.basename(backup))

def mutate(d):
    sessions = ((d.get("program") or {}).get("sessions") or {})
    changed = []
    for k in TARGETS:
        s = sessions.get(k) or {}
        note = s.get("warmupNote") or ""
        if not PAT.search(note):
            continue
        s["warmupNote"] = PAT.sub(NEW, note)
        changed.append(k)
    if not changed:
        return None
    now = datetime.datetime.now(datetime.timezone.utc)
    # JS toISOString format exactly: mergeInData compares these stamps as STRINGS,
    # and Python's default "+00:00" sorts below "Z", so a naive stamp reads as older
    # than the phones' copy and the edit silently never arrives.
    d.setdefault("program", {})["updatedAt"] = (
        now.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (now.microsecond // 1000))
    return changed

changed = C._github_update(mutate, "Cable external rotation in both upper warm-ups")
print("changed:", changed)
print("backup is %s if it needs putting back" % os.path.basename(backup))
