#!/usr/bin/env python3
"""Read-only audit: is every past run stored in a state the coach can infer from?

Pulls the live store, then for each Garmin-linked or running session reports what
is actually there and flags anything that would mislead. Writes nothing.
"""
import base64, io, json, urllib.request
try:
    import truststore; truststore.inject_into_ssl()
except Exception:
    pass

env = json.load(io.open(r"C:\Users\danie\Documents\TrainingTracker\.mcp.json",
                        encoding="utf-8"))["mcpServers"]["training-tracker"]["env"]
url = "https://api.github.com/repos/%s/contents/%s" % (env["TT_GITHUB_REPO"], env["TT_GITHUB_PATH"])
req = urllib.request.Request(url, headers={"Authorization": "Bearer " + env["TT_GITHUB_TOKEN"],
    "Accept": "application/vnd.github+json", "User-Agent": "tt-audit"})
with urllib.request.urlopen(req, timeout=30) as r:
    d = json.loads(base64.b64decode(json.load(r)["content"]).decode("utf-8"))
io.open(r"C:\Users\danie\Documents\TrainingTracker\scratchpad\store.json", "w",
        encoding="utf-8").write(json.dumps(d, indent=1))

def is_run_entry(e):
    cols = [str(c).lower() for c in (e.get("cols") or [])]
    return any("dist" in c for c in cols) and any("time" in c for c in cols)

def has_rows(e):
    return any(any(str(v).strip() for v in (row or [])) for row in (e.get("rows") or []))

logs = [l for l in d.get("logs", []) if l]
runs = []
for l in logs:
    ents = l.get("entries") or []
    if l.get("garminActivityId") or any(is_run_entry(e) for e in ents) or l.get("garminWanted"):
        runs.append(l)
runs.sort(key=lambda l: (l.get("date") or "", l.get("person") or ""))

flags = []
print("=" * 96)
print("%-11s %-7s %-26s %-11s %s" % ("DATE", "WHO", "SESSION", "GARMIN", "RUN ENTRY"))
print("=" * 96)
for l in runs:
    g = l.get("garmin") or {}
    ents = l.get("entries") or []
    run = next((e for e in ents if is_run_entry(e)), None)
    aid = l.get("garminActivityId")
    where = "linked" if aid else ("awaiting" if l.get("garminWanted") else "none")
    desc = "(no run entry)"
    if run:
        desc = "%s rows=%d %s" % (run.get("name"), len(run.get("rows") or []),
                                  "typed/filled" if has_rows(run) else "EMPTY")
    print("%-11s %-7s %-26s %-11s %s" % (l.get("date"), l.get("person"),
                                          (l.get("sessionName") or "")[:26], where, desc))
    # ---- the checks -------------------------------------------------------
    if run and not has_rows(run):
        flags.append((l, "run entry has no numbers at all - nothing to infer from"))
    if l.get("garminWanted") and not aid:
        flags.append((l, "still awaiting a Garmin link - never matched"))
    if aid and not g:
        flags.append((l, "linked to an activity but carries no garmin metrics"))
    if aid and g and not g.get("avg_hr"):
        flags.append((l, "linked but no average HR stored"))
    reps = g.get("reps")
    if isinstance(reps, dict) and reps.get("reps"):
        src = "trace" if "speed trace" in (reps.get("source") or "") else "run/walk splits"
        secs = [r.get("sec") for r in reps["reps"] if r.get("sec")]
        print("%-11s %-7s   reps=%-2s via %-16s durations=%s" % ("", "", reps.get("count"), src, secs))
        if secs and max(secs) > 2 * max(1, min(secs)):
            flags.append((l, "stored reps have wildly different lengths (%s) - may not be a rep set" % secs))
    if g.get("reps_skipped"):
        print("%-11s %-7s   reps refused: %s" % ("", "", g["reps_skipped"][:70]))
    if g.get("effort_drift"):
        ed = g["effort_drift"]
        print("%-11s %-7s   effort_drift=%s over %ss" % ("", "", ed.get("drift_bpm"), ed.get("effort_sec")))
    # typed speed vs what the watch measured, where both exist
    if reps and isinstance(reps, dict) and reps.get("reps"):
        iv = next((e for e in ents if e.get("cols") and
                   any("km/h" in str(c).lower() for c in e["cols"])), None)
        if iv and has_rows(iv):
            typed = [row[0] for row in (iv.get("rows") or []) if row and str(row[0]).strip()]
            meas = [r.get("kmh") for r in reps["reps"] if r.get("kmh")]
            if typed and meas:
                print("%-11s %-7s   typed speeds=%s   watch=%s" % ("", "", typed, meas))

print("\n" + "=" * 96)
print("FLAGS (%d)" % len(flags))
print("=" * 96)
for l, why in flags:
    print("  %s  %-7s %-26s %s" % (l.get("date"), l.get("person"),
                                    (l.get("sessionName") or "")[:26], why))

# ---- duplicates: same person + date + session -----------------------------
seen = {}
for l in logs:
    k = (l.get("person"), l.get("date"), l.get("sessionKey"))
    seen.setdefault(k, []).append(l)
dupes = {k: v for k, v in seen.items() if len(v) > 1}
print("\nDUPLICATE person+date+session groups: %d" % len(dupes))
for k, v in dupes.items():
    print("   %s x%d  ids=%s" % (k, len(v), [x.get("id") for x in v]))
print("\ndeletedLogs tombstones: %d" % len(d.get("deletedLogs") or []))
