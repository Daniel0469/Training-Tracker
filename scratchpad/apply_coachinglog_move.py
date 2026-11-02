#!/usr/bin/env python3
"""Move `coachingLog` out of data.json into its own coaching-log.json.

The history is the coach's working memory - what it has already told them, so each
week builds on the last - and nothing in the app reads it. Left in the store it had
grown to 367KB of a 609KB file: 60% of everything both phones push and pull on
every sync, for a card that was removed on 14 Sep.

Idempotent and safe to re-run. Backs data.json up next to this script first, writes
the history file, verifies every entry arrived by id, and only then removes the key
from data.json. If anything looks wrong it stops before the removal.

    python scratchpad/apply_coachinglog_move.py training-tracker [--commit]

Without --commit it is a dry run and writes nothing anywhere.
"""
import sys, os, json, datetime, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(g); g.loader.exec_module(G)
G._load_server_env(sys.argv[1] if len(sys.argv) > 1 else "training-tracker")
c = importlib.util.spec_from_file_location("ttc", os.path.join(ROOT, "mcp-coach", "server.py"))
C = importlib.util.module_from_spec(c); c.loader.exec_module(C)

COMMIT = "--commit" in sys.argv

data, sha, url, token = C._github_read_with_sha()
in_store = [e for e in (data.get("coachingLog") or []) if isinstance(e, dict)]
existing, _s, _u, _t = C._log_read_with_sha()
have = {e.get("id") for e in existing if isinstance(e, dict)}
todo = [e for e in in_store if e.get("id") not in have]

before = len(json.dumps(data))
print("data.json          %6.1f KB" % (before / 1024))
print("coachingLog        %6.1f KB, %d entries" % (len(json.dumps(in_store)) / 1024, len(in_store)))
print("coaching-log.json  %6.1f KB, %d entries already there"
      % (len(json.dumps(existing)) / 1024, len(existing)))
print("to move:           %d" % len(todo))
if not COMMIT:
    print("\nDRY RUN - nothing written. Re-run with --commit.")
    sys.exit(0)

stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = os.path.join(ROOT, "scratchpad", "data-backup-%s.json" % stamp)
json.dump(data, open(backup, "w", encoding="utf-8"), indent=1)
print("\nbacked up -> %s" % os.path.basename(backup))

# 1. history file first. If this fails, data.json still holds everything.
for rec in todo:
    C._log_append(rec, "Migrate coaching history out of data.json")
print("wrote %d entr%s to the history file" % (len(todo), "y" if len(todo) == 1 else "ies"))

# 2. verify every entry is really there before removing anything
after, _s, _u, _t = C._log_read_with_sha()
landed = {e.get("id") for e in after if isinstance(e, dict)}
missing = [e.get("id") for e in in_store if e.get("id") not in landed]
if missing:
    raise SystemExit("!! %d entries did NOT land (%s...) - data.json left untouched"
                     % (len(missing), missing[:3]))
print("verified: all %d entries present in coaching-log.json" % len(in_store))

# 3. only now drop the key
def mutate(d):
    if "coachingLog" not in d:
        return None                        # already migrated; nothing to write
    d.pop("coachingLog")
    return True

if C._github_update(mutate, "Move coaching history out of data.json") is None:
    print("data.json already had no coachingLog - nothing to remove")
else:
    now, _s, _u, _t = C._github_read_with_sha()
    print("data.json %.1f KB -> %.1f KB (-%.0f%%)"
          % (before / 1024, len(json.dumps(now)) / 1024,
             (1 - len(json.dumps(now)) / before) * 100))
print("\nNOTE: a phone on a build older than tt-v128 still carries coachingLog and will")
print("push it back on its next sync. get_coaching_history unions both, so nothing is")
print("lost either way - but data.json only stays small once both phones have updated.")
