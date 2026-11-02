"""Read-only: dump each session's warm-up / cool-down note verbatim."""
import base64, io, json, urllib.request
try:
    import truststore; truststore.inject_into_ssl()
except Exception:
    pass
p = r"C:\Users\danie\Documents\TrainingTracker\.mcp.json"
env = json.load(io.open(p, encoding="utf-8"))["mcpServers"]["training-tracker"]["env"]
repo, token, path = env["TT_GITHUB_REPO"], env["TT_GITHUB_TOKEN"], env["TT_GITHUB_PATH"]
url = "https://api.github.com/repos/%s/contents/%s" % (repo, path)
req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token,
    "Accept": "application/vnd.github+json", "User-Agent": "tt-probe"})
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.loads(base64.b64decode(json.load(r)["content"]).decode("utf-8"))
prog = data["program"]
print("updatedAt:", prog.get("updatedAt"))
for k in prog.get("order", []):
    s = prog["sessions"][k]
    print("\n===== %s [%s] day=%s" % (s.get("name"), k, s.get("day")))
    for f in ("warmupNote", "cooldownNote"):
        v = s.get(f) or ""
        print("-- %s (%d chars, %d lines):" % (f, len(v), v.count("\n")+1 if v else 0))
        print(v)
