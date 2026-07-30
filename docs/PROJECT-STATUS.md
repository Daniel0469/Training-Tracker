# Training Tracker — project status & handoff

**Read this first if you're picking the project up in a new chat.** It captures everything built,
how it's set up, the decisions behind it, and what's left. Pair with `CLAUDE.md` (conventions) and
the other `docs/`.

## What it is
A workout + health tracker for up to two people sharing a device (built for Daniel & Cerys; a
fresh install starts blank and anyone can create their own account). Plain static site - HTML/CSS/
vanilla JS, data in `localStorage` (key `flLiveTracker_v1`), Chart.js from CDN, no build step.
Installable PWA, works offline. Growing into a shared health/fitness hub with Claude as coach.

## Repos
- **App:** https://github.com/Daniel0469/Training-Tracker  (this repo; deploy on GitHub Pages)
- **Sync data (private):** https://github.com/Daniel0469/Training-Data  (holds `data.json` for cloud sync)

## Status: where we are (2026-07-23)
**Live & set up:** app deployed on GitHub Pages → **https://daniel0469.github.io/Training-Tracker/**.
Cloud **sync is working** (both Daniel + Cerys → `Training-Data/data.json`). The **MCP coach is
connected** in Claude Code and is **two-way** - it reads the data and can `write_coaching` notes
that show in the app. Coaching happens in a **separate Claude Code chat** - see
`docs/coaching-prompt.md`. App development continues in the main chat.

**This session (2026-07-23):** made the app usable by someone other than Daniel/Cerys.
- **Blank-slate onboarding:** a genuinely fresh install has no accounts and no program - a
  **Create account** screen (name + colour swatch) gates the app until at least one exists; a
  second account is optional and skippable ("just me for now"). Capped at 2 accounts per device
  (not forced to 2) - a third person needs their own separate install, by design.
- **Per-account colour**, replacing the old hardcoded Daniel-navy/Cerys-purple binary: 6 preset
  swatches, applied app-wide (buttons, pills, focus rings) via a `data-color` attribute. The
  picker disables/greys out whichever colour the other account already has, so two accounts can't
  end up visually identical.
- **Delete this account** (Settings) frees a slot; logged history stays under the old name rather
  than being erased (same philosophy as renaming).
- **Session sharing:** a Share button sends a session's exercise list (no personal numbers) via
  the phone's native share sheet as a paste-able code; Import shared session adds it to another
  install's program. Closed a related gap: Program previously had no way to create a brand-new
  session at all, only edit existing ones (**+ Add session** now exists).
- **Manual muscle tagging** on exercises (a "Works" picker), for names the auto-guess misses.
- **Fixed a pre-existing bug:** Export/Import/Coach-brief were fully implemented in JS but had no
  buttons anywhere in the UI - unreachable until this session.
- **Fixed a dark-mode contrast bug:** the toast notification was white text on a near-white
  background in dark mode (used `--ink`, which flips between themes, as a background).
- **Settings** gained a **"What's not set up yet"** panel (cloud sync live-checked, Garmin
  auto-import, AI coaching - none of it is code-gated per account, all laptop-side setup) and a
  30-day stale-export reminder + `navigator.storage.persist()` request for local-only users.
- **Fixed the exercise-name dropdown being empty for any account with no history yet** - it only
  ever sourced suggestions from the current program + logged history, so a brand-new blank account
  had nothing to pick from. Seeded with a `COMMON_EXERCISES` list (48 common lifts/movements).
- Planned and delivered three items from the "Next up" roadmap below: **rename-warning**, **RPE
  per set**, and **superset/circuit grouping** (see the roadmap section for what shipped).
- `CACHE_NAME` is now `tt-v68`.

**Backlog session (2026-07-28)** — six in-app suggestions cleared, all deployed:
- **Log form no longer loses entries.** A sync landing mid-workout re-rendered the form without
  capturing it (that's the "adding a suggestion resets the workout entries" report), and drafts were
  memory-only so a phone discarding the page reloaded into an empty form (the "cleared randomly"
  one). Drafts + timers now persist (see the file map) and every re-render path captures first.
- **Number pad on every numeric column** (`colInputMode`), not just lifting ones — lunges'
  *Distance (m)* used to pop the text keyboard. *Time*/*Pace*/*Notes* deliberately still don't.
- **🔧 machine settings are shown on the exercise** when set, instead of only after tapping.
- **Per-session 🔥 warm-up / 🧊 cool-down notes** (`session.warmupNote`/`cooldownNote`), written in
  the Program editor, shown as cards either side of the exercises on Log, included in a shared
  session.
- Then, after Daniel picked between the options: **➕ Add an exercise for today** (Tom's suggestion -
  add rather than swap) and **per-exercise load types** so bodyweight and assisted movements score
  by what they actually load. Both shipped the same day — see "Build order remaining" items 7 & 8.
  `CACHE_NAME` is now `tt-v82`.

**Warm-up/cool-down rollout + program sync (2026-07-29):**
- **The program now syncs** (`saveProgram()` stamps `program.updatedAt` and pushes immediately;
  `mergeInData` adopts the store's copy only when it's newer, and never mid-workout while a draft
  is open). Before this a sync only ever *pushed* the program, so each phone kept a drifting copy
  and the store held whichever synced last. Devices with no sync configured are unaffected, so
  separate installs (Tom's, with his own program) cannot be reached by it. `CACHE_NAME` → tt-v83.
- **Daniel & Cerys's real program updated in the store** from the warm-up/cool-down document:
  `warmupNote`/`cooldownNote` on all six sessions (Tuesday's rest/mobility day deliberately left
  out of the app), the document's ramp sets on Leg press / Squat / Bench press, and the adductor
  traffic-light + red-flag block on both lower days. Cerys's PAILs/RAILs and hip-flexor-stretch
  exclusions are written inline in the shared notes (notes are per session, not per person).
- **Exercise names tidied, in the program and in past logs** (agreed pair by pair with Daniel):
  Calf raise → Standing calf raise, Seated row → Seated cable row, triceps ext → Triceps pushdown,
  Russian Twists → Russian twists (+ its `Kg`/`reps` columns), Incline bench → Incline bench press
  (kept separate from Incline DB press). **Flat press (DB) deliberately NOT merged into Bench
  press** - it's a genuine dumbbell→barbell switch, so merging would put dumbbell loads under a
  barbell PR. Treadmill intervals columns settled on `Hard/Easy speed (km/h)`, and Cerys's 01/07
  row (entered the columns the wrong way round) corrected to 10/6 on Daniel's instruction.
- The one-off script is `scratchpad/apply_program.py` (idempotent, writes a data.json backup first).
- **`Pull-ups (assisted to weighted)` is now `load:"assist"`** with columns `Assist (kg)` / `Reps` -
  0 typed means that person's full bodyweight, anything typed is help coming off. Matches every set
  already logged (Daniel 4.5 → 0, Cerys 36 → 32, both progressing downward), and the entries are
  stamped so they keep scoring that way. Daniel's best correctly flipped to **78.4 kg unassisted**
  (2026-07-13) instead of the 4.5 kg-assisted set. **Cerys's does not score yet - she has no
  bodyweight on record at all** (no weigh-ins, blank in Settings), so `setLoad` falls back to the
  typed number and her best still reads 36 kg. Verified it self-corrects the moment she records
  one. Script: `scratchpad/apply_pullups.py`.
- **Program tab sessions collapse** (one row each: name, day, exercise count; `openSessions` in
  memory, all closed on reload). `CACHE_NAME` → tt-v84.

**Backlog batch 29 Jul, cleared 2026-07-30** (`docs/BACKLOG.md` sections A, B, C - **D still open**):
- **RPE now covers running**, not just lifting: the gate widened to
  `isLifting(ex) || isGarminCardio(ex)`, which picks up Treadmill intervals and Easy run (Zone 2)
  and skips the `Min`/`Notes` warm-up and cool-down rows. All the RPE plumbing was already
  type-agnostic. `tt-v86`.
- **The goals box grows to fit** (in-app suggestion `1785353252857`). It was the `#pGoals` textarea
  in the gear menu, not the display - reuses the existing `autoGrow()` helper. `tt-v87`.
- **`DEFAULT_PROGRAM` deleted (429 lines) and "Reset program to default" became "Clear program".**
  The hardcoded default had drifted months behind the real program and, since it was only reachable
  from Reset, its only remaining effect would have been destructive: `saveProgram()` stamps a fresh
  `updatedAt` and pushes, so `mergeInData` on the other phone would have adopted the stale copy.
  There is now **no default program at all** - a fresh install starts blank (as it already did) and
  Clear program empties it, after downloading a backup and asking for `RESET` to be typed.
  `exportData()` returns success/failure so a blocked download aborts the clear. `tt-v88`.
- **Home's "last run" card split into 🏃 last Zone 2 run + ⚡ last intervals.** The combined card
  keyed on `isRunning()` (distance + time columns), so the treadmill interval sessions - logged as
  speeds - **could never appear on Home at all**, Garmin HR and all. Classified by exercise shape,
  not session name: `isIntervalEntry()` resolves a logged entry back to its program definition by
  name to read `garminRun` (logged entries don't carry that flag), the same fallback `loadTypeOf()`
  uses. Both cards show best pace / best speed, avg **and max** HR, and the zone bar. Duration now
  prefers Garmin's `moving_time` over the session timer - the timer covers the whole gym session, so
  a cardio+core day read 1:12:33 beside an 18:31 zone bar. That also makes Cerys's 26 Jul card show
  Garmin's 4:26 rather than the stored 48s (see the duration item in `docs/BACKLOG.md`). `tt-v89`.
- **Cardio: Speed + Core warm-up/cool-down edits** from the 29 Jul session feedback, applied to the
  live store (`scratchpad/apply_cardiospeed.py`, idempotent, backs up `data.json` first). Worth
  knowing for next time: **the mobility work is `warmupNote`/`cooldownNote` free text, not
  exercises**, so all nine were text edits to two blocks. Scoped to that one session on Daniel's
  instruction - hip CARs, 90/90s and the closing breaths line appear in all six warm-ups/cool-downs
  and the other five were left alone.

Done and committed previously: the original handoff backlog, backlog **item 3**, **Phase 1** (hub +
coaching foundation) and **Phase 2** (analysis features). **Phase 3 nice-to-haves (rest timer,
kg/lb toggle, Hevy CSV, plate calc) are explicitly NOT wanted** - don't resurrect these.

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
  cost) AND `write_coaching(person, overall, by_exercise, by_session)` lets Claude push notes back →
  shown as purple 🧠 Coach cards on Home + Log: a **per-session** focus note (`by_session`, keyed by
  session name), an optional general `overall`, and a **per-exercise next-step** cue (`by_exercise`)
  on each exercise. (Replaced the old auto-generated per-exercise plan.) Every write is also appended
  to a **coaching history** (`coachingLog`, synced): the app shows it as a collapsible **🧠 Coaching
  history** on Home, and the coach reads it back via the **`coaching_history(person)`** tool to track
  whether past advice was followed and the numbers improved. Coaching-chat starter prompt:
  `docs/coaching-prompt.md`. **`by_session` + `coaching_history` need a Claude Code restart to load.**

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
  `muscleColor`/`paintMuscleMap`. `formDrafts` + `sessionTimers` (the in-progress log form) persist
  to their own localStorage key `flLiveTracker_v1_drafts` via `loadDrafts`/`saveDrafts`, expiring
  after 12h — deliberately **not** part of the export/sync payload.
- `sw.js` — service worker (cache-first shell + Chart.js). **Bump `CACHE_NAME` (tt-vN) on ANY
  change to a cached file.** Currently `tt-v89`.
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

### Automation to-do (on the plan)
The two "make it hands-free" jobs:
1. **Garmin auto-schedule (Daniel):** ✅ **DONE — Windows Task Scheduler task "TT Garmin sync
   (Daniel)" is live** (runs `python mcp-garmin/server.py --sync training-garmin`; verified,
   LastResult 0). **Free.** Cadence: **hourly all day Wed + Sat, and hourly 00:00–05:00 Thu + Sun**
   (the 05:00 cutoff matches the app's ~5am training-day rollover, so a cardio session that spills
   past midnight is still caught). Matcher uses the same 5am window, so an after-midnight Garmin run
   links to the prior day's session. Runs only while the laptop is on. Manage it in Task Scheduler
   or with `schtasks /Delete /TN "TT Garmin sync (Daniel)" /F`. **Cerys: Garmin fully set up DONE**
   (2026-07-19). Session cached at `~/.garminconnect-cerys` via
   `python server.py --login training-garmin-cerys` (verified it read a recent activity), **and the
   Task Scheduler job "TT Garmin sync (Cerys)" is live** — an exact clone of Daniel's (hourly Wed/Sat
   all day + Thu/Sun 00:00–05:00), running `--sync training-garmin-cerys`; verified with a manual run
   (`ok:true`, nothing pending). Remove with `schtasks /Delete /TN "TT Garmin sync (Cerys)" /F`. Both
   people are now on the hands-free Garmin auto-link.
   NB: signing in took several tries — Garmin **429-rate-limits** repeated `--login` attempts; what
   unblocked it was Cerys logging into connect.garmin.com in a browser on the laptop (cleared a
   verification challenge) plus fixing a library-API break — see `mcp-garmin/README.md`
   → *Troubleshooting sign-in*.
2. **Hands-free coaching:** weekly **GitHub Action** calling the Anthropic API to write coaching,
   instead of pasting the prompt weekly. **~£0.30–1/month** (Sonnet 5 vs Opus 4.8; a scheduled job
   can't use the subscription). Turn on once the coaching quality feels calibrated — it pushes
   coaching to the phones without Daniel reviewing it first.

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
2. **Hub:** ~~home **dashboard**~~ ✅ → **nutrition** (protein/calorie + targets) → **sleep/wellness
   check-in** → **auto weekly review**.
   - **Nutrition now has a planned data source:** a separate **Home Hub** app (plants/chores/climate,
     home server) will capture meals by barcode/camera and write them to the shared `data.json`;
     this app displays them and feeds them to the coach. Contract + tracker-side work in
     `docs/home-hub-link.md`. Nothing built yet.
   - **Home dashboard — ✅ built.** New **Home** tab (`renderHome`), now the app's default landing.
     Per active person: greeting + today's session (with a **Log it** shortcut), 🧠 Coach card,
     stat tiles (sessions + volume this week, latest bodyweight with trend arrow, total sessions),
     last session (with 🥇 + Garmin status), last run (km/time/HR), a bodyweight-trend mini-chart,
     and goals. Reuses existing helpers; arrows jump to History/Body. Verified light+dark, nav works,
     no console errors. `.tile`/`.tiles` CSS themed via vars. `CACHE_NAME` → tt-v31; Guide updated.
   - **Scale input via phone screenshot (come back to when building the hub):** Daniel logs
     bodyweight by taking a **screenshot of his scale app on the phone**. Add an in-app flow to
     input a bodyweight (and later other body metrics) **from a screenshot on the phone** — e.g. a
     "read from screenshot" button on the Body tab that lets him attach/paste the scale screenshot
     and pulls the number out, rather than typing it. (Today's path is pasting the screenshot into
     Claude's vision; the hub goal is to do it in-app on the phone. Keep it dependency-light — see
     the scale decision below re: no heavy in-app OCR.)

## Next up (agreed with Daniel, 2026-07-23)

Prioritised, scoped and sequenced by asking Daniel through each candidate area and each open design
fork, rather than assuming. **Nothing here is started yet** - this is the plan, not a build log.

**Parked for later - still wanted, just not this round** (not "no," just "not yet" - come back to
these): sleep/wellness check-in, auto weekly review, hands-free coaching (still deliberately held
off - human reviews coaching first), starter program templates at account creation (stays blank,
per the earlier decision - not reopened), injury/niggle log, colour-collision check on import,
real PWA icons, CSV export of raw log data, History search by exercise name, streak/consistency
tracker, accessibility pass, progress photos (`localStorage` doesn't scale to image blobs - would
need IndexedDB or cloud-only storage), multi-week periodization/mesocycles (the most open-ended
item considered).

**Design principle across the health-feature items below:** make them **opt-in per person**, not
forced on every account - a settings toggle per account for which of these are tracked/shown.

### Build order (effort-sized: S/M/L)
1. ✅ **[S] DONE - Warn before a plain rename orphans history.** Confirm before an existing
   account's name changes, matching the Delete-account warning; a first-time name (new account)
   still saves with no prompt.
2. ✅ **[S-M] DONE - RPE per set**, reusing the existing 1-10 scale (not a separate powerlifting-
   style 6-10 half-step scale) - a per-set input, lifting exercises only, stored as a sparse
   `entry.rpe` array, shown in History, carried through drafts.
3. **[M] Body measurements beyond weight** - folds into the existing **Body tab**, not a new top-
   level tab. New `state.measurements` entries (person, date, type, value) alongside the existing
   `state.bodyweights`; a type selector (waist/chest/arms/etc.) and a trend chart per type,
   mirroring the bodyweight chart pattern. No dependencies.
4. **[M-L] Nutrition UI** - also folds into the **Body tab**. Daily kcal/protein targets per
   person (alongside the existing goals), a manual add/edit entry form (description + kcal +
   protein, optional carbs/fat - matching the `meals` contract already defined for the Home Hub
   link), and today's totals + a weekly trend chart. Data plumbing (`state.meals`, merge-by-id)
   already exists (`docs/home-hub-link.md` item 2) - this is purely the missing display layer.
   Works standalone whether or not the Home Hub ever gets built.
5. **[S] Coach sees nutrition** - a `nutrition(person, days)` MCP tool + a line in `coachBrief`.
   **Depends on #4.** Mention in `docs/coaching-prompt.md` so the weekly chat actually uses it.
6. ✅ **[L] DONE (scoped down) - Superset/circuit grouping.** Investigation found true round-by-
   round interleaved entry would mean rebuilding per-exercise wiring (drafts, RPE, warm-ups,
   notes, PR detection, muscle tagging) - Daniel picked the smaller, confirmed-safe scope instead:
   **visual grouping only**. Program editor gets tick-to-select + "Group as superset"
   (`groupId` field, `exerciseBlocks()` contiguous-run helper, group-aware `move()`); the Log form
   wraps a grouped run's already-unmodified per-exercise cards in a bordered `.superset` block.
   Zero changes needed to `saveSession`/`captureDraft`/`restoreDraft`/`wireExCard`.
7. ✅ **[M] DONE (2026-07-28) - Add an exercise for today only.** Tom's suggestion. Daniel chose
   *add* over *swap* (adding covers it - you just leave the one you skipped blank). The existing
   exercise dialog opens in a today-only mode; the result goes into `formExtras`, persisted with
   the drafts and never into `state.program`. `logExercises()` (program exercises + today's extras)
   is what every `data-ei` on the log form indexes into, so extras get drafts, RPE, warm-ups, PR
   medals and Garmin detection for free. Dashed card + "Today only" pill, ✕ to drop it (shifts the
   draft entries), and the save popup offers **Add to program** for any that were logged.
8. ✅ **[M] DONE (2026-07-28) - Bodyweight / assisted exercises score by real load.** Per-exercise
   `load` (`"bw"` = bodyweight×`bwPct`% + typed, `"assist"` = bodyweight − typed, absent = normal),
   set in the exercise dialog, which also renames the column Added/Assist. Everything scoring-
   related goes through `setLoad()`: `bestWeightSoFar`, `personPRs`, `personRecords`, save-time
   volume + PR detection, `updateSetMedal`, the progress chart. Bodyweight is taken **as at the
   session date** (`bodyweightOn`); entries are stamped with their load type on save, and older
   unstamped ones fall back to the program definition by name, so flagging an exercise re-scores
   its history. **Saved per-session volume totals are deliberately left as logged** (Daniel's call)
   - records/PRs recompute live, History's per-session number doesn't move.
9. **[blocked] Garmin sync off the laptop** - move the scheduled `--sync` jobs onto a home
   server/Pi once the Home Hub hardware exists (`docs/home-hub-link.md` item 5), removing the
   "only runs while the laptop is on" caveat. Not pure app-code work - independent of the ordering
   above, revisit whenever the Pi is up.

## Other open items
- **Restart Claude Code** after any MCP server/`.mcp.json` change to load new tools (e.g.
  `write_coaching` + `coaching_history`, `suggestions`, `resolve_suggestion_tool`, and `garmin_*`).
- **Garmin one-time login:** run `python mcp-garmin/server.py --login` once to cache the session
  (answers MFA), then register the `training-garmin` server — see `mcp-garmin/README.md`.
- **Set goals** — **Daniel's are now set** (sub-20 5k, 100kg bench, 200kg squat, 200kg deadlift, as
  of 2026-07-30). **Cerys's are still blank**, which makes her coaching weaker.
- **Cerys has no bodyweight recorded** (0 weigh-ins, blank in Settings) — needed for her pull-up
  scoring to work at all, and for any future bodyweight/assisted exercise. One entry on the Body
  tab fixes it retrospectively, since bodyweight is looked up per session date.
- **The two cardio sessions still carry `Warm-up jog` / `Warm-up` / `Cooldown` as logged
  exercises**, which now duplicate the session's warm-up and cool-down note cards. Ask Daniel
  whether to remove them from the program (their logged history would stay).
- **1byone date mapping:** ambiguous slash dates default to D/M/Y; confirm against a real export.
- **PWA icons:** replace placeholder `icons/` with real branding when available.
- Done: code review, GitHub Pages deploy, auto-sync, MCP coach (read + write), in-app suggestions.
  **Phase 3 mini-features (rest timer, kg/lb toggle, Hevy CSV, plate calc) are NOT wanted.**

## Dev notes
- Serve any static way; a **no-cache dev server** avoids the browser HTTP/bfcache serving stale
  css/js (send `Cache-Control: no-store`; navigate to a fresh `?v=N` URL to bust bfcache).
- Verify features in-browser (light + dark, no console errors). Commit per feature. **Never add a
  `Co-Authored-By` trailer or any other AI attribution** - Daniel asked for this explicitly and had
  the existing history rewritten to remove it. (This line used to say the opposite, contradicting
  `CLAUDE.md`.)
- **Beware `\n` and `\'` inside a Bash heredoc** when scripting edits to `js/app.js`: the escapes
  get eaten and you end up with real newlines inside a JS string literal, i.e. a parse error the
  service worker will then happily cache. Use the Edit/Write tools for anything with backslashes,
  and if the app suddenly has no globals, clear the SW caches before debugging anything else.
