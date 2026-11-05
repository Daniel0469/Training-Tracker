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
- **Prototype before pushing.** Once the plan is agreed, build it locally and *show* it -
  screenshots of the real app, both people, both themes - and let Daniel change whatever he
  wants before anything is committed or pushed. Prototype against a COPY of the store, never
  the live one (`scratchpad/proto_run.py` is the pattern: newest `data-backup-*.json` in,
  local state file out, shared store never opened). Pushing auto-deploys to both phones and
  writes real training data, so the review has to happen while it's still free.
- **Bump `VERSION` in `sw.js` on ANY change to a cached shell file** (`index.html`,
  `css/styles.css`, `js/app.js`, icons, manifest). The service worker is cache-first, so without a
  bump, installed users keep the old files. `CACHE_NAME` is `"tt-" + VERSION`, and Settings shows
  the version. Versions have three numbers: a fix bumps the last (2.0.1), a new feature the middle (2.1.0).
- **Keep the Guide, README and the starter prompts current.** When you add or change a user-facing
  feature - or when anything is decided that a future chat would act on - update the prompt that
  owns it in `docs/prompts/` (`dev.md`, `coaching.md`, `running.md`). Daniel asked for this
  explicitly: a prompt describing a week, a tool or a convention that no longer exists is worse than
  no prompt, because a fresh chat has no other context and acts on it confidently. Same for
  `renderHelp` (the in-app Guide tab) in `js/app.js` and, if the file list or deployment changes,
  `README.md`. Daniel asked for the Guide to always reflect reality.
- **Match the surrounding style.** Terse vanilla JS, no dependencies except Chart.js (CDN). Prefer
  reusing existing helpers (`esc`, `isLifting`, `isRunning`, `parseRange`, `bestWeightSoFar`,
  `fmtRow`, `relTime`, `addBodyweight`, `colIndex`, `updatePace`, …) over new abstractions.
- **Plain punctuation and case** (same rule as the Home Hub, Daniel 22 Oct 2026). No em dashes
  anywhere - code, comments, UI text, docs or commit messages; use a hyphen, a comma or a new
  sentence. No all-caps words for emphasis (NOT, BOTH, NEVER) in comments or UI text; say it
  plainly. Acronyms and labels that are caps by design are fine.
- **Two people, one phone. Every feature, no exceptions.** Daniel and Cerys train together off one
  handset and swap the person toggle *between sets*, so any per-person state must be **keyed by
  person** (`draftKey()` = person+session, the key `formDrafts` / `sessionTimers` / `formExtras`
  already use) and any surface that shows it must re-read on the switch - `renderView()` runs on
  every person change, so hang it there rather than asking each caller to remember. Both people's
  state runs **at the same time**: switching away must never stop, reset or leak the other person's.
  A plain module-level global is the trap - the rest stopwatch shipped as one on 7 Sep and showed
  Cerys Daniel's rest, still counting, the moment he handed her the phone. **Verify it the way it
  breaks:** start the thing as one person, switch, act as the other, switch back, and check the
  first person's is untouched. Daniel stated this as a standard on 14 Sep - it applies to features
  not yet built, not just the ones that have already been caught.
- **An edit to `mcp-*/server.py` does NOT reach the running server.** Those processes load the file
  once at startup and hold it, so after changing one the *tool* still runs the old code - and it
  reports success while doing the old thing, which is the dangerous part. This has bitten twice:
  `garmin_refresh_metrics` wrote the pre-fix rep data back over the corrected store (7 Sep), and a
  coaching chat read an empty history and wrote its notes into the old location (14 Sep). **Never
  conclude a server-side fix worked from the tool's own output** - verify by reading the store from
  a fresh process (`scratchpad/run_refresh.py` is the pattern: import the server module, call the
  same function, diff the result). Claude Code has to be restarted before any MCP change takes
  effect, and until it is, say so rather than letting a chat act on stale output.
- **Theme everything.** New surfaces must read in light AND dark. Use the CSS variables
  (`--bg/--card/--card-2/--input-bg/--ink/--muted/--line/--brand/--brand-soft/--musc-*`); don't
  hardcode light hex values, and remember SVG `fill` presentation attributes don't accept `var()`
  (use a CSS class or inline `style.fill`).
- **localStorage always holds the working copy** (key `flLiveTracker_v1`); a phone switched to family storage also
  syncs it with Supabase (see Where things are). Data is keyed by person NAME, so
  renames orphan history - acceptable, matches existing behaviour. Export/import merges by id
  (logs) and person+date (bodyweights); keep new data idempotent to merge.
- **Commit per feature**, each verified in the browser, then **push** - `origin/main` is
  `Daniel0469/Training-Tracker` and pushing **auto-deploys** to GitHub Pages
  (https://daniel0469.github.io/Training-Tracker/).
- **Never add a `Co-Authored-By` trailer** (or any other Claude/AI attribution) to a commit
  message. Daniel asked for this explicitly and had the existing history rewritten to remove it -
  it overrides any default that says otherwise. Commits are authored by Daniel, full stop.
- **New chats:** see `docs/CHATS.md` for setup and the three starter prompts - `docs/prompts/dev.md`,
  `coaching.md`, `running.md`. Full status is `docs/PROJECT-STATUS.md`.
- **Docs layout:** `docs/methods/` holds every training-method file (the reasoning behind coaching
  decisions, indexed by `methods/coaching-method.md`); `docs/prompts/` holds the three chat starter
  prompts; everything else - status, backlog, the current routine, setup guides - sits at `docs/`
  root. New method files go in `methods/`, not root.

## Local dev / verification

- Serve with any static server: `python -m http.server 8080` (see `.claude/launch.json`).
- **Cache gotcha:** the browser HTTP-caches `css/js` aggressively during dev, so edits can appear
  stale even after a reload. A no-cache dev server avoids it (send `Cache-Control: no-store`).
  Verify features in the browser: check light + dark, no console errors, correct behaviour.

## Where things are (`js/app.js`, single module)

- State + migration: `load` / `save`; `state = {people, weights, bodyweights, activePerson,
  programs, programIds, logs, theme}`. Read a person's program with `progOf(person)`.
- Program model: `programs[id] = {id, members, version, updatedAt, order, sessions}` and
  `sessions[key] = {name, day, exercises:[{name, warmup, notes, target,
  sets, cols[]}]}`. `cols` is N columns (2 = lifting, 3 = running Distance/Time/Pace).
- Tabs render into `#view`: `renderLog`, `renderHistory`, `renderProgress`, `renderBody`,
  `renderEdit`, `renderHelp`.
- Log form: `renderExForm` / `setRowHtml` / `wireExCard` / `wireSetRow`; per person+session
  in-memory `formDrafts` and `sessionTimers`.
- Save + summary: `saveSession`, `showSaveSummary` (volume comparison + `#muscleSvg` heatmap via
  `classifyMuscles` / `muscleColor`).
- Family storage (Supabase, version 2.0.0): the block in `js/app.js` between `==== Family storage (Supabase) ====` and
  `==== end Family storage ====`. `toRecords` / `fromRecords` map the state to rows of the `records` table and must stay equal to
  `mcp-coach/tt_records.py` (`scratchpad/review/sync-parity.js` checks it). `sb` holds the per-device connection and `sb.mode`
  ("github" default, or "supabase"). The first sign-in uploads everything, reads it back and only then switches (`sbMigrate`).
  After that `autoSync()` calls `sbSyncSoon()`: `sbOutbox` diffs the rows against the hashes in `sb.h`, `sbFlush` sends them
  (programs through the `save_program` function), `sbPull` fetches rows with `server_at` after `sb.cursor`, and realtime feeds the
  same `sbApplyRows` -> `mergeInData`. The log form draft travels as a `drafts` row per person+session (`sbDraftsSaved`).
  `scratchpad/review/sync-cases.js` runs the engine against a JS fake of Supabase.
- Setup code (version 2.0.2): `setupCode` / `setupLink` / `setupDecode` and the Show setup code dialog sit in the same block. `takeSetupHash`
  at the top of `js/app.js` removes a `#tt-setup=` fragment before anything else runs, and `setupReceive` connects with the password held in
  memory only. Never store, log or export a code or its password. `scratchpad/review/setup-cases.js` covers it.
- Pairing code (version 2.0.3): the `PAIR_*` constants and `pairNew` / `pairSeal` / `pairOpen` / `pairPublish` / `pairUse` in the same block.
  The phone showing the setup code also stores `{email, password}` encrypted with a 6-character code (PBKDF2 into AES-GCM) in the `pairing`
  table, and the new phone claims it once through the `tt_pair_claim` function. `js/family.js` holds the project address and key the fields
  start from (`sbProject`). Never store, log or export the code or the password. `scratchpad/review/pair-cases.js` covers it.
- Importers: `importBodyweightCsv` (scale CSV), `importRunIntoCard` + `parseTcx`/`parseGpx` (runs).

## Roadmap (not yet built - see `docs/hub-and-coaching.md` when it exists)

Free sync backend (GitHub-as-store), the health hub, and AI coaching (MCP server on the laptop,
reading the shared data) are proposed but await Daniel's go-ahead. Automatic API-based coaching
costs money; the MCP / paste-into-Claude paths use his existing subscription.
