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
- `garmin_hr_zones(person)` — refresh the configured HR zones and race predictions, and backfill
  time-in-zone / missing run entries on older links.
- `garmin_enrich_session(session_id, activity_id, person)` — link one specific run to one specific
  session by hand, for a session `fill_pending` can't reach.
- `garmin_refresh_metrics(person)` — re-read Garmin for sessions that are **already linked**, so
  they pick up fields this server didn't extract when they were first linked. Both `--sync` and
  `garmin_enrich_session` deliberately skip anything already linked (right for linking, wrong for
  adding new fields), so this is the way to backfill. Same never-overwrite merge. CLI:
  `python server.py --refresh training-garmin`.

Then in Claude you just ask, e.g. *"Import my last run for Daniel,"* or *"Show me my runs this week
and how my pace is trending."*

## What gets attached to a session
Everything below comes out of responses the server already fetches, so none of it costs extra Garmin
calls. Only keys the watch actually recorded are stored, which keeps it honest across devices —
Daniel's Forerunner 255 reports running power and ground contact time, Cerys's Vívoactive 5 reports
neither, and her sessions simply arrive without those keys rather than with zeros.

- **Heart rate** — avg, max, min, and seconds in each of the five zones.
- **Per-rep detail** (`garmin.reps`) — on **any** session Garmin segmented into repeats, each
  rep's distance, duration, average speed, pace, avg + max HR, cadence and power, plus the recovery
  that followed it (duration, average speed, and the *lowest* HR reached, from the per-second
  trace). Derived from **Garmin's own run/walk split detection**, not a threshold we picked.
  Verified against the 29 Jul sessions (6 reps for Daniel, 5 for Cerys, matching what they typed)
  and Cerys's 20 Aug 6×1min.
  **This used to fire only for sessions whose reps are typed as speeds**, so a rep session logged
  with Distance/Time columns — which is how both run sessions are built now — produced no per-rep
  data at all. It is no longer gated on the column shape.
- **Refused rather than guessed** (`garmin.reps_skipped`) — reps are *repeats*, and Garmin's run/walk
  detection finds every continuous run block, which on a mixed recording is not the same thing.
  Daniel's 20 Aug trial holds three warm-up build-ups and one 2 km effort; calling those "4 reps"
  gave a consistency of 24.7% and a fade of 0%, describing nothing that happened. When the blocks
  are too unalike to be a set, no reps are stored and the reason is.
- **Derived trend numbers** (`garmin.reps.derived`) — cardiac **drift** across the reps, average and
  best **HR recovery**, rep **consistency** and **fade**, best and average speed. Drift is only
  reported when the first and last rep were run at a similar speed; otherwise a `drift_skipped`
  reason is stored instead, because subtracting HRs across two different speeds measures someone
  slowing down, not their heart drifting.
- **Drift within one effort** (`garmin.effort_drift`) — for a sustained effort like a time trial,
  which has no reps to compare: the longest continuous run block in the activity, first half against
  second half, with the block reported back so the assumption can be checked. Same speed guard as
  above — if the halves were run at different speeds it is `drift_skipped`, not a number. Daniel's
  20 Aug 2 km: **151 → 174 bpm, +23**, where the activity-level average said 134 and covered a
  ten-minute walk.
- **Efficiency** (`garmin.efficiency`) — efficiency factor (metres per minute per bpm), taken over
  the **running blocks only** where Garmin segmented them, since a whole-activity average moves when
  someone walks more; plus watts/kg using the bodyweight already in the app as at the session date.
- **Running dynamics** — ground contact time, vertical oscillation, vertical ratio, stride length,
  step count, cadence (avg + max).
- **Running power** — average, max and normalised watts, and seconds in each power zone.
- **Load and effort** — aerobic and anaerobic training effect, the effect label, activity training
  load, moderate/vigorous intensity minutes, estimated sweat loss, calories, moving time.
- **What you told the watch** — the post-run **RPE** and **Feel** prompts, stored on the same 1-10
  scale the app uses for its own RPE so the two are comparable. They are two different answers to
  the same question, not a duplicate: the watch asks once at the end, the app asks per exercise.

Two known blanks, both expected rather than broken: **VO₂max** has never had a value for either
person, because Garmin only estimates it from outdoor GPS runs and all the recent running is on a
treadmill (the key starts appearing the day someone runs outside); and Garmin's own **training
status / load** metrics read "detraining" regardless, because five gym sessions a week never reach
the watch — they are deliberately not extracted for that reason.

### Interval speeds: what's stored vs what you typed
The typed speed stays the record, and Garmin's per-rep speeds are stored alongside it — **except**
when the interval entry was left completely blank, in which case the per-rep speeds fill it in, the
same way per-km splits already fill a blank run entry. Anything typed is never touched.

Worth knowing, because an earlier note in this repo said the opposite: treadmill speed off the wrist
is *not* uniformly 10-15% high. That figure came from the **peak** of the speed trace. The per-rep
**average** came out at 13.1 km/h against Daniel's typed 13, which is why per-rep speed is now
stored at all. Cerys's 29 Jul is the interesting counter-case — she typed 11 km/h and the watch says
12.7 average / 14.1 best — so keeping both numbers is the point.

## Auto-link runs to cardio sessions (hands-off)
When you save a **cardio/running** session in the app it's tagged *⌚ awaiting run…*. A scheduled
`--sync` on the laptop then finds that day's Garmin run, matches it by person + date, and adds the
extra info **onto that session** (the full list is above — HR and zones, per-rep interval detail,
running dynamics, power, load, your watch RPE), plus per-km splits *if you left them blank*. It
**never overwrites** what you typed; the app shows it as a **⌚ Garmin** line in History after the
next sync (which happens automatically on open).

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

## Troubleshooting sign-in
Getting `--login` through can be fiddly — from experience setting up Cerys:
- **`429 — IP rate limited by Garmin` on the mobile paths:** repeated `--login` runs (each fires
  several attempts) get the account/IP throttled. **Stop retrying** — every run resets the clock.
  Wait it out, or use a different network (phone hotspot / VPN) for a fresh IP.
- **Falls to an MFA prompt on a no-MFA account:** that's the widget fallback the library uses when
  the mobile path is blocked; there's nothing to type. What reliably cleared it: **log into
  `connect.garmin.com` in a browser on the same laptop** first — that answers Garmin's verification
  challenge, after which `--login` signs in with no prompt (the `429` lines may still show; ignore
  them once you see `Signed in.`).
- **`AttributeError: 'Garmin' object has no attribute 'garth'`:** newer `garminconnect` exposes the
  token client as `g.client`, not `g.garth`. Handled now via `_dump_session()` (saves via whichever
  exists), so keep `garminconnect` reasonably current.
- Success looks like: `Signed in. Session cached at …` followed by a real `Recent activity:` line.

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
