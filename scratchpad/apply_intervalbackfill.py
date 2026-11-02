"""Backfill garmin.intervals onto interval sessions that were linked before
detect_intervals existed.

The Garmin sync only enriches sessions still flagged garminWanted, and
garmin_enrich_session refuses one that already has a linked run, so neither can
reach an already-linked session. This adds the derived rep structure - and
nothing else - to any interval-shaped session that has a Garmin activity but no
`intervals` yet.

"Interval-shaped" means: linked to Garmin, and with no distance+time run entry.
A steady Zone 2 run has no structure to recover and detect_intervals returns
None for one anyway.

Reads each person's Garmin credentials from .mcp.json, the same way
`server.py --sync <name>` does. Idempotent, backs data.json up first, and only
ever ADDS a key - it never edits what was typed, the splits, or anything else on
the session.

    python scratchpad/apply_intervalbackfill.py            # dry run
    python scratchpad/apply_intervalbackfill.py --apply    # push
"""
import base64
import io
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "mcp-garmin"))

import server  # noqa: E402  - also brings truststore + the CA-bundle fix


def mcp_env():
    p = os.path.join(REPO, ".mcp.json")
    servers = json.load(io.open(p, encoding="utf-8"))["mcpServers"]
    out = {}
    for name, cfg in servers.items():
        env = cfg.get("env") or {}
        if env.get("TT_PERSON") and env.get("GARMIN_TOKENSTORE"):
            out[env["TT_PERSON"]] = env
    return out


def cfg():
    p = os.path.join(REPO, ".mcp.json")
    env = json.load(io.open(p, encoding="utf-8"))["mcpServers"]["training-tracker"]["env"]
    return env["TT_GITHUB_REPO"], env["TT_GITHUB_TOKEN"], env["TT_GITHUB_PATH"]


def api(url, token, data=None, method=None):
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "tt-apply-intervalbackfill",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def is_interval_session(log):
    if not log.get("garminActivityId"):
        return False
    for e in (log.get("entries") or []):
        if server._is_run_entry(e):
            return False          # a real distance+time run, not reps
    return True


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

    envs = mcp_env()
    changed = 0
    skipped = 0

    for log in data.get("logs", []):
        if not log or not is_interval_session(log):
            continue
        person = log.get("person")
        g = log.get("garmin") or {}
        if g.get("intervals"):
            print("  [already] %-7s %s  %s" % (person, log.get("date"), log.get("sessionName")))
            skipped += 1
            continue
        env = envs.get(person)
        if not env:
            print("  [skip]    %-7s %s  no Garmin server configured" % (person, log.get("date")))
            continue

        # Each person has their own cached Garmin session; force a fresh client.
        server._client = None
        os.environ["GARMIN_TOKENSTORE"] = env["GARMIN_TOKENSTORE"]
        os.environ["GARMIN_EMAIL"] = env.get("GARMIN_EMAIL", "")
        os.environ["GARMIN_PASSWORD"] = env.get("GARMIN_PASSWORD", "")

        aid = log["garminActivityId"]
        series = server.fetch_detail_series(aid)
        iv = server.detect_intervals(series)
        if not iv:
            print("  [none]    %-7s %s  %s  (%d samples, no rep structure)"
                  % (person, log.get("date"), log.get("sessionName"), len(series)))
            continue
        print("  [add]     %-7s %s  %s" % (person, log.get("date"), log.get("sessionName")))
        print("            %d reps %s, recoveries %s"
              % (iv["reps"], iv["rep_secs"], iv["recovery_secs"]))
        log.setdefault("garmin", {})["intervals"] = iv
        changed += 1

    print("\n%d to add, %d already had one." % (changed, skipped))
    if not changed:
        print("Nothing to do.")
        return
    if dry:
        print("\nDry run. Re-run with --apply to push.")
        return

    body = json.dumps({
        "message": "Backfill derived interval structure onto past cardio sessions",
        "content": base64.b64encode(json.dumps(data).encode("utf-8")).decode("ascii"),
        "sha": meta["sha"],
    }).encode("utf-8")
    api(url, token, data=body, method="PUT")
    print("\nPushed.")


if __name__ == "__main__":
    main()
