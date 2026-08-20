"""Write the two per-person run sessions to the shared store.

The change itself lives in `run_sessions.py` (shared with `proto_run.py`, so what
was prototyped in the browser is byte-for-byte what gets pushed):

  * adds `Run: Daniel` and `Run: Cerys`, each owned by its person, on Wednesday
  * retires `Cardio: Speed + Core` - its logged history keeps that name
  * moves `Cardio: Endurance + Core` to `Optional`, kept as the backup easy run,
    with its Zone 2 run drawing a row per km

Idempotent, backs up data.json first, and refuses to run if the program has moved
underneath it.

    python scratchpad/apply_run_sessions.py            # dry run
    python scratchpad/apply_run_sessions.py --apply    # push
"""
import base64, io, json, os, sys, urllib.request
from datetime import datetime, timezone

import run_sessions

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
EXPECTED = {"lower1", "lower2", "upper1", "upper2", "cardioSpeed", "cardioEndurance",
            "weekendRun", "runDaniel", "runCerys"}


def cfg():
    p = r"C:\Users\danie\Documents\TrainingTracker\.mcp.json"
    env = json.load(io.open(p, encoding="utf-8"))["mcpServers"]["training-tracker"]["env"]
    return env["TT_GITHUB_REPO"], env["TT_GITHUB_TOKEN"], env["TT_GITHUB_PATH"]


def api(url, token, data=None, method=None):
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "tt-apply-run-sessions",
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
    print("backup written:", backup)

    unknown = set(data["program"]["sessions"]) - EXPECTED
    if unknown:
        raise SystemExit("!! the program has sessions this script doesn't know about: %s\n"
                         "   Re-read it before pushing." % sorted(unknown))
    for who in ("Daniel", "Cerys"):
        if who not in (data.get("people") or []):
            raise SystemExit("!! %r isn't in people: %s" % (who, data.get("people")))

    changed = run_sessions.apply_to_program(data["program"])
    if not changed:
        print("\nNothing to do - the store already matches.")
        return

    print("\nchanges:")
    for c in changed:
        print("  *", c)
    print("\nthe week now reads:")
    for k in data["program"]["order"]:
        s = data["program"]["sessions"][k]
        print("   %-24s %-10s %s" % (s["name"], s.get("day"), s.get("person") or ""))

    if dry:
        print("\n(dry run - nothing pushed. Re-run with --apply)")
        return

    now = datetime.now(timezone.utc)
    data["program"]["updatedAt"] = now.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (now.microsecond // 1000)
    body = json.dumps({
        "message": "Program: a run session each, per person, with Zone 2 kept as the backup",
        "content": base64.b64encode(json.dumps(data, indent=2).encode("utf-8")).decode("ascii"),
        "sha": meta["sha"],
    }).encode("utf-8")
    api(url, token, body, "PUT")
    print("\npushed. program.updatedAt =", data["program"]["updatedAt"])
    print("Both phones pick it up on their next Sync (not mid-workout).")


main()
