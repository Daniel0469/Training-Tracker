"""Split the treadmill program out of each run session's warm-up note and into
its own `setupNote` field.

Coach-raised, approved by Daniel on 25 Aug 2026, and the same operation as
apply_recording_split.py did for the recording plan five days earlier - it reuses
that script's split_note for exactly that reason. The treadmill program is the
session written out as numbered time + speed blocks to key in before starting;
the belt then runs the session so nothing has to be adjusted mid-run, which is
the whole point of programming it.

Wrong in the warm-up for the same three reasons the recording plan was: it isn't
warm-up content and pushes the warm-up below the fold; it is rewritten every time
the session structure changes, which meant re-sending the hand-written warm-up to
correct a single speed; and it is read once before starting rather than followed
during, so it belongs to a different moment.

Split point is the `WARM-UP` heading again - both notes are written that way, and
the script refuses rather than guesses if one isn't. Only sessions with a `person`
field, the two owned run sessions, are touched.

Idempotent: a session that already has a setupNote is left alone. Writes a
timestamped backup of data.json next to this script before pushing.

    python scratchpad/apply_setup_split.py            # dry run
    python scratchpad/apply_setup_split.py --apply    # push
"""
import base64, io, json, os, sys, urllib.request
from datetime import datetime, timezone

from apply_recording_split import api, cfg, split_note

HERE = os.path.dirname(os.path.abspath(__file__))


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
    owned = [(k, s) for k, s in sessions.items() if (s or {}).get("person")]
    if not owned:
        raise SystemExit("!! no session has a `person` field - expected Run: Daniel / Run: Cerys")

    changed = []
    for key, s in owned:
        who = "%s (%s)" % (s.get("name"), s.get("person"))
        if s.get("setupNote"):
            print("  [already] %s: setupNote set, left alone" % who)
            continue
        note = s.get("warmupNote") or ""
        if not note.strip():
            print("  [skip]    %s: no warm-up note to split" % who)
            continue
        got, why = split_note(note)
        if not got:
            raise SystemExit("!! %s: cannot split - %s. Fix by hand rather than guessing." % (who, why))
        setup, wu = got
        s["setupNote"], s["warmupNote"] = setup, wu
        changed.append((who, len(note), setup, wu))

    if not changed:
        print("\nNothing to do - already split.")
        return

    for who, n0, setup, wu in changed:
        print("\n== %s   warm-up was %d chars -> program %d + warm-up %d"
              % (who, n0, len(setup), len(wu)))
        print("   program starts: %r" % setup.split("\n")[0][:72])
        print("   program ends:   %r" % setup.split("\n")[-1][:72])
        print("   warm-up starts: %r" % wu.split("\n")[0][:72])
        # The block table is the point of the field - make sure it came across whole.
        print("   numbered block lines kept: %d"
              % len([l for l in setup.split("\n") if l.strip()[:2].strip().isdigit()]))

    if dry:
        print("\n(dry run - nothing pushed. Re-run with --apply)")
        return

    now = datetime.now(timezone.utc)
    data["program"]["updatedAt"] = now.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (now.microsecond // 1000)
    body = json.dumps({
        "message": "Run sessions: treadmill program into its own setupNote",
        "content": base64.b64encode(json.dumps(data, indent=2).encode("utf-8")).decode("ascii"),
        "sha": meta["sha"],
    }).encode("utf-8")
    api(url, token, body, "PUT")
    print("\npushed. program.updatedAt =", data["program"]["updatedAt"])
    print("Both phones pick it up on their next Sync now (not mid-workout).")


if __name__ == "__main__":
    main()
