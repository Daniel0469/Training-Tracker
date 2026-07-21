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
| **Bodyweight display** | one tile | ✅ Body tab, trend chart, goals |

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
  "estimated": true                // true when macros came from an LLM guess, not a database
}
```

Rules, all matching existing conventions:

- **Merge by `id`, upsert.** Same as `logs` (`mergeInData`, [js/app.js:1582](../js/app.js#L1582)).
  Re-syncing the same meal must never duplicate it.
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

### 1. Multi-writer retry (do this first — it's the only real risk)
`data.json` already has 3+ writers: both phones, `mcp-coach`, `mcp-garmin`. The hub makes 4+.
Every writer sends the file's `sha`, so a concurrent write **409s rather than silently losing data**
— the safety property is already there. But **nothing retries on 409**, so it just errors
(`_github_write`, [mcp-coach/server.py:76](../mcp-coach/server.py#L76)).

Add a shared `pull → modify → push, retry on 409 (3 attempts, small backoff)` helper and use it in
both Python servers. Small, self-contained, and it makes the store safe for a fourth writer.

### 2. `meals` in state + merge
- Add `meals: []` to `state`, `exportPayload` ([js/app.js:1572](../js/app.js#L1572)), and
  `mergeInData` (upsert by id, mirroring the `logs` branch).
- Migration in `load()` for existing installs (missing key → `[]`).
- Bump `CACHE_NAME` in `sw.js` (currently `tt-v41`).

This alone makes hub-written meals survive sync, before any UI exists.

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

## What this app must NOT do

- **Don't call the hub.** No outbound dependency on a home server from a public GitHub Pages app.
- **Don't move the store.** GitHub-as-store stays; the hub adopts it, not the reverse.
- **Don't put the hub's GitHub token anywhere client-side.** Hub backend only.
- **Don't build meal capture here** (barcode/camera) — that's the hub's half of the split.

## Sequencing with the hub

Hub phases 1–4 (Home Assistant, plants, climate, chores/bills) touch none of this — they can run to
completion before anything here starts. Only **hub phase 5** needs this side, and it needs items 1–2
above to exist first.

Sensible order: **item 1 → item 2** (small, safe, unblocks the hub) → hub builds capture → **items
3–4** land the display and coaching side → **item 5** whenever the Pi is up.
