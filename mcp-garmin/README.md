# Training Tracker — Garmin MCP server

Lets **Claude read your Garmin runs** and, when you ask, **import one into Training Tracker** so it
shows up in the app's History like any logged session. Runs locally on your laptop, on your **Claude
subscription — no API billing**.

Garmin has no official personal-data API for this, so this uses the community
[`garminconnect`](https://github.com/cyberjunky/python-garminconnect) library — the same login
Garmin's own website uses. **Your Garmin credentials stay on this laptop** (env vars + a local token
cache); they're never committed or sent anywhere but Garmin. This is the *file-import decision's*
follow-up — see `docs/running-import.md` for why we avoid the Strava/Garmin *developer* APIs.

## What it exposes
- `garmin_recent_runs(limit)` — your latest runs (date, distance, time, pace, avg HR).
- `garmin_recent_activities(limit)` — latest activities of any type.
- `garmin_activity(activity_id)` — one activity in detail, with per-split rows.
- `garmin_import_run(activity_id, person)` — **import** a run into Training Tracker for `person`
  (needs the GitHub store env vars with write access). Merges by activity id, so it's safe to run
  twice — re-importing updates rather than duplicating.

Then in Claude you just ask, e.g. *"Import my last run for Daniel,"* or *"Show me my runs this week
and how my pace is trending."*

## Setup (once, on the laptop)

### 1. Requirements
- Python 3.10+
- `python -m pip install -r mcp-garmin/requirements.txt` (installs `mcp`, `garminconnect`,
  `truststore`). Use `python -m pip`, not bare `pip`, if pip isn't on PATH. `truststore` makes SSL
  use the OS trust store — needed if antivirus/proxy TLS inspection causes `CERTIFICATE_VERIFY_FAILED`.

### 2. Sign in to Garmin once (creates the cached session)
Garmin accounts often have MFA, which can't be answered from the headless MCP server. So do an
interactive login **once** to write the token cache; after that the server signs in silently from
the cache (tokens last ~a year):
```
cd mcp-garmin
set GARMIN_EMAIL=you@example.com        &  set GARMIN_PASSWORD=...   (Windows: use `set`)
python server.py --login                 # answer the MFA code if prompted
```
This writes the session to `%USERPROFILE%\.garminconnect` (override with `GARMIN_TOKENSTORE`).
You can then clear `GARMIN_PASSWORD` — the server resumes from the cache.

Sanity-check the mapping without Garmin or a network at all:
```
python server.py --selftest sample-activity.json
```

### 3. For importing runs — point it at the shared store
Import writes into the **GitHub store** the app syncs to (the same repo as cloud sync):
- `TT_GITHUB_REPO`  — `Daniel0469/Training-Data`
- `TT_GITHUB_TOKEN` — a fine-grained token with **Contents: read AND write** on that repo
- `TT_GITHUB_PATH`  — optional, default `data.json`

Reading runs (the `garmin_*` list/detail tools) doesn't need these — only importing does.

### 4. Register it with Claude

**Claude Code** — from the repo:
```
claude mcp add training-garmin -- python mcp-garmin/server.py
```
then set the env vars for that server (`GARMIN_TOKENSTORE` if you moved it, and the `TT_GITHUB_*`
trio for import), e.g. with `claude mcp add -e KEY=value …`.

**Claude Desktop / config JSON** — add alongside the coach server:
```json
{
  "mcpServers": {
    "training-garmin": {
      "command": "python",
      "args": ["C:\\Users\\danie\\Documents\\TrainingTracker\\mcp-garmin\\server.py"],
      "env": {
        "GARMIN_TOKENSTORE": "C:\\Users\\danie\\.garminconnect",
        "TT_GITHUB_REPO": "Daniel0469/Training-Data",
        "TT_GITHUB_TOKEN": "github_pat_…",
        "TT_GITHUB_PATH": "data.json"
      }
    }
  }
}
```
**Restart Claude Code / Desktop** after adding it so the `training-garmin` tools load.

## Notes
- **Credentials never leave the laptop** and are read from the environment / token cache — don't
  commit them. `.garminconnect` and any `.mcp.json` stay off git.
- Imported runs get `sessionKey: "garmin-run"`, `source: "garmin"`, and the Garmin `activityId` as
  their log id, so cloud sync merges them by id (no duplicates). After importing, tap **Sync now**
  on the phone to pull them in.
- Runs come in as a single `Run` exercise with Distance/Time/Pace split rows (one per Garmin lap),
  matching the app's TCX/GPX importer — so they render in History and count toward the weekly view.
- Works on the laptop where you run Claude, not on the iPhone tracker (matches the split: log on the
  phone, coach/import on the laptop).
