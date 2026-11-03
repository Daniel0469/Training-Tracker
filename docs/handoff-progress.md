# Handoff progress

Resume checklist for the Training Tracker handoff plan (v6, decisions made 2 Nov 2026). The plan
itself lives in Daniel's Downloads as `Training Tracker Handoff Plan.md`. Tick each item as it lands.
The order of work is not decided. Anything that needs Daniel is marked blocked, and work carries on
around it. Items marked 🤔 or 💡 in the plan need Daniel's go-ahead before they are built.

## Phase 1: Quick fixes

### 1.1 Timed exercises
- [x] Volume counts weight x reps sets only, recalculated on read (Ski erg metres x time was the
      real cause of the huge number). Coach `volume_kg` follows the same rule.
- [x] "Recorded by time" tag on an exercise, set in the exercise dialog.
- [x] Timed PRs: longest hold at a given weight, bodyweight = 0. App and coach `prs`.
- [x] Per-set stopwatch: tap to start/stop, count up or down, grace per exercise, auto-fill toggle.
      Stopping does not start the rest timer.

### 1.2 Rest timer
- [x] Colour change when the rest is up (built 14 Oct).

### 1.3 Sets-done progress
- [x] "Sets done / sets planned" bar at the bottom of the Session tab.

## Phase 2: Friday run to GitHub issues
- [x] Labels on Home-Hub: `needs-confirmation`, `rejected`, `from:coach`, `from:Daniel`, `from:Cerys`.
- [x] Already-built suggestions marked done so they are not filed.
- [x] `weekly-coach` task files open in-app suggestions as `training` issues and marks them done.
- [x] Coach ideas go straight to issues with `from:coach`. Rejected issues are read before proposing.

## Phase 3: Edit saved sessions
- [x] Edit sets dialog in the open History card: sets, warm-up marks, RPE, difficulty, note (built 3 Nov, version 1.3).
- [x] Saving keeps every other key, stamps `editedAt` and `updatedAt`, and checks PRs again for the changed exercises on later sessions.
- [x] Undo for the last five edits per person, 14 days, this phone only.
- [x] `set_log_entry` in mcp-coach stamps `updatedAt`.
- [x] Reviewed by Daniel and shipped as version 1.3 (3 Nov).

## Phase 4: Family setup
- [ ] Blocked on Daniel: export the data from Mum's, Dad's and Brother's phones.
- [ ] Blocked on Daniel: create the free Supabase project.

## Phase 5
- [x] Settings split built as version 1.2 (3 Nov): Profile and Admin tabs, four per-person switches,
      Admin behind a family PIN, and the coach skipping a person with Garmin and coach off.
- [x] Reviewed by Daniel and shipped as version 1.2 (3 Nov).

## Phase 6: Progression
- [x] Research: double progression, with the step by equipment (`docs/methods/strength-method.md`).
- [x] In-app rule with switches: one per person in Settings, one per exercise under the wrench.
- [x] The target shows in the kg and reps boxes, and a blank tick fills it.
- [x] Deloads only on stalls, and only by the coach: the app flags a stall and never changes the load.
- [x] Machine steps learned from the logged weights, and confirmed by a `Step:` line in the setup note.
- [x] Coach tools: `progression`, `write_machine_step`, and targets with a why in `write_coaching`.
- [x] Reviewed by Daniel and shipped as version 1.0 (2 Nov).

## Phase 7
- [ ] Not started.
