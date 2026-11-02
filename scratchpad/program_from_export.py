"""Push the PROGRAM (and machine settings) from an app export into the store.

For edits made in a browser that has no sync set up: Daniel edits Program, taps
Export, and this script carries just those two things across. Logs, notes, goals,
coaching and everything else in the store are left exactly as they are.

    python scratchpad/program_from_export.py <export.json> <base.json>          # diff only
    python scratchpad/program_from_export.py <export.json> <base.json> --apply  # backup + push

<base.json> is the store copy the export was started from. If the live store's
program has moved on since then (a phone edited it), the script stops rather than
overwrite that edit.
"""
import base64, io, json, os, sys, time
from datetime import datetime, timezone
from apply_recording_split import api, cfg

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ("target", "sets", "warmup", "cols", "load", "bwPct", "garminRun", "betterWhen", "groupId", "muscles")
SFIELDS = ("name", "day", "person", "cardio", "warmupNote", "cooldownNote", "recordingNote", "setupNote", "garminNote")


def diff(old, new):
    out = []
    os_, ns = old.get("sessions") or {}, new.get("sessions") or {}
    oo, no = old.get("order") or [], new.get("order") or []
    for k in no:
        if k not in os_:
            s = ns[k]
            out.append("+ NEW SESSION %s (%s): %s" % (s.get("name"), s.get("day"), ", ".join(e["name"] for e in s.get("exercises") or [])))
    for k in oo:
        if k not in ns:
            out.append("- REMOVED SESSION %s" % os_[k].get("name"))
    if [k for k in oo if k in ns] != [k for k in no if k in os_]:
        out.append("~ session order: %s" % " / ".join(ns[k].get("name") for k in no))
    for k in no:
        if k not in os_:
            continue
        a, b = os_[k], ns[k]
        tag = b.get("name")
        for f in SFIELDS:
            if (a.get(f) or "") != (b.get(f) or ""):
                av, bv = str(a.get(f) or "")[:70], str(b.get(f) or "")[:70]
                out.append("~ %s: %s  %r -> %r" % (tag, f, av, bv))
        ae = {e["name"]: e for e in a.get("exercises") or []}
        be = {e["name"]: e for e in b.get("exercises") or []}
        for n in be:
            if n not in ae:
                e = be[n]
                out.append("+ %s: add %s (%s, %s sets)" % (tag, n, e.get("target"), e.get("sets")))
        for n in ae:
            if n not in be:
                out.append("- %s: remove %s" % (tag, n))
        common_a = [e["name"] for e in a.get("exercises") or [] if e["name"] in be]
        common_b = [e["name"] for e in b.get("exercises") or [] if e["name"] in ae]
        if common_a != common_b:
            out.append("~ %s: order now %s" % (tag, " > ".join(common_b)))
        for n in common_b:
            for f in FIELDS:
                if ae[n].get(f) != be[n].get(f):
                    out.append("~ %s / %s: %s %r -> %r" % (tag, n, f, ae[n].get(f), be[n].get(f)))
    return out


def ms_diff(old, new):
    out = []
    for p, by in (new or {}).items():
        for n, e in by.items():
            o = ((old or {}).get(p) or {}).get(n)
            if (o or {}).get("text") != e.get("text"):
                out.append("~ settings %s / %s: %r -> %r" % (p, n, (o or {}).get("text"), e.get("text")))
    return out


def main():
    exp = json.load(io.open(sys.argv[1], encoding="utf-8"))
    base = json.load(io.open(sys.argv[2], encoding="utf-8"))
    repo, token, path = cfg()
    url = "https://api.github.com/repos/%s/contents/%s" % (repo, path)
    meta = api(url, token)
    live = json.loads(base64.b64decode(meta["content"]).decode("utf-8"))
    moved = (live["program"].get("updatedAt") != base["program"].get("updatedAt"))
    print("base program stamp:", base["program"].get("updatedAt"))
    print("live program stamp:", live["program"].get("updatedAt"), "<- CHANGED SINCE YOUR COPY" if moved else "(unchanged since your copy)")
    print("export program stamp:", exp["program"].get("updatedAt"))
    changes = diff(live["program"], exp["program"]) + ms_diff(live.get("machineSettings"), exp.get("machineSettings"))
    print("\n%d change(s) vs the live store:" % len(changes))
    for c in changes:
        print("  " + c)
    if "--apply" not in sys.argv:
        return
    if moved:
        raise SystemExit("\n!! the live program changed since your copy - not overwriting it")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    io.open(os.path.join(HERE, "data-backup-%s.json" % stamp), "w", encoding="utf-8").write(json.dumps(live, indent=1))
    prog = exp["program"]
    now = int(time.time() * 1000)
    prog["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (now % 1000)
    live["program"] = prog
    ms = live.setdefault("machineSettings", {})
    for p, by in (exp.get("machineSettings") or {}).items():
        for n, e in by.items():
            cur = (ms.get(p) or {}).get(n)
            if not cur or (+e.get("updatedAt", 0)) > (+cur.get("updatedAt", 0)):
                ms.setdefault(p, {})[n] = e
    body = {"message": "Program edited on the laptop (Daniel)", "sha": meta["sha"],
            "content": base64.b64encode(json.dumps(live, indent=2).encode("utf-8")).decode("ascii")}
    api(url, token, json.dumps(body).encode("utf-8"), "PUT")
    print("\npushed; backup data-backup-%s.json" % stamp)


if __name__ == "__main__":
    main()
