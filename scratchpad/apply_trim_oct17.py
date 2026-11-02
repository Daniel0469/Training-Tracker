"""Write Daniel's 17 Oct program trim (edited by hand in a local copy) to the store.

Replaces exercises + warmupNote on the four lifting sessions with
scratchpad/trim_oct17_sessions.json. Refuses if live has changed since the
copy was taken (scratchpad/proto-trim-state.json). Dry run unless --commit.

    python -X utf8 scratchpad/apply_trim_oct17.py            # diff only
    python -X utf8 scratchpad/apply_trim_oct17.py --commit   # back up + write
"""
import sys, os, json, datetime, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(g); g.loader.exec_module(G)
G._load_server_env("training-tracker")
c = importlib.util.spec_from_file_location("ttc", os.path.join(ROOT, "mcp-coach", "server.py"))
C = importlib.util.module_from_spec(c); c.loader.exec_module(C)

COMMIT = "--commit" in sys.argv
KEYS = ("upper1", "upper2", "lower2", "lower1")
FIELDS = ("exercises", "warmupNote")
new = json.load(open(os.path.join(ROOT, "scratchpad", "trim_oct17_sessions.json"), encoding="utf-8"))
base = json.load(open(os.path.join(ROOT, "scratchpad", "proto-trim-state.json"), encoding="utf-8"))["program"]["sessions"]

def diff(live):
    S = live["program"]["sessions"]
    for k in KEYS:
        for f in FIELDS:
            if S[k].get(f) != base[k].get(f):
                sys.exit("!! %s.%s changed on live since the copy was taken - stopping, nothing written." % (S[k]["name"], f))
    lines = []
    for k in KEYS:
        a, b = S[k], new[k]
        an = {e["name"]: e for e in a["exercises"]}; bn = {e["name"]: e for e in b["exercises"]}
        out = []
        out += ["  - %s" % n for n in an if n not in bn]
        out += ["  + %s (%s sets)" % (n, bn[n].get("sets")) for n in bn if n not in an]
        for n, e in bn.items():
            o = an.get(n)
            if not o: continue
            for f in sorted(set(o) | set(e)):
                if o.get(f, "") != e.get(f, ""):
                    out.append("  ~ %s .%s: %r -> %r" % (n, f, o.get(f), e.get(f)))
        if a.get("warmupNote") != b.get("warmupNote"):
            ol = set((a.get("warmupNote") or "").splitlines())
            out += ["  warm-up drops: %s" % l.strip() for l in ol - set(b["warmupNote"].splitlines())]
        if [x["name"] for x in a["exercises"] if x["name"] in bn] != [x for x in bn if x in an]:
            out.append("  order changed")
        lines.append("%s (%s)\n%s" % (a["name"], a.get("day"), "\n".join(out) or "  no change"))
        lines.append("  now: " + ", ".join("%s %s" % (e["name"], e.get("sets")) for e in b["exercises"]))
    return "\n".join(lines)

live, *_ = C._github_read_with_sha()
print(diff(live))
if not COMMIT:
    print("\nDRY RUN - nothing written. Re-run with --commit.")
    sys.exit(0)

stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
json.dump(live, open(os.path.join(ROOT, "scratchpad", "data-backup-%s.json" % stamp), "w", encoding="utf-8"), indent=1)
print("\nbacked up -> data-backup-%s.json" % stamp)

def mutate(data):
    diff(data)  # re-checks live hasn't moved, on every retry
    S = data["program"]["sessions"]
    for k in KEYS:
        for f in FIELDS:
            S[k][f] = new[k][f]
    data["program"]["updatedAt"] = C._now_iso()
    return True

C._github_update(mutate, "Program trim 17 Oct: B-day exercises moved to A days, sets and warm-ups trimmed")
print("written")
