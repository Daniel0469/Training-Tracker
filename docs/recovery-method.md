# Recovery method - sleep, tissue tolerance, and the data we are not collecting

**Written 2026-09-02.**

Three things are covered here, in descending order of how much they would change if acted on:

1. **Sleep**, which is the largest untouched lever either of them has.
2. **Tissue tolerance and load management**, which is Cerys's governor and the reason her training
   has been stop-start.
3. **What to actually measure**, including a specific finding about the wellness data that
   `coaching-method.md` says does not exist.

---

# Part 1 - Sleep

## The size of the effect

This is not a marginal-gains topic. The numbers are larger than almost anything else available to
them:

- **Athletes sleeping fewer than 8 hours a night were 1.7 times more likely to be injured** than
  those sleeping 8 or more.
- **Time to exhaustion at 80% VO2max dropped by 11% after sleep loss.** Sleep deprivation also
  raises heart rate, ventilation and lactate accumulation at submaximal intensities - meaning a
  session feels harder and the physiological readouts look worse for reasons that have nothing to
  do with training.
- **Sleep extension studies** in athletes habitually sleeping around 7 hours produced 5% faster
  sprint times, 9% better free-throw accuracy and 9.2% better three-point accuracy, plus better
  wellbeing and fatigue ratings.
- Most athletes benefit from **8-10 hours**, and the practical extension prescription is
  **+46 to 113 minutes** on a habitual 7 hours.

An 11% change in time to exhaustion, and a 1.7x change in injury risk, are both larger than any
programming change this project has made in three months.

## Why it is on the list for these two specifically

- **Daniel's notes repeatedly say "feel tired", "low energy".** `coaching-method.md` already flags
  that no overnight data exists to say whether that is load, sleep or fuelling. It is one of those
  three and nobody can currently tell which. `fuelling-method.md` covers one branch; this covers
  another.
- **Cerys has flagged three joints in six weeks.** Injury risk is the outcome sleep affects most
  strongly, and hers is the training that keeps getting interrupted.
- **Neither has any sleep data recorded**, despite both wearing Garmins that measure it.

## What a sleep prescription looks like

Deliberately short, because the evidence supports duration far more strongly than it supports any
particular hygiene ritual:

- **Target 8 hours in bed as a floor, not a ceiling.** For someone habitually on 7, adding an hour
  is the whole intervention.
- **Consistency of timing** matters alongside duration.
- Everything else - screens, temperature, caffeine cut-offs - is secondary to actually being in bed
  long enough, and should not be allowed to become the conversation.
- **Caffeine timing is the one crossover with `fuelling-method.md`**: an evening training session
  fuelled with 3-6 mg/kg of caffeine at 6pm is a sleep problem as well as a performance aid. If
  sessions are late, caffeine dosing needs to account for it.

**This is a proposal, not a coaching note**, and it is arguably not even that - it is a
conversation. But it is the largest single lever in this entire document set and it costs nothing.

---

# Part 2 - Tissue tolerance and load management

## The rule that actually predicts injury

Covered in full in `running-method.md` Part 6, summarised here because it belongs to both:

An 18-month cohort of **5,205 runners and over half a million runs** found that weekly mileage
totals and the acute:chronic workload ratio had **little to no predictive value**, while
**single-run spikes did**:

| Single run vs longest run in last 30 days | Injury risk |
|---|---|
| 10-30% longer | +64% |
| 30-100% longer | +52% |
| over 100% longer | +128% |

**The rule: do not increase your longest run by more than about 10% over your furthest in the last
30 days.** Weekly totals matter much less than that one number.

## The acute:chronic workload ratio is not the tool it is sold as

Worth stating explicitly so nobody builds a feature on it. ACWR validity has been questioned on the
heterogeneity of the load measures used to compute it; the activity thresholds and "sweet spots" have
limited evidential support; and in at least one professional-sport cohort **spikes in ACWR were
dissociated from injury occurrence**. Rapid load increases genuinely do raise injury risk. ACWR is
not a reliable way to detect them.

## Medial tibial stress syndrome - what the evidence adds

`coaching-method.md` Part 1 already carries the return-to-run sequence and it is correct. What the
wider literature adds is the *why*, and three levers that sit alongside it:

**Return-to-run sequence (unchanged, restated for completeness):** pain-free walking for 10-14
consecutive days; restart with run/walk intervals at roughly a third of pre-injury running volume;
build over 2-4 weeks at no more than ~10% more running per week; **hold rep length constant and add
reps first**, because rep length is what loads shins hardest; calf and hip strengthening throughout;
stop at the *first* twinge, and one flare means hold, not go back.

**What to add:**

1. **Gait retraining, and specifically cadence.** A 10% cadence increase reduced peak tibial
   acceleration by 11.5% and vertical average loading rate by 15.6%; across runners, each additional
   step per minute is associated with roughly 5% lower bone stress injury risk. Reducing stride
   length and widening the base of support work in the same direction. The evidence is not unanimous
   - two studies found no clear directional effect - so treat it as cheap and promising. **Cerys's
   per-rep running cadence is 140-151 spm**, which is genuinely low, and this is the closest match
   between a lever and a problem in either of their data. Full detail in `running-method.md` Part 5.
2. **Calf strengthening is not optional.** Graded running, calf strengthening and calf stretching are
   the standard prescription, gastrocnemius-soleus stretching and eccentric calf work are the usual
   targets, and **calf length is shin insurance**. Note that Cerys already has a 70 kg standing calf
   raise, so the raw strength is there - the eccentric and endurance qualities may not be.
3. **Hip abductor training has direct RCT support** in runners with MTSS, working on pelvic drop and
   knee valgus. She already has a 50 kg hip abduction. Again the question is whether the strength
   transfers to control while running, which is a different quality.
4. **Graded running itself strengthens the tibial cortex.** This is the important framing: running is
   not merely the thing that hurt her, it is also the only thing that makes the bone able to
   tolerate running. That is why the answer is graded return rather than avoidance, and why
   cross-training - which preserves fitness but does not load bone - cannot substitute for it (see
   `running-method.md` Part 2).

## The pattern worth watching, not diagnosing

**Three joints flagged in six weeks: shins, left hip, right shoulder.** None serious, all settling.
`coaching-method.md` already says this warrants caution rather than bravery, and that stands.

What this file adds is that **two of the three plausible systemic explanations are measurable and
neither is being measured**: sleep (Part 1) and energy availability (`fuelling-method.md` Part 1).
Low energy availability specifically produces injuries "such as stress fractures and tendon
injuries due to weakened tissue and immune changes". That is not a diagnosis and must not be
presented as one. It is a reason to collect the data before concluding it is bad luck.

---

# Part 3 - What to measure, and what the numbers are worth

## The finding: the wellness pipeline already exists

`coaching-method.md` says of Daniel's tiredness notes: "No overnight wellness data exists to tell
whether that is load, sleep or fuelling."

**The tooling to collect it is already built.** `garmin_wellness` in both Garmin MCP servers stores
sleep and its stages, sleep score, overnight HRV, resting heart rate, respiration and training
readiness. It is incremental and safe to re-run.

Its own documentation names the reason it returns nothing: **"Expect nothing back while the watch is
only worn for workouts."**

So **the wellness gap is behavioural, not technical.** The single action that closes it is wearing
the watch overnight. Nothing needs building. That is worth knowing before anyone proposes a feature
to solve it.

Two caveats to set expectations:

- **HRV status needs about three weeks of overnight wear** before it means anything. There is no
  quick read here; it is a habit or it is nothing.
- `garmin_wellness` **writes to the shared store**, so it is a real data-changing call and belongs in
  an agreed session, not a casual one.

## How much to trust the numbers once they exist

Be careful here, because the composite scores are the seductive part and the weakest part.

- **The underlying measures have support.** Daily resting HRV recordings have been used to guide
  endurance training prescription in untrained, recreationally trained and well-trained
  participants, producing greater endurance improvements than fixed predefined training. Resting HR
  and sleep duration are straightforward measurements.
- **The composite scores do not.** Garmin's Body Battery and Training Readiness are proprietary
  models built on top of the HRV estimate. **No independent validation study has been published for
  the composite score against a reference standard**, and the models are not published in a form that
  allows scrutiny. Training Readiness blends six inputs - sleep score, HRV status, remaining
  recovery time, acute training load, sleep history and stress history - by an undisclosed method.

**The rule:** use **sleep duration, resting HR and HRV trend** as inputs to a conversation. Treat
Body Battery and Training Readiness as **trend indicators, never as instructions**, and never write
a coaching note that hangs on one. This is the same principle already in `coaching-method.md` about
not trusting an average over mixed work: know what a number is made of before you act on it.

## The measurement priority list

Ordered by value per unit of effort. All of it is data collection; none of it changes training.

1. **Wear the watches overnight.** Unlocks sleep, resting HR, HRV and respiration in one move, with
   no new code and no new habit beyond charging the watch during the day instead of at night.
2. **Cerys weighs in more than once.** One reading from 1 August is not a trend, and it also blocks
   correct pull-up scoring - which is her stated goal.
3. **Daniel weighs in often enough to see a trend.** Eleven of thirteen readings are an identical
   77.2 kg, which suggests the scale data is not arriving as often as the record implies.
4. **Keep logging RPE and the feel notes.** They are already there, already honest, and they are the
   only subjective signal in the system. `coaching-method.md` already notes that Cerys's notes
   under-record what went well - that is a reason to prompt for the good part, not a reason to trust
   the notes less.

---

# Part 4 - What this file deliberately does not do

- **It does not diagnose.** `coaching-method.md` Part 3 is explicit: pain notes get deload, mobility,
  footwear and "if it persists, get it checked". Nothing in Part 2 changes that, and the RED-S
  material in `fuelling-method.md` is subject to the same limit with knobs on.
- **It does not prescribe recovery modalities.** Ice baths, compression, massage guns, foam rolling
  as a general practice, sauna - none of it was researched for this file because none of it is close
  to sleep, load management and fuelling in effect size. If one comes up specifically, research it
  then.
- **It does not propose any change to the program.** Everything here is either data collection or a
  conversation. Anything that would change sets, reps, targets or which exercises goes through
  `propose_suggestion_tool` for Daniel to approve.

---

## Sources

- Sleep: [The impact of sleep interventions on athletic performance - systematic review](https://link.springer.com/article/10.1186/s40798-023-00599-z),
  [A narrative review of the impact of sleep on athletes](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11779686/),
  [Sleep and athletic performance - multidimensional review](https://www.mdpi.com/2077-0383/14/21/7606),
  [Sleep and the elite athlete - GSSI](https://www.gssiweb.org/sports-science-exchange/article/sse-113-sleep-and-the-elite-athlete).
- Load management: [Marathon Handbook on the Nielsen et al. 5,205-runner BJSM study](https://marathonhandbook.com/the-10-rule-new-study-suggests-weve-been-doing-it-wrong-this-whole-time/),
  [The acute:chronic workload ratio - challenges and prospects](https://arxiv.org/pdf/1907.05326),
  [Spikes in acute:chronic workload are dissociated from injury occurrence](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7739681/).
- MTSS: [Medial tibial stress syndrome - scoping review](https://pmc.ncbi.nlm.nih.gov/articles/PMC11958822/),
  [MTSS - StatPearls](https://www.ncbi.nlm.nih.gov/books/NBK538479/),
  [Effect of hip abductor training on pelvic drop and knee valgus in runners with MTSS - RCT](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11520670/),
  [The treatment of MTSS in athletes - randomized clinical trial](https://pmc.ncbi.nlm.nih.gov/articles/PMC3352296/),
  [The influence of running technique modifications on vertical tibial loading](https://doi.org/10.3390/biomechanics5020022),
  [Medial Tibial Stress Syndrome - Physiopedia](https://www.physio-pedia.com/Medial_Tibial_Stress_Syndrome).
- Wearable metrics: [Garmin Training Readiness - the5krunner](https://the5krunner.com/garmin-features/training/training-readiness/),
  [Garmin HRV accuracy against clinical ECG](https://the5krunner.com/2026/02/18/garmin-hrv-accuracy/),
  [Validity of wrist-worn devices for HR and HRV at rest](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8747571/).
