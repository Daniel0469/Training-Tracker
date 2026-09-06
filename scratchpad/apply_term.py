"""Apply the term routine to the LIVE shared store. This one really writes.

Backs the store up locally first, then does a read -> mutate -> write through
mcp-coach's own `_github_update`, so a concurrent phone sync 409s and is retried
rather than silently losing data. Only `program` is touched; logs, bodyweights,
coaching and everything else are left exactly as they are.

    python scratchpad/apply_term.py --dry-run     # show the diff, write nothing
    python scratchpad/apply_term.py --apply       # do it

Credentials come from .mcp.json, which is gitignored.
"""
import datetime, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "mcp-coach"))

cfg = json.load(io.open(os.path.join(ROOT, ".mcp.json"), encoding="utf-8"))
os.environ.update(cfg["mcpServers"]["training-tracker"]["env"])

import server                      # mcp-coach/server.py - import-safe
import term_sessions

DRY = "--apply" not in sys.argv
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def summarise(program):
    DOW = {"monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4,
           "friday": 5, "saturday": 6, "sunday": 7}
    keys = sorted(program["order"],
                  key=lambda k: DOW.get(str(program["sessions"][k].get("day", "")).lower(), 8))
    for k in keys:
        s = program["sessions"][k]
        print("   %-9s %-22s %-7s %2d exercises" % (
            s.get("day"), s.get("name"), s.get("person") or "both", len(s.get("exercises", []))))


# ---- back the live store up before touching it ------------------------------
live = server.load_data()
backup = os.path.join(HERE, "data-backup-%s.json" % stamp)
io.open(backup, "w", encoding="utf-8").write(json.dumps(live, indent=1))
print("backed up live store ->", os.path.basename(backup))
print("   %d logs, %d sessions, program.updatedAt=%s\n"
      % (len(live.get("logs", [])), len(live["program"]["sessions"]),
         live["program"].get("updatedAt")))

print("BEFORE")
summarise(live["program"])

if DRY:
    changed = term_sessions.apply_to_program(live["program"])
    print("\nWOULD CHANGE")
    for c in changed:
        print("  *", c)
    print("\nAFTER")
    summarise(live["program"])
    print("\n-- dry run, nothing written. Re-run with --apply to write. --")
    raise SystemExit(0)


def mutate(data):
    changed = term_sessions.apply_to_program(data["program"])
    # The phones adopt whichever program has the newest stamp, so this is what
    # actually makes the change reach them.
    data["program"]["updatedAt"] = datetime.datetime.now(datetime.timezone.utc)\
        .isoformat().replace("+00:00", "Z")
    return changed


changed = server._github_update(
    mutate, "Term routine: rebuild the week around the uni timetable")

print("\nWRITTEN")
for c in changed:
    print("  *", c)

# ---- read it back and check it actually landed ------------------------------
after = server.load_data()
print("\nVERIFIED FROM THE STORE")
summarise(after["program"])
print("\n   program.updatedAt =", after["program"].get("updatedAt"))
print("   logs still present:", len(after.get("logs", [])),
      "(was %d)" % len(live.get("logs", [])))
