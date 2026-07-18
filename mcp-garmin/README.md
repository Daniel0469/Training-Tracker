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
- `garmin_fill_pending(person)` — **link** Garmin runs to cardio sessions the app flagged as
  awaiting a run (see below). This is what the scheduled `--sync` calls; use it to fill on demand.

Then in Claude you just ask, e.g. *"Import my last run for Daniel,"* or *"Show me my runs this week
and how my pace is trending."*

## Auto-link runs to cardio sessions (hands-off)
When you save a **cardio/running** session in the app it's tagged *⌚ awaiting run…*. A scheduled
`--sync` on the laptop then finds that day's Garmin run, matches it by person + date, and adds the
extra info **onto that session** — avg/max **heart rate**, **cadence**, **elevation gain**,
**calories**, **moving time**, **aerobic training effect**, **VO₂max**, and per-km splits *if you
left them blank*. It **never overwrites** what you typed; the app shows it as a **⌚ Garmin** line in
History after the next sync (which happens automatically on open).

This is safe to run often: it only contacts Garmin when there's actually a flagged session to fill.

**Run it manually:**
```
python server.py --sync training-garmin        # Daniel (reads that server's creds from .mcp.json)
python server.py --sync training-garmin-cerys   # Cerys
```
`--sync <server-name>` pulls that server's `env` block from `.mcp.json`, so no secrets go on the
command line. It needs **`TT_PERSON`** in that env block (e.g. `"Daniel"`) to know whose sessions to
fill — add it alongside the Garmin/GitHub vars.

**Schedule it (Windows Task Scheduler)** — a light cadence is plenty since it no-ops when nothing's
pending. E.g. hourly:
```
schtasks /Create /TN "TT Garmin sync (Daniel)" /SC HOURLY ^
  /TR "\"C:\Users\danie\AppData\Local\Python\pythoncore-3.14-64\python.exe\" \"C:\Users\danie\Documents\TrainingTracker\mcp-garmin\server.py\" --sync training-garmin"
```
(Repeat with `training-garmin-cerys` for Cerys.) The task only runs while the laptop is on/awake —
that's the trade-off vs. a cloud job, and it's fine for a daily-ish catch-up.

## Setup (once, on the laptop)

### 1. Requirements
- Python 3.10+
- `python -m pip install -r mcp-garmin/requirements.txt` (installs `mcp`, `garminconnect`,
  `truststore`). Use `python -m pip`, not bare `pip`, if pip isn't on PATH.
- **SSL behind antivirus/proxy TLS inspection** (`unable to get local issuer certificate` /
  `CERTIFICATE_VERIFY_FAILED`): handled automatically on Windows — the server exports your Windows
  cert store to a PEM and points `curl_cffi` (which the Garmin login uses), `requests` and stdlib SSL
  at it. No action needed.
- **`429 — IP rate limited by Garmin`**: too many login attempts in a short window. Wait ~30–60 min
  before trying `--login` again; retrying immediately just extends the block.

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

**Already have the server in `.mcp.json`?** Pass its name and `--login` reuses that block's
email / password / `GARMIN_TOKENSTORE` — nothing to type but the MFA code, no password on the
command line:
```
python server.py --login training-garmin         # Daniel
python server.py --login training-garmin-cerys    # Cerys (writes .garminconnect-cerys)
```

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

## Two people (Daniel + Cerys)
Each Garmin account needs its **own** server instance and — importantly — its **own
`GARMIN_TOKENSTORE`**, or the two sessions overwrite each other. Add a second block with a distinct
name and token cache, e.g.:
```json
"training-garmin-cerys": {
  "command": "python",
  "args": ["C:\\Users\\danie\\Documents\\TrainingTracker\\mcp-garmin\\server.py"],
  "env": {
    "GARMIN_EMAIL": "cerys@example.com",
    "GARMIN_PASSWORD": "…",
    "GARMIN_TOKENSTORE": "C:\\Users\\danie\\.garminconnect-cerys",
    "TT_GITHUB_REPO": "Daniel0469/Training-Data",
    "TT_GITHUB_TOKEN": "github_pat_…",
    "TT_GITHUB_PATH": "data.json"
  }
}
```
With that block in `.mcp.json`, sign Cerys in once — reuses her configured creds + token store, so
you only answer her MFA code:
```
python server.py --login training-garmin-cerys
```
Then **restart Claude Code** so the `training-garmin-cerys` tools load. In Claude, name whose runs
you mean ("show **Cerys's** Garmin runs") so it picks the right server, and import with that person
(`garmin_import_run(activity_id, "Cerys")`).

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
