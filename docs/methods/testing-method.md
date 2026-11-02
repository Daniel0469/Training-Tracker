# Testing method - how to know where they actually are

**Written 2026-09-02.**

Almost every number this project coaches from is an **inference**, not a measurement. The 5k
estimates are reasoned from partial evidence and one of them is explicitly labelled low confidence.
Neither person has ever done a formal test of anything. Cerys has no threshold at all.

That is not a criticism of the coaching - the inferences have been careful and honestly caveated.
It is an argument that a small number of cheap tests would improve every decision downstream of
them, and this file says which ones and why.

**The governing rule, before any of it:** *a test earns its place only if the result would change a
decision.* Tests cost a session and some fatigue. A number nobody will act on is a number not worth
collecting.

---

# Part 1 - The zone problem, which is the big one

## Where their zones come from

| | Daniel | Cerys |
|---|---|---|
| Zone method | `LACTATE_THRESHOLD` | `HR_MAX` |
| Max HR | 200 | 199 |
| Resting HR | 52 | 67 |
| **Threshold HR** | **173** | **not established** |
| Zone floors | 100 / 120 / 140 / 160 / 180 | 100 / 119 / 139 / 159 / 179 |

**Daniel's zones are anchored to a threshold estimate. Cerys's are percentages of a maximum.** Those
are not equivalent, and the difference is larger than it looks.

## Why percentage-of-max is the weaker anchor

- **Two athletes at the same percentage of max HR can be at completely different physiological
  intensities.** Lactate accumulation and metabolic transitions vary enormously between individuals,
  and a percentage-based zone does not track where anyone's actual transitions sit.
- Where the maximum itself comes from a formula, the error is large: **220-minus-age is off by 10-15
  bpm on average**, with age-based methods ranging ±10-30 bpm. That error propagates into every zone
  boundary.

**One thing in Cerys's favour, and it should be said:** her max of 199 is probably not a formula
artefact. She has been recorded at **192 bpm** in a real session, which is 96% of the stated max, so
the ceiling looks broadly right. **The missing piece is the threshold, not the maximum** - and
threshold is what zone boundaries ought to key off, because it is the boundary that actually means
something physiologically.

## Why this matters for the coaching, concretely

Her whole training picture is described in HR terms - "Zone 4 within a minute", "ten minutes above
Zone 4", "incline walking sits reliably at HR ~139". Those observations are used to make real
decisions. They rest on zone boundaries derived by a cruder method than Daniel's.

**This does not mean the observations are wrong.** The 192 bpm reading and the 139 bpm incline-walk
figure are direct measurements and stand on their own. What is unreliable is the *labelling* -
whether 139 is genuinely her Zone 2, and whether the Zone 3/4 boundary at 159 is anywhere near her
actual threshold.

---

# Part 2 - The 30-minute field test

The standard, and the best-validated field option.

## Protocol

1. Warm up easy for 10-15 minutes.
2. Run a hard, steady **30-minute time trial, alone** - alone matters, because company changes
   pacing.
3. **Press lap at exactly 10 minutes.**
4. **Your average HR over the final 20 minutes is your lactate threshold HR (LTHR).**

The first 10 minutes are discarded because heart rate is still climbing toward the effort.

## Why this one

Of four field tests compared against blood draws, **the 30-minute time trial estimate was the only
one that did not differ significantly from the laboratory measurement.** That is a strong result for
a test that needs no equipment beyond a watch.

## Setting zones from LTHR

| Zone | % of LTHR |
|---|---|
| 1 - Recovery | under 85% |
| 2 - Aerobic | 85-89% |
| 3 - Tempo | 90-94% |
| 4 - Threshold | 95-105% |
| 5 - VO2max | over 106% |

**Retest every 6-8 weeks** and update the zones the same day, otherwise the zones drift out of date
while the athlete improves and every session gets prescribed slightly wrong.

## Running it on their treadmills

Their equipment constrains this, and the constraints are already documented in `coaching-method.md`
Part 4:

- **Run it manually, not as a programmed sequence.** A programmed sequence holds a fixed speed; a
  time trial needs the athlete to be able to adjust. Fixing the speed turns it into a different test.
- **Turn auto-lap off** so the manual lap press at 10 minutes is clean.
- **The belt's own numbers are the record, typed in.** Both watches read high on a treadmill -
  Daniel ~9%, Cerys ~13% - and typed values are never overwritten by the Garmin sync.
- **HR is the output that matters here**, and HR is measured directly rather than estimated from
  wrist movement, so the treadmill's distance inaccuracy does not affect the result.

---

# Part 3 - Cerys cannot do that test, and pretending otherwise would hurt her

**Her longest continuous run is about one minute.** A 30-minute running time trial is not a test she
would fail; it is a test she cannot start, and attempting it would be an injury given a shin history
that has already flared three times.

This is exactly the case `coaching-method.md` Part 3 exists for: the textbook protocol is wrong for
this athlete, and the override is stated rather than quietly worked around.

## What to do instead, in order of preference

1. **Wait.** Her running threshold becomes measurable when she can run for 30 minutes, and getting
   there is already the plan (`hyrox-method.md` Phase 0, and the MTSS sequence). **The test is not
   urgent, because nothing currently being decided would change on the result.** By the governing
   rule at the top of this file, that means it does not earn its place yet.
2. **Use what is already measured, because it is better than a formula.** Her incline walking sits
   **reliably at HR ~139** and is genuinely pain-free aerobic work. That is an empirical, repeated,
   modality-specific observation of where her easy aerobic work lands. It is worth more than a zone
   boundary computed from a percentage, and the coaching already uses it correctly.
3. **If a threshold number is genuinely wanted sooner, test it on a modality she can sustain** - the
   ski erg, the rower, or incline walking. **But label it honestly:** threshold is
   modality-specific, so a rowing LTHR is a rowing number and does not transfer cleanly to running
   HR zones. It would be useful for pacing the Hyrox erg stations and misleading for anything else.
4. **Never** infer her running threshold from Daniel's, from a formula, or from her interval
   sessions, where the HR reflects repeated short efforts rather than a sustained one.

## Daniel's is fine, and worth confirming once

His threshold of 173 comes from Garmin's lactate-threshold method, which is a real estimate rather
than a formula, and his 26 Aug session is consistent with it - he held 11.0 km/h for 13:44 settling
at 153 then 162, comfortably below 173, with only 9 bpm of drift. **A 30-minute test would confirm
it and would also, usefully, be his longest ever continuous run.** Two birds.

That last point is worth sitting with: for Daniel the test *is* the training. His limiter is
duration, a 30-minute TT is 30 minutes of duration, and it produces a number that improves every
subsequent prescription.

---

# Part 4 - The other tests worth having

## Running

- **A 5k or 2 km time trial.** Daniel has already done a 2 km (9:34, max HR 183, conservatively
  paced and still climbing at the finish). Repeating it periodically is the cleanest read on whether
  the 5k estimate is moving. The pacing framework in `coaching-method.md` Part 1 applies: expect the
  first attempt at an unfamiliar distance to be run too conservatively.
- **Judging whether an effort was maximal** is already covered in `coaching-method.md` - finish at
  ~95% of max HR, HR still climbing means they ran out of distance not engine, a large negative
  split means the start was too cautious. Apply that to every test, or the test result is a pacing
  measurement rather than a fitness one.

## Strength

- **Do not 1RM test.** It carries injury risk, it needs technique they have not built, and it is
  unnecessary: a rep-max at a given RPE gives an equally usable number at a fraction of the cost.
- **Use the RPE that is already being collected.** The app records RPE per set for every lifting
  exercise. A top set at a stated RPE *is* a test, taken every session, at zero extra cost. Nothing
  currently reads it - see `strength-method.md` Part 3.
- Daniel's deadlift needs **more sessions before it needs a test.** One entry is not a baseline.

## Hyrox

- **The benchmark is the event itself**: 1 km run, station, 1 km run, station, through all eight.
  Run to competition standards, after **48 hours of rest**.
- **A half simulation (4 runs, 4 stations) comes first**, and for Daniel and Cerys even that is
  some way off - a full simulation is 8 km of running, which is Phase 0 of the build.
- Record **RPE at the end of each run and each station**. The published study did exactly this, and
  it is the cheapest way to find out which stations actually cost them, as opposed to which ones they
  expect to.
- **Station-by-station benchmarks come before any simulation** and are much cheaper: a 1000 m ski erg
  time, a 1000 m row time, a 50 m sled push at a submaximal load. Each is a five-minute test that
  makes the next prescription concrete.

## Mobility

Already built and already correct: the Mobility assessment session, nine tests, fourteen
measurements, floor- or wall-referenced, **measured cold**. `flexibility-method.md` section 9 now
carries reference values so a result can be interpreted rather than only compared to itself. The
gap identified there - **no hip-extension measure** - is the one addition worth making.

## Body

- **Bodyweight**, which already exists as a feature and is barely used. One reading ever for Cerys;
  eleven identical readings for Daniel. See `fuelling-method.md` Part 6.
- **Bloods including ferritin**, optional and personal, covered in `female-athlete-method.md` Part 2.

---

# Part 5 - What to test first

Ordered by "would the result change a decision", which is the only ordering that matters.

1. **Daniel: the 30-minute threshold test.** Confirms his threshold, doubles as his longest ever
   continuous run, and improves every subsequent running prescription. Highest value by a distance.
2. **Station benchmarks for both, at submaximal loads.** Five minutes each, they have the kit for
   seven of eight stations, and every Hyrox prescription is currently generic because nobody has any
   station data at all.
3. **Read the RPE that is already being collected.** Not a test - a feature. It converts every
   lifting session into a measurement.
4. **The Mobility assessment, actually done.** It was built, it is waiting on them, and
   `flexibility-method.md` says the whole flexibility plan is blocked on it.
5. **Cerys's threshold test: not yet.** It is not that it would be nice and is impractical - it is
   that no current decision would change on the answer, and the incline-walk observation already
   covers what the zones would be used for. Revisit when she can run 30 minutes.
6. **Bodyweight, regularly, for both.** Not a test, a habit, and it unblocks pull-up scoring.

---

# Part 6 - How to not let testing become the training

Three cautions, because testing is seductive and this project is capable of over-instrumenting.

- **Retest zones every 6-8 weeks, not more.** More often and you are measuring noise and day-to-day
  variation rather than adaptation.
- **A test is a hard session.** It comes out of the week's budget, not on top of it. For two people
  training five days a week with one run each, a test replaces the quality session; it does not
  supplement it.
- **Do not test what the training already tells you.** Daniel's squat has moved 40 → 100 in eight
  weeks in ordinary sessions. That is a better progress signal than any test, and a 1RM attempt would
  add risk and no information.

---

## Sources

- Field testing: [Lactate threshold field test, 30-minute protocol](https://steelcityendurance.com/testing/lactate-threshold-field-test-30-min/),
  [How to calculate lactate threshold: 3 tests that work - Runners Connect](https://runnersconnect.net/how-to-calculate-your-lactate-threshold/),
  [Field test vs lab lactate test: a practical assessment](https://mtntactical.com/research/field-test-vs-lab-lactate-test-a-practical-lactate-threshold-assessment/).
- Zones: [Joe Friel's quick guide to setting training zones - TrainingPeaks](https://www.trainingpeaks.com/learn/articles/joe-friel-s-quick-guide-to-setting-zones/),
  [Lactate threshold explained: LT1, LT2 and your zones](https://www.trainingzones.io/en/guides/lactate-threshold),
  [Max heart rate by age: 4 formulas compared, and the field test that beats them](https://marathonhandbook.com/max-heart-rate-by-age/).
- Reliability: [Heart-rate and RPE running-speed thresholds show acceptable test-retest reliability](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12377137/).
- Hyrox testing: [Acute physiological responses and performance determinants in Hyrox (Frontiers in Physiology, 2025)](https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2025.1519240/full),
  [How to benchmark your Hyrox readiness - TrainRox](https://www.trainrox.com/articles/hyrox-readiness-test/).
