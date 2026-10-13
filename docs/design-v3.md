# Design v3 — Training Tracker restyle (dark first)

Status: **design agreed with Daniel. Every screen built in dark and pushed (13 Oct, tt-v151); light mode still to do.** Written 13 Oct 2026 from a design canvas in Claude
(Cowork): https://claude.ai/code/artifact/f972d4f0-eae6-4caa-adbe-06c979b55da6 — Daniel can open it;
a dev chat probably can't, so this file is meant to be enough on its own.

This is a **restyle**, not new features. Every screen keeps the data, behaviour and rules it has today.
Where the mockups show numbers or names, they are sample data.

## Ground rules (from CLAUDE.md — still apply)

- Agree the plan with Daniel first (AskUserQuestion), prototype against a COPY of the store,
  screenshots of both people before pushing.
- **Dark mode first.** Light mode is parked until the end — Daniel will ask for it. Keep light
  working (don't break it), but only design-review dark for now.
- Bump `CACHE_NAME` in `sw.js` for every shell change. Update the Guide, README and prompts.
- Two people, one phone: the person toggle must stay reachable while logging.
- Personal use only — colour-blind safety is not a requirement.

## Look

One shared look with the Home Hub. Chunky rounded cards, heavy headings, monospaced numbers.

### Fonts — new dependency, approved by Daniel
- **Manrope** (400, 500, 600, 700, 800) for all text.
- **JetBrains Mono** (500, 700) for every number: weights, reps, times, dates, paces, stats.
- **Bundle them** (woff2 under `fonts/`, `@font-face` in `css/styles.css`) and add them to the
  service-worker cache. No Google Fonts link — the app must work offline.

### Dark tokens (map onto the existing CSS variables)
| Variable | Value | Use |
|---|---|---|
| `--bg` | `#121417` | page |
| `--card` | `#1B1E22` | cards, toggles, inputs on page |
| `--card-2` / `--input-bg` | `#24282D` | raised: inputs inside cards, chips, secondary buttons |
| `--line` | `#2A2E34` | card borders, row dividers |
| (new) `--line-2` | `#2F343A` | input / outline-button borders |
| `--ink` | `#ECEDEE` | text |
| (new) `--ink-2` | `#C9CDD2` | secondary body text |
| `--muted` | `#9BA1A8` | labels, meta |
| (new) `--nav` | `#16191C` | bottom tab bar |
| PR / "soon" | `#E8C15A` | PR medal (dark text `#2A1F00` on it), PR row tint `#2A2617` |
| bad | `#FF7A6B` | delete / danger |
| `--brand` | person swatch, unchanged | dark values of `SWATCHES` as now |
| on-brand text | `#121417` in dark, `#FFFFFF` in light | text on brand buttons |

Light tokens for later (parked): bg `#F4F5F3`, card `#FFFFFF`, raised `#EEF0ED`, line `#E1E4DF`,
line-2 `#D5D9D3`, ink `#15181B`, ink-2 `#33393F`, muted `#5E656D`.

### Shape and spacing
- Radii: inputs 10–12, buttons 12–16, rows 14, cards 20, pills 999.
- Touch targets 44 px minimum; primary buttons 48–52 px tall.
- Page padding 20 px, gap between cards 12–14 px.
- Section labels: 11 px, weight 800, uppercase, letter-spacing .08em, `--muted`.
- Screen title: 28 px weight 800, with a 13 px uppercase muted line above it.
- Icons: simple 2 px line icons. **No emoji in the UI** (section titles currently use them).

### Shared pieces
- **Header** (replaces the sticky topbar look): small uppercase line + big title on the left; on the
  right the **person toggle** as a pill (active person filled with `--brand`) and a round 44 px
  **gear** button that opens Settings. Keep it sticky.
- **Bottom tabs**: Home, Session, History, Progress, Program — icon over 11 px label, active one in
  `--brand`, bar `--nav`.
- **Pills/segmented switches** (Progress panes, theme): container `--card`, active segment `--card-2`.
- **Pickers 1–10** (RPE, difficulty): ten equal buttons, selected one filled `--brand`.

## Screens

**Create account** — centred: app mark, "Welcome", hint, Name input (brand-coloured border), six
colour swatches (taken one greyed out on the second account), Create account; second account adds
"Skip — just me for now".

**Home** (top to bottom): today's session card (big name, day, "Log it →" brand button, and a ticked
line if another of today's sessions is already logged) · Next cardio card · session-swap card (both:
label, "assigned" outline pill, session name, why, coach hint) · coach note (outlined card, chat icon) ·
2×2 stat tiles (mono numbers) · Last session · Last Zone 2 run with a zone bar · What the week trains
(per muscle: grey planned track, brand fill for ticked, "ticked/planned" in mono) · Sleep & recovery
(duration, score, stage bar, HRV / resting HR / breaths) · Heart rate zones (max/resting/threshold,
five rows with colour chip and bpm range). Cards that have no data stay hidden, as now.

**Session**: header says "Logging for <person>" · Session select + Date side by side · timer card
(big mono time, Pause/Start, Reset) · Warm-up / Cool-down as fold-out rows · exercise cards: name +
target in mono, set table **Set | kg | Reps | Last | ✓**, tap set number for warm-up (W), PR row
tinted with medal, e1RM line in PR gold, then **one RPE picker per exercise** under the sets, Smith
tick and +/− set on one row · supersets: brand bar down the left, "Superset" label · dashed
"Machine taken? + Add exercise" row · "How did the session feel?" card: difficulty picker + notes ·
Clear + Save session · **rest bar**: full-width pill above the tab bar (ink background, mono time,
"tap to dismiss").

**History**: this-week card (7 day squares — filled = lifted, outlined = today) + 8-week volume bars
(current week in brand) · session rows: big mono day/month, name, PR medal, mono meta line, chevron.

**Progress**: 5-way switch **Lifts · Run · Flex · Time · Body** (Run/Flex only when they have data,
as now).
- Lifts: exercise + metric selects, big current value, line chart, Records table (Exercise, Best,
  e1RM, When — recent ones in PR gold).
- Run: Estimated 5k card · Trend select + chart for both people (legend) · session cards with stats
  row, zone bar and rep table.
- Flex: ladder table (Test, Now, Change, Measured), lowest rung tagged; test select + chart.
- Time: session select, duration chart for both, recent list.
- Body: goals card, bodyweight chart, add weigh-in row (date, kg, Add), CSV import, recent list.

**Program**: coach proposal card (Decline / Approve) · horizontal session chips · session card with
exercise rows (name, mono target, ↑ ↓ Edit), supersets with brand bar · action buttons (+ Exercise,
Group as superset, Session notes, Share) · dashed "+ Add session" / "Import shared".

**Settings** (dialog): title "Settings · <person>" + close · theme switch + Open Guide · person card
(name, swatches, bodyweight, goals) · Improve the app · Backup & data (Export, Import / merge, Coach
brief) · Cloud sync with a status dot · What's not set up yet (fold-out) · danger buttons + version.

**Guide**: back button, intro card, the ten sections as fold-out panels with numbered badges.
Text unchanged.

## Suggested order
1. Fonts + tokens + header/tabs (everything changes a bit, nothing breaks).
2. Session (most used) → Home → History → Progress → Program → Settings/Guide/Create account.
3. Light mode last, when Daniel asks.

## Decisions made while building (13 Oct)

- Header title is the screen name only; Session reads **"Logging"** (the person pill says who).
- Home's hub card drops its date line - the header shows it.
- Program tab keeps the inset brand **border** for a waiting coach proposal (not a dot).
- Session: Warm-up / Cool-down stay **open cards** (not fold-outs). No e1RM line. A ticked set is a
  brand-filled tick with a faint brand row tint; a PR row is gold with a **PR** badge. Rest bar is in
  the **person's colour**, not ink. Session is denser than the 44px rule: set boxes 26px, tick 24px, 5px gap between set rows (three rounds of "too big"),
  RPE (and session difficulty) buttons 26px, smaller timer (Daniel found the first pass too big). Run tables drop the
  always-empty Last column. Session + Date sit side by side with a narrow date box.
- The **PR badge replaces the 🥇 medal** on History and Home's Last session too, when those steps land.
- The restyle was committed step by step and pushed in one go on 13 Oct.
- Home keeps the four cards the mockup left out (Last intervals, Estimated 5k, Bodyweight trend,
  Goals) and follows the doc's order with them added: Today · Next cardio · Swap · Coach · tiles ·
  Last session · Last Zone 2 run · Last intervals · What the week trains · Sleep · HR zones · 5k ·
  Bodyweight · Goals. Week bars are grey planned / brand ticked (no heat colours). Sleep gets the
  stage bar and a three-stat row. Today shows a ticked line for anything else saved today.
- History: the this-week card is volume + 7 day squares + 8 HTML volume bars (the muscle body-map and
  the Chart.js weekly chart went). Rows are date block · name · PR badge · person · meta · chevron;
  tap the row to fold it open, **Delete session** sits inside the open detail. The person filter
  stays as an Everyone / person switch, starting on Everyone. PR badge on the row and on each PR
  exercise inside.
- Progress: pane labels are plain words (Lifts · Run · Flex · Time · Body). Lifts follows the doc -
  pickers, big current value with change since first, chart, then Records (Exercise · Best as
  weight × reps · e1RM · compact When), bests from the last 14 days in PR gold. Run is restyled
  as-is (rep tables still scroll sideways - up to nine columns of watch data). Flex's **"lowest
  rung" tag** can't be computed by the app (it is the coach's call per the flexibility method), so
  it is a coach-written field (13 Oct): `write_coaching(lowest_rung=...)` stores
  `coaching[person].lowestRung = {skill: {test, why}}`, and the ladder puts a gold `pr-badge`
  "LOWEST RUNG" pill plus the skill name on its own full-width line under that test's row (inside
  the Test cell it widened the column and forced a sideways scroll), with each skill's `why` under
  the table. Hidden while unset. Time keeps its four
  tiles in the Home tile style. Body is goals · chart · add weigh-in · import · list.
- Program: sessions are a swipeable chip row, one session shown at a time (opens on today's); a dot
  on a chip marks a coach change waiting. Pending changes for the chosen session sit in one
  **Coach suggests** card at the top (Approve / Decline, the exercise named), with a "change
  waiting" tag on the row. Rows are name · mono target · ↑ ↓ Edit; **Remove from program** moved
  into the Edit dialog; superset tick-boxes only appear after "Group as superset" (Group (n) /
  Cancel). The intro hint card is gone; "+ Add session" and "Import shared session" are dashed
  rows at the bottom.
- Program session notes start **closed** behind the Session notes button (they used to open
  whenever a session had any), and stay open across re-renders once opened.
- Settings: theme is a Light / Dark switch; cloud sync shows a status dot (green / red / pulsing /
  grey) and "Sync now", with repo / path / token folded under "Change sync settings" once set up.
  The person details and the version line stay where they were (Daniel didn't take those two).
  Emoji gone from every button. Guide: Back button, intro card, the ten sections as fold-out panels,
  **all closed**, numbered badges (icons for Home and Quick tips); text unchanged apart from labels
  that no longer exist. Create account: centred, a dumbbell mark filled with the picked swatch, which
  also colours the name border and the Create button as you tap swatches.
- **All screens done and pushed (13 Oct, tt-v151). Light mode is next, when Daniel asks.**
