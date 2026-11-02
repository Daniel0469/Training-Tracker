"""Read-only: dump the program's sessions/exercises so a change can be grounded
in what the store actually holds. Prints nothing personal beyond exercise names."""
import base64, io, json, os, urllib.request
try:
    import truststore; truststore.inject_into_ssl()
except Exception:
    pass

def cfg():
    p = r"C:\Users\danie\Documents\TrainingTracker\.mcp.json"
    env = json.load(io.open(p, encoding="utf-8"))["mcpServers"]["training-tracker"]["env"]
    return env["TT_GITHUB_REPO"], env["TT_GITHUB_TOKEN"], env["TT_GITHUB_PATH"]

repo, token, path = cfg()
url = "https://api.github.com/repos/%s/contents/%s" % (repo, path)
req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token,
    "Accept": "application/vnd.github+json", "User-Agent": "tt-probe"})
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.loads(base64.b64decode(json.load(r)["content"]).decode("utf-8"))

prog = data["program"]
print("order:", prog.get("order"))
print("updatedAt:", prog.get("updatedAt"))
for k in prog.get("order", []):
    s = prog["sessions"][k]
    print("\n== %s  [%s]  day=%s" % (s.get("name"), k, s.get("day")))
    for i, e in enumerate(s.get("exercises") or []):
        print("   %d. %-32s sets=%-3s target=%-12s cols=%s%s%s" % (
            i, e.get("name"), e.get("sets"), (e.get("target") or "")[:12],
            e.get("cols"),
            "  load=%s" % e["load"] if e.get("load") else "",
            "  group=%s" % e["groupId"] if e.get("groupId") else ""))
        if e.get("notes"):
            print("        notes: %s" % e["notes"].replace("\n", " | ")[:150])
        if e.get("warmup"):
            print("        warmup: %s" % e["warmup"])

# How much history is keyed to the calf raise name, and at what loads?
print("\n\n== logged history for calf-raise-ish names ==")
from collections import defaultdict
seen = defaultdict(list)
for l in data.get("logs", []):
    for e in (l.get("entries") or []):
        n = (e.get("exercise") or e.get("name") or "")
        if "calf" in n.lower() or "goblet" in n.lower() or "lunge" in n.lower():
            seen[(l.get("person"), n)].append((l.get("date"), e.get("rows") or e.get("sets")))
for (p, n), v in sorted(seen.items()):
    v.sort()
    print("  %-8s %-28s %2d logs, %s -> %s" % (p, n, len(v), v[0][0], v[-1][0]))
    print("        last rows: %s" % (v[-1][1],))
