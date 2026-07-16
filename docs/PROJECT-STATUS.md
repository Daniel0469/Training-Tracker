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
- **Coaching:** **semi-auto now** (open the coaching chat weekly, paste the prompt — free, keeps a
  human in the loop while calibrating). **Later, optional:** a weekly **GitHub Action** that calls
  the Anthropic API to write coaching — fully hands-off but **not free** (~£0.10–0.30/month).
- **Code fixes / self-improvement:** **semi-auto now** (in-app 💡 suggestions sync to the backlog;
  a dev chat reads them via the `suggestions` MCP tool, auto-applies easy fixes, consults on hard).
  **Later, optional:** a scheduled agent that opens **pull requests for Daniel to review/merge** —
  *not* auto-push to the live app. Deliberately keep a human merge gate (code deploys to both
  phones; unlike coaching text, a bad change can break the app). Also token-heavy → would bill.

## Build order remaining (each stops for review)
1. **Garmin MCP** — unofficial-login server so Claude reads runs + optional auto-import (Daniel OK'd
   storing his Garmin login locally).
2. **Hub:** home **dashboard** → **nutrition** (protein/calorie + targets) → **sleep/wellness
   check-in** → **auto weekly review**.

## Other open items
- **Restart Claude Code** after any MCP server/`.mcp.json` change to load new tools (e.g. the
  `write_coaching`, `suggestions`, `resolve_suggestion_tool` tools).
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
