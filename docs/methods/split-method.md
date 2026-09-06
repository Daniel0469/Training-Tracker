# Split method - choosing the training week, and the evidence that decides it

**Written 2026-09-05.** Research pass on training splits, scoped to Daniel and Cerys's real
constraints.

## Why this file exists

`week-method.md` Part 7 listed the questions worth answering while the week is rebuilt around
Daniel's new schedule, and then deliberately stopped, because the schedule was not known. This file
answers everything that can be answered **before** the timetable lands, so that when it does the
decision is a lookup rather than a research project.

It covers both of them, the whole week rather than the lifting alone, and it treats nothing as
fixed. Daniel's instruction on 5 September: goals can change but a change needs a reason, 60 minutes
is a target rather than a hard cap, and the number of sessions is not capped - find what is
actually optimal.

## How to use it

- **Part 1** is the constraint map. Read it first; it rules out more than the evidence does.
- **Part 2** is the evidence, and Part 2.4 is the single finding that matters most.
- **Part 3** judges each candidate split against those constraints.
- **Part 4** covers the two-a-day and the 05:00 start, which Daniel asked to be designed around.
- **Part 5** covers running and lifting on the same day, which is the only thing here that changes
  how many *days* the week needs.
- **Part 6** is the scenario matrix. **When the timetable arrives, go straight here.**
- **Part 7** is the recommendation, and **Part 8** is the honest problem with the goal set.

**Nothing here is a program change.** `coaching-method.md` Part 3 is explicit that program structure
is Daniel's, not the coach's. This is the reasoning a proposal would cite.

---

# Part 1 - The constraints, stated honestly

## What is known as of 5 September

| Constraint | Detail |
|---|---|
| **Uni** | Mon-Fri, **a window of 09:00-17:00, not fully booked**. Some days are lighter, some days are off entirely. Which ones is not yet known. |
| **Commute** | **1 hour each way.** This is the expensive part of the day, and it is the reason a gap between lectures is not usable training time. |
| **Work** | **Both weekend days**, roughly a **9-hour shift** inside a 10:00-21:00 window. |
| **Gym** | **24/7 access, near home.** Not near uni. |
| **Two-a-days** | Available and on the table. |
| **05:00 starts** | Available and to be designed around, not treated as a last resort. |
| **Cerys** | Can work around Daniel's schedule, so joint sessions are possible but need not be assumed. |

## The slots this actually produces

This is the table that matters, because it converts a timetable into training capacity.

| Slot | When | Length available | Quality |
|---|---|---|---|
| **Weekday early** | 05:30-07:00, leaving home ~07:45 | ~60-75 min in the gym | Good, but paid for in sleep (Part 4) |
| **Weekday evening** | 18:30-20:30, home from ~18:00 | 60-90 min | Variable - end of a 12-hour day |
| **Light/off uni day** | Anywhere | Unconstrained | **The best slots in the week** |
| **Weekend early** | 06:30-09:00, before a 10:00 start | ~90 min | Good, but before a 9-hour shift |
| **Weekend late** | After a shift ending 19:00-21:00 | Short | Poor - assume unusable |

**There is no shortage of slots. There are potentially ten or more a week.** The limiter is not
where a session fits, it is how much training a person can absorb across a 12-hour uni day, a 2-hour
commute and two 9-hour weekend shifts. That reframes the whole question, and it is why "how many
sessions is optimal" has a different answer here than it would for someone with a normal week.

## What the constraints rule out before the evidence is consulted

1. **The 90-minute session is dead.** It survived in the old week because sessions were evening-only
   and there was nothing after them. In a 05:30 slot before a commute it is arithmetically
   impossible, and after a 12-hour day it is the thing that gets abandoned at exercise six - which
   `week-method.md` Part 3 already documented happening repeatedly.
2. **Anything requiring the same slot every week is fragile.** The uni window is not fully booked and
   the weekend rota moves. A split whose logic depends on Monday always being Monday will drift,
   exactly as the current one does.
3. **A split needing 5-6 long lifting days is out**, not on evidence but on time.
4. **Midday training is out** unless a gym near uni appears. One hour each way makes a lunchtime
   session a three-hour round trip.

---

# Part 2 - What the evidence actually says

## 2.1 The split itself is close to irrelevant. What it delivers is not.

This is the least intuitive finding and it needs stating first, because it stops the wrong argument.

- A meta-analysis of **14 randomised controlled trials, 392 participants**, found the choice between
  split and full-body routines had **minimal impact on strength and hypertrophy when weekly volume
  was equated**.
- A 12-week RCT in **50 untrained women** compared full-body twice a week against an upper/lower
  split four times a week. **No between-group difference** in 1RM bench, lat pulldown or leg press,
  jump height, power or muscle mass.
- A volume-matched RCT in **well-trained men** comparing full-body five days a week against a
  split routine found no hypertrophy or strength advantage either way, though full-body produced
  greater fat mass loss.

**So "which split" is the wrong question in isolation.** A split is a delivery mechanism. The right
question is: *which arrangement delivers the volume and frequency the goals need, in sessions that
actually get finished, on the days that actually exist?* Everything below is that question.

## 2.2 Volume: the returns are real, and they run out fast

The best current evidence is Pelland et al., published in *Sports Medicine* in December 2025:
**67 studies, 2,058 participants**, modelling weekly sets as a continuous variable rather than
comparing arbitrary buckets. They counted indirect sets as half a set - the "fractional" method,
which fitted the data best.

Both hypertrophy and strength improve with more weekly sets, with a 100% posterior probability the
slope is positive. But the shape differs sharply, and the authors published it as efficiency tiers.

**Hypertrophy - fractional weekly sets per muscle:**

| Tier | Sets | What each further increment costs |
|---|---|---|
| Minimum effective dose | **4** | Enough to produce detectable growth |
| Higher efficiency | **5-10** | ~6 more sets per further detectable increment |
| Intermediate | 11-18 | ~8.5 more sets |
| Lower | 19-29 | ~10.75 more sets |
| Lowest | 30-42 | ~12.5 more sets |

**Strength - fractional weekly sets for the trained exercise:**

| Tier | Sets | What each further increment costs |
|---|---|---|
| Minimum effective dose | **1** | Enough to produce detectable strength gain |
| Higher efficiency | **2** | ~0.75 more sets per further increment |
| Intermediate | **3-4** | ~2.25 more sets |
| Lower | **5+** | **Additional weekly sets do not consistently add strength** |

Read the strength table again. **Beyond roughly four hard weekly sets of a given lift, more sets
stop reliably buying more strength in that lift.** The best-fit model was reciprocal - it has a
functional plateau, and hypertrophy's does not.

## 2.3 Frequency: the one place strength and size genuinely diverge

Same paper, and this is the part that decides the split.

- **For hypertrophy, frequency did essentially nothing on a volume-adjusted basis.** The slope was
  +0.32% per session, 91.3% probability of being above zero, and the credible interval contained
  zero. The authors' word is "compatible with negligible effects".
- **For strength, frequency mattered, with 100% probability.** +3.27% of maximal strength per
  weekly session (95% CrI 2.74 to 3.84), again with diminishing returns.

That is a **tenfold difference in slope** between the two outcomes for the same variable.

Supporting evidence points the same way:

- The **Norwegian frequency project**: 16 competitive powerlifters, 15 weeks, **identical total
  volume, intensity and exercises**, split into either 3 or 6 weekly sessions. The 6-session group
  gained roughly **double** the squat and bench strength. Volume was equal; only its distribution
  changed.
- Volume-matched trials in ordinary trained men generally find **no additional benefit** past about
  2-4 sessions - so the effect has a ceiling, and it is not licence to train seven days a week.
- Mechanistically the likely driver is skill: **more exposures to the barbell with less fatigue in
  each one**. That matters more for a technical lift than for a machine.

## 2.4 What this means for Daniel specifically, which is the finding of this file

Daniel's three strength goals are the **squat, the bench and the deadlift**. Here is how often each
is currently trained.

| Lift | Session it lives in | Programmed frequency | Actually achieved |
|---|---|---|---|
| Squat | Lower 2 | 1x per week | ~1x per week |
| Bench | Upper 1 | 1x per week | ~1x per week |
| Deadlift | Lower 1 | 1x per week | **twice since 20 July** |

Now set that against the two tables above.

1. **Frequency is the variable with a proven dose-response for strength, and all three lifts sit at
   the bottom of it.** One session per week is the lowest rung. Going to two roughly doubles the
   frequency dose for the variable that reliably drives the outcome he wants.
2. **Volume per lift is at or past the point where it stops paying.** The recurring note in the log -
   *"is 4 sets of the main exercise too much? - twice in a row now"* - has an evidence-based answer:
   for strength, the fourth set of a weekly-trained lift sits in the intermediate-efficiency tier at
   best, and it is the set that pushes the session past 90 minutes and causes the last three
   exercises to be dropped. **It is the worst-value set in the week.**
3. **These two facts have the same fix.** Take the fourth set off the main lift, and the session
   fits. Do the session twice a week instead of once, and total volume is *higher* than it was while
   each session is *shorter* - and the frequency dose doubles.

> **The current week trains three strength goals at the minimum effective frequency, in sessions too
> long to finish, and one of the three barely happens at all. Shorter, more frequent sessions fix
> the length problem and the frequency problem with a single change.**

This is a rare case where what the evidence prefers and what a fragmented timetable can accommodate
are the same thing. It is worth saying plainly because it will not be true of every decision in this
project.

## 2.5 The cost of a long session is not theoretical

`week-method.md` Part 3 documented the pattern in Daniel's own words: sessions cut short for
hunger, low energy, time, classes. To that, the general evidence adds:

- Shorter sessions **lower the perceived time barrier**, which is the main predictor of whether a
  session happens at all.
- In a large cohort of resistance-training app users, **higher frequency reduced dropout risk more
  strongly than longer sessions did** - a one-SD increase in frequency cut 11-week dropout risk by
  33% among long-workout users.
- Splitting a high-volume session into two shorter ones **accelerated recovery** of bench press
  throw power and muscle thickness.

**An exercise that is programmed but not performed contributes nothing.** The eight-exercise session
that ends at exercise six is not an eight-exercise session, and the exercises lost are always the
same ones - which is how the deadlift ended up with one top set on record.

## 2.6 Concurrent training: still not the constraint at two runs

Restating from `week-method.md` Part 4 because it bounds the options here:

- Schumann et al.'s updated meta-analysis (**43 studies**) found concurrent training did **not**
  significantly reduce maximal strength (SMD -0.06) or hypertrophy (SMD -0.01) versus lifting alone.
  Explosive strength took a small hit (SMD -0.28), and that hit was **larger when both were done in
  the same session** than when separated by 3+ hours.
- Interference tends to appear when **endurance frequency reaches about 3+ sessions a week**, and to
  be driven more by endurance *volume* than intensity.

**At two runs a week, interference is not the binding constraint.** It becomes one at three or more
hard runs alongside four heavy lifting days. Worth revisiting if the Hyrox date forces the run count
up, and worth remembering that the explosive-strength penalty is the argument for separating a
same-day lift and run by hours rather than minutes.

---

# Part 3 - The candidate splits, judged

Scored against this week: sessions must be short, the barbell lifts want frequency, two runs need to
fit, and the schedule will move week to week.

## Full body, 3x per week

Each session: 1 main barbell lift heavy, 1-2 secondary compounds, 2 accessories.

| | |
|---|---|
| **Frequency delivered** | Squat/bench/deadlift **2-3x each per week** if rotated |
| **Session length** | 45-60 min |
| **Pros** | Best frequency-per-hour of any option. Missing one session costs a third of each lift's volume, not all of it - **the single most robust structure against a drifting week**. Leaves 4 days for runs and rest. Strongly supported by the volume-matched RCTs. |
| **Cons** | Every session has a barbell main lift, so no session is truly easy. Needs discipline to keep accessory volume low. Per-muscle hypertrophy volume tops out around the 5-10 set tier rather than higher. |
| **Verdict** | **The strongest fit for the strength goals and the strongest fit for an unpredictable week.** |

## Upper / Lower, 4x per week

| | |
|---|---|
| **Frequency delivered** | Each lift 2x per week |
| **Session length** | 50-65 min if held to 5-6 exercises |
| **Pros** | Also delivers 2x frequency on everything. More room for accessory and Hyrox-station work than full body. Familiar - it is the current structure, just halved and doubled. |
| **Cons** | **Needs 4 lifting days plus 2 runs = 6 training days.** Missing one session costs an entire half of the body that week. Lower days are the long ones and lower days are the ones that get dropped. |
| **Verdict** | **The best option if 4 lifting days are genuinely available and reliable.** Higher ceiling than full body, lower robustness. **Part 5 changes this verdict** - with two same-day run/lift pairings it becomes a four-day week rather than a six-day one, which removes the main objection. |

## Push / Pull / Legs, 3x per week

| | |
|---|---|
| **Frequency delivered** | **1x per muscle per week** |
| **Verdict** | **Rules itself out.** This is the frequency the current week already delivers, and Part 2.4 is the argument against it. A 3-day PPL is the worst available answer to a frequency problem. |

## Push / Pull / Legs, 6x per week

| | |
|---|---|
| **Frequency delivered** | 2x per muscle per week |
| **Pros** | Sessions can be genuinely short (40-50 min). High total volume. Real-world data show PPL users average ~18 sets per muscle per week versus ~13.6 for upper/lower. |
| **Cons** | **6 lifting days plus 2 runs does not fit this timetable** without two-a-days on most days. The same real-world data show PPL users train 5.4 sessions a week versus 3.8 - **42% more gym time for a 12% faster compound-lift progression**. Given the commute, that trade is bad here. Zero robustness to a moved shift. |
| **Verdict** | **No.** Good split, wrong life. |

## Bro split (one muscle per day, 5x)

| | |
|---|---|
| **Frequency delivered** | 1x per muscle per week |
| **Verdict** | **No.** Worst frequency of any option, needs the most days, and offers nothing the goals want. Included only so it is on the record as considered and rejected. |

## Upper / Lower / Full, 3x per week

A hybrid: one upper day, one lower day, one full-body day.

| | |
|---|---|
| **Frequency delivered** | ~1.7x per muscle per week; main lifts 2x if placed deliberately |
| **Pros** | Only 3 lifting days. More per-session specialisation than pure full body. Leaves the most room for runs and Hyrox stations. |
| **Cons** | Slightly less frequency than either 4-day upper/lower or 3-day full body. The full day risks becoming the long one. |
| **Verdict** | **A good compromise if 3 days is the honest number** and pure full body feels too compressed. |

## Hyrox-conventional: 2 strength + 3 runs

The template most Hyrox plans use - 2 strength-and-stations sessions, 3 runs, 60-90 min each.

| | |
|---|---|
| **Verdict** | **Right for the Hyrox goal, wrong for the barbell goals.** Two lifting days cannot deliver 2x frequency on three barbell lifts *and* station work. Correct destination for a specific-phase block near a race date (`hyrox-method.md` Phase 3), wrong for a general block with no race booked. |

## Daily micro-sessions, 6-7x, 25-40 min

Minimum-dose sessions most days: one main lift, 2-3 sets, one or two accessories, out in 30 minutes.

| | |
|---|---|
| **Frequency delivered** | **3x per lift per week**, the highest of any option |
| **Pros** | Directly exploits Part 2.3. Fits a 05:30 slot better than anything else. Each session is small enough that a bad day costs almost nothing. Consistent with the minimal-dose literature: loads at or above 80% 1RM with very low set counts maintain and build strength. |
| **Cons** | **Seven trips to the gym.** Warm-up overhead becomes a large fraction of each session. Frequency benefits plateau by roughly 2-4 sessions per lift, so the seventh day buys little. Highest risk of accumulating fatigue with no clear rest day, against a 12-hour uni day and two 9-hour shifts. |
| **Verdict** | **Genuinely interesting, and probably too much for this week.** Its logic is right; its dose is beyond where the evidence shows returns. Best used as a *component* - a 25-minute second session - rather than as the whole plan. See Part 4. |

---

# Part 4 - The 05:00 start and the two-a-day

Daniel asked for these to be designed around rather than hedged. Here is what the evidence supports
and what it costs.

## Two-a-days: the evidence is better than expected

- The direct trial: resistance-trained men, same weekly volume, split into **once-daily versus
  twice-daily** sessions per muscle group. Squat 1RM rose **16.1%** in the twice-daily group against
  **7.8%** once-daily. **Bench, muscular endurance and every muscle-thickness measure showed no
  difference between groups.**
- The Norwegian powerlifting result is the same phenomenon at a weekly scale: identical volume,
  distributed more finely, roughly double the strength gain.
- Splitting volume across two same-day sessions **speeds recovery** of power and muscle thickness
  compared with one long session.

**Two useful conclusions, and the second one is the one people miss:**

1. **A two-a-day is a legitimate tool for lower-body strength**, which is where two of Daniel's three
   barbell goals live.
2. **It did nothing for upper-body strength or for size.** So a two-a-day is worth spending on a
   squat or deadlift day and is largely wasted on an arms-and-shoulders session.

The practical shape: **lift in the morning, second session in the evening, separated by the whole
uni day**. That separation is 10+ hours, far beyond the 3-6 hours the interference literature asks
for, so a morning lift and an evening easy run is close to a free combination.

## Time of day: it matters less than folklore says

- The meta-analysis of time-of-day-specific training: **strength gains were similar** whether people
  trained in the morning or the evening, regardless of when strength was later tested.
- Absolute strength **is** higher in the evening at baseline, but **morning training closes that
  gap** - train in the morning and morning strength rises to meet evening levels.
- The one caveat: the strongest single study on muscle *growth* favoured evening training.

**So a 05:30 lift is not a compromised lift, provided it is habitual.** The first few weeks will feel
worse; the adaptation is specific to the time you train. Expect lower absolute loads early and do not
read that as regression.

## The sleep cost, which is the real objection

This is where the honesty is owed, because `recovery-method.md` Part 1 already calls sleep the
largest single lever in the entire document set.

A 05:00 alarm with an 8-hour sleep need means **lights out by 21:00**. After getting home at 18:00,
eating, and anything resembling a life, that is tight. If it does not happen, the 05:00 start is a
sleep-restriction protocol with a workout attached:

- Athletes sleeping **under 8 hours were 1.7x more likely to be injured**.
- Sleep restriction reduces force output in **multi-joint** movements - squats and deadlifts, the
  exact lifts the early slot exists to serve - while leaving single-joint work largely intact.
- Sleep restriction blunts **myofibrillar protein synthesis** and alters the muscle transcriptomic
  response to training, so the same session yields less adaptation.
- The effect is chronic, not acute. One early start is fine. Five a week at 6.5 hours is not.

**The rule that follows:**

> **Early starts are a scheduling tool, not a way to buy extra training time.** An 05:30 session that
> replaces an evening session is close to free. An 05:30 session *added on top* of the same evening
> load, at the cost of an hour of sleep, is very probably negative - the injury and adaptation
> numbers above are larger than any frequency gain in Part 2.3.

**The single best use of the light and off uni days is to protect sleep**, not to add a session.
That is a genuinely counterintuitive recommendation and it is the one the evidence most strongly
supports.

## Where a two-a-day actually earns its place

Given all of the above, the defensible pattern is narrow:

- **On a light or off uni day**, where the morning session costs no sleep at all.
- **Morning: lift. Evening: easy run.** Ten hours apart, lift first, which is the sequence the
  interference literature endorses.
- **Not on consecutive days**, and not as the default structure of the week.
- **Spent on squat or deadlift** if the second session is also lifting, since that is where the
  twice-daily evidence is positive.

---

# Part 5 - Running and lifting on the same day

**This is the highest-leverage question in the file**, because it is the only decision here that
changes how many *days* the week needs. Everything else changes what happens inside them.

## What it buys, which is a whole day

| Week | Days needed, one session per day | Days needed, with 2 pairings |
|---|---|---|
| 3 lift + 2 run | **5** | **3** |
| 4 lift + 2 run | **6** | **4** |
| 3 lift + 2 run + 1 flexibility | 6 | 4 |

Endurance coaching has a name for this: **consolidation of stressors**. Put the hard things on the
same day so that the easy days are genuinely easy and whole days come back free. That is precisely
the shape a week wants when it contains 12-hour uni days, two 9-hour shifts, and lighter days that
are not yet known.

**It is also the answer to the tension in Part 3.** Upper/lower on four lifting days was rejected as
a six-day week. With two pairings it is a four-day week, which changes the verdict.

## Order: lift first, and the evidence is now specific

`week-method.md` rule 4 already said "if both happen in one day, lift first". That rule now has a
number behind it. A 2023 meta-analysis of **19 RCTs and 482 participants** compared
strength-then-endurance against endurance-then-strength in the same session:

| Outcome | Which sequence won | Effect |
|---|---|---|
| **Lower limb strength** | **Strength first** | SMD 0.19 (95% CI 0.02-0.37, p = 0.032) |
| **VO2max** | Neither | SMD 0.02 (95% CI -0.21-0.25, p = 0.859) |

**The asymmetry is what makes the decision easy.** Lifting first costs the run nothing measurable in
adaptation. Running first costs the lift something real. There is no trade to weigh.

Note that some endurance sources recommend the opposite - endurance first, then a 3-hour gap. That
advice is aimed at people whose priority is the run. **For someone with three barbell goals it is
the wrong way round**, and the 19-RCT result is the reason.

## The acute cost, which is a separate question

Whether the training adapts over months and whether *today's second session is any good* are two
different questions, and the answers differ by direction.

**Run first, lift second - expensive:**

- Squat performance (3 sets to failure at 80% 1RM) fell **26.7%** thirty minutes after an interval
  cycling protocol.
- Squat repetitions fell by **5-9** following aerobic work.
- The effect is **largest on the lower body** and small on the upper body.
- With **4 hours** between them, box squat bar velocity showed no significant difference.

**Lift first, run second - cheaper, but not free:**

- Running economy is reduced for up to **8 hours** after lower-limb strength work.
- **But it is impaired mainly for subsequent high-intensity running (~90% VO2max).** Easy running is
  much less affected.
- For a genuinely hard run after a heavy lower-body session, the recommendation is **48 hours**.

**Those two asymmetries collapse into one rule:**

| Pairing | Same day? | Verdict |
|---|---|---|
| Heavy lift, then **easy** run | Yes, lift first | **Cheap. This is the pairing to use** |
| Heavy lower lift + **quality** run | No | Expensive in either order |
| Upper-body lift + quality run | Yes | Fine - the interference is lower-body specific |
| Run first, then lift | Only if the run is the priority | Costs the lift 5-9 reps or ~27% |

## Separation: how many hours is enough

| Gap | What the evidence says |
|---|---|
| **Same session, back to back** | Worst case. Schumann's explosive-strength penalty (SMD -0.28) was **larger same-session** than when sessions were separated by 3+ hours |
| **3 hours** | The molecular minimum *if endurance comes first* - AMPK takes ~3 h to return to baseline, and AMPK inhibits mTORC1, the strength pathway |
| **6 hours** | The commonly recommended figure for minimising acute interference on running economy |
| **10+ hours** | Past every threshold in the literature |

**The commute is an asset here, which is not something that gets said often.** A 05:30 lift and an
18:30 run are separated by the entire uni day - more than ten hours, comfortably past every
threshold above. The day that looks worst for training is the day that supports pairing best.

## The Hyrox exception, which inverts the whole rule

**Compromised running - running on legs already wrecked by station work - is the single most
Hyrox-specific quality there is.** For that session the interference *is* the training effect, and
the specificity argument beats every acute-cost number above. `hyrox-method.md` Phase 3 covers it.

So there are **two different same-day pairings** and they must not be confused:

| | Scheduling pairing | Compromised-run session |
|---|---|---|
| **Purpose** | Free up a day | Train a race-specific quality |
| **Gap** | Hours apart | Back to back, deliberately |
| **Order** | Lift, then run | Stations, then run, repeatedly |
| **Run intensity** | Easy | Hard, and hard *because* the legs are gone |
| **How often** | As often as the week needs | 1x per week at most, as a quality session |

**A compromised run is not a way to save time.** It is a hard session that happens to look like one.
Counting it as the week's time-saving pairing is how a week ends up with two quality sessions
stacked on one day.

## What it changes in the scenario matrix

Part 6's matrix counts days. Pairing changes the conversion, so read it with this in mind:

- **A 5-session week fits in 3 days** if two days carry a lift and an easy run.
- **A 6-session week fits in 4 days.**
- **The recommended default - full body 3x plus 2 runs - can be a 5-day week or a 3-day week**, and
  which one it is should be decided by the timetable, not by the split.

That is the single most useful thing to know before the timetable arrives: **the day count in the
matrix is a maximum, not a requirement.**

## For Cerys, this is cheaper, with one caution

Her aerobic work is **incline walking, not running**, while shins are the governor
(`coaching-method.md` Part 3). That makes same-day pairing *less* costly for her, not more - incline
walking is not high-intensity running, so the running-economy penalty above barely applies, and it
carries none of the impact load.

**The caution is the opposite one.** A lower-body lift plus incline walking loads the calf complex
twice in a day, and the calf complex is the tissue that keeps flagging. Pair her incline walking
with an **upper-body** day rather than a lower-body one, and the whole objection disappears.

## What not to do with same-day pairing

- **Do not pair the heaviest lift with the quality run.** That is the one combination expensive in
  both directions.
- **Do not run first when the lift is the priority.** It costs 5-9 squat reps, and the adaptation
  data says the same thing over months.
- **Do not use pairing to add sessions.** It exists to free a day, not to fill one. This is the same
  trap as Part 4's early starts.
- **Do not confuse the scheduling pairing with the compromised run.** One saves time; the other
  spends it deliberately.

---

# Part 6 - The scenario matrix

**When the timetable lands, come here.** Count the days that are honestly available - not aspirational
ones - and read across. Every row assumes runs are included in the day count.

**Read the day count as a maximum, not a requirement.** Part 5 shows a day can carry a lift and an
easy run, hours apart, so the "Compressed" column is the same week folded onto fewer days. If the
timetable gives fewer days than the row you want, that column is how you still get there.

| Honest days/week | Recommended shape | Compressed with pairing | Lifting frequency per lift | Runs | Why |
|---|---|---|---|---|---|
| **3** | Full body A/B/A, alternating | - | **1.5x** | 0-1, inside a session or on a lifting day | Below 3 days nothing accumulates. Full body is the only structure that keeps all three barbell lifts alive on 3 days. |
| **4** | Full body A/B/A + 1 run | **3 days**, 1 pairing | **1.5x** | 1 | The floor for a real hybrid week. Run is easy and goes furthest from the heaviest lift. |
| **5** | **Full body A/B/A + 2 runs** | **3 days**, 2 pairings | **2x** | 2 (1 quality, 1 easy) | **The recommended default.** Hits 2x frequency on all three lifts, 2 runs, sessions of 50-60 min, and one genuine rest day. |
| **5** *(alternative)* | Upper/Lower x2 + 1 run | **4 days**, 1 pairing | 2x | 1 | Choose this over full body only if station and accessory volume matters more than the second run. |
| **6** | Upper/Lower x2 + 2 runs | **4 days**, 2 pairings | **2x** | 2 | Highest ceiling that still fits. **With pairing this stops being a six-day week**, which is what made it hard to recommend. |
| **6** *(alternative)* | Full body x3 + 2 runs + 1 flexibility | **4 days**, 2 pairings | 2x | 2 | Same day count, lower total fatigue, adds the flexibility session `flexibility-method.md` has been waiting for a slot for. |
| **7+** | Do not | - | - | - | See Part 9. |

## Session-length variants, orthogonal to the above

| Time available | What fits | What to cut first |
|---|---|---|
| **75-90 min** | Main lift 3-4 sets, 2 secondary, 3 accessories | Nothing - but note Part 2.2 says the 4th set is near-worthless for strength |
| **50-60 min** *(the target)* | Main lift 3 sets, 1 secondary compound, 2-3 accessories | The 4th set of the main lift |
| **35-45 min** | Main lift 3 sets, 1 secondary, 1 accessory | Accessories, isolation last |
| **20-25 min** | Main lift 2-3 sets at or above 80% 1RM, nothing else | Everything else. The minimal-dose literature says this still builds and holds strength |

**The 20-25 minute row is the one that rescues a bad week.** A session that has shrunk to one lift is
not a failed session; it is the minimum effective dose for strength, done. That framing is worth
having in advance, because the alternative - skipping entirely - is what currently happens.

## Applying the matrix to the known timetable shape

| Day type | Likely count | Best use |
|---|---|---|
| Full uni day (09:00-17:00 booked) | ? | **One session, 45-60 min, morning or evening, not both.** Protect sleep. |
| Light uni day | ? | **The best training day of the week.** Longest session, or the two-a-day if one is being used. |
| Off uni day | ? | Longest session, or sleep, depending on the week |
| Weekend work day | 2 | Early session before the shift, 45-60 min, or rest |

**The counts in column two are the only thing missing.** Once they are known, Part 6's first table
gives the split and this one gives the placement.

---

# Part 7 - The recommendation, with the timetable still unknown

## For Daniel

**Full body, three lifting days, plus two runs.** Each session: one barbell main lift, one secondary
compound, two or three accessories, 50-60 minutes.

The reasoning, in order of weight:

1. **It doubles the frequency of every barbell lift**, and frequency is the only variable with a
   demonstrated 100%-probability dose-response for strength (Part 2.3).
2. **It shortens sessions below the point where they get abandoned**, which is what actually removed
   the deadlift from his training (Part 2.5, `week-method.md` Part 2).
3. **It is the most robust structure to a moving schedule.** Missing one of three full-body days
   costs a third of each lift's weekly volume. Missing one of four upper/lower days costs an entire
   half of the body. Given a rota that moves and a uni window that is not fully booked, robustness is
   worth more here than a slightly higher ceiling.
4. **It leaves two days for running and one for rest**, which is what the two-runs finding needs
   without a sixth day.
5. **It removes the 4th set of the main lift**, which Part 2.2 shows is the worst-value set in the
   week and which he has now questioned twice in his own session notes.

**Go to four days (upper/lower x2) only once the week has proved it can hold five sessions.** The
evidence supports the higher ceiling; the execution history does not yet support the assumption.

**The deadlift needs an explicit position, not an inherited one.** `week-method.md` established that
whatever sits last in the week is what gets lost. On a full-body rotation the deadlift appears in
more than one session, so its survival no longer depends on one fragile Friday.

## For Cerys

**The same three-day full-body structure, different content.** Her stated goals are an unassisted
pull-up and Hyrox.

- **The pull-up is a frequency problem, not a volume problem.** It is a skill and a strength
  expression, and Part 2.3 says skill-heavy strength responds to exposures. Her current 2x per week
  in Upper 1 and Upper 2 is already better than any of Daniel's barbell lifts. A full-body rotation
  supports **3x per week of low-volume pull-up work** - dead hangs, negatives, assisted reps - which
  is the highest-value change available to her.
- **Her limiter is tissue, not capacity.** Shins, a shoulder that pops, hips that click. Shorter,
  more frequent sessions distribute load rather than concentrating it, which is the right direction
  for all three. Her impact work stays governed by `running-method.md` Part 2 and
  `coaching-method.md` Part 3 - **incline walking, not running**, while shins are the governor.
- **She should not simply mirror Daniel's session.** They already diverge on run days; the same
  divergence applies here. Training at the same time is a logistics decision. Training the same
  session is a programming decision, and the two do not have to match.

## What is common to both

- **60 minutes as the design target**, with the 20-25 minute version defined in advance as the
  fallback rather than improvised.
- **One genuine rest day**, protected.
- **Sleep before extra sessions**, every time (Part 4).
- **Same-day pairing used to compress the week, not extend it** (Part 5). On the days the timetable
  is tightest, a morning lift and an evening easy run is close to free - and it is the mechanism that
  lets a five-session week land on three days if it has to.

---

# Part 8 - The problem with the goal set, since goals are open

Daniel said goals can change but a change needs a reason. Here is the reason, offered as a finding
rather than a recommendation.

**The five goals pull in different directions, and two of them pull hardest against the rest.**

| Goal | What it asks for |
|---|---|
| 100 kg bench | Modest. A rebuild plus 5 kg on a lifetime best (`strength-method.md` Part 2) |
| **200 kg squat** | **2.68x bodyweight at 74.6 kg. Advanced, edging elite** |
| **200 kg deadlift** | **2.68x bodyweight, and +21% on a lifetime best on his historically weaker lift** |
| Sub-20 5k | Aerobic development, and rewards being light |
| Hyrox | Compromised running, aerobic base, and rewards being light |

The tension is not about time in the gym. It is that **200/200 at 74.6 kg is an advanced powerlifting
total that most people reach by adding bodyweight**, while sub-20 and Hyrox are both easier the
lighter he is. Pursuing all five simultaneously means each one gets a fraction of the specificity it
needs, and the barbell goals are the ones that suffer most, because Part 2.6 shows the endurance
work does not interfere much but the *attention* does.

**Three honest options, none of which is "drop a goal":**

1. **Sequence them in blocks.** A strength-priority block (3 full-body lifting days, 1 easy run,
   maintenance-only aerobic work) followed by a Hyrox-priority block near a race date. The
   minimal-dose literature is explicit that **strength is maintained for 4-8 weeks on as little as
   one session a week provided intensity stays high** - so the aerobic block does not cost the
   barbell numbers. This is the cheapest resolution and it changes no goal.
2. **Re-time them.** Keep all five, accept that 200/200 is a multi-year target
   (`strength-method.md` Part 2 already costs it that way), and stop treating it as concurrent with
   a Hyrox build.
3. **Revise one number.** If Hyrox and sub-20 are the near-term priorities, a 180 kg squat and
   deadlift are a materially cheaper pair of goals that keep the same training shape.

**No decision is needed here and none is being proposed.** But "goals can change with a reason" is an
invitation, and this is the reason: **the goal set currently assumes no trade-off exists, and one
does.**

---

# Part 9 - What not to do

- **Do not pick a split before counting the honest number of days.** Part 6 is a lookup table for
  exactly this reason. Choosing a 6-day structure and executing 4 is how the current week broke.
- **Do not add sessions on top of an unchanged sleep schedule.** The injury and adaptation costs in
  Part 4 are larger than the frequency gains in Part 2.3. This is the most likely way for the
  05:00 plan to make things worse.
- **Do not run a 3-day PPL.** It delivers 1x frequency per muscle - the exact problem being fixed.
- **Do not keep 4 sets on the main lift while adding frequency.** That doubles a session's worth of
  the lowest-value sets in the program and rebuilds the 90-minute session at twice the rate.
- **Do not make both runs hard.** Restated from `week-method.md` Part 8 because it is the commonest
  error when moving from one run to two.
- **Do not pair the heaviest lift with the quality run.** It is the one combination that is expensive
  in both directions (Part 5). Pair heavy lifts with easy runs only.
- **Do not run first on a paired day.** It costs 5-9 squat reps acutely and the lower-body strength
  adaptation over months. Lift first unless the run is explicitly the priority that day.
- **Do not use same-day pairing to add sessions.** It exists to free a day, not to fill one - the
  same trap as the 05:00 start.
- **Do not assume Cerys does Daniel's session.** She can work around his schedule; that is a
  logistics fact, not a programming one.
- **Do not treat the 20-minute session as a failure.** Define it in advance as the minimum effective
  dose, because the alternative is skipping.
- **Do not finalise anything until the timetable is known.** This file exists so that the work is
  already done when it is - not so that the decision can be made without it.

---

## Sources

**Volume and frequency dose-response**
- Pelland JC, Remmert JF, Robinson ZP, Hinson SR, Zourdos MC. *The Resistance Training Dose
  Response: Meta-Regressions Exploring the Effects of Weekly Volume and Frequency on Muscle
  Hypertrophy and Strength Gains.* Sports Medicine, 2025.
  [Springer](https://link.springer.com/article/10.1007/s40279-025-02344-w) ·
  [PubMed](https://pubmed.ncbi.nlm.nih.gov/41343037/) ·
  [SportRxiv preprint](https://sportrxiv.org/index.php/server/preprint/view/460)
- [Effects of training frequency on muscular strength for trained men under volume-matched
  conditions](https://peerj.com/articles/10781/) (PeerJ)
- [Equal-volume strength training with different training frequencies induces similar hypertrophy
  and strength improvement](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8766679/)
- [High frequency training for a bigger total: the Norwegian powerlifting
  project](https://www.strongerbyscience.com/high-frequency-training-for-a-bigger-total-research-on-highly-trained-norwegian-powerlifters/) ·
  [a closer look at the same study](https://muscleevo.net/norwegian-frequency-project/)

**Split versus full body**
- [Efficacy of split versus full-body resistance training on strength and muscle growth: a systematic
  review with meta-analysis](https://www.researchgate.net/publication/379724552_Efficacy_of_Split_Versus_Full-Body_Resistance_Training_on_Strength_and_Muscle_Growth_A_Systematic_Review_With_Meta-Analysis)
  (14 RCTs, 392 participants)
- [A randomized trial on split-body versus full-body resistance training in non-resistance trained
  women](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9107721/)
- [Split or full-body workout routine: which is best to increase muscle strength and
  hypertrophy?](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8372753/)
- [Full-body resistance training promotes greater fat mass loss than a split-body routine in
  well-trained males](https://pubmed.ncbi.nlm.nih.gov/38874955/)
- [PPL vs upper/lower: a data analysis of real training logs](https://arvo.guru/blog/ppl-vs-upper-lower-data)

**Two-a-days and session structure**
- [Twice-daily sessions result in greater muscle strength and similar muscle hypertrophy compared to
  once-daily sessions in resistance-trained
  men](https://www.researchgate.net/publication/349657740_Twice-daily_sessions_result_in_a_greater_muscle_strength_and_a_similar_muscle_hypertrophy_compared_to_once-daily_session_in_resistance-trained_men)
- [Two vs. one resistance exercise sessions in one day: acute effects on recovery and
  performance](https://pubmed.ncbi.nlm.nih.gov/34982021/)
- [Effects of one long vs. two short resistance training sessions on training volume and affective
  responses](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9557220/)

**Time of day**
- Grgic J et al. [The effects of time of day-specific resistance training on adaptations in skeletal
  muscle hypertrophy and muscle strength](https://pubmed.ncbi.nlm.nih.gov/30704301/), Chronobiology
  International, 2019
- [Best time of day for strength and endurance training to improve health and performance? A
  systematic review with meta-analysis](https://link.springer.com/article/10.1186/s40798-023-00577-5)

**Sleep**
- [Inadequate sleep and muscle strength: implications for resistance
  training](https://pubmed.ncbi.nlm.nih.gov/29422383/)
- Milewski MD et al. [Chronic lack of sleep is associated with increased sports injuries in
  adolescent
  athletes](https://www.ovid.com/jnls/pedorthopaedics/fulltext/10.1097/bpo.0000000000000151~chronic-lack-of-sleep-is-associated-with-increased-sports),
  J Pediatr Orthop, 2014
- Saner NJ et al. [The effect of sleep restriction on myofibrillar protein
  synthesis](https://physoc.onlinelibrary.wiley.com/doi/full/10.1113/JP278828), J Physiol, 2020
- [The interactive effect of sustained sleep restriction and resistance exercise on skeletal muscle
  transcriptomics in young
  females](https://journals.physiology.org/doi/full/10.1152/physiolgenomics.00010.2024)

**Concurrent training**
- Schumann M et al. [Compatibility of concurrent aerobic and strength training for skeletal muscle
  size and function: an updated systematic review and
  meta-analysis](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8891239/) (43 studies)
- [Endurance training intensity does not mediate interference to maximal lower-body strength
  gain](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5093324/)
- [The role of intra-session exercise sequence in the interference
  effect](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5752732/)

**Same-day pairing, order and separation (Part 5)**
- [Effects of concurrent training sequence on VO2max and lower limb strength performance: a
  systematic review and
  meta-analysis](https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2023.1072679/full)
  - 19 RCTs, 482 participants. The source of the lift-first recommendation
- [The effects, mechanisms, and influencing factors of concurrent strength and endurance training
  with different sequences: a semi-systematic
  review](https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2025.1692399/full)
  - the AMPK / mTORC1 rationale for the 3-hour minimum
- [Concurrent training programming: the acute effects of sprint interval exercise on subsequent
  strength training](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9145373/)
- [Acute neuromuscular, physiological and performance responses after strength training in runners:
  a systematic review and meta-analysis](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9385928/)
- [Effect of strength and endurance training sequence on endurance
  performance](https://pmc.ncbi.nlm.nih.gov/articles/PMC11359207/)
- [Exercise-induced muscle damage and running economy in
  humans](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3575608/)
- [Concurrent training for Hyrox: how to run and lift without sabotaging
  either](https://www.hyroxvault.com/blog/hyrox-concurrent-training) - and
  [compromised running](https://xendurance.com/blogs/blog/compromised-running-hyrox-s-biggest-game-changer)

**Minimal dose and maintenance**
- [Resistance exercise minimal dose strategies for increasing muscle strength in the general
  population: an overview](https://pmc.ncbi.nlm.nih.gov/articles/PMC11127831/)
- [The minimum effective training dose required for 1RM strength in
  powerlifters](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8435792/)

**Adherence**
- [Predictors of long-term resistance exercise adherence: evidence from a large cohort of mobile app
  users](https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2026.1855668/full)

**Hyrox**
- [How to structure your HYROX running training](https://hyroxdatalab.com/articles/hyrox-running-training-structure)

**Their own data**
- `recent_sessions`, `goals`, `limiters` and the program, read 2026-09-05, plus
  `week-method.md`, `strength-method.md`, `running-method.md`, `recovery-method.md`,
  `hyrox-method.md` and `flexibility-method.md`.
