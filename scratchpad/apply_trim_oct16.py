"""Write the 16 Oct trimmed session notes (scratchpad/trim_oct16_drafts.py) to the store.

Daniel approved the drafts on 16 Oct 2026. Goes through the coach server's own
set_session_notes / set_run, from a fresh process, so it is the same write path the
tools use. Backs the store up first; dry run unless --commit.

    python -X utf8 scratchpad/apply_trim_oct16.py            # dry run
    python -X utf8 scratchpad/apply_trim_oct16.py --commit   # write
"""
import sys, os, json, datetime, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scratchpad"))
g = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(g); g.loader.exec_module(G)
G._load_server_env("training-tracker")
c = importlib.util.spec_from_file_location("ttc", os.path.join(ROOT, "mcp-coach", "server.py"))
C = importlib.util.module_from_spec(c); c.loader.exec_module(C)
import trim_oct16_drafts as T

COMMIT = "--commit" in sys.argv
FIELD = {"garmin": "garminNote", "setup": "setupNote", "recording": "recordingNote",
         "warmup": "warmupNote", "cooldown": "cooldownNote"}
# Person-owned sessions go through set_run (shared ones refuse a person's own session).
OWNED = {"Zone 2: Daniel": ("Daniel", "thursday"), "Quality run: Daniel": ("Daniel", "monday"),
         "Quality run: Cerys": ("Cerys", "monday"), "Zone 2: Cerys": ("Cerys", "thursday"),
         "Mobility: Daniel": ("Daniel", "mobility"), "Mobility: Cerys": ("Cerys", "mobility")}

data, *_ = C._github_read_with_sha()
live = {(s or {}).get("name"): s for s in ((data.get("program") or {}).get("sessions") or {}).values()}
new = T.render()

for name, fields in new.items():
    s = live.get(name)
    if s is None:
        sys.exit("No live session called %r - stopping, nothing written." % name)
    diff = [f for f, t in fields.items() if (s.get(FIELD[f]) or "").strip() != t.strip()]
    print("%-22s %s" % (name, ", ".join(diff) or "already matches"))

if not COMMIT:
    print("\nDRY RUN - nothing written. Re-run with --commit.")
    sys.exit(0)

stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = os.path.join(ROOT, "scratchpad", "data-backup-%s.json" % stamp)
json.dump(data, open(backup, "w", encoding="utf-8"), indent=1)
print("\nbacked up -> %s\n" % os.path.basename(backup))

for name, fields in new.items():
    if name in OWNED:
        person, which = OWNED[name]
        res = C.set_run(person, which=which, **fields)
    else:
        res = C.set_session_notes(name, **fields)
    ok = res.get("ok", True) and not res.get("error")
    print("%-22s %s" % (name, "written: %s" % res.get("changed") if ok else "!! %s" % res.get("error")))
