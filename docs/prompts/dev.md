# Development chat - starter prompt

Use this in a Claude Code chat **opened on the Training Tracker project folder**
(`C:\Users\danie\Documents\TrainingTracker`), which auto-loads `CLAUDE.md` and saved memory.
Coaching stays in its own chat; see [coaching.md](coaching.md) and [running.md](running.md).

**Before first use:** if `.mcp.json` or anything under `mcp-coach/` changed since last time, fully
restart Claude Code so the `training-tracker` tools reload. New tools do not appear until you do.

---

## Paste this to start

> You're the developer on **Training Tracker** - a two-person workout + health tracker on its way to
> an all-round health & fitness hub. **First read `docs/PROJECT-STATUS.md` and `CLAUDE.md`** for the
> full state, decisions and conventions, and `docs/handoff-progress.md` for where the current plan
> stands. The backlog lives on GitHub: every Friday the coach run files the in-app suggestions as
> `training` issues on `Daniel0469/Home-Hub` (`gh issue list --repo Daniel0469/Home-Hub --label training`).
> Work only on issues without `needs-confirmation`, never on `rejected` ones. Anything still in the
> app's list (the `training-tracker` **`suggestions`** tool) hasn't been filed yet. **Auto-apply the
> easy/safe ones** (verify in the browser - light + dark, no console errors - commit per feature,
> bump `sw.js` VERSION on any shell change, then push to deploy), and **list the harder/riskier
> ones for me to decide**. Close each issue you finish, or mark an in-app one done with
> **`resolve_suggestion_tool`**. Also read
> **`docs/coach-tooling-brief.md`** - the coaching chat's own account of what it can and cannot do,
> with the blocked coach-owned jobs and a suggested build order. Today I want: **‹your task›**.

---

## What the chat must not get wrong

These are in `CLAUDE.md` too, and they are the ones that cost real time when missed.

- **Ask before implementing.** Investigate, put the open decisions up with `AskUserQuestion`, and
  only build once they are answered. A wrong guess means rework, or worse, silent changes to real
  training data.
- **Prototype before pushing.** Build locally against a **copy** of the store
  (`scratchpad/proto_term.py` is the pattern) and show screenshots - both people, both themes -
  before anything is committed. Pushing auto-deploys to both phones.
- **Bump `VERSION` in `sw.js`** on any change to a cached shell file (`CACHE_NAME` is
  `"tt-" + VERSION`, and Settings shows it). Versions have three numbers: a fix bumps the last (2.0.1), a
  new feature the middle (2.1.0). The service worker is cache-first; without a bump, installed users keep the old files.
- **Keep the Guide, the README and these prompts current** when a feature or a decision changes.
- **A coach-owned job can be impossible, not just undone.** Before assigning work to the coaching
  chat, check the tool can actually do it - `docs/coach-tooling-brief.md` lists what cannot be
  reached today. The 25 Sep settings-box cleanup and the 6 Oct warm-up ramps were both handed over
  as coach jobs and neither is possible on a lifting exercise, because `write_program_change` can
  only edit `sets` and `target`.
- **No AI attribution in commit messages**, ever.

## Notes

- Pushing to `main` **auto-deploys** to <https://daniel0469.github.io/Training-Tracker/> (~1 min).
- The build order is in `docs/PROJECT-STATUS.md` -> *Build order remaining*.
- **Design v3 restyle: dark done** - spec in `docs/design-v3.md` (dark first, light parked until
  Daniel asks). Step 1 (fonts, tokens, header + icon tabs, shared shapes) and every screen are built in dark,
  pushed on 13 Oct (tt-v151). Light mode is the remaining step, when Daniel asks for it. New UI uses the v3 tokens (`--line-2`,
  `--ink-2`, `--nav`, `--on-brand`, `--gold`, `--gold-ink`, `--pr-tint`), `var(--mono)` / `.num` for
  every number, line icons (`ico()` in `js/app.js`, `svg.ico` in CSS) rather than emoji, and
  `var(--on-brand)` - never `#fff` - for text on a brand fill. Session-only card styles are scoped
  under `#exForm` because `.ex`, `.superset` and `.notes` are shared with Program/Progress/History.
- **Lift targets are built, not typed** (14 Oct): the setup dialog has Sets, Reps min-max and an
  extra; `joinTarget` makes "3x8-12 each leg" and `splitTarget`/`parseRange` read it back (a
  single count like "2x5" is 5-5). Non-lifts keep a free-text target. `restSec` on an exercise is
  its suggested rest; the rest bar shows it and turns gold when reached, still counting. The
  header kicker shows the workout time on Session. The Smith tick covers any barbell lift.
- **Machine settings are per person** (13 Oct): `state.machineSettings[person][exercise name] =
  {text, updatedAt}`, read/written via `msGet`/`msSet`, merged per entry (newer wins). The program
  exercise has no `notes` any more, and the coach MCP cannot write settings. An install without
  sync migrates old `notes` on load; synced phones got them from `scratchpad/apply_machine_settings.py`.
- **Family storage** (built 3 Nov 2026 as version 2.0.0, on branch `p4-app`, not pushed): a phone can switch from GitHub sync to
  the family's Supabase project in gear -> Admin -> Family storage. The connection (project address, publishable key, family
  email) is typed per phone and kept in localStorage `flLiveTracker_v1_sb`, never in the repo. The password is never kept. The
  first sign-in is automatic: every account on the phone is uploaded (rows keyed `kind`+`key`, merged newest-wins by the table,
  so two phones with the same accounts never duplicate), read back and compared, and only a match switches `sb.mode` to
  "supabase". Nothing local is deleted. The engine is the Family storage block in `js/app.js`. `save()` is unchanged. `toRecords`
  must give the same rows as `mcp-coach/tt_records.py`. Rows are sent when changed (hash map `sb.h`), pulled by `server_at`
  cursor, and realtime goes through the same merge. Member program saves use `save_program(id, body, base_version)` and a
  `conflict` shows the "Changed since you opened it" card. The log form draft is a `drafts` row per person+session with a 10 s
  typing guard and a 12 h limit. `scratchpad/review/sync-cases.js` and `sync-parity.js` run under VS Code's Code.exe with
  `ELECTRON_RUN_AS_NODE=1`. The server side is in `docs/supabase-setup.md` and `docs/supabase-schema.sql`.
- **Setup code** (built 5 Nov 2026 as version 2.0.2, on branch `setup-code`, not pushed): on a connected phone, Admin -> Family
  storage -> Show setup code asks for the family password (typed each time, never stored), checks it with a sign-in, and shows a
  QR code and a text link for 60 seconds (countdown, Hide, Copy; hidden when the dialog closes or the app goes to the
  background). The link is the app's own address plus `#tt-setup=` and base64url of `{v:1, url, key, email, password}`. At the
  top of `js/app.js`, `takeSetupHash` removes the fragment with `history.replaceState` before anything else runs.
  `setupReceive` fills Family storage and calls `sbConnect(password)` with the password held in memory only (a phone with no
  account yet keeps it in `setupPending` until the first account exists). Admin -> Family storage -> Paste a setup code takes the
  full link or the bare code. A bad or old code shows a clear message. The QR library is qrcodejs 1.0.0 from cdnjs
  (`QR_LIB_URL` and `QR_LIB_SRI` in `js/app.js`, also cached best-effort in `sw.js`), loaded by `loadLib` only when Show setup
  code is used. The app reads the module grid from the library and draws the canvas itself, so the library never renders an
  image. Never log, store, export or screenshot a code. Cases: `scratchpad/review/setup-cases.js`. Review stage:
  `scratchpad/review/setup-stage.html`.
- **Programs are per person** (3 Nov 2026, built on branch `p4-app`, not pushed): `state.programs[id] = {id, name?, members, version,
  updatedAt, updatedBy, order, sessions}` and `state.programIds[person] = {id, updatedAt}`. Daniel and Cerys share one program
  (`p-daniel-cerys`), anyone else gets their own. Read a program with `progOf(person)` (no argument is the active person) -
  never `state.program`, which no longer exists. `load()` wraps an old single `program` once (`migratePrograms`), and an old-shape
  export or store is wrapped the same way (`incomingPrograms`). Programs merge per id, newest `updatedAt` wins, held back while
  someone on the program has a log draft open (`mergePrograms`). `saveProgram(prog)` bumps `version`. The push still writes the
  active first person's program as the old top-level `program`, so readers that predate programs keep working.
  The Program tab edits `editProg()`: the live program for a member, a copy for anyone else. Sending that copy, or a session copy,
  adds a record to `state.programChanges` with `kind` "person" or "copy" (coach changes have none): `{id, kind, programId, from,
  baseVersion, base, proposed, createdAt, status}`, where `base` and `proposed` hold only the sessions that differ. A member accepts it
  on Home or Program (`applyEdit`): a session is applied only if it is unchanged since `base`, the rest are listed in `clashes`.
  Cases: `scratchpad/review/programs-cases.js`. Review stage: `scratchpad/review/programs-stage.html`
  (`python scratchpad/proto_programs.py` builds its data).
- **Coach questions are per person** (3 Nov 2026): `state.coachQuestions[person] = [{id, question, why,
  priority, decision, askedAt, nextFollowUp, reminders, answer, answeredAt, status, updatedAt}]`, shown on
  Home for the active person only and merged per question id, newest `updatedAt` (ms) wins
  (`mergeCoachQuestions`). The coach adds and closes them through `mcp-coach`; the phones answer. A
  closed one is hidden, never deleted, so the merge cannot bring it back.
- **Settings has two tabs and per-person switches** (3 Nov 2026, version 1.2): Profile (name, colour,
  bodyweight, goals, four switches, Improve the app) and Admin (export, import, sync, accounts list,
  clear program, delete account, change PIN). `state.features[person] = {food|body|garmin: {on,
  updatedAt}}`, read with `featOn(person, key)` (absent means on, `progression` delegates to its own
  switch) and written with `featSet`, merged per switch by newest `updatedAt` (`mergeFeatures`). Every
  surface a switch hides checks `featOn` for the person being shown, and `coachOf(person)` returns no
  coach notes while Garmin and coach is off. A switch hides and never deletes. New work that adds a
  coach, watch, food or body surface must check the matching switch. The coach server refuses notes,
  targets and questions for a person with Garmin and coach off (`progression.coach_on`).
- **Admin PIN** (3 Nov 2026): `state.adminPin = {salt, hash, updatedAt}`, the hash being SHA-256 of
  the salt bytes plus the PIN, in hex. Newest `updatedAt` wins, except that a phone with no `sha` in
  its sync config yet takes the store's PIN (`mergeAdminPin`). `adminUnlocked` is cleared when
  Settings opens and closes. It is a light lock. To reset a forgotten PIN, set `"adminPin":
  {"updatedAt": <now in ms>}` in the store's `data.json` with no hash.
- **Saved sessions can be edited** (3 Nov 2026, version 1.3): **Edit sets** in an open History card opens
  `#editLogDlg`. `applyLogEdit(log, edit, now)` replaces only `rows`, `warmup`, `done` and `rpe` on each
  entry (indices renumbered when blank rows drop) plus the log's `feedback` and `difficulty`, keeps every
  other key (`garmin`, `corrections`, `load`, `timed`, `smith`), recomputes `volume` and stamps
  `editedAt` and `updatedAt`. An exercise left with no sets is dropped, a run is kept. If a run's rows
  change and `garmin.rows_from` starts with `reps` or `laps` it becomes `edited in app`, which mcp-garmin's
  `_fill_run_entry` does not replace. `prChanges(person, names, fromLog)` walks the person's logs in date
  then id order with a running best (`indexLog`, `prevBestLookup`, `entryPr`) and recomputes `pr` for the
  changed exercise names from the edited log on. `applyPrChanges` writes the flips and stamps `updatedAt`
  on those logs only. Undo steps live in `localStorage` key `flLiveTracker_v1_undo` as `{person: [steps]}`,
  outside the export and sync, five per person for 14 days, each holding before and after copies of every
  log it touched. Undo is a new edit (fresh `updatedAt`, recheck, sync) and puts `editedAt` back to null,
  because `mergeRecord` adopts a key a log no longer holds. The note editor records a step too. Cases:
  `scratchpad/review/edit-cases.html` (or `edit-cases.js` under Electron as node). `set_log_entry` in
  mcp-coach now stamps `updatedAt`. A stored `pr` flag can disagree with a full recompute (16 flags on 8
  sessions in the 2 Nov copy, all June and July), so a recheck only touches the exercises an edit changed.
- The Home Hub is a **separate app in its own repo with its own chat**. Don't build hub features
  here - see [../home-hub-link.md](../home-hub-link.md) for the shared data contract.
