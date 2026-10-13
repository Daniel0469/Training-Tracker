# Design v3 — Training Tracker restyle (dark first)

Status: **design agreed with Daniel. Step 1 and Session built (13 Oct, not yet pushed - Daniel wants the restyle pushed in one go at the end); other screens not yet.** Written 13 Oct 2026 from a design canvas in Claude
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
