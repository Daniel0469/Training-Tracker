"""Prototype Option 1 locally. Pushes NOTHING.

Fetches the live store READ-ONLY (so the prototype carries the real program and
history, including the 14 September run rewrites), writes a fresh timestamped
data-backup-*.json next to this script, applies the day swap in memory, and
writes scratchpad/proto-dayswap-state.json for the browser to load into
localStorage. The shared store is never written to.

    python scratchpad/proto_dayswap.py
"""
import io, json, os, sys, urllib.request
from datetime import datetime, timezone

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

import day_swap

HERE = os.path.dirname(os.path.abspath(__file__))


def cfg():
    p = r"C:\Users\danie\Documents\TrainingTracker\.mcp.json"
    env = json.load(io.open(p, encoding="utf-8"))["mcpServers"]["training-tracker"]["env"]
    return env["TT_GITHUB_REPO"], env["TT_GITHUB_TOKEN"], env["TT_GITHUB_PATH"]


def get(url, token):
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "User-Agent": "tt-proto-dayswap",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


repo, token, path = cfg()
meta = get("https://api.github.com/repos/%s/contents/%s" % (repo, path), token)
import base64
data = json.loads(base64.b64decode(meta["content"]).decode("utf-8"))

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = os.path.join(HERE, "data-backup-%s.json" % stamp)
io.open(backup, "w", encoding="utf-8").write(json.dumps(data, indent=1))
print("fresh backup:", os.path.basename(backup), "(read-only fetch, nothing pushed)")

print("\nBEFORE:")
for d, on in day_swap.week(data["program"]):
    print("  %-10s %s" % (d, ", ".join(s.get("name") for _, s in on)))

changes = day_swap.apply_to_program(data["program"])
print("\nCHANGES:")
for c in changes:
    print("  *", c)

print("\nAFTER:")
for d, on in day_swap.week(data["program"]):
    names = []
    for k, s in on:
        who = s.get("person") or ""
        names.append("%s%s" % (s.get("name"), (" [%s]" % who) if who else ""))
    print("  %-10s %s" % (d, ", ".join(names)))

data["activePerson"] = 0
data["theme"] = data.get("theme") or "light"
out = os.path.join(HERE, "proto-dayswap-state.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(data, indent=1))
print("\nwrote", os.path.basename(out), "- load it in the browser. Nothing pushed.")
