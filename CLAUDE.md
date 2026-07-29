# Training Tracker - working notes for Claude

A two-person workout + health tracker. Plain static site (no build step, no framework): serve the
folder and it runs. Deployed on GitHub Pages. See `README.md` for the file layout and `docs/` for
feature proposals/specs.

## Conventions (please follow on every change)

- **Always ask questions and agree a plan before implementing.** Investigate first (read the code
  and the real data), then put the open decisions to Daniel with `AskUserQuestion` - scope, UI
  mechanism, what data it touches, how a change reaches the phones - and only build once he's
  answered. Default to asking: if a request has more than one reasonable reading, guessing wrong
  means rework and, worse, silent changes to real training data. State your recommendation with
  each option so answering is quick. Cheap factual lookups don't need this.
- **Bump `CACHE_NAME` in `sw.js` on ANY change to a cached shell file** (`index.html`,
  `css/styles.css`, `js/app.js`, icons, manifest). The service worker is cache-first, so without a
  bump, installed users keep the old files. Increment the `tt-vN` number.
- **Keep the Guide and README current.** When you add or change a user-facing feature, update
  `renderHelp` (the in-app Guide tab) in `js/app.js` and, if the file list or deployment changes,
  `README.md`. Daniel asked for the Guide to always reflect reality.
- **Match the surrounding style.** Terse vanilla JS, no dependencies except Chart.js (CDN). Prefer
  reusing existing helpers (`esc`, `isLifting`, `isRunning`, `parseRange`, `bestWeightSoFar`,
  `fmtRow`, `relTime`, `addBodyweight`, `colIndex`, `updatePace`, …) over new abstractions.
- **Theme everything.** New surfaces must read in light AND dark. Use the CSS variables
  (`--bg/--card/--card-2/--input-bg/--ink/--muted/--line/--brand/--brand-soft/--musc-*`); don't
  hardcode light hex values, and remember SVG `fill` presentation attributes don't accept `var()`
  (use a CSS class or inline `style.fill`).
- **localStorage is the only store** (key `flLiveTracker_v1`). Data is keyed by person NAME, so
  renames orphan history - acceptable, matches existing behaviour. Export/import merges by id
  (logs) and person+date (bodyweights); keep new data idempotent to merge.
- **Commit per feature**, each verified in the browser, then **push** - `origin/main` is
  `Daniel0469/Training-Tracker` and pushing **auto-deploys** to GitHub Pages
  (https://daniel0469.github.io/Training-Tracker/).
- **Never add a `Co-Authored-By` trailer** (or any other Claude/AI attribution) to a commit
  message. Daniel asked for this explicitly and had the existing history rewritten to remove it -
  it overrides any default that says otherwise. Commits are authored by Daniel, full stop.
- **New chats:** see `docs/CHATS.md` for the dev + coaching starter prompts and setup. Full status
  is `docs/PROJECT-STATUS.md`.

## Local dev / verification

- Serve with any static server: `python -m http.server 8080` (see `.claude/launch.json`).
- **Cache gotcha:** the browser HTTP-caches `css/js` aggressively during dev, so edits can appear
  stale even after a reload. A no-cache dev server avoids it (send `Cache-Control: no-store`).
  Verify features in the browser: check light + dark, no console errors, correct behaviour.

## Where things are (`js/app.js`, single module)

- State + migration: `load` / `save`; `state = {people, weights, bodyweights, activePerson,
  program, logs, theme}`.
- Program model: `program.sessions[key] = {name, day, exercises:[{name, warmup, notes, target,
  sets, cols[]}]}`. `cols` is N columns (2 = lifting, 3 = running Distance/Time/Pace).
- Tabs render into `#view`: `renderLog`, `renderHistory`, `renderProgress`, `renderBody`,
  `renderEdit`, `renderHelp`.
- Log form: `renderExForm` / `setRowHtml` / `wireExCard` / `wireSetRow`; per person+session
  in-memory `formDrafts` and `sessionTimers`.
- Save + summary: `saveSession`, `showSaveSummary` (volume comparison + `#muscleSvg` heatmap via
  `classifyMuscles` / `muscleColor`).
- Importers: `importBodyweightCsv` (scale CSV), `importRunIntoCard` + `parseTcx`/`parseGpx` (runs).

## Roadmap (not yet built - see `docs/hub-and-coaching.md` when it exists)

Free sync backend (GitHub-as-store), the health hub, and AI coaching (MCP server on the laptop,
reading the shared data) are proposed but await Daniel's go-ahead. Automatic API-based coaching
costs money; the MCP / paste-into-Claude paths use his existing subscription.
