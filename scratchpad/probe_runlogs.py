import base64, io, json, urllib.request
try:
    import truststore; truststore.inject_into_ssl()
except Exception: pass
env = json.load(io.open(r"C:\Users\danie\Documents\TrainingTracker\.mcp.json", encoding="utf-8"))["mcpServers"]["training-tracker"]["env"]
url = "https://api.github.com/repos/%s/contents/%s" % (env["TT_GITHUB_REPO"], env["TT_GITHUB_PATH"])
req = urllib.request.Request(url, headers={"Authorization": "Bearer " + env["TT_GITHUB_TOKEN"],
    "Accept": "application/vnd.github+json", "User-Agent": "tt-probe"})
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.loads(base64.b64decode(json.load(r)["content"]).decode("utf-8"))
io.open(r"C:\Users\danie\Documents\TrainingTracker\scratchpad\store.json", "w", encoding="utf-8").write(json.dumps(data, indent=1))
logs = [l for l in data.get("logs", []) if l.get("garminActivityId")]
logs.sort(key=lambda l: l.get("date") or "")
for l in logs[-8:]:
    g = l.get("garmin") or {}
    ents = [(e.get("name"), e.get("cols")) for e in (l.get("entries") or [])]
    print("%s  %-8s  %-26s act=%s" % (l.get("date"), l.get("person"), l.get("sessionName"), l.get("garminActivityId")))
    print("      garmin keys: %s" % sorted(g.keys()))
    print("      reps: %s" % (g.get("reps", {}).get("count") if isinstance(g.get("reps"), dict) else None))
    for n, c in ents:
        print("        - %-22s %s" % (n, c))
