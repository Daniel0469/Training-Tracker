# Home Hub link — tracker-side plan & data contract

**Status: proposal, nothing built.** Companion to the Home Hub planning doc (kept outside this repo).
This file is the **owner of the shared data contract** — the hub reads it, doesn't fork it.

## The short version

Daniel is planning a second app: a **Home Hub** (plants, chores, climate/air quality via Home
Assistant, bills, inventory) running on a home server, reachable over Tailscale. Two of its features
overlap this app:

- it wants to **log meals** (barcode + free-text), which belongs with training data
- it wants to **show** latest bodyweight and today's session on its home screen

**Decision: two apps, one store.** The hub does *not* absorb this app and this app does *not* call
the hub. Both read/write the existing `Training-Data/data.json`. If the hub is off, this app is
unaffected — which matters, because this app is used on two phones away from home while the hub sits
behind a home VPN.

That also means **no new backend is needed for either side**: the GitHub-as-store sync built in
Phase 1 already is one.

## Division of labour

| | Hub | This app |
|---|---|---|
| **Meal capture** | ✅ barcode scan, camera, free-text → macro estimate | — |
| **Meal display** | a simple "logged today" list | ✅ daily totals vs targets, trends, History |
| **Coaching context** | — | ✅ meals feed the MCP coach alongside training |
| **Bodyweight capture** | ✅ scale-screenshot read (phone camera) | manual entry (as today) |
| **Body-metrics capture** | ✅ the whole scale readout, not just weight | manual entry |
| **Bodyweight display** | one tile | ✅ Body pane of Progress, trend chart, goals |

**Re-confirmed 2026-08-11.** Daniel asked for scale-screenshot capture in *this* app, we designed
it, and he parked it back here — capture stays the hub's job. He also widened it: he wants the
screenshot to yield **the whole readout** (body fat, muscle mass, water, …), not just the weight,
because that is the point of using the scale's own app.

The design work is done and recorded in `PROJECT-STATUS.md` (→ hub → *Scale input via phone
screenshot*). Read it before building this — it settles the mechanism, the three costs, the
open-schema record shape, and a fourth approach (parse OS-OCR text rather than the image) that had
not been considered. The load-bearing check is already verified: `mcp.server.fastmcp.Image` accepts
raw bytes, so an MCP tool can hand Claude the screenshot for its vision to read.

**Whatever the hub captures, bodyweight still writes to `state.bodyweights`** in this app's store —
`setLoad`, records, Home's tiles and the coach all depend on it.

Rationale: the hub is doing phone-camera work anyway; this app owns everything that needs training
context. Nutrition is on this app's roadmap already (`PROJECT-STATUS.md` → hub → nutrition), so
without this split it gets built twice.

## Data contract — the `meals` array

New top-level array in `data.json`, alongside `logs` / `bodyweights` / `coachingLog` / `suggestions`.

```jsonc
{
  "id": "meal-1721558400000-a3f",  // unique; hub generates. Merge key.
  "person": "Daniel",              // MUST match a name in `people` exactly (case-sensitive)
  "date": "2026-07-21",            // training day, 5am rollover (see below)
  "loggedAt": "2026-07-21T12:40:00.000Z",
  "description": "Chicken breast, rice, broccoli",
  "barcode": "5000159407236",      // optional; present on scanned items
  "kcal": 620,
  "protein": 48,                   // grams
  "carbs": 55,
  "fat": 18,
  "source": "barcode",             // "barcode" | "text" | "manual"
  "estimated": true,               // true when macros came from an LLM guess, not a database
  "updatedAt": 1787141028912       // ms epoch, REQUIRED - see the conflict rule below
}
```

Rules, all matching existing conventions:

- **Merge by `id`, upsert** — but *not* a wholesale replace. Since **tt-v107** both `logs` and
  `meals` go through `mergeRecord` (`js/app.js`), which merges field by field:
  - **Whichever side has the newer `updatedAt` wins** a genuine conflict.
  - If the *other* side is newer, it still adopts keys it doesn't hold — so a partial write from
    one writer doesn't erase another's fields.
  - **An absent or empty incoming field never erases a value the other side holds.**
  - Two records with *no* stamp on either side fall back to the old "incoming wins".

  **The hub MUST stamp `updatedAt` on every meal it writes or rewrites.** An unstamped hub write
  loses to any stamped phone edit of the same meal, and silently. This replaced a wholesale
  replace that destroyed a locally-edited session note on 19 Aug 2026 — the same defect was
  already sitting in the `meals` branch, untriggered only because the hub doesn't exist yet.
- Re-syncing the same meal must never duplicate it.
- **`person` is a name**, not an id — this app keys everything by person name. A meal whose person
  doesn't match a known person is kept but not displayed (don't drop data).
- **`date` uses the ~5am training-day rollover**, so a late meal lands on the same training day as
  the session it followed. The hub must replicate this; it's the same rule this app uses to pick
  today's session.
- **kg / grams / kcal.** No unit field, no lbs.
- **`estimated: true` should be visible in the UI** — a free-text macro guess is not a barcode
  lookup, and the coach shouldn't treat them as equally reliable.
- Unknown fields on incoming meals are preserved, not stripped (forward compatibility).

### Reads the hub does

Nothing new needed — it reads `data.json` directly:
- **Latest bodyweight:** newest `bodyweights` entry for that person (kg).
- **Today's session:** derived from `program` + weekday + the 5am rollover. Not a stored field.

## Work needed in this app

Ordered; each is independently useful and stops for review, per the usual convention.

### 1. Multi-writer retry ✅ DONE
`data.json` already has 3+ writers: both phones, `mcp-coach`, `mcp-garmin`. The hub makes 4+.
Every writer sends the file's `sha`, so a concurrent write **409s rather than silently losing data**
— the safety property is already there. But **nothing retries on 409**, so it just errors
(`_github_write`, [mcp-coach/server.py:76](../mcp-coach/server.py#L76)).

`_github_update(mutate, message)` in both servers does `read → mutate → write`, re-reading and
reapplying on 409/412 (3 attempts, backoff) and then failing with a readable message. Other HTTP
errors still raise immediately. `fill_pending` keeps its Garmin calls *outside* the retry loop, and
re-checks on write that an activity wasn't claimed meanwhile, so a race can't link one run twice.

**The store is now safe for a fourth writer — the hub can be pointed at it.**

**Amended tt-v107 (19 Aug 2026).** Retry-on-409 stopped concurrent writes *losing the file*, but
the record merge itself was still a wholesale replace, which lost a *field*: a session note typed
on a phone was overwritten by the store's older copy and pushed back empty. `mergeRecord` fixes it
for `logs` and `meals` both — see the conflict rule under the `meals` contract above. **The hub
must stamp `updatedAt`**; that is now a hard requirement of being a writer, not a nicety.

### 2. `meals` in state + merge ✅ DONE
`state.meals`, `exportPayload`, and a `mergeInData` branch that upserts by id (mirroring `logs`),
plus a `load()` migration for installs saved before the change. Unknown fields on incoming meals are
preserved, so the hub can add fields without a change here. `CACHE_NAME` → `tt-v42`.

**Hub-written meals now survive sync in both directions, with no UI yet.** Nothing is displayed until
item 3 — a meal in the store is currently invisible in the app.

### 3. Nutrition UI (the roadmap item, now with a data source)
- Per-person daily targets (kcal + protein) alongside the existing goals.
- Today's totals on **Home** as a tile — reuse the `.tile` pattern from `renderHome`.
- A **Nutrition** view or a Body-tab section: day list, per-meal rows, weekly protein trend
  (Chart.js, as the bodyweight trend does).
- Manual add/edit, so the app is usable with the hub off or not yet built.
- Light + dark, no console errors, and **update `renderHelp`** — the Guide must reflect it.

### 4. Coach sees nutrition
- Add a `nutrition(person, days)` tool to `mcp-coach/server.py` (daily kcal/protein totals, target
  adherence, `estimated` flagged).
- Include a nutrition line in `coachBrief`.
- Mention it in `docs/coaching-prompt.md` so the weekly chat actually uses it.

### 5. Move the Garmin sync to the home server (free win)
The Task Scheduler jobs run on the laptop, with the known caveat *"only runs while the laptop is on."*
Once the Pi exists for Home Assistant, move both jobs (`--sync training-garmin` and
`--sync training-garmin-cerys`) onto it as cron entries. Deterministic Python, no laptop-specific
dependency, no code change — the caveat just disappears. Needs `.mcp.json`-equivalent env on the Pi
and a re-login to cache each Garmin session there.

### 6. Run the coach itself on the Pi - unattended coaching

**Status: agreed in principle 2026-08-19, nothing built.** Daniel's call: *"unattended is fine for the
coach - it pushes new coaching, with anything changing to the program either being pushed because I
asked for the change, or any changes suggested by the coach are pushed to the app for me to agree to."*

A cron job on the Pi runs Claude Code headless against `docs/coaching-prompt.md`, so a review happens
without anyone opening a chat. Feasible because the pieces are already portable:

- Both MCP servers are Python reading the **GitHub store**, with no laptop-specific state - the same
  property that makes item 5 free.
- The reasoning runs on Daniel's **Claude subscription**, not the paid API, so the "keep it free"
  constraint from `hub-and-coaching.md` §B3.3 still holds. That section rules out *API-on-save*; it
  does not rule this out.

#### The permission model already exists in the tools

| Tool | Reaches the phones | Gate |
|---|---|---|
| `write_coaching` | immediately | none - intended, this is the point |
| `propose_suggestion_tool` | only once approved | gear menu, Daniel approves |
| `write_session_notes` | immediately | **none - this is the gap** |

**Decide this before the first unattended run.** `write_session_notes` rewrites warm-ups and
cool-downs, which is a program change by any reasonable definition, and it writes straight through.
An unattended coach could rewrite both athletes' warm-ups overnight with no approval step. Two
options: route session-note changes through the suggestion gate as well (preferred - more useful, and
it matches the rule Daniel has already set), or restrict unattended runs to `write_coaching` +
`propose_suggestion_tool` and leave notes for when he is in the chat.

#### Trigger on a schedule, NOT on save

Load-bearing, and learned the hard way on 2026-08-19: Daniel added a note to his Upper 1 session
**after** saving it. The app supports that deliberately (backlog item *"add option to add notes after
saving a workout"*, shipped), and the note is the single highest-value part of a session for
coaching - injuries, form cues and program requests live there and nowhere else. A save-triggered
review would routinely coach a session whose note does not exist yet, and would never see it.

So: **fixed daily schedule, late** (04:00 suits, and matches the ~5am training-day rollover). Coach
everything logged since the newest `coachingLog` entry for that person. Late enough that both the
notes and the Garmin runs have landed; no-ops cheaply on a rest day.

**Ordering matters:** `--sync` (item 5) must run *before* the coach, or the coach reviews a cardio
session with no run attached to it.

#### Setup

1. Python 3 + deps; clone the repo (or copy `mcp-coach/` and `mcp-garmin/`).
2. `.mcp.json`-equivalent env: GitHub token, both Garmin credential blocks. Same secrets item 5
   needs, so do the two together.
3. Claude Code installed, and authenticated **once interactively** to cache subscription auth. This
   is the fiddly step on a headless box and the only genuinely new setup cost.
4. Cron: `--sync` for both people, then the coach, in that order.

#### What this does not solve

Quality. Every review so far has turned on something only Daniel could supply - the stated limiters,
his *"is 4 sets too much?"* question, the 100kg squat that overturned advice given three days earlier.
Unattended coaching is a good **floor** (nobody has to remember to ask), not a replacement for the
weekly chat. Detection alone - an in-app "N sessions since your last coaching" badge, computed from
`logs` vs `coachingLog` with no server at all - captures much of the value for far less machinery,
and should probably land first.

## What this app must NOT do

- **Don't call the hub.** No outbound dependency on a home server from a public GitHub Pages app.
- **Don't move the store.** GitHub-as-store stays; the hub adopts it, not the reverse.
- **Don't put the hub's GitHub token anywhere client-side.** Hub backend only.
- **Don't build meal capture here** (barcode/camera) — that's the hub's half of the split.

## Sequencing with the hub

Hub phases 1–4 (Home Assistant, plants, climate, chores/bills) touch none of this — they can run to
completion before anything here starts. Only **hub phase 5** needs this side, and it needs items 1–2
above to exist first.

Sensible order: ~~item 1 → item 2~~ ✅ **done — the hub is unblocked** → hub builds capture →
**items 3–4** land the display and coaching side → **items 5–6** whenever the Pi is up.

Items 5 and 6 share their whole setup - same box, same secrets, same cron file - so they are one
piece of work, not two. Item 6 also has a cheap precursor that needs no Pi at all: the in-app
"N sessions since your last coaching" badge described at the end of it.
