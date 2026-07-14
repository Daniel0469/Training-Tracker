# Training Tracker — Claude Code Handoff Brief

## What this is
A personal workout tracker web app for **two people (Daniel & Cerys)**. It is a single,
self-contained `index.html` file — HTML + CSS + vanilla JavaScript, no build step, no
dependencies except Chart.js loaded from a CDN. All data is stored in the browser's
`localStorage`. It is currently hosted as a static site on GitHub Pages and added to the
phone home screen.

**`index.html` is both the app and the spec — read it fully before changing anything.**

## Files in this folder
- `index.html` — the complete app (read this first).
- `Daniel-import.json` / `Cerys-import.json` — export/import files showing the exact data
  format (program + logs); contain each person's imported Hevy history.
- `sample-daniel.json` / `sample-cerys.json` — **full current exports (2026-07-14)** with real
  logged sessions (incl. cardio). Best fixtures to load into the app and test against.
- `claude-code-handoff.md` — this brief.

## Current features (all working)
- Two-person toggle (Daniel / Cerys); editable names + bodyweight in a settings dialog.
- 6 sessions ordered by weekday: Lower 1 (Mon), Cardio Speed (Wed), Upper 1 (Thu),
  Lower 2 (Fri), Cardio Endurance (Sat), Upper 2 (Sun).
- **Log tab**: pick session + date, enter weight/reps per set. Inputs start blank; each
  exercise shows that person's **last session** in a "Last" column to beat. Date auto-selects
  the matching weekday's session.
- Auto **next-session plan** per exercise on save (progressive-overload logic).
- **Save popup**: total volume with a fun animal/vehicle comparison, gold-medal weight PRs,
  and a front/back **muscle map** shaded by sets worked.
- **History** (per-person, expandable, deletable), **Progress** chart (Chart.js),
  **Edit Program** (add/edit/remove/reorder exercises), and a **Guide** tab.
- **Export / Import** for moving data between devices. Import upserts by log `id`
  (re-importing a session updates it in place).

## Data model (localStorage key `flLiveTracker_v1`)
```
{
  people: ["Daniel","Cerys"],
  weights: ["",""],              // bodyweight per person
  activePerson: 0,
  program: {
    order: ["lower1","cardioSpeed","upper1","lower2","cardioEndurance","upper2"],
    sessions: { lower1: { name, day, exercises: [ {name,warmup,target,cols:[c1,c2],sets} ] }, ... }
  },
  logs: [
    { id, date:"YYYY-MM-DD", person, sessionKey, sessionName,
      entries: [ {name, cols:[c1,c2], rows:[[val1,val2],...], pr? } ],
      feedback, difficulty, suggestions:[{name,text}], volume }
  ]
}
```
Import/export files use the same shape wrapped as `{version, exportedAt, people, weights, program, logs}`.

## Known constraints / context
- Data is **per-device** — no cross-device sync. Daniel's phone and Cerys's phone keep
  separate data; syncing is currently manual via Export/Import.
- Everything is intentionally in one file so far. You may split it into sensible files
  (e.g. index.html + app.js + styles.css) for maintainability — just keep it deployable as a
  **static site on GitHub Pages** unless we agree otherwise.

## Backlog (do in this order)
1. **Make it an installable PWA** — add a web app manifest + service worker so it installs
   from Safari/Chrome with its own icon, splash screen, standalone display, and **offline**
   support. This is the top priority.
2. **(Optional) Live sync backend** — add a lightweight backend (e.g. Supabase/Firebase) so
   Daniel and Cerys see each other's logs automatically instead of manual Export/Import.
   Discuss approach before building; keep the front end able to work offline.
3. **Additional requests from Daniel** (group and tackle in a sensible order):

   **Bug fixes**
   - Possessive names render wrong: "Cerys's" should be "Cerys'". If a name ends in `s`, use a
     trailing apostrophe only (`name + "'"`), otherwise `name + "'s"`. Applies everywhere the
     possessive is shown (e.g. the "…'s last session" note and the bodyweight labels).

   **Log-form data entry (mobile UX)**
   - Number pad: set inputs should trigger the numeric/decimal keypad on phones
     (`inputmode="decimal"` for weight, `"numeric"` for reps), not the full keyboard.
   - Autofill subsequent weights: after entering the **first** set's weight, pre-fill the
     remaining sets' weight fields with the same value. Never overwrite a field already filled.
   - Per-set "completed" tickbox: add a checkbox to each set row that marks the set done and
     visually flags it. When ticked, if the **reps** field is empty, auto-fill it with the top
     of that exercise's target rep range (e.g. "3x8–12" → 12). Never overwrite an entered value.
   - Live PR medal: when a set is ticked complete, if its weight beats that person's previous
     best for that exercise, show the gold medal **there and then**, not only in the save popup.

   **"Last" reference**
   - Show the "Last" column as **relative time** ("3 days ago", "2 weeks ago") instead of a date.
   - Also show, per exercise, the **most recent weight lifted for that movement across any
     session**, with how long ago (days/weeks).

   **Two people from one phone**
   - Allow switching to the other person's workout mid-entry **without erasing** already-entered,
     unsaved data — so if only one phone is present, both people's sets can be entered. Keep a
     per-person draft of the in-progress form and restore it on toggle.

   **Sessions & timing**
   - Whole-session **timer**: track total workout length (start when logging begins / on demand,
     stop on save) and store it with the session. Session-level only, not per-exercise.
   - Auto date→session should consider the **time of day**: a session logged at, say, 1am Friday
     should pick **Thursday's** workout. Treat the training day as starting ~4–5am (i.e. subtract
     a few hours before computing the weekday).

   **Program & exercises**
   - Per-exercise **configuration notes**: machine settings, seat height, pin position, etc.
     Persistent per exercise, shown on the log form for reference.
   - **Warm-up as a percentage**: express warm-up sets as a % of the working weight and compute
     the actual kg from the entered top set, rather than fixed numbers.
   - **Exercise picker/library**: when editing the program, select exercises from a list rather
     than free-typing, to avoid duplicates caused by spelling/wording differences.

   **Cardio / running**
   - Change running to track **speed and time** (proper running fields, not weight×reps).
   - Proper running/cardio tracking generally (distance, pace, time, ideally splits).
   - Investigate pulling running data from **Garmin** (Garmin Connect) into the cardio session.
     Flag feasibility: likely needs Garmin API access/approval or a FIT/GPX import path — research
     and propose an approach before building.

   **Appearance**
   - Dark / light mode toggle.

   **Sharing / sync**
   - Be able to share workouts / have logs accessible to both people. Ties into the live-sync
     backend in item 2 above — the two are the same underlying feature.

4. **Extra ideas suggested by Claude (optional — Daniel to prioritise):**
   - **Rest timer between sets** — auto-start a short countdown when a set is ticked complete;
     pairs naturally with the completed-set tickbox.
   - **Warm-up set flag** — let a set be marked as a warm-up so it's **excluded from volume
     totals and PR detection**. Fixes warm-up sets inflating volume/PRs (a real issue today,
     especially with imported Hevy data).
   - **In-app Hevy CSV import** — parse a Hevy CSV/TSV directly in the app (map exercise names,
     convert units) so future Hevy history imports need no external help.
   - **Bodyweight history** — log bodyweight over time with a trend chart, rather than storing a
     single current value (a bodyweight field already exists).
   - **Estimated 1RM per lift** — compute e1RM (e.g. Epley) and chart it; a better progress
     signal than top-set weight alone.
   - **Records / PR page** — a per-person list of current bests per exercise.
   - **Data-loss protection** — `localStorage` can be wiped by the browser/OS, which would lose
     all history. Add an automatic periodic export/backup (or rely on the sync backend) so data
     can't silently vanish. Worth prioritising given everything is local today.
   - **kg / lb unit toggle** (per person).
   - **Weekly view** — accumulated weekly volume and a weekly muscle heatmap (extends the
     per-session muscle map already in the save popup).
   - **Plate calculator** — for barbell lifts, show which plates to load for a target weight.

## Deployment
Static site. Host on GitHub Pages (serve `index.html` at the repo root). Keep it working as a
plain static bundle so it can be dragged onto Netlify or GitHub Pages without a build server.
