"""Push Option 1 - the 21 September day swap - to the shared store.

Dry run by default. Re-run with --apply to push.

    python scratchpad/apply_dayswap.py            # show what would change
    python scratchpad/apply_dayswap.py --apply    # push it

The change itself lives in day_swap.py, which is also what proto_dayswap.py uses,
so what was prototyped in the browser is exactly what goes out. Days only - no
exercise, target, set or note content is touched, and nothing touches logged
history. Writes a timestamped backup of the store before pushing anything, and
refuses to run if any session is not on the day it expects.
"""
import base64, io, json, os, sys, urllib.request
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


def api(url, token, data=None, method=None):
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "tt-apply-dayswap",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    dry = "--apply" not in sys.argv
    repo, token, path = cfg()
    url = "https://api.github.com/repos/%s/contents/%s" % (repo, path)
    meta = api(url, token)
    data = json.loads(base64.b64decode(meta["content"]).decode("utf-8"))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = os.path.join(HERE, "data-backup-%s.json" % stamp)
    io.open(backup, "w", encoding="utf-8").write(json.dumps(data, indent=1))
    print("backup written:", os.path.basename(backup))

    prog = data["program"]
    changes = day_swap.apply_to_program(prog)
    moved = [c for c in changes if not c.startswith("(no change)")]
    for c in changes:
        print("  *", c)

    if not moved:
        print("\nNothing to change - already applied.")
        return

    print("\n--- the week now reads ---")
    for d, on in day_swap.week(prog):
        print("  %-10s %s" % (d, ", ".join(s.get("name") for _, s in on)))

    if dry:
        print("\nDry run. Re-run with --apply to push.")
        return

    # Stamp the program so both phones adopt it on their next sync (mergeInData
    # only takes the store's copy when its updatedAt is newer than the device's).
    prog["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    body = json.dumps({
        "message": "Program: swap the runs - quality to Monday, Zone 2 to Thursday",
        "content": base64.b64encode(json.dumps(data).encode("utf-8")).decode("ascii"),
        "sha": meta["sha"],
    }).encode("utf-8")
    api(url, token, data=body, method="PUT")
    print("\nPushed. program.updatedAt =", prog["updatedAt"])


if __name__ == "__main__":
    main()
