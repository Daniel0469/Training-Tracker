# Backlog

Open work, newest batch first. Raised from session feedback notes and the in-app Suggestions box.
Coaching notes belong in the app (via `write_coaching`); anything that needs a code or program change
lands here instead.

---

## Batch: 29 Jul 2026 (Daniel, from Cardio: Speed + Core feedback) - DONE 30 Jul

Sections A, B and C are shipped. **Section D is still open** and needs Daniel's approval.

### A. App code changes - ✅ done

- [x] **RPE for running exercises.** Gate widened from `isLifting(ex)` to
      `isLifting(ex) || isGarminCardio(ex)`. `isGarminCardio` already existed and picks out exactly
      the cardio worth rating (Treadmill intervals, Easy run (Zone 2)) while leaving the `Min`/
      `Notes` warm-up and cool-down rows alone. Everything downstream - draft capture/restore,
      save, the History readout - was already type-agnostic, so no other change was needed.
      Guide updated. `tt-v86`.
- [x] **Goal section expands to fit.** The *display* was never the problem (it's
      `white-space:pre-wrap`). It was the `#pGoals` textarea in the gear menu, pinned at a two-row
      `min-height` with the overflow hidden, so Daniel's four goals scrolled out of sight while he
      typed them. Now uses the existing `autoGrow()` helper. In-app suggestion `1785353252857`
      resolved. `tt-v87`.
- [x] **Standing *or* seated quad stretch.** Daniel confirmed he meant the cheap reading: the
      cool-down line now reads "Standing or seated quad stretch - 40s each side". A genuine
      either/or picker on an exercise is **not** built - see "Parked" below.

### B. Program-data edits - Cardio: Speed + Core warm-up/cooldown - ✅ done

**These were never exercise edits.** The mobility work lives in the session's free-text
`warmupNote` / `cooldownNote` (added 29 Jul), so all nine are text edits to two blocks on
`cardioSpeed`. Applied straight to the live store, which both phones adopt on their next sync.
Script: `scratchpad/apply_cardiospeed.py` (idempotent, writes a `data.json` backup first).

Scope confirmed with Daniel: **Cardio: Speed + Core only.** Hip CARs, 90/90s and the closing
breaths line appear in all six sessions; the other five keep their own numbers.

- [x] Add pigeon pose to the warm-up — placed in the **warm-up** as asked. Flagged first that a
      deep static glute stretch before speed work is usually a cool-down item and that the
      cool-down already has Figure-4; Daniel chose the warm-up anyway.
- [x] Clams → 10 slow reps each side — was in the **cool-down**, not the warm-up
      ("Isometric side-lying clam - 3 x 20s"), so it also stops being an isometric.
- [x] Hip hikes → 2 sets (down from 3) — also a **cool-down** line.
- [x] Hip CARs → 5 each side
- [x] 90/90s → 10 each side
- [x] Remove strides from the warm-up — flagged that strides are what primes the first hard rep,
      which pulls against section D; removed as asked.
- [x] Remove breaths
- [x] Remove the cardio item from the cooldown — Daniel confirmed he meant the **jog line in the
      note text**, not the `Cooldown` exercise card. Flagged that "do not stop dead after the last
      interval" is the one line with a real job; removed as asked.
- [x] Make warm-up/cooldown cardio generic — "Easy jog, 5 min" → "Any easy cardio, 5 min".
- [x] *(consequence, not a request)* Cool-down header 10 min → **5 min**, since dropping the
      3 min jog + 2 min walk took half the block out.

### C. Repo default program had drifted from the live program - ✅ resolved by deletion

The drift was real and worse than first written up, but **the fix was to delete the default, not
to sync it** (Daniel's call).

Correction to the original note: this would **not** have bitten a fresh install. `load()`'s
blank-install fallback returns `program:{order:[], sessions:{}}` and onboarding builds from there.
`DEFAULT_PROGRAM` was reachable from exactly one place - Settings → "Reset program to default".

That made it a **live footgun**, not a cosmetic staleness: `saveProgram()` stamps a fresh
`updatedAt` and pushes immediately, and `mergeInData` adopts any program whose stamp is newer. So
one tap of Reset would have pushed the July snapshot to the store and **both phones would have
adopted it**, silently replacing the warm-up/cool-down notes, the corrected exercise names, the
pull-up `load:"assist"`, the supersets and the muscle tags.

- [x] `DEFAULT_PROGRAM` deleted (429 lines). The program lives in the synced store; the repo no
      longer carries a copy to go stale.
- [x] "Reset program to default" → **"Clear program"**: downloads a backup file first, then
      requires typing `RESET`. `exportData()` now reports success so a blocked download aborts the
      clear rather than pressing on with no backup. Guide, settings caption and `CAPABILITIES.md`
      updated. `tt-v88`.

### D. Proposed - needs Daniel's approval (program structure)

- [ ] **Lengthen the treadmill interval reps.** The target is currently
      `6x1 min hard / 2 min easy` (`js/app.js:335`). On 29 Jul Daniel ran those reps at 13 km/h
      (4:37/km) and peaked at **max HR 157** - 79% of a 200 max, against a 173 threshold, with zero
      seconds above Zone 3 across 18 minutes. One-minute reps are too short for his HR to catch up,
      which is why a faster-than-race pace session came out easy.
      Suggested change: `5 x 2-3 min hard / 90 s easy`, and hold the speed at 12 km/h.
      This is a program-structure change, so it needs a yes before anyone edits it.

      **Status 30 Jul: still awaiting Daniel's approval - deliberately not actioned.** Note that
      section B removed the strides from this session's warm-up, which pulls the same way (less
      priming before the first hard rep), and the coaching note already visible on the session says
      the same thing: drop to 12 km/h, 2-3 minute reps, shorter recoveries, finish in Zone 4.

### Parked (raised 30 Jul, not built)

- [ ] **A real either/or alternatives feature on an exercise.** The 29 Jul quad-stretch request was
      settled with a rename, but the underlying gap is real: the program model
      (`{name, warmup, notes, target, sets, cols[]}`) has no concept of "this movement or that one".
      A proper version needs a `variants` array, editor UI, a picker on the log form, and a decision
      on whether history is shared across variants or split - which runs straight into the
      exercise-name-fork problem below. Scope it on its own, not as a sub-item.

---

## Also outstanding (raised 29 Jul, separate write-up)

- [ ] **Exercise-name forks are breaking the app's own progression suggestions.** Same movement
      logged under multiple names, so the "up from last session" comparison resets each time:
      `Bench press` / `Flat press (DB)`; `Incline bench` / `Incline DB press`;
      `Seated row` / `Seated cable row`; `Standing calf raise` / `Calf raise`;
      `triceps ext` / `Triceps pushdown`; `Russian twists` / `Russian Twists` (capitalisation only).
      `Squat` now covers two different variations (front/goblet and back squat), which also makes the
      PR list misleading.
      Note: renames orphan history, so this needs a plan rather than a find-and-replace.
- [ ] **Bodyweight entries look carried-forward, not measured.** Daniel is logged at exactly 77.2 kg
      every day from 14-26 Jul with nothing on 27-29 Jul. Worth checking whether something is
      auto-filling the previous value. Cerys has no bodyweight logged at all.
- [ ] **Session duration can disagree with Garmin.** Cerys' 26 Jul session stored
      `durationSec: 48` while the linked Garmin activity recorded 4:26 moving time, which made the
      MCP `running_form` tool report a nonsense 1:38/km pace.
