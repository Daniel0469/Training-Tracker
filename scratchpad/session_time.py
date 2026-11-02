"""Extrapolate full session length from past logs. Read-only.  python -X utf8 scratchpad/session_time.py [state.json]"""
import json, sys, re
src = sys.argv[1] if len(sys.argv) > 1 else "scratchpad/proto-trim-state.json"
d = json.load(open(src, encoding="utf-8"))
P = d["program"]["sessions"]
KEYS = ("upper1", "upper2", "lower2", "lower1")
def per_leg(t): return 2 if re.search(r"each (leg|arm)", t or "", re.I) else 1
def factor(skey, name):
    for e in P[skey]["exercises"]:
        if e["name"] == name: return per_leg(e.get("target"))
    return 1
def filled(e): return [r for r in e.get("rows", []) if any(str(c).strip() for c in r)]
pts = []
for l in sorted(d["logs"], key=lambda x: x["date"]):
    k = l["sessionKey"]
    if k not in KEYS or l["date"] < "2026-09-14" or not l.get("durationSec"): continue
    done = sum(len(filled(e)) * factor(k, e["name"]) for e in l["entries"])
    plan = sum(int(e.get("sets") or 0) * per_leg(e.get("target")) for e in P[k]["exercises"])
    pts.append((k, l["date"], l["person"], l["durationSec"] / 60, done, plan))
# least squares: minutes = a + b * slots
n = len(pts); xs = [p[4] for p in pts]; ys = [p[3] for p in pts]
mx, my = sum(xs) / n, sum(ys) / n
b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs); a = my - b * mx
print("fit over %d logs: minutes = %.0f + %.2f per set-slot" % (n, a, b))
for k in KEYS:
    rows = [p for p in pts if p[0] == k]
    ext = [dur + (plan - done) * b for _, _, _, dur, done, plan in rows]
    plan = rows[0][5] if rows else 0
    print("\n%s (%d set-slots as written)  ->  ~%.0f min (fit)   ~%.0f min (avg of per-log extrapolations)" %
          (P[k]["name"], plan, a + b * plan, sum(ext) / len(ext) if ext else 0))
    for (kk, dt, who, dur, done, plan), e in zip(rows, ext):
        print("   %s %-5s took %3.0f, did %2d/%d slots -> full ~%3.0f" % (dt, who, dur, done, plan, e))
