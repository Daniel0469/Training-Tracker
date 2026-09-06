# Exercise notes - what Daniel and Cerys say about each exercise

**Written 2026-09-02.** Two halves. **Part 1** is what they have actually said about the exercises
they do, keyed by exercise instead of by session. **Part 2** is a bench of candidates to try, each
one tied to a complaint in Part 1 or to a gap against a goal.

## Why this file exists

The raw material was already there and nothing was reading it. Every logged session carries a
free-text `feedback` field and there are **47 of them going back to 24 June**. It is keyed by
SESSION and by DATE, so a complaint about one exercise is buried inside a note about a whole
evening, and the same complaint made four times over six weeks reads as four unrelated remarks.

Keyed by exercise, it stops being remarks and starts being a pattern. The case that proves it:

| Date | Cerys wrote |
|---|---|
| 2026-07-04 | "Hips hurt on adduction, try stretching them more often" |
| 2026-08-11 | "Hips are too tight for adduction and abduction" |
| 2026-08-12 | "Left hip clicks everytime on side-lying hip abduction" |
| 2026-08-13 | "Left hip keeps clicking on side-lying hip abduction" |

Four flags in six weeks. `Hip abduction` and `Hip adduction` are both still in Lower 2, unchanged.
Nobody ignored her; the shape of the store just never let anyone see it as one thing.

## What belongs here, and what does not

| Store | Holds | Grain | Who writes |
|---|---|---|---|
| `limiters(person)` | what is holding a whole session back | per **session** | them, via the coach |
| `ex.notes` on the program | setup detail: seat height, pins, platform | per exercise, **shared by both** | either of them, in the editor |
| `coaching[person].byExercise` | the coach's next step on that exercise | per exercise, per person | the coach, overwritten each write |
| `feedback` on a logged session | whatever they typed that evening | per **session**, per person | them, in the app |
| **this file** | **their opinion of an individual exercise, accumulated** | per exercise, per person | the coach, distilling `feedback` |

This file does not duplicate any of them. It is the distillation of the last row into the grain the
other rows cannot express: **the same exercise, over time, in their own words.**

## The rules

1. **Their words, not my reading.** Quote them. Anything I conclude *from* these notes belongs in
   [coaching-method.md](coaching-method.md) Part 2 or in the relevant method file, and should link
   back here. A file that mixes evidence with inference stops being evidence within a month.
2. **Dated, attributed, and appended - never overwritten.** Oldest first inside each exercise, so
   the repeat reads as a story. A one-line **Status** at the top carries the current state, and that
   line is bookkeeping (open / actioned, how, when), not coaching.
3. **Per person.** Daniel's shoulder is not Cerys's shoulder. Facts about the *kit* rather than
   about a body go in the shared section at the end, so they are not written twice.
4. **Keyed by the exercise name as the program spells it.** Same known weakness as everything else
   here: `Bench press` and `Flat press (DB)` fork, and so will their notes. See the open item in
   [BACKLOG.md](../BACKLOG.md).
5. **This file changes nothing on its own.** Program structure is not the coach's to change
   ([coaching-method.md](coaching-method.md) Part 3). Anything here that should become a program
   edit goes through `propose_suggestion_tool` or `write_program_change` for Daniel to approve.

Apostrophes in the quotes below have been normalised; nothing else in them is edited.

## How to use it in a review

Read Part 1 for the person you are reviewing, before you write anything. You are looking for two
things and only two:

- **A repeat.** The same exercise flagged twice or more. That is the signal, and it is invisible in
  any other view of the data.
- **An open ask.** Something they requested that never got actioned. Cerys asked for a replacement
  for the plank pull through on 13 August; it was actioned in her run session and **not** in the
  cardio session she shares with Daniel, where it still sits. Three weeks.

---

# Part 1 - What they have said

## Daniel

### Incline DB press / Incline bench press
**Status: open. Flagged once, never actioned.**
- **2026-07-02.** "incline at setting 3 / shoulders clicking on incline press"

### Triceps pushdown
**Status: open.** See also Cerys, who flagged the same exercise two days earlier.
- **2026-08-21.** "slight pain in left elbow on triceps- previous injury"

### Seated leg curl
**Status: he found his own fix and it was never written into the program.**
- **2026-07-04.** "leg curl setting 4-3-4?"
- **2026-07-20.** "leg curl is pulling body instead of weight- try lying or keep weight under 50kg"
- **2026-07-27.** "switched to single leg on leg curls- felt good"

### Leg press
**Status: open, deliberately deferred.** His own proposal to drop it is parked until the uni
timetable lands and all eight sessions are rewritten together.
- **2026-07-20.** "leg press is heavy"
- **2026-09-02.** His own suggestion to drop the leg press and move the hip work
  ([coaching-method.md](coaching-method.md), Daniel, 2026-09-02).

### Squat
**Status: partly actioned** - shoulder mobility now sits in the warm-ups after the 2 Sep rewrite.
**Cerys flagged the same problem on the same date**; see hers. Two people, one complaint, six weeks
old, and it is what Part 2 section F is aimed at.
- **2026-07-27.** "switched to back squats / work on shoulder mobility for back squats"

### Leg raises
**Status: open, and the exercise is no longer in the program** - so this is a note about his hip,
not about a slot that needs filling.
- **2026-07-01.** "right hip popping when doing leg raises"
- **2026-07-29.** "left hip hurt on slow speeds- perfectly fine on fast"

### Calf raise
**Status: actioned 2026-08-19** - moved onto the leg press and renamed `Leg press calf raise`.
Cerys flagged the same machine on the same day, independently.
- **2026-08-11.** "remove calf raise on warmup / add shoulders to warmup"
- **2026-08-18.** "move calf raises onto leg press machine to stop pads digging into shoulders"

### Walking/sandbag lunges
**Status: actioned 2026-08-19** - Lower 2 reordered so the lunges follow the seated leg curl.
- **2026-08-18.** "did lunges last due to classes being on- move lunges after leg curls"

### Pull-ups (assisted to weighted)
**Status: actioned** - added to Upper 1 as well, same name so it stays one trend.
- **2026-08-21.** "did warm up of 5 at 50% for pull ups / should pull ups be in both upper sessions?"

### Bench press
**Status: actioned** - 4 sets down to 3.
- **2026-08-12.** "bench on smith machine today(10kg bar resistance)"
- **2026-08-19.** "Bench still says 4 sets- can you not change this yet?"

### Lat pulldown
**Status: unconfirmed.** Worth checking the current target against this.
- **2026-08-12.** "change lat pulldown rep range to 6-10"

### Glute bridge (Upper 1 warm-up)
**Status: actioned** in the 2 Sep warm-up rewrite. Kept because the *principle* in it is reusable:
warm-ups should be specific to the session.
- **2026-08-19.** "why am i doing glute bridge on an upper session- some hip work is okay, but the
  warm up should be specific to the session"

### Banded work (Upper 2 warm-up)
**Status: unconfirmed** against the current warm-up text.
- **2026-08-21.** "add banded dislocations to warm up as well as a banded press to link with banded
  pull aparts"

### Lateral raise
**Status: open, raised as a candidate.** Not a complaint - a suggestion. See Part 2 section F.
- **2026-09-02.** Suggested the **Lu raise** (Lü Xiaojun's lateral raise taken overhead), describing
  it as "like lateral raises". `Lateral raise` is programmed in both Upper 1 and Upper 2, so it is
  the natural slot for it.

## Cerys

### Hip abduction / Hip adduction
**Status: OPEN, four flags in six weeks, nothing changed.** The strongest open item in this file.
Note the two are not the same slot: the `Hip abduction` and `Hip adduction` machines are exercises
in Lower 2, and `side-lying hip abduction` is a warm-up line. She has flagged both.
- **2026-07-04.** "Hips hurt on adduction, try stretching them more often"
- **2026-07-27.** "Left hip hurt had to stop lunge :( / Ended early due to hip pain"
- **2026-08-11.** "Hips are too tight for adduction and abduction / Do yoga when possible"
- **2026-08-12.** "Left hip clicks everytime on side-lying hip abduction"
- **2026-08-13.** "Left hip keeps clicking on side-lying hip abduction"
- **2026-08-20.** "Left hip hurts a bit, could be due to hips popping earlier"

Six weeks of the same joint, twice naming the same exercise. Painless clicking is usually benign,
but "if it persists, get it checked" has been earned several times over. Candidates in Part 2.

### Triceps pushdown
**Status: open, self-managed.** She reduced the load and changed the attachment herself. Daniel
flagged the same exercise two days later for a different reason.
- **2026-08-19.** "Shoulder popping on tricep push down had to stop early, pop itself wasn't
  painful. Just didn't feel right"
- **2026-08-21.** "Went lighter on tricep push down as well as trying the straight bar"

### Pull-ups (assisted to weighted)
**Status: actioned** - a note on the exercise tells her to skip the second Upper 1 slot until the
shoulder has been clear for a couple of weeks. Quiet since.
- **2026-08-21.** "The shoulder that popped in the other session is aching after pull ups"
- **2026-09-02.** First pull-up session since 19 Aug with no shoulder ache afterwards, at a higher
  effort than the one that caused it. One quiet session is not a pattern yet.

### Squat
**Status: partly actioned** - goblet squat added to Lower 2 on 2026-08-19, at her request, to work
depth. Sets cut to 3. The shoulder discomfort under the bar has not been addressed as such.
**Daniel flagged the same shoulder-mobility problem on the same date**; see his. Part 2 section F.
- **2026-07-04.** "Try have legs shoulder width for squats"
- **2026-07-27.** "Shoulders hurting on squats, add some shoulder mobility to improve. / Keep an eye
  on bum wink when squatting low"
- **2026-08-11.** "Swaying on squats and leaning forward a bit / Cut down on squats to 3 sets,
  taking too long"
- **2026-08-18.** "Try goblet squats at end as accessory to help work on squat depth as having to
  stop above parallel on back squats"

### Plank pull through
**Status: HALF actioned.** Her run session got `Dead bug` in its place. The exercise is still in
`Cardio: Endurance + Core`, which she also does. Three weeks open.
- **2026-08-13.** "Not good at doing the pull through find another exercise"

### Leg press calf raise
**Status: actioned 2026-08-19.** Same day, same machine, independently of Daniel.
- **2026-08-18.** "Calf machine is too heavy for shoulders not calf's"

### Lateral raise
**Status: open.** No form cue has been written for it since.
- **2026-07-13.** "Need to keep eye on form for lateral raises. Very tired :("

### Incline walk
**Status: keep.** The only unambiguously positive exercise note either of them has written, and it
matches what the data says - reliable HR ~139, genuinely pain-free aerobic work.
- **2026-08-13.** "Incline walk feels much better / Shins feels good, no pain"

### Seated leg curl
- **2026-07-04.** "Leg curl setting 4,4,4"

## Kit and the gym

Not personal, so recorded once rather than under each of them.

- **The calf machine's shoulder pads cap the load before the calves are worked.** Both of them,
  independently, 2026-08-18, both stuck at 70 kg. Resolved by moving to the leg press.
- **Floor space disappears when a class is on.** Lower 2's lunges had to be done last on
  2026-08-18 for this reason. The session order now accounts for it.
- **The seated row gets taken.** Daniel, 2026-08-12: "seated row taken". Worth a fallback in the
  session rather than a lost exercise.
- **Bench is sometimes done on the Smith machine** (10 kg bar resistance), by both, 2026-08-12.
  Loads logged on those days are not comparable with free-bar loads.
- **Confirmed present:** rower and/or ski erg, sled (push and pull), sandbags.
  **Confirmed absent:** a wall ball. Daniel, 2026-09-02, see [hyrox-method.md](hyrox-method.md).

---

# Part 2 - Candidates to try

**Read this constraint first.** Their sessions already run 66-90 minutes and both of them have cut
sessions short for time. There is an open backlog item saying *shorten the sessions before adding
anything to the week*. So **every candidate below is a swap, not an addition**, and none of them
happens without Daniel approving it.

## A. Cerys's hips - the open one

Replacing `Hip abduction` and `Hip adduction` in Lower 2.

| Candidate | Why it might suit | Watch out for |
|---|---|---|
| **Banded lateral walk / monster walk** | Standing and loaded through the whole range rather than pinned against a pad. Cheap, no machine queue | Easy to do badly; knees track over toes, tension held throughout |
| **Bench-supported cable hip abduction** | She controls the arc instead of the machine dictating it, and it takes load off the support leg | Needs a free cable station |
| **Copenhagen plank** (for adduction) | Adduction loaded through a long lever, and it scales from a bent-knee short lever upward | Genuinely hard; start at the shortest lever |
| **Side plank with hip abduction** | High glute medius activation, no external load, doubles as core work | Not a like-for-like load progression |

**Stated honestly:** the evidence does not say the machine is a bad exercise. Side-lying, clamshell
and the machine give comparable glute medius activation, and there is a paper arguing the machine
beats free weights for it. So this is a swap **for comfort, not for effect** - the case for it is
that she has flagged the same joint six times, not that the machine is inferior.

**And the more important point:** six weeks of the same hip is past the point where the answer is a
different exercise. The honest recommendation is that she gets it looked at, and swaps in the
meantime rather than instead.

## B. Triceps pushdown - both of them, within 48 hours

| Candidate | Suits | Not for |
|---|---|---|
| **Single-arm cable pushdown** | Both. Lets the shoulder and elbow rotate naturally through the rep instead of being locked by a fixed bar | - |
| **Rope vs straight bar** | The cheapest test of all, and Cerys has already started it herself on 21 Aug | Not a fix if the issue is the shoulder position rather than the grip |
| **Close-grip press** | Daniel. Elbow-friendly, loads the triceps through a press pattern he already trains | Adds a barbell exercise to an already long session |
| **Overhead cable extension** | Daniel, possibly | **Wrong for Cerys.** It puts the shoulder into deep flexion, which is the position she is already flagging |
| **Band pushdown** | Both, as a deload option | Hard to progress |

## C. Daniel's incline press - flagged 2 July, never actioned

Shoulders clicking on the incline press. Candidates, cheapest first: **drop the bench angle to
15-30 degrees**; **neutral-grip dumbbell incline** so the shoulder is not forced into external
rotation; **landmine press** if the clicking persists at any angle.

## D. Cerys's squat depth - goblet squat is in, what else

She stops above parallel on back squats. The goblet squat was her own idea and is already in Lower 2.
Two more worth trying, neither of which needs a new slot:

- **Heel-elevated squat** (plate or wedge under the heels). Explicitly a *teaching tool*: it gets
  her body into the depth, and the elevation comes down over time. Not a permanent fixture.
- **Box squat to a set depth**, so the target is a thing she touches rather than a feeling.

Worth pairing with an ankle dorsiflexion check before assuming it is a hip problem. The deep squat
is already one of the five assessments in [flexibility-method.md](flexibility-method.md), so the
measurement exists and just needs taking.

## E. Plank pull through - close the half-open ask

`Cardio: Endurance + Core` still prescribes it. She already does `Dead bug` in its place in her run
session and gets on with it. Swapping it there too costs nothing and answers a three-week-old ask.

## F. Lu raise - Daniel's suggestion, 2026-09-02

Named after **Lü Xiaojun**, the Olympic weightlifting champion who popularised it. Daniel described
it as "like lateral raises", which is exactly right and is what makes it different from everything
else in this section: it is a **true lateral raise variant**, not a different exercise that resembles
one.

**What it is.** It starts identically to a dumbbell lateral raise - weights at the sides, palms in,
slight bend at the elbow, raise out to the sides. Instead of stopping at shoulder height it
**continues overhead** into a wide V, pauses, and lowers back down the same path. Often done with
small weight plates rather than dumbbells. It trains the deltoids through the whole range, plus the
traps and rotator cuff, and the case for it is the extended range: strength and size *and* shoulder
mobility and joint stability, where a lateral raise stops at shoulder height and keeps the demand on
the middle delt.

**Why it fits these two specifically, and it is a better fit than it first looks.**

1. **It can replace the lateral raise directly.** `Lateral raise` is programmed twice a week, in
   Upper 1 and Upper 2, and it is the exercise Cerys has an open form flag on from 2026-07-13. A Lu
   raise occupies the same slot and the same movement pattern, so this costs no session time - which
   matters, because sessions already overrun and nothing new can simply be added.
2. **Both of them flagged shoulder mobility on the squat, on the same day.** Daniel, 2026-07-27:
   "work on shoulder mobility for back squats". Cerys, same date: "Shoulders hurting on squats, add
   some shoulder mobility to improve." The back-squat rack position is exactly the externally
   rotated, near-overhead range a Lu raise trains under load. This is a repeat across two people six
   weeks old, and it is the single clearest case in this file of a candidate matching a stated
   complaint.
3. **It extends an ask Daniel already made.** 2026-08-21: "add banded dislocations to warm up as
   well as a banded press to link with banded pull aparts". Same category of work, still marked
   unconfirmed in Part 1.
4. Both have live shoulder complaints - her popping on the triceps pushdown and aching after
   pull-ups, his clicking on the incline press.

**Four honest caveats.**

1. **It needs the mobility it is meant to build.** This is the real tension. Going overhead under
   load is not the place to start if the overhead position is the problem. Start unloaded or with the
   lightest plates in the gym, and if the top of the range pinches or hurts, it is not the exercise
   yet - the mobility work comes first and the Lu raise comes after.
2. **Much lighter than anyone expects.** The extended range means loads drop hugely against a normal
   lateral raise. That is normal and not a regression.
3. **Log it under its own name, `Lu raise`.** Not as `Lateral raise`. Records, the Last column and
   the progress chart all key on the NAME, so reusing the lateral raise name would splice two
   different loads into one trend and read as a collapse. Same reasoning that kept
   `Leg press calf raise` separate. See the exercise-name fork item in [BACKLOG.md](../BACKLOG.md).
4. **Cerys before Daniel is the wrong order.** Her shoulder popped on 19 Aug and ached after pull-ups
   on 21 Aug, and has been quiet for exactly one session (2 Sep). One quiet session is not a pattern.
   Daniel can start now; she should wait, or start with the warm-up version only.

**Recommended placement, cheapest first.**

- **Into the Upper 1 and Upper 2 warm-ups**, unloaded or with the lightest plates, as shoulder
  preparation. Costs no exercise slot, needs no approval because warm-up text is coach-writable, and
  it passes Daniel's own 2026-08-19 test that a warm-up should be specific to its session. The
  sources are clear that the Lu raise works as a warm-up as readily as an accessory.
- **Then as a loaded slot replacing `Lateral raise` in ONE of the two upper sessions**, keeping the
  lateral raise in the other. No time cost, and it hedges - if the overhead range turns out not to
  suit one of them, the original movement is still trained twice a fortnight. This one is a program
  change and needs Daniel's approval.

### Related, but not the same thing: the letter raises

Written up while identifying the Lu raise, and kept because they answer a different question. **None
of these is a like-for-like lateral raise swap** - they are scapular and rotator-cuff exercises that
merely look similar, so choosing one trades delt work for shoulder control.

| | Arms do | Mainly trains |
|---|---|---|
| **Y** | Straight, overhead at ~45 degrees from the body, thumbs up | **Lower trapezius**, scapular upward rotation |
| **T** | Straight, out to the sides at 90 degrees to the torso | **Rear deltoid and middle trapezius**, plus rhomboids |
| **W** | Elbows bent, pulled back and down into a W | Rear delts, rhomboids, mid and lower trap, **external rotators** |
| **L** | Elbows bent 90 degrees at the sides, forearms rotate outward | **Rotator cuff** (infraspinatus, teres minor) |

The prone Y is the gold-standard exercise for lower-trapezius recruitment, performed above 90 degrees
of elevation, with the highest peak lower-trap EMG of the five exercises it was compared against. For
scale, a prone V-raise measured 57.2 %MVIC in the lower trap against 18.3 %MVIC for a modified prone
cobra. Two points that generalise: **adding external-rotation resistance decreases upper-trapezius
activity** while trunk extension increases it, so arching the back works against the point; and the
evidence sits on the prone or incline-supported versions, because those remove momentum.

**Do not sell any of this as a pain fix.** The link between scapular dyskinesis and shoulder pain is
genuinely contested. Scapula-focused programmes do improve pain and function in subacromial
impingement, but "your scapula is why it hurts" is a claim the evidence does not support.

## G. The Hyrox station gap

The program contains **no station work at all** except `Walking/sandbag lunges`, against a goal of
mixed doubles. They own the sled, the sandbags and a rower and/or ski erg, so seven of the eight
stations are trainable directly. This is the largest gap in Part 2 and the one that most needs a
decision from Daniel, because it cannot be a swap into an existing session - it wants its own slot,
which runs straight into the overrun problem.

**Wall balls are the exception**: no ball, so the station cannot be rehearsed as written.
Substitutes, in order of how closely they match the squat-to-press pattern:

1. **Dumbbell thruster** - the same pattern minus the throw and catch. The standard substitute.
2. **Goblet squat to press** - lighter, easier to learn, and it uses the kettlebell they have.
3. **Push press** - trains the hip-and-upper-body power but drops the full squat, so it is the
   least complete of the three.

The cheapest real fix stays what the backlog already says: **buy a medicine ball and mark a wall at
2.74 m and 3.00 m.**

---

# Maintaining this file

After every review, read the `feedback` on any session logged since the last one and split each line
three ways, which is the triage that already applies to session notes:

- **an opinion about an exercise** goes in Part 1, under that exercise, dated and quoted;
- **a request** goes in Part 1 too, and its Status line stays `open` until it is actually done in
  every session that contains the exercise - not just the first one;
- **an app problem** goes to `propose_suggestion_tool`, not here.

Then look only for repeats and open asks. Everything else in this file is context.

# Sources

Their own logged `feedback` fields, 2026-06-24 to 2026-08-21, plus
[coaching-method.md](coaching-method.md), [hyrox-method.md](hyrox-method.md),
[flexibility-method.md](flexibility-method.md), [BACKLOG.md](../BACKLOG.md) and
[PROJECT-STATUS.md](../PROJECT-STATUS.md).

Exercise candidates:
- [Gluteus Medius Training - E3 Rehab](https://e3rehab.com/gluteusmedius/)
- [Hip abduction machine vs free weights for gluteus medius - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1360859222000018)
- [EMG analysis during side-lying hip abduction - PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10501417/)
- [Tricep pushdown alternatives - Lift Vault](https://liftvault.com/exercises/tricep-pushdown-alternatives/)
- [Elbow pain: tricep pushdown alternatives - Gym-Pact](https://www.gym-pact.com/tricep-pushdown-alternative)
- [HYROX alternative exercises without the official kit](https://www.simongpt.co.uk/hyrox-exercise-alternatives-how-to-train-without-the-official-equipment/)
- [Wall ball alternatives - Horton Barbell](https://hortonbarbell.com/wall-ball-alternatives/)
- [Squat mobility exercises for depth - Gymshark](https://www.gymshark.com/blog/article/best-squat-mobility-exercises-for-squat-form-and-strength)
- [Improving ankle dorsiflexion for the squat - FlexibilityRx](https://www.flexibilityrx.com/improving-ankle-dorsiflexion-for-the-squat/)
- [Shoulder-abduction angle and trapezius activity - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8675318/)
- [Systematic review: exercises producing optimal scapular muscle activation - PubMed](https://pubmed.ncbi.nlm.nih.gov/27274418/)
- [Comparison of lower trapezius EMG activity across exercises - KoreaScience](https://koreascience.kr/article/JAKO201915061087047.pub?lang=en)
- [Evidence-based shoulder exercises - The Prehab Guys](https://theprehabguys.com/evidence-based-shoulder-exercises/)
- [Stop blaming scapular dyskinesis for shoulder pain - Barbell Rehab](https://barbellrehab.com/scapular-dyskinesis/)
- [Prone T raises: form and progressions - GetFitCraft](https://getfitcraft.com/exercises/t-raise)
- [Prone W raises: rear delt and rotator cuff guide - GetFitCraft](https://getfitcraft.com/exercises/w-raise)
- [Y-T-W raises for shoulder health - BoxRox](https://www.boxrox.com/3-reasons-why-y-t-w-raises-are-the-perfect-way-to-optimise-your-shoulder-health-and-fitness/)
- [EMG analysis of lateral raise variations - PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7503819/)
- [How to perform a Lu raise - Mirafit](https://mirafit.co.uk/blog/how-to-perform-a-lu-raise-for-bigger-shoulders/)
- [Master Lu raises - luxiaojun.com](https://luxiaojun.com/blogs/blogs/master-lu-raises-lu-xiaojuns-ultimate-shoulder-workout)
- [Is the Lu raise the perfect upper body exercise? - BoxRox](https://www.boxrox.com/is-the-lu-raise-the-perfect-upper-body-exercise-for-jacked-shoulders/)
- [Lateral raises vs Lu raises](https://stevenfitspot.com/lateral-raises-vs-lu-raises/)
