"""Split the Garmin recording protocol out of each run session's warm-up note
and into its own `recordingNote` field.

Coach-raised, approved by Daniel on 20 Aug 2026. The protocol - one activity or
several, where Start / Lap / End go, what each lap will hold, what to type in
and what to report back - was the first twenty-odd lines of `warmupNote`, which
was wrong three ways: it pushed the actual warm-up off a phone screen at the
moment they need it; it has to be rewritten whenever the session structure
changes (the lap points mean nothing against a different structure), which meant
re-sending the whole hand-written warm-up to touch it; and it is read AFTER the
session too, by the coach, to work out which lap holds which piece of a mixed
activity - a warm-up, a time trial and an easy jog all sit in one recording, so
the activity-level averages are meaningless without it.

Split point is the `WARM-UP` heading: everything above it is the protocol,
everything from it down is the warm-up proper. Both run notes are written that
way, and the script refuses rather than guesses if one isn't.

Only sessions with a `person` field - the two owned run sessions - are touched.
Nothing else in the program has a recording block.

Idempotent: a session that already has a recordingNote is left alone. Writes a
timestamped backup of data.json next to this script before pushing.

    python scratchpad/apply_recording_split.py            # dry run
    python scratchpad/apply_recording_split.py --apply    # push
"""
import base64, io, json, os, sys, urllib.request
from datetime import datetime, timezone

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
MARKER = "WARM-UP"


def cfg():
    p = r"C:\Users\danie\Documents\TrainingTracker\.mcp.json"
    env = json.load(io.open(p, encoding="utf-8"))["mcpServers"]["training-tracker"]["env"]
    return env["TT_GITHUB_REPO"], env["TT_GITHUB_TOKEN"], env["TT_GITHUB_PATH"]


def api(url, token, data=None, method=None):
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "tt-apply-recording-split",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def split_note(note):
    """(recording, warmup) or (None, why-not). The marker has to start a line."""
    lines = note.split("\n")
    for i, line in enumerate(lines):
        if line.strip().upper().startswith(MARKER):
            rec = "\n".join(lines[:i]).strip()
            wu = "\n".join(lines[i:]).strip()
            if not rec:
                return None, "nothing above the %s heading" % MARKER
            if not wu:
                return None, "nothing below the %s heading" % MARKER
            return (rec, wu), None
    return None, "no line starting %r" % MARKER


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
        if s.get("recordingNote"):
            print("  [already] %s: recordingNote set, left alone" % who)
            continue
        note = s.get("warmupNote") or ""
        if not note.strip():
            print("  [skip]    %s: no warm-up note to split" % who)
            continue
        got, why = split_note(note)
        if not got:
            raise SystemExit("!! %s: cannot split - %s. Fix by hand rather than guessing." % (who, why))
        rec, wu = got
        s["recordingNote"], s["warmupNote"] = rec, wu
        changed.append((who, len(note), len(rec), len(wu), rec, wu))

    if not changed:
        print("\nNothing to do - already split.")
        return

    for who, n0, nr, nw, rec, wu in changed:
        print("\n== %s   warm-up was %d chars -> recording %d + warm-up %d" % (who, n0, nr, nw))
        print("   recording starts: %r" % rec.split("\n")[0][:70])
        print("   recording ends:   %r" % rec.split("\n")[-1][:70])
        print("   warm-up starts:   %r" % wu.split("\n")[0][:70])
        # Nothing may be lost in the split: every non-blank line has to survive.
        src_lines = [l.strip() for l in (rec + "\n" + wu).split("\n") if l.strip()]
        print("   lines preserved:  %d" % len(src_lines))

    if dry:
        print("\n(dry run - nothing pushed. Re-run with --apply)")
        return

    now = datetime.now(timezone.utc)
    data["program"]["updatedAt"] = now.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (now.microsecond // 1000)
    body = json.dumps({
        "message": "Run sessions: recording protocol into its own recordingNote",
        "content": base64.b64encode(json.dumps(data, indent=2).encode("utf-8")).decode("ascii"),
        "sha": meta["sha"],
    }).encode("utf-8")
    api(url, token, body, "PUT")
    print("\npushed. program.updatedAt =", data["program"]["updatedAt"])
    print("Both phones pick it up on their next Sync now (not mid-workout).")


# Guarded: proto_recording.py imports split_note from here, and an import must not
# reach for the network or write a backup.
if __name__ == "__main__":
    main()
