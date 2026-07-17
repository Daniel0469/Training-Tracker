# Training Tracker — what it can do (and can't)

A plain-English reference to **everything the app does** and its **known limitations**. If you're
after conventions or architecture, see `CLAUDE.md` and `docs/PROJECT-STATUS.md`; this file is the
user-facing "what's possible" list. The in-app **Guide** tab (`renderHelp` in `js/app.js`) is the
same information framed as a how-to — keep both in step when a feature changes.

## In a sentence
A shared workout + health tracker for two people (Daniel & Cerys). A static site — no account, no
backend, works offline, installable to your phone's home screen. All data lives on the device
(`localStorage`), with optional free cloud sync so both phones and a Claude coach stay in step.

---

## What it can do

### Home
- Opens here by default. At-a-glance hub for the selected person: today's session (with a **Log it**
  shortcut), any **🧠 Coach** note, quick stat tiles (sessions & volume this week, latest bodyweight
  with trend arrow, total sessions), last session and last run, a bodyweight-trend mini-chart, and
  goals. Arrows jump to the full History / Body tabs.

### Log a workout
- Pick who you are (blue/orange name toggle); everything logged belongs to the selected person.
- **Switch person mid-entry without losing typed data** — handy for logging both people from one phone.
- Date auto-picks the right session for that weekday; a late-night session (before ~5am) counts as
  the **previous** training day.
- Per-set **weight + reps** (numeric keypad on phones); first set's weight auto-fills the rest.
- **Done checkbox** per set: fills empty reps to the top of the target range and shows a gold
  **🥇 PR medal** live if the weight beats your best.
- **Last** column shows what that person did last time (relative time; hover for the date); a
  **🕑 Most recent** chip flags a more-recent instance in another session.
- Percentage **warm-ups** (e.g. `40%x8`) resolve to actual kg once a working weight is known.
- **Tap a set number** to mark it a **warm-up** (shows `W`) — excluded from volume, PRs and the
  muscle map so it doesn't inflate numbers.
- Session **timer** (auto-starts on entry; pause/reset), a **difficulty 1–10**, and free-text notes.
- **Save** shows total volume with a fun comparison, any PRs, and a **muscle-map heatmap** of what
  you worked.

### Cardio & running
- N-column exercises; a **running** exercise uses Distance / Time / Pace, auto-computes **pace**, and
  treats each row as a **split**.
- **⬆ Import run (TCX/GPX)** pulls a Garmin/Strava-exported file straight into the splits.
- **Garmin auto-link (⌚):** saving a cardio session tags it *awaiting run…*; the Garmin sync on the
  laptop later finds that day's run and enriches it with HR, cadence, elevation, calories, moving
  time, training effect and per-km splits — **never overwriting** what you typed (needs the laptop
  set up; see `mcp-garmin/`).

### History, Progress & Records
- **History:** opens with a **This week** summary (total volume, session count, muscle heatmap,
  weekly-volume bar chart), then every saved session newest-first — filter by person, expand for
  detail, delete.
- **Progress:** current **bests** (weight, reps, estimated 1RM per exercise), then a chart of your
  top set for any exercise over time with both people on one graph and a top-weight vs Est. 1RM toggle.

### Body, goals & bodyweight
- Bodyweight over time with a trend chart; add by hand or **⬆ Import from scale (CSV)** (e.g.
  1byone Health — auto-detects the date and weight columns, lb→kg).
- Per-person **goals** (gear menu) — shown on Body, and travel with the data so a coach can see them.
- **Coach brief (Markdown)** button bundles goals, PRs, bodyweight and recent sessions to paste into
  Claude / Obsidian.

### Coaching (two-way, via Claude)
- A local **MCP server** (`mcp-coach/`) exposes the shared data to Claude on your existing
  subscription (no API cost). Claude can **write coaching back** into the app:
  - a **per-session** focus note (keyed by session name),
  - an optional **overall/general** note,
  - a **per-exercise next-step** cue on each exercise.
- Notes show as purple **🧠 Coach** cards on Home and the Log tab. Every write is appended to a
  **🧠 Coaching history** (collapsible on Home, synced) so both you and the coach can see how advice
  changed and whether the numbers improved.

### Program editor
- Add / edit / reorder / remove exercises; **name-suggestion library** avoids duplicate spellings.
- Per exercise: target, warm-up (fixed or %), setup notes, Lifting/Running column presets, optional
  3rd column. Program edits only affect **future** logging; past history is untouched.
- **Reset program to default** (gear) restores default workouts and keeps your logs.

### Data, backup & sync
- Everything saves **on this device**. **Export** writes a full file; **Import / merge** on another
  device merges by unique id (logs) and person+date (bodyweights) — no duplicates.
- **Cloud sync (GitHub)** is optional and free: set a private repo + fine-grained token once, then it
  syncs **automatically** on open and after each save. Doubles as off-device backup; the token is
  stored only on the device and **never** included in exports.
- **Installable PWA** — Add to Home Screen and it works **offline**.

### Theme
- Dark / light toggle (persisted, follows the OS default). Every surface is themed for both.

---

## Limitations & things to know

- **Data is keyed by person NAME.** Renaming a person **orphans** their history — by design.
- **localStorage only.** Clearing the browser's site data wipes local history — keep cloud sync or
  regular exports as backup. Two devices only stay in step if cloud sync is on (or you import/export).
- **Two people, fixed.** The app is built around Daniel & Cerys, not an arbitrary number of users.
- **No Strava/Garmin live API.** Runs come in via **exported files** or the laptop-side Garmin sync
  — not a direct phone-to-Strava/Garmin API (Strava forbids feeding data to AI; Garmin's dev program
  is on hold). The Garmin auto-link only runs **while the laptop is on**.
- **Coaching isn't automatic.** It runs when someone opens the coaching chat and prompts Claude (free,
  on the subscription). A fully hands-free weekly version would use the paid API and is deliberately
  **not** switched on.
- **Scale import is CSV/manual.** No Bluetooth/API to the scale (iOS blocks web Bluetooth); the
  1byone CSV export is flaky, so manual entry or pasting a scale screenshot into Claude's vision is
  the practical path. Ambiguous slash dates default to **D/M/Y**.
- **Muscle map is heuristic.** Muscles are inferred from the exercise **name** (`classifyMuscles`);
  an unusual name may map to the wrong muscle or none.
- **e1RM is an estimate** (Epley formula), not a measured 1-rep max.
- **PWA icons are placeholders** — real branding is a TODO.
- **No build step, minimal deps.** Vanilla JS + Chart.js (CDN) only. The service worker is
  cache-first, so an installed app keeps old files until `CACHE_NAME` in `sw.js` is bumped on deploy.

---

*Keep this file honest: when a user-facing feature is added or changed, update this list, the in-app
**Guide** (`renderHelp`), and — if the file list or deployment changes — `README.md`.*
