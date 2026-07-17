# Training Tracker — project status & handoff

**Read this first if you're picking the project up in a new chat.** It captures everything built,
how it's set up, the decisions behind it, and what's left. Pair with `CLAUDE.md` (conventions) and
the other `docs/`.

## What it is
A two-person (Daniel & Cerys) workout + health tracker. Plain static site — HTML/CSS/vanilla JS,
data in `localStorage` (key `flLiveTracker_v1`), Chart.js from CDN, no build step. Installable PWA,
works offline. Growing into a shared health/fitness hub with Claude as coach.

## Repos
- **App:** https://github.com/Daniel0469/Training-Tracker  (this repo; deploy on GitHub Pages)
- **Sync data (private):** https://github.com/Daniel0469/Training-Data  (holds `data.json` for cloud sync)

## Status: where we are (2026-07-16)
**Live & set up:** app deployed on GitHub Pages → **https://daniel0469.github.io/Training-Tracker/**.
Cloud **sync is working** (both Daniel + Cerys → `Training-Data/data.json`; store currently has
~19 sessions across both). The **MCP coach is connected** in Claude Code (`.mcp.json` on this
laptop, gitignored; `truststore` installed for SSL) and is **two-way** — it reads the data and can
`write_coaching` notes that show in the app. Full inline **code review done**.
- ⚠️ **After the last commit, restart Claude Code once** so the MCP server picks up the new
  `write_coaching` tool. The read tools were already live.
- Coaching now happens in a **separate Claude Code chat** — see `docs/coaching-prompt.md`. App
  development continues in the main chat.

Done and committed: the original handoff backlog, all of backlog **item 3**, a batch of **additional
fixes**, **Phase 1** (hub + coaching foundation) and **Phase 2** (analysis features). **Phase 3
nice-to-haves are explicitly NOT wanted.** Next up: a **full inline code review** (then fix findings).

### Features built (high level)
- **Log:** sessions by weekday, auto date→session (training day rolls over ~5am), per-set numeric
  keypad, first-weight autofill, done-tickbox with rep-range autofill, **live PR medal**, session
  **timer**, per-person **draft** (switch person mid-entry without losing data), **% warm-ups**
  resolved to kg, per-exercise **setup notes**, **"Last" as relative time** + cross-session
  "most recent" chip, **warm-up set flag** (tap set number → excluded from volume/PRs/heatmap).
- **Cardio/running:** N-column exercises; running = Distance/Time/Pace with auto-pace + splits;
  **TCX/GPX import** (Garmin/Strava files).
- **History:** **This-week summary** (volume + muscle heatmap + weekly-volume bar chart), full
  session list, filter/expand/delete.
- **Progress:** **Records table** (current bests: weight/reps/**e1RM**/date) + exercise chart with
  a **top-weight vs Est. 1RM** metric toggle.
- **Body:** per-person **goals**, **bodyweight history** + trend chart + **scale CSV import**
  (1byone-style, auto-detects date/weight columns, lb→kg).
- **Save popup:** volume + fun comparison, PR medals, redrawn **muscle map** heatmap.
- **Program editor:** add/edit/reorder, **exercise-name library** (avoid dup spellings), Lifting/
  Running presets, optional 3rd column, setup notes, warm-up (fixed or %).
- **Theme:** dark/light toggle (persisted, follows OS default).
- **Data:** export/import (merge by id / person+date), **free GitHub cloud sync** + off-device
  backup, **Coach-brief Markdown export** (paste into Claude / Obsidian).
- **Coaching (two-way):** `mcp-coach/` MCP server exposes the data to Claude (subscription, no API
  cost) AND `write_coaching` lets Claude push notes back → shown as a purple 🧠 Coach card + per-
  exercise cues on the Log tab after a sync. Coaching-chat starter prompt: `docs/coaching-prompt.md`.

## File / architecture map
- `index.html` — markup, dialogs, PWA meta, the muscle-map SVG (class-scoped styles, cloned for the
  weekly heatmap).
- `css/styles.css` — all styling; theme via CSS vars (`--bg/--card/--card-2/--input-bg/--ink/
  --muted/--line/--brand/--brand-soft/--musc-*`).
- `js/app.js` — single module. State + migration (`load`/`save`; `state = {people, weights, goals,
  bodyweights, activePerson, program, logs, theme}`). Tabs render into `#view`: `renderLog`,
  `renderHistory`(+week summary), `renderProgress`(+records), `renderBody`, `renderEdit`,
  `renderHelp`. Key helpers: `esc`, `possessive`, `relTime`, `weekMonday`, `isLifting`, `isRunning`,
  `parseRange`, `bestWeightSoFar`/`personPRs`/`personRecords` (warm-up-aware), `epley`, `fmtRow`,
  `addBodyweight`, `importBodyweightCsv`, `parseTcx`/`parseGpx`/`importRunIntoCard`, `coachBrief`,
  cloud sync (`syncNow`/`mergeInData`/`exportPayload`/GitHub Contents API), `classifyMuscles`/
  `muscleColor`/`paintMuscleMap`. In-memory (not persisted): `formDrafts`, `sessionTimers`.
- `sw.js` — service worker (cache-first shell + Chart.js). **Bump `CACHE_NAME` (tt-vN) on ANY
  change to a cached file.** Currently `tt-v25`.
- `manifest.webmanifest`, `icons/` — PWA (icons are placeholders; TODO real branding).
- `mcp-coach/` — Python MCP coaching server (`server.py`, `README.md`, `requirements.txt`).
- `mcp-garmin/` — Python MCP Garmin server (`server.py`, `README.md`, `requirements.txt`,
  `sample-activity.json`). Reads runs from Garmin Connect + imports one into the shared store;
  maps a Garmin activity → the app's run-log shape. Same stdlib GitHub read/write as `mcp-coach`;
  `garminconnect` imported lazily so `--selftest` runs without it.
- `docs/` — `github-sync-setup.md`, `running-import.md`, `hub-and-coaching.md`, this file.
- `sample-daniel.json` / `sample-cerys.json` — **gitignored** real exports, local test fixtures only.

## Setup to switch things on (done by Daniel; I don't handle tokens)
1. **Cloud sync** — gear → Cloud sync (GitHub): repo `Daniel0469/Training-Data`, a fine-grained
   token with Contents: read & write on that repo, then **Sync now**. Repeat on Cerys's phone. See
   `docs/github-sync-setup.md`.
2. **Claude coaching** — `python -m pip install mcp`, set `TT_GITHUB_REPO=Daniel0469/Training-Data`
   + `TT_GITHUB_TOKEN` (read), add the server to Claude Desktop/Code. See `mcp-coach/README.md`.

## Decisions (so they're not relitigated)
- **File import, not Garmin/Strava APIs:** Strava's API forbids feeding data to AI; Garmin's dev
  program is on hold; self-exported files avoid both. (`docs/running-import.md`)
- **MCP coaching over automatic API calls:** MCP runs on the Claude subscription (free); automatic
  on-save API calls cost money and are not wanted.
- **GitHub-as-store for sync:** free, no server, reuses the upsert-by-id merge; token stored only on
  device, never in exports.
- **Scale (1byone):** no usable API/Bluetooth (iOS blocks web Bluetooth); its export "doesn't work"
  for Daniel → manual entry, or paste a scale **screenshot into Claude** (its vision reads the
  number) rather than adding a heavy in-app OCR dependency.
- **Data keyed by person NAME; drafts/timers in-memory.** Warm-ups stored as `entry.warmup` (row
  indices) and excluded from volume/PRs/e1RM/heatmap everywhere.

## Automation approach (decided)
Rule of thumb: **auto is fine when it's free + deterministic; keep a human gate when it bills or can
break something.**
- **Garmin run auto-import:** ✅ **fully hands-free by design, FREE** (no LLM). Event-driven: saving
  a cardio session flags it (`garminWanted`); a scheduled `python mcp-garmin/server.py --sync
  <server>` on the laptop links that day's run and the app auto-syncs on open. It's deterministic
  Python (garminconnect + GitHub), so it doesn't use Claude and costs nothing. **Only remaining
  step to make it hands-free: add the Windows Task Scheduler job(s)** — see `mcp-garmin/README.md`.
  Caveat: runs when the laptop is on (the phone can't reach Garmin itself; slight delay also helps,
  since the watch uploads a few min after you finish).
- **Coaching:** **semi-auto now** (open the coaching chat weekly, paste the prompt — free, on the
  subscription, keeps a human in the loop while calibrating). **Later, optional — fully hands-free
  costs money:** a weekly **GitHub Action** calling the Anthropic API (a scheduled job can't use the
  subscription). Est. **pennies/run, well under £1/month**: ~£0.30–0.60/mo on Sonnet 5, ~£0.50–1.00
  on Opus 4.8, weekly, depending on how much history it reads. Real tradeoff isn't the money — it
  pushes coaching to the phones **without Daniel reviewing it first** (lower stakes than code; a bad
  cue is ignorable, not app-breaking).
- **Code fixes / self-improvement:** **semi-auto now** (in-app 💡 suggestions sync to the backlog;
  a dev chat reads them via the `suggestions` MCP tool, auto-applies easy fixes, consults on hard).
  **Later, optional:** a scheduled agent that opens **pull requests for Daniel to review/merge** —
  *not* auto-push to the live app. Deliberately keep a human merge gate (code deploys to both
  phones; unlike coaching text, a bad change can break the app). Also token-heavy → would bill.

### To decide (open questions Daniel raised)
- **Turn on hands-free Garmin?** Add the Task Scheduler job(s) so linking happens without running
  `--sync` by hand. Free. Just needs Daniel's go-ahead (and choosing a cadence — hourly is cheap
  since it no-ops when nothing's pending).
- **Turn on hands-free coaching?** Build the weekly paid GitHub Action (~£0.30–1/mo) vs. keep
  pasting the prompt weekly. Decide once the coaching quality feels calibrated.

## Build order remaining (each stops for review)
1. **Garmin MCP** — ✅ **built** (`mcp-garmin/`), pending Daniel's setup. Unofficial-login server
   (community `garminconnect`) so Claude reads your runs and can **import a run into the app** (it
   lands in History like any session; merges by Garmin activity id, no dupes). Reading needs only a
   Garmin login; importing also needs the `TT_GITHUB_*` store token (Contents: read+write).
   - **Auto-link on cardio days:** saving a cardio/running session tags it `garminWanted` (shown as
     *⌚ awaiting run…*). A scheduled `python server.py --sync <server>` (or the `garmin_fill_pending`
     tool) matches that day's Garmin run by person+date and **enriches the logged session** with HR,
     cadence, elevation, calories, moving time, training effect, VO₂max + per-km split HR — **never
     overwriting** entered data. Shows as a **⌚ Garmin** line in History. `--sync <server-name>`
     reads that server's creds from `.mcp.json` (needs `TT_PERSON` in its env); schedule via Windows
     Task Scheduler (it no-ops when nothing's pending, so hourly is cheap). Verified in-browser
     (linked + awaiting sessions render, light+dark, no console errors); pure mapping via `--selftest`.
   - **To switch on:** `pip install -r mcp-garmin/requirements.txt`, run `python server.py --login`
     once (handles MFA → caches the session), register the `training-garmin` server, restart Claude
     Code, then add the Task Scheduler job(s). See `mcp-garmin/README.md`. Credentials stay on the
     laptop (env + `~/.garminconnect` cache).
2. **Hub:** home **dashboard** → **nutrition** (protein/calorie + targets) → **sleep/wellness
   check-in** → **auto weekly review**.
   - **Scale input via phone screenshot (come back to when building the hub):** Daniel logs
     bodyweight by taking a **screenshot of his scale app on the phone**. Add an in-app flow to
     input a bodyweight (and later other body metrics) **from a screenshot on the phone** — e.g. a
     "read from screenshot" button on the Body tab that lets him attach/paste the scale screenshot
     and pulls the number out, rather than typing it. (Today's path is pasting the screenshot into
     Claude's vision; the hub goal is to do it in-app on the phone. Keep it dependency-light — see
     the scale decision below re: no heavy in-app OCR.)

## Other open items
- **Restart Claude Code** after any MCP server/`.mcp.json` change to load new tools (e.g. the
  `write_coaching`, `suggestions`, `resolve_suggestion_tool` tools, and the new `garmin_*` tools).
- **Garmin one-time login:** run `python mcp-garmin/server.py --login` once to cache the session
  (answers MFA), then register the `training-garmin` server — see `mcp-garmin/README.md`.
- **Set goals** for both people in the app (gear → goals) — blank makes coaching weaker.
- **1byone date mapping:** ambiguous slash dates default to D/M/Y; confirm against a real export.
- **PWA icons:** replace placeholder `icons/` with real branding when available.
- Done: code review, GitHub Pages deploy, auto-sync, MCP coach (read + write), in-app suggestions.
  **Phase 3 mini-features (rest timer, kg/lb toggle, Hevy CSV, plate calc) are NOT wanted.**

## Dev notes
- Serve any static way; a **no-cache dev server** avoids the browser HTTP/bfcache serving stale
  css/js (send `Cache-Control: no-store`; navigate to a fresh `?v=N` URL to bust bfcache).
- Verify features in-browser (light + dark, no console errors). Commit per feature; end messages
  with the Co-Authored-By trailer.
