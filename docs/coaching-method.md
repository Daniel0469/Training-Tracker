# Coaching method - principles, observations and constraints

**Read this at the start of every coaching chat, before writing any session.** It exists so the
coach does not re-research the same ground every week, and so that what has been *learned* about
Daniel and Cerys survives between conversations instead of living only in one chat's context.

## How to use it

Three rules, in priority order:

1. **Their logged data beats this file.** If a principle here says one thing and their numbers say
   another, the numbers win and the file gets updated. A method file that cannot be contradicted
   becomes dogma within a month.
2. **Their stated limiters beat both.** `limiters(person)` is the athlete's own account of what is
   holding a session back. It is not derivable from the data and it overrides the coach's reading -
   say so out loud rather than quietly coaching around it.
3. **Principles and observations are kept apart, deliberately.** Principles are slow-changing
   training theory. Observations are what we have learned about these two specific people, and every
   one carries a date. A stale observation dressed up as a principle is worse than no file at all.

This file does **not** duplicate what the tools already return. PRs, session history, limiters,
goals and past coaching all come from `training-tracker`. Read those too.

## Every review, without exception

**Re-write the 5k card after every run.** Call `running_form(person)` and pass `five_k` on the
`write_coaching` call, every time, even when the number does not move - say what the new run added
and what it did not. The card shows its own last-updated date, so leaving it out makes it look
neglected even when the figure is still right.

The trap that caused this to be missed twice in one week: **`write_run` has no `five_k` field.** A
session can be re-prescribed all day without the estimate ever being touched. If a run has been
logged and the only tool called was `write_run`, the review is not finished.

---

# Part 1 - Principles

## Which session type, at which level

The single most important call, and it changes as they get faster.

| Current 5k | Emphasis | Why |
|---|---|---|
| Over ~25 min | **Threshold**, almost exclusively | The race is a 25-30 min effort. It is an endurance event for them, closer to what a 10k runner trains for. |
| 20-25 min | Threshold-led, occasional race-pace work | Still endurance-dominant, but race-pace rehearsal starts to pay. |
| Under 20 min | VO2max work matters more | Racing at the edge of maximum aerobic capacity, so intervals at 5k pace push the actual ceiling. |

**The common error is copying elite sessions.** A 13-minute 5k runner is racing at VO2max, so their
5k-pace intervals are VO2max work. A 25-minute runner doing the same session burns out at 15 minutes
because nothing trained them to keep going. Train the duration they will actually race.

**Threshold** means comfortably hard - an effort sustainable for 25-30 minutes. Typically 5k pace
plus 15-25 s/km, or roughly 5-7% slower than 5k pace. Classic shape: 4-5 x 6 min with 1-1.5 min
recovery.

With **one run per week**, threshold is the default. It is the highest-yield single session for
anyone over 20 minutes, and it is also what stops the aerobic base eroding.

## Current pace vs goal pace

They are two different tools and both matter:

- **Long reps (1000m / 5 min and above): run at CURRENT race pace.** That is where fitness actually
  is, and it builds race-specific endurance.
- **Short reps (under 1000m / under 5 min): run at GOAL pace.** Short enough to handle the speed, and
  it teaches the body to move efficiently at the pace being chased.

Sanity check first: if current and goal pace are within a few seconds per km, the distinction is
academic and either number works. That is currently true for Daniel (5:06 vs 5:00).

## Recovery: standing, walk, or float

Ranked by how race-like they are:

1. **Standing rest** - easiest, least specific. Fine only when the point of the session is the rep
   quality and nothing else.
2. **Walk** - the middle option, and the right one when total impact load must be controlled
   (returning from injury).
3. **Float** (easy jog between reps) - hardest and most race-specific. Trains the body to clear
   lactate *while still running*, which is what kilometre four of a race actually demands.

**Float is the goal for a healthy runner, and doubly so for Hyrox** where running on tired legs is
the entire event. Expect rep times to suffer at first while adapting. Do **not** prescribe float to
someone whose limiter is tissue tolerance - see the overrides.

## Progression rules

- **Duration before intensity.** Add time at a pace before adding pace.
- **Hold a known speed across weeks** while volume climbs, so the sessions are comparable.
- **A completed rep range earns the next load**, not a good feeling.

## Returning to running after shin splints (MTSS)

Evidence-based sequence, and it is worth following properly - roughly half of people who rush this
end up back where they started:

1. Pain-free **walking** for 10-14 consecutive days before any running.
2. Restart with **run/walk intervals**, around a third of pre-injury running volume.
3. Build over **2-4 weeks**, no more than ~10% more running each week.
4. **Rep length is the variable that loads shins hardest** - hold it constant and add reps first.
5. Calf and hip strengthening throughout; calf length is shin insurance.
6. Stop at the *first* twinge, not the second. One flare means hold at the current step, not go back.

## Hyrox specifics

- The event is **8 x 1km runs** separated by eight stations. The skill is **compromised running** -
  running well on legs that are already wrecked.
- The winning quality is **metronomic consistency** across all eight runs, not a fast first one.
- **Target pace = 15-20 min time-trial pace + 10-15 s/km**, to account for station fatigue and the
  stop-start.
- A repeat is usually the right training unit. Compromised-running sessions (run straight off a
  lifting station) are the most specific thing available.

## Race pacing framework

Useful for time trials as well as races, and it fixes the most common pacing error:

- **Km 1-2** - get into rhythm. Should feel manageable, not easy.
- **Km 3-4** - this is where the race is won. Expect to suffer. Aim to speed up slightly; in practice
  holding the same pace while it feels much harder is the win.
- **Km 5** - the free kilometre. Empty the tank.

Anyone can run the first two and the last one. Km 3 and 4 are the ones to win.

## Reading the data: never trust an average over mixed work

This has produced two wrong coaching cues in a single week, so it is a principle rather than a note.

**An average is only meaningful over work of one kind.** A recording that contains a warm-up, an
effort and a walk produces summary figures that describe none of them:

- Daniel's whole-activity **cadence read 116 spm**, and he was told to shorten his stride. His actual
  running cadence was 157-166. The 116 was dragged down by ten minutes of walking at 82.
- Cerys appeared to **drift 158 to 166 bpm** across a rep block, and was warned her recoveries were
  too short. Rep by rep her heart rate was flat at 167-172 from rep 2 onward; the "drift" was two
  lap averages containing different amounts of walking.

**Always read the per-rep or per-lap figures before drawing a conclusion, and say which you used.**
`garmin.reps` gives per-rep speed, HR, cadence and recovery; `effort_drift` gives first-half against
second-half HR within a single continuous effort; `garmin_activity` splits carry their own HR. The
activity-level `avg_hr` and `cadence_spm` describe the whole recording and are routinely misleading
for any session with more than one kind of work in it. **Pace for a run comes from
`efficiency.run_pace`**, which is measured over the running blocks only; the old `pace_per_km` field
was removed on 26 Aug 2026 because it divided whole-session time by running distance and reported
figures like 56:13/km.

Corollary: when a metric contradicts what the athlete reports, check the metric's basis before
telling them they are wrong.

## Judging whether an effort was truly maximal

- A genuine maximum finishes at **~95% of max HR**. Finishing at 90-91% means there was more in there.
- **HR still climbing at the finish** means they ran out of distance, not out of engine.
- Time spent **below threshold HR early** in a max effort is time given away.
- A negative split is good judgement, but a *large* one means the start was too conservative.

---

# Part 2 - Observations

Dated. These are about these two people specifically and they expire - re-check rather than assume.

## Daniel

- **2026-08-20.** Responds to load faster than an incremental model predicts. Three times running he
  has overtaken a prescribed progression and it landed: squat 70 to 80 when 75 was asked, bench 20 to
  50 when 40 was asked, squat 80 to 100 when a rep target was asked. Give a target and a ceiling and
  let him pick inside it, rather than a single number.
- **2026-08-20.** Huge speed reserve, thin endurance base. Held 13 km/h reps at 79% of max HR back in
  July, but his longest run ever is 3.45km. Speed has never been the limiter; duration at pace is.
- **2026-08-20.** Paces conservatively when the distance is unfamiliar. In his first 2km trial he ran
  the whole first kilometre below threshold and finished at 91% of max HR, still climbing.
- **2026-08-20.** Running cadence is 157-166 spm and is fine. Do not read whole-activity cadence -
  a recording containing a long walk drags it to ~116 and it means nothing.
- **2026-08-19.** Sessions overrun and end early when the main lift is 4 sets. At 3 sets the same
  session finished in 66 minutes with every lift held or improved.
- Repeated notes of "feel tired", "low energy", "ended early - hungry". **No overnight wellness data
  exists** to tell whether that is load, sleep or fuelling.

## Cerys

- **2026-08-20, corrected 2026-08-21.** Heart rate runs hot the moment she runs - Zone 4 within a
  minute even at an easy 10 km/h. This matches her own limiter ("Zone 2 is a walk for me, not a
  run"), so **do not fix it by asking her to slow down**; control the session with the recoveries.
  But it **plateaus rather than drifting**: rep by rep on 20 Aug she went 143 (still catching up
  from the warm-up), then 167, 168, 172, 170, 169 - flat across five reps. An earlier version of
  this entry said she drifted 158 to 166, which was a lap-average artefact. See the reading note
  in part 1.
- **2026-08-21.** Recovers well between reps and is improving at it: 40 bpm dropped per walk down to
  around 140 on 20 Aug, against 33 bpm and only down to 151 on 29 Jul. Consistency across reps went
  from 30.8% spread to 11.6%, fade from 28% to 11%.
- **2026-08-21.** Times hand-run reps generously. Her prescribed 6 x 1:00 actually ran 64, 80, 77,
  97, 76 and 65 seconds. Not a criticism - she was counting them herself - but it means any
  hand-timed session's volume is understated. The programmed treadmill sequence removes this.
- **2026-08-20.** Shins are the governor, not fitness. Her 29 July intervals hit max HR 192 with ten
  minutes above Zone 4; she is plenty fit. Twelve days of walking-only fixed a three-week problem.
- **2026-08-20.** Executes a fixed-speed prescription accurately. Given "10.0 km/h every rep" she held
  it across every rep bar one. Prefer explicit numbers over "whatever feels right".
- **2026-08-20.** Incline walking at 4-6% sits reliably at HR ~139 and is genuinely pain-free aerobic
  work. It is her engine while running rebuilds, not a consolation prize.
- **2026-08-19.** Third joint flagged in six weeks (shins, left hip, right shoulder). None serious,
  all settling, but the pattern warrants caution rather than bravery.
- Her notes under-record what went well. Say the good part explicitly.

---

# Part 3 - Overrides and do-nots

- **Float recovery is for Daniel, not Cerys** - while her limiter is tissue tolerance, the walks are
  deliberate load management and replacing them would undo the point of the session.
- **Never prescribe Cerys a low-HR run.** She has told us she cannot run slowly enough to sit in
  Zone 2, and the data agrees. Non-impact incline walking is how she gets Zone 2.
- **Pull-ups are Cerys's only stated strength goal** and need neither shins nor hips. When something
  else is injured, that is an opportunity, not a lost week.
- **Do not diagnose.** Pain notes get deload, mobility, footwear and "if it persists, get it checked".
- **Program structure is not the coach's to change** except each person's own run session. Sets, reps,
  targets and which exercises go through `propose_suggestion_tool` for Daniel to approve.

## Writing warm-ups and cool-downs

Daniel set these on 2026-09-02, after we rewrote all eight sessions together. They apply to every
future write of a `warmupNote` or `cooldownNote`.

**These are settled decisions, not suggestions, and the coach does not get to undo them.** Do not
reinstate anything removed below, do not re-add a traffic light or a person-specific line to a note,
and do not restore a strength exercise to a cool-down because the session looks light without it. If
you think one of them is wrong, say so and put it through `propose_suggestion_tool` for Daniel to
approve - never just write it back.

What was removed on 2026-09-02, so you can recognise an accidental restoration:

- Copenhagen plank, side plank, dead bug, seated march and single-leg glute bridge, out of the
  Lower 1 and Lower 2 cool-downs.
- Hip hike and side-lying clam, out of the Run: Cerys cool-down.
- PAILs/RAILs in 90/90, out of the Cardio: Endurance + Core cool-down. It is flexibility training and
  belongs in its own session, not on the end of a cardio day.
- The adductor traffic light (green/amber/red), out of both Lower warm-ups.
- The leg press, squat and flat press ramps, out of the notes - each is already on its exercise card.

**Equally, do not overwrite what was moved INTO coaching.** The Cerys cautions on Lower 1, Lower 2,
Upper 1, Upper 2, Cardio: Endurance + Core and Run: Cerys, and the adductor red flags on both Lower
sessions for both people, now live in `coaching.bySession` because that is the only place they are
allowed to live. They are the reason those lines are no longer in the notes. A `write_coaching` that
replaces a `bySession` entry wholesale will silently delete safety guidance - carry the existing text
forward and add to it.

**What each block is for**

- A **warm-up is preparation for today's session and nothing else.** The range it buys is
  viscoelastic and gone within hours - which is exactly what a warm-up is for. Never write one as
  though it builds flexibility.
- A **cool-down is stretches and breathing.** No strength work, no flexibility training. If an item
  has sets and reps and you would *work* at it, it is an exercise and does not belong here.
- **Lasting flexibility is trained in its own session**, not bolted onto either end of a lifting day.
  It is training rather than recovery, and it fatigues like training - which is why doing it while
  already fatigued suppresses the adaptation you wanted.

**What does not go in them**

- **No decision rules.** Traffic lights, train-if/skip-if gates and red-flag lists are read before you
  start, not performed. They are not warm-up items.
- **No person-specific notes.** Anything addressed to one of them goes in coaching (`bySession`, keyed
  by session name), never inline in the note text.
- **No ramp that is already on the exercise card.** `ex.warmup` renders on the card itself, so
  repeating it in the note prints it twice on one screen.

**Numbers**

- The stated duration is **computed from the list, not asserted.** Both Lower warm-ups claimed 12-13
  min for months while actually running past 20, because the isometrics were never counted.
  `scratchpad/note_times.py` does the arithmetic. Correct the list or correct the number, but never
  leave the two disagreeing.

**Formatting - phone rules, not taste**

Session notes render `white-space: pre-wrap`, so a hard line break is kept *and* the line is wrapped
again when it is too long for the screen.

- **Never align columns with runs of spaces.** A wrapped line loses its indent completely and the
  table collapses into rubble. This is what destroyed the first rewrite of the adductor traffic light
  at 375px.
- **Keep lines under about 95 characters**, matching the existing notes. Continuation lines then read
  as an ordinary paragraph.
- Use `- ` for list items. A four-space indent for a continuation line under an item is fine.

---

# Part 4 - Equipment constraints

These shape what can actually be prescribed. Ignoring them produces sessions that cannot be run.

## The treadmills

- **Only TIME and SPEED can be set**, and time only in **5-second increments**. There is no distance
  target. So **every run session must be written as time x speed blocks**, never as "4 x 1000m".
  Distance still falls out of it (6:00 at 11.0 km/h = 1100m) and can be used for calibration.
- **They take a programmed sequence, capped at 20 stages.** The whole session goes in as a list of
  blocks up front and the belt steps through it on its own. Daniel's explicit reason for wanting it
  that way is so he does not have to adjust anything mid-run.

  **Count the blocks before prescribing.** A 21-block session for Cerys on 26 Aug exceeded the limit,
  so the tail of it - her incline walk - was cut short. A rep set costs 2n-1 blocks, so 8 reps with
  walks is 15 before any warm-up or cool-down. Move the warm-up to the bike when the count is tight.

  **Do not read a truncated program as a badly executed session.** On that same run the rep detection
  reported 10 reps of 36-81s at up to 13.6 km/h, and the obvious inference - that she had run too many,
  too fast - was wrong. She ran the eight prescribed slots at the prescribed speed and eased off on
  one. Two of the "reps" were her warm-up jog tests. Check the count against the program before
  concluding anyone deviated, and prefer their account.

  Two consequences for session design. **Speed changes are free** - there is no reason to keep a
  session monotonous to spare them fiddling with buttons, so progression runs, pyramids, alternating
  blocks and surges are all viable. And **every session should be written as a complete
  program-entry table**, warm-up through cool-down, in the order it is entered.

  The one thing that still costs them effort is **lap presses**, since the watch cannot know about the
  belt's program. Most stage changes beep, so "press lap when the belt changes speed" is the cheapest
  possible instruction. Only ask for laps where the data actually needs them - if the recovery is a
  walk, Garmin's run/walk detection finds the reps by itself and no laps are needed at all.
- **They use two different machines**, side by side, same make and model. Same-model units still drift
  apart with belt and roller wear, so a discrepancy between the two of them is not automatically a
  watch problem.

## The watches

Both watches estimate treadmill distance from wrist movement, and both read high:

| | Watch reads | Established |
|---|---|---|
| Daniel | ~9% high | 2km trial measured 2.19km, 2026-08-20 |
| Cerys | ~13% high | per-rep distances against a known 10.0 km/h belt speed, 2026-08-20 |

Cerys's figure is the better-grounded of the two: six reps at a prescribed 10.0 km/h came out at
11.2-11.6 km/h on the watch, giving a ratio of about 1.13 across every rep independently. The
earlier ~15% was inferred from a single typed number. **A known belt speed held for several reps is
the cheapest and most reliable calibration available** - prefer it over a whole-session total,
because it repeats.

Correct for this before drawing conclusions from any watch pace or distance. Prefer the treadmill's
own number wherever it exists, and have them **type** it - typed values are never overwritten by the
Garmin sync.

"Calibrate & Save" at the end of an indoor run improves it over time and is worth doing every session.

## Recording

Every run session gets a **⌚ Recording block** written for that specific session: when to start, each
lap point, when to end, and a map of what each lap holds. It is dual-purpose - the athlete follows it
during the session, and the coach uses it afterwards to find the right data in a mixed activity. See
`garmin-recording-guide-per-run` in the coach's memory.

**Garmin's 1km auto-lap fragments manual laps and must be turned off.** On Daniel's 26 Aug threshold
run the manual presses were correct and captured all four reps and three floats - but auto-lap fired
at every kilometre as well, splitting each 6-minute rep into two laps and producing 14 laps for an
11-block session. The data was recoverable only by pairing each 1.00km auto-lap with the partial lap
after it. With auto-lap off, the manual presses alone give clean per-rep splits.

Until the trace segmentation is fixed, **manual laps are the ground truth** for any session whose
recovery is a jog rather than a walk - the automatic rep detection inverts those, treating the
threshold blocks as recovery.

---

## Sources

Training principles above draw on:

- [HYROX running strategy](https://hyroxdatalab.com/articles/hyrox-running-strategy) and
  [holding pace across 8x1km](https://rb100.fitness/articles/cardio/hyrox-running-engine-8x1km-pace/)
- [Medial tibial stress syndrome - Physiopedia](https://www.physio-pedia.com/Medial_Tibial_Stress_Syndrome)
  and [shin splints return-to-run plan](https://injury.vision/guides/return-to-running-after-shin-splints)
- [McMillan 5K training guide](https://www.mcmillanrunning.com/5k-training-plan-guide/)
- Nicklas Rossner, "5 tactics to run a faster 5K" (YouTube, transcript reviewed 2026-08-20). Source of
  the level-based threshold/VO2max split, the current-vs-goal-pace distinction, float recovery and the
  km 3-4 pacing framework. The linked "5K Speed Blueprint" is an email-capture page with no plan
  behind it; the transcript is the whole of the useful content.
