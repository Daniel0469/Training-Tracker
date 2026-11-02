# Coach tooling brief - for the dev chat

**Written by the coaching chat, 6 October 2026.** Paste this into the dev chat, or point it at this
file. It says what the coach can already do (so nothing gets rebuilt), what it is blocked on (so the
right things get built), and what is the coach's own job (so the dev chat does not take it on).

Everything below was verified against `mcp-coach/server.py` at commit `712d6fe`, not assumed.

> **Status, updated 6 Oct after `6d1d876`.** The dev chat built the top two items the same day:
> **3.1 and 3.2 are now DONE** and are kept below with their evidence, because the reasoning is
> what justifies the rest of the list. Everything in 3.3 - 3.8 still stands. **The new tools do not
> reach a running coach chat until Claude Code is restarted**, so a coach chat opened before
> `6d1d876` still cannot do these jobs and should say so rather than trying.

---

## 1. How the coach reaches the app

One MCP server, `mcp-coach/server.py`, 23 tools, reading and writing the shared `data.json` on
GitHub. Coaching history lives in its own `coaching-log.json`, off the phones.

Three different routes reach the athletes, and they are not interchangeable:

| Route | Tool | Lands as | Needs a tick? |
|---|---|---|---|
| Advice | `write_coaching` | Teal cards on Home + the log form | No - appears on Sync now |
| Program | `write_program_change` | A card on that exercise in the Program tab | **Yes, Daniel ticks it** |
| Session notes | `write_session_notes` | The 🔧/⌚/🔥/🧊 blocks | No, and **both people see it** |

**An edit to `server.py` does not reach a running server.** Claude Code has to be restarted. The
6 Oct `warmup` schema change needed one, and until it happened the coach chat could not see the new
field. Worth saying in the commit message every time a tool signature moves.

---

## 2. What the coach can already do

Do not build UI or tooling for any of this.

**Reads:** `people`, `goals`, `limiters`, `recent_sessions`, `session(session_id)` (one logged
session in full), `prs`, `bodyweight`, `progress(person, exercise)`, `running_form` (every run, rep
by rep off the watch, HR zones, Garmin's race predictions), `coaching_history`, `suggestions`,
`program_changes`, `session_notes`, `run_session(person, which)`. Plus the two Garmin servers for
activities and wellness.

**Writes:**
- `write_coaching` - `overall`, `by_session`, `by_exercise`, `five_k`, `next_cardio`,
  `session_swap`. All merge. This is the main instrument and it is in good shape.
- `write_run` - re-prescribes one run session **completely**: exercise list, targets, sets, columns,
  per-exercise `notes` and `warmup`, plus all five note fields. The coach owns the run sessions
  outright, so nothing here needs a tick or a developer.
- `create_session` - a whole new session, full control, including per-exercise `notes`/`warmup`.
- `write_program_change` - `sets`/`target` on an existing exercise, `add` a new one (arbitrary
  fields, optional `after`), or `remove` one. The tick-to-apply flow works correctly.
- `write_session_notes` - `garmin`, `setup`, `recording`, `warmup`, `cooldown`, with `append`.
- `write_log_entry` - corrects rows on an already-logged session (for bad Garmin fills).
- `write_limiter`, `propose_suggestion_tool`, `resolve_suggestion_tool`.

**The one-week `session_swap` (25 Sep) works well** and is the right pattern: per person, spent on
first log, reverts itself, dead if it names a missing session. Worth copying for anything similar.

---

## 3. Blockers - what the coach cannot do

Ordered by how much they cost. Each one has the evidence and the concrete ask.

### 3.1 Cannot set `warmup` or `notes` on an existing exercise - DONE in `6d1d876`

> **Fixed.** `edit` now carries `warmup` and `notes`. Deliberately not every field `add` accepts:
> `cols` decides how an exercise is scored and drawn, and changing it under a logged history is a
> worse thing. Verified end to end - the ramp resolves to "bar x8, 30kgx5, 45kgx3" off Daniel's
> last 60kg bench, which is the 28 Sep complaint working again. The original case follows.

`propose_program_change` builds its edit payload from `sets` and `target` only:

```python
else:
    op, fields = "edit", {}
    if sets is not None:   fields["sets"] = int(sets)
    if target is not None: fields["target"] = str(target)
```

Only the `add` branch takes arbitrary fields (`fields = dict(add)`).

**Why this matters now:** the 6 Oct batch made restoring the warm-up ramps the coach's job, and the
25 Sep batch made stripping the settings box back to machine settings the coach's job. **Neither is
possible on any of the 23 lifting exercises.** They are impossible rather than merely undone, which
is a different thing to carry on a backlog.

This is also a live user-facing complaint: Daniel asked "why does it not suggest warm up set
weights?" on 28 Sep, the answer is that no exercise has a ramp saved, and the coach cannot put one
back.

**Do not suggest remove-then-add as the workaround.** It is two ticks per exercise, and a ticked
remove without the matching add deletes the lift from the program.

**Ask:** let `edit` carry `warmup` and `notes` (and ideally any field `add` accepts). One line in
the `fields` dict.

### 3.2 No read path for a lifting session's exercises - DONE in `6d1d876`

> **Fixed.** `program_session(name)` returns a programmed session in full: every exercise in order
> with target, sets, cols, settings, ramp and load, plus the day, who owns it and the four note
> fields. It answered the open question immediately - **Upper A has nine exercises and both
> `Seated cable row` and `Seated row` are in it**, so the 28 Sep row swap is unblocked. The
> original case follows.

`run_session` returns exercises, but only for run sessions. `session_notes` returns name, day and
the four note fields and nothing else. `session(session_id)` returns a **logged** session, not the
program. So for Upper A, Upper B, Lower A, Lower B, Mobility and the assessment the coach has **no
way to see what is prescribed** - exercise names, order, targets, sets, current notes or ramps.

The coach has been inferring the list from `docs/term-routine.md` and from whatever the athletes
logged. That is how a real job got dropped this week: Daniel asked on 28 Sep to make the
plate-loaded `Seated row` permanent and retire the `Seated cable row` slot in Upper A, and the
coach could not do it safely without knowing whether `Seated row` is in the program at all.
Removing the wrong one leaves the session with no row.

The only way found to see a list is to send a deliberately-failing `write_program_change` and read
`failed["exercises"]` out of the error. That is a hack, it writes nothing but looks like a write,
and the sandbox blocks it about half the time.

**Ask:** a `program_session(name)` read tool returning the full exercise list in order - name,
target, sets, cols, notes, warmup, load, plus the session's day and person. It is the mirror of
`run_session` and it is the single biggest gap in the set.

### 3.3 Program changes are not per person

`write_program_change` edits the shared program. There is no per-person form.

**The case in front of us:** Cerys's hips hurt on the hack squat on 22 and 29 Sep, **both times
with no plates added**, so there is no lighter version to try. Daniel's hack squat is his best lift
(70kg 3x8 at RPE 7, a PR). Removing or changing it is right for one of them and costs the other his
best lift, so the coach can only write "skip it" as a coaching note - which does not change what
the app prescribes, and will need re-writing every single week until her hips settle.

Run sessions are already per person and `session_swap` is already per person, so the concept exists.

**Ask:** an optional `person` on `write_program_change`, or a per-person "skip this exercise"
state the Log tab honours. The second is probably cheaper and covers the common case.

### 3.4 Cannot reorder an existing exercise

`op` is only `add`, `remove` or `edit`. `after` exists on `add` only.

The 6 Oct docstring says "Place work that matters EARLY: the deadlift sat last in Lower 1 and went
unlogged for months" - good advice the coach can only follow when adding something new.

**Live cost:** Daniel's farmers carry has now gone unlogged four reviews running. It is a Hyrox
station at race weight and his only direct grip work, and it dies at the end of Upper A every week.
The fix is to move it up the session. The coach cannot. Same shape for the back squat technique
sets, the calf raise, the hip abduction and the back extension in Lower A, all missed on 29 Sep,
all sitting behind work that overruns.

**Ask:** an `op: "move"` taking `after` (or a position), or just let `edit` accept `after`.

### 3.5 No way to withdraw or replace a pending program change

`propose_program_change` refuses a duplicate on `(session, exercise, op)` while one is pending, and
there is no delete. So a change the coach got wrong sits in the Program tab until Daniel ticks or
declines it, and cannot be corrected in place.

**Ask:** a `withdraw_program_change(id)`, matching `resolve_suggestion_tool`.

### 3.6 The set tick does not aggregate for the coach

The 6 Oct work saves `done` on each entry, and `session(session_id)` returns the raw log entry, so
**the tick will reach the coach** once sessions are logged with it. Nothing had it yet when this was
written, which is expected - it starts from 6 Oct.

What is missing is any aggregate. `recent_sessions` does not surface it, and there is no equivalent
of the muscle card's done-against-planned across a week. Judging adherence one `session()` call at a
time is expensive, and adherence is most of what a weekly review is.

**Ask:** put done/planned counts on `recent_sessions` rows, and ideally a weekly per-muscle
done-vs-planned read matching what the Home card now draws.

### 3.7 Machine offsets have to be carried in the athletes' heads

Three machines have a known fixed offset and it has been reported repeatedly:

- Hack squat - 47.6kg starting resistance, counts added plates only (Daniel, 7 Sep; Cerys, 7 Sep)
- Romanian deadlift on the Smith - 20kg added (Daniel, 7 Sep)
- Bench on the Smith - 10kg bar resistance (Daniel, 12 Aug)

Every coaching note on the hack squat has to say "75 added is about 123kg moved", and every PR and
volume figure is wrong by the offset. Cerys's 29 Sep hack squat is logged with a blank weight and
8/6/5 reps, which is the honest answer to "what weight was it" and useless as a trend.

The new Smith tick is the right precedent - a per-exercise flag the coach reads.

**Ask:** an optional `baseWeight` on an exercise, added to the typed figure for volume, PRs and
trends, and shown in the settings box. One number per machine, entered once.

### 3.8 `write_program_change` is intermittently blocked by Claude Code's sandbox

Not an app problem, but it affects delivery. Auto mode classifies it as "Modify Shared Resources"
and refused two calls on 22 Sep and one on 6 Oct while letting others through. Daniel can clear it
with a permission rule for `mcp__training-tracker__write_program_change`. Worth noting in
`docs/CHATS.md` as setup, since the tool looks broken rather than blocked when it happens.

---

## 4. Not the dev chat's job

Leave these with the coach. They are written down so nobody builds a feature for them.

- **The run sessions' notes still describe their old days.** `Zone 2: Daniel` says "Tuesday has no
  class and no train now" and its cool-down says "there is no longer a train to make"; both are
  false on Thursday. `Quality run: Daniel` reads as a Thursday session and sits on Monday. The
  coach can fix all of it with `write_session_notes` / `write_run` and owes it.
- **The run sessions' `setupNote` still carries explanatory prose** (the "WHY THE WARM-UP IS NOT IN
  THE PROGRAM" paragraphs), which the 25 Sep settings-only rule says should go. The coach can fix
  these, because `write_run` takes `setup`. It is only the **lifting** exercises that are blocked.
- **Chest volume, the leg curl, the hack squat, the run slot.** All decided with Daniel on 6 Oct and
  recorded in `docs/prompts/coaching.md`. Programming judgement, not app work.
- **Cerys's hips.** Pending a hip check, which the coach is asking about each review.

---

## 5. Suggested build order

1. ~~**`program_session(name)` read tool** (3.2)~~ - **done, `6d1d876`.**
2. ~~**`warmup` + `notes` on `edit`** (3.1)~~ - **done, `6d1d876`.**
3. **`op: "move"`** (3.4) - fixes the farmers carry and everything else dying at the end of a
   session. Now the top item.
4. **`baseWeight`** (3.7) - retires a complaint that has come back four times across three machines.
5. **Per-person program state** (3.3) - the hack squat needs it now; it will need it again.
6. **done/planned on `recent_sessions`** (3.6), **withdraw** (3.5), **permission rule** (3.8).

## 6. What the coach owes now that 3.1 and 3.2 are done

These were impossible before `6d1d876` and are merely outstanding after it. **All of them need a
Claude Code restart first.**

- **Restore the warm-up ramps** on the main lifts - the first two exercises of each session, per
  Daniel's 6 Oct scope. Syntax `"bar x8, 50%x5, 75%x3"`; `%` resolves against that person's top set.
- **Strip the 23 lifting `notes` back to machine settings**, moving the reasoning into the
  `by_exercise` cards. Carry `warmup` through on every edit or it gets erased again.
- **Retire the `Seated cable row` slot in Upper A**, which Daniel asked for on 28 Sep - now that
  `program_session` confirms both rows are in the session, the removal is safe.
- **Rewrite the run sessions' notes for their real days** (`Zone 2: Daniel` still says Tuesday has
  no train), and strip the prose out of their `setupNote`.
