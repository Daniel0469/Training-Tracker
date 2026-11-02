"""Merge duplicate logs of the same session on the same day into one.

Cerys's 1 Aug 2026 got saved three times, and the pieces landed apart:

    1785619831492  Garmin-linked (act. 23817236814), 642s + splits, no note
    1785619795068  completely empty, stuck "awaiting run"
    1785619895366  difficulty 6 + the shin note, stuck "awaiting run"

The two unlinked ones can never clear: the Garmin matcher will not reuse an
activity id it has already assigned, so they wait for a run that does not exist.
Meanwhile History shows one session three times, with the numbers on one and how
it felt on another.

A cardio session can always be saved empty by design - that is the "just log and
save, let Garmin fill it in" flow - so a second tap makes a phantom. Daniel
chose not to add a guard for now; this just cleans up what is there.

Merge rule: the log with the Garmin link is the primary (else the one with the
most typed rows). Feedback, difficulty, duration and volume are taken from
whichever sibling has them; the primary's entries are kept. REFUSES if a
non-primary holds typed rows the primary does not, because then it is not a
duplicate and picking one would lose data.

Idempotent (nothing to merge once merged), backs data.json up first.

    python scratchpad/apply_mergedupes.py            # dry run
    python scratchpad/apply_mergedupes.py --apply    # push
"""
import base64
import io
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))


def cfg():
    p = r"C:\Users\danie\Documents\TrainingTracker\.mcp.json"
    env = json.load(io.open(p, encoding="utf-8"))["mcpServers"]["training-tracker"]["env"]
    return env["TT_GITHUB_REPO"], env["TT_GITHUB_TOKEN"], env["TT_GITHUB_PATH"]


def api(url, token, data=None, method=None):
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "tt-apply-mergedupes",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def typed_cells(log):
    """How many cells actually have something in them - the measure of 'real data'."""
    n = 0
    for e in (log.get("entries") or []):
        for row in (e.get("rows") or []):
            for v in (row or []):
                if str(v).strip() not in ("", "None"):
                    n += 1
    return n


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

    groups = {}
    for l in data.get("logs", []):
        if not l:
            continue
        key = (l.get("person"), l.get("date"), l.get("sessionName"))
        groups.setdefault(key, []).append(l)

    drop_ids = set()
    merged = 0

    for key, logs in sorted(groups.items(), key=lambda kv: str(kv[0])):
        if len(logs) < 2:
            continue
        person, date, name = key
        print("\n  %s  %s  %s  - %d logs" % (person, date, name, len(logs)))

        linked = [l for l in logs if l.get("garminActivityId")]
        if len(linked) > 1:
            print("     !! more than one is Garmin-linked - skipping, check by hand")
            continue
        primary = linked[0] if linked else max(logs, key=typed_cells)
        others = [l for l in logs if l is not primary]

        blocked = False
        for o in others:
            if typed_cells(o) > 0 and typed_cells(o) >= typed_cells(primary):
                print("     !! %s holds typed data the primary does not (%d cells vs %d)"
                      % (o.get("id"), typed_cells(o), typed_cells(primary)))
                blocked = True
        if blocked:
            print("     skipping - not a clean duplicate")
            continue

        print("     keep  %s  (%d typed cells%s)"
              % (primary.get("id"), typed_cells(primary),
                 ", Garmin-linked" if primary.get("garminActivityId") else ""))
        for o in others:
            bits = []
            fb = (o.get("feedback") or "").strip()
            if fb and fb not in (primary.get("feedback") or ""):
                primary["feedback"] = ((primary.get("feedback") or "").strip()
                                       + ("\n" if (primary.get("feedback") or "").strip() else "")
                                       + fb)
                bits.append("feedback")
            if primary.get("difficulty") in (None, "") and o.get("difficulty") not in (None, ""):
                primary["difficulty"] = o["difficulty"]
                bits.append("difficulty %s" % o["difficulty"])
            if not primary.get("durationSec") and o.get("durationSec"):
                primary["durationSec"] = o["durationSec"]
                bits.append("duration")
            if not primary.get("volume") and o.get("volume"):
                primary["volume"] = o["volume"]
                bits.append("volume")
            print("     drop  %s%s" % (o.get("id"),
                                       ("  -> took " + ", ".join(bits)) if bits else "  (nothing to take)"))
            drop_ids.add(o.get("id"))
        # A merged session is no longer waiting for anything.
        if primary.get("garminActivityId"):
            primary["garminWanted"] = False
        merged += 1

    if not drop_ids:
        print("\nNo duplicates to merge.")
        return

    data["logs"] = [l for l in data["logs"] if l and l.get("id") not in drop_ids]
    # TOMBSTONE, or this merge does not hold. Learned the hard way: run on 11 Aug
    # 2026, this removed Cerys's two phantom 1 Aug saves from the store and they
    # were back within a day, because mergeInData unions logs by id and a phone
    # that still held them pushed them straight back. Removing a log says nothing;
    # `deletedLogs` is what says "this is gone on purpose", and it is re-asserted
    # on every push. The app has done this since tt-v101 - the script hadn't.
    tomb = data.get("deletedLogs")
    if not isinstance(tomb, list):
        tomb = []
    have = {str(x) for x in tomb}
    for i in drop_ids:
        if str(i) not in have:
            tomb.append(i)
            have.add(str(i))
    data["deletedLogs"] = tomb
    print("\n%d group(s) merged, %d log(s) removed, %d tombstone(s) now on file. %d logs remain."
          % (merged, len(drop_ids), len(tomb), len(data["logs"])))

    if dry:
        print("\nDry run. Re-run with --apply to push.")
        return

    body = json.dumps({
        "message": "Merge duplicate saves of the same session into one",
        "content": base64.b64encode(json.dumps(data).encode("utf-8")).decode("ascii"),
        "sha": meta["sha"],
    }).encode("utf-8")
    api(url, token, data=body, method="PUT")
    print("\nPushed.")


if __name__ == "__main__":
    main()
