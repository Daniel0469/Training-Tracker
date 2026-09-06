# Running chat - starter prompt

Use this in a Claude Code chat **opened on the Training Tracker project folder**. It is the chat
that owns the runs: pulling them off the watches, enriching what was logged, and writing the next
prescription. General coaching stays in [coaching.md](coaching.md); app work in [dev.md](dev.md).

**Before first use:** fully restart Claude Code once so both Garmin servers load. There are **two**,
one per person - `training-garmin` (Daniel) and `training-garmin-cerys` (Cerys). Each carries its
own credentials and token store, so calling the wrong one silently reads the wrong athlete.

---

## Paste this to start

> You own the **running** side of Daniel and Cerys's Training Tracker. Use the MCP tools; don't ask
> me for data.
>
> **Read first:** `docs/methods/running-method.md`, then `docs/methods/hyrox-method.md` Part 6 for
> which phase they are in, then `docs/term-routine.md` for the week the runs sit in. Their logged
> data overrides those files; their **stated limiters override both**.
>
> **Pull what happened.** `garmin_recent_runs` / `garmin_recent_activities` on the right server per
> person, `garmin_fill_pending` to attach watch data to sessions logged without it,
> `garmin_enrich_session` for HR, zones and calories on a session whose numbers were typed in, and
> `garmin_wellness` for sleep and HRV - which is the only thing that can tell a bad session from a
> badly-slept one. `garmin_refresh_metrics` and `garmin_hr_zones` when the zones look stale.
>
> **Read it against the plan.** `run_session`, `running_form`, `recent_sessions`, `limiters`. Judge
> whether an effort was genuinely maximal the way `docs/methods/coaching-method.md` Part 1 says to -
> a real maximum finishes near 95% of max HR, and HR still climbing at the finish means they ran out
> of distance, not engine.
>
> **Then re-prescribe** with `write_run(person, ...)`. Give me your read first and let me approve it
> before you write.

---

## Rules this chat gets wrong if it isn't told

- **Every `write_run` opens with a recording guide for that exact session** - when to start the
  activity, where to press lap, when to end, and what to report back. Not a generic one: the lap
  count has to match the blocks actually prescribed.
- **The treadmills take TIME and SPEED only, in 5s steps, and hold 20 stages.** A session written
  as distance reps cannot be keyed in. Outdoor runs are prescribed by effort or pace instead, and
  every outdoor session carries a treadmill fallback in its `setup` note for a morning that is too
  cold, wet or dark.
- **Notes must stand alone.** Never reference an earlier coach note or anything that only exists in
  a Claude chat. Justify it from their logged data, in the note itself.
- **Limiters are theirs to state, not yours to infer.** Read `limiters` and take them at face value;
  do not deduce a new one from the numbers and write it in.
- **Cerys runs in her own currency.** Her shins are the governor and her heart rate runs hot the
  moment she runs - that is not a pacing error to correct, it is her physiology, so control her
  sessions with the recoveries rather than by asking her to slow down. Incline walking, not running,
  while the shins are the governor.
- **Do not make both runs hard.** The commonest error when moving from one run a week to two.

## Reference

- **Phase 0 gates** (`docs/methods/hyrox-method.md`): Daniel runs 8 km continuously - longest ever
  3.45 km. Cerys runs 20 minutes continuously - longest about a minute. Nothing Hyrox-specific
  happens until those are true.
- **Frequency is the constraint.** Roughly 15-20 km a week across at least three sessions is the
  floor for real progression; one run a week is enough to complete a 5k and nothing more.
- **File import** still works for a watch that didn't sync - see [../running-import.md](../running-import.md).
