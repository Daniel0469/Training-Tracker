#!/usr/bin/env python3
"""One-off: drop wellness rows that hold nothing but a resting HR.

The first --wellness run stored a row for any date Garmin offered ANY number for,
which pulled in three dates where the watch was only worn for a workout. Garmin's
"resting" HR is the lowest it saw all day, so those rows read 70, 80 and 91 bpm
against the 52 measured on the one night Daniel actually wore it overnight - a
resting-HR trend drawn out of three warm-ups.

fetch_wellness_day now returns None unless sleep was recorded, so this cannot
recur; this clears what the first run already wrote. Idempotent, backs data.json up
next to itself first (that backup is gitignored - it's real training data).
"""
import truststore; truststore.inject_into_ssl()
import json, base64, os, datetime, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = json.load(open(os.path.join(ROOT, ".mcp.json")))["mcpServers"]["training-tracker"]["env"]
URL = "https://api.github.com/repos/%s/contents/%s" % (
    env["TT_GITHUB_REPO"], env.get("TT_GITHUB_PATH", "data.json"))
HDR = {"Authorization": "Bearer " + env["TT_GITHUB_TOKEN"],
       "Accept": "application/vnd.github+json", "User-Agent": "tt-fix"}

j = json.load(urllib.request.urlopen(urllib.request.Request(URL, headers=HDR), timeout=30))
data = json.loads(base64.b64decode(j["content"]))
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup = os.path.join(ROOT, "scratchpad", "data-backup-%s.json" % stamp)
json.dump(data, open(backup, "w", encoding="utf-8"), indent=1)
print("backed up to", backup)

# A row is only worth keeping if it has something that needs overnight wear.
OVERNIGHT = ("sleep_sec", "sleep_score", "readiness")
dropped = []
for person, days in (data.get("wellness") or {}).items():
    for date in sorted(days):
        if not any(k in days[date] for k in OVERNIGHT):
            dropped.append((person, date, days[date]))
for person, date, row in dropped:
    print("  dropping %s %s -> %s" % (person, date, row))
    del data["wellness"][person][date]
# Don't leave an empty person key behind.
for person in [p for p, d in (data.get("wellness") or {}).items() if not d]:
    del data["wellness"][person]
if not data.get("wellness"):
    data.pop("wellness", None)

if not dropped:
    print("nothing to drop - already clean")
    raise SystemExit(0)

body = {"message": "Drop wellness rows holding only a workout-day 'resting' HR",
        "content": base64.b64encode(json.dumps(data, indent=2).encode()).decode(),
        "sha": j["sha"]}
req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="PUT", headers=HDR)
urllib.request.urlopen(req, timeout=30)
print("wrote data.json - dropped %d row(s)" % len(dropped))
