# Plan: a permanent Session tab, and Body folded into Progress

**Status: proposal, awaiting Daniel's go-ahead.** Nothing here is built. From the in-app
suggestion (11 Aug): *"put body section into progress and reimplement a session tab instead of
having to click log it every time you go off of it"*.

## The problem

There are five tab slots and six views. `renderLog` lost its slot when Home was added, so the log
form is reachable **only** via Home's **Log it** button ([js/app.js](../js/app.js), `switchTab`
comment: *"Works even for views without a bottom-bar tab (Log, Guide)"*). Mid-workout that means
every trip to History to check last week's numbers costs three taps to get back: Home, scroll,
Log it. The draft itself survives (drafts persist to `flLiveTracker_v1_drafts`), so this is a
**navigation** annoyance, not a data-loss one - but it's the tab you're standing in the gym with.

Body is the natural donor. It's two things - bodyweight and goals - both of which are "how the
body is progressing", and Progress is already the tab about progressing.

## Proposed shape

Bottom bar becomes: **Home · Session · History · Progress · Program**

### 1. Session tab

- New bar button, `data-tab="log"`. **Keep the internal key `"log"`** - `activeTab==="log"` gates
  draft capture in four places (js/app.js:367, 512, 2119, 2909) and renaming the key would silently
  break draft persistence. Only the label changes.
- Renders `renderLog()` exactly as it does today. No change to the form itself.
- **Any day of the week.** `sessionForDate()` returns nothing for Sat/Sun, and `renderView`
  already falls back to `program.order[0]`; the session dropdown at the top of the form is how you
  pick something else. So the tab is always usable, it just opens on a sensible default.
- **Blank install:** `renderView` currently forces `activeTab="edit"` when `program.order` is
  empty. Keep that, and additionally disable/grey the Session button until a first session exists,
  so tapping it can't land on an empty form.
- Home's **Log it** button stays. It's still the shortcut that *sets the session for today* and
  jumps, which is a different action from "open the tab I was in".

### 2. Body folds into Progress

Progress becomes two sub-views behind a toggle at the top of the tab, reusing the existing
`.ptoggle` pill idiom (the person switcher in the header) rather than inventing a control:

```
[ Lifts | Body ]
```

- **Lifts** = today's Progress: 🏅 Records table + the exercise chart with its
  exercise/metric selects.
- **Body** = today's Body tab, unchanged: 🎯 goals, the bodyweight add form + CSV import, the
  trend chart, the entries list.
- Which sub-view you're on is remembered in memory for the session (a module-level `progressPane`,
  same pattern as `openSessions` in the Program tab) and resets to **Lifts** on reload.

**Why a toggle and not one long page:** stacked, the tab would be a records table, a chart, a goals
card, an entry form, a second chart and a list - about two and a half phone screens before you
reach the bodyweight box you opened it for. Both halves also own a Chart.js instance (`chart` and
`bwChart`); rendering one at a time keeps that to one live chart, and each render path already
destroys its own before recreating.

## Work involved

| # | Change | Files | Size |
|---|---|---|---|
| 1 | Add the Session tab button; label + disabled state | `index.html`, `js/app.js` | S |
| 2 | Remove the Body tab button | `index.html` | S |
| 3 | `renderProgress` wraps the existing markup in a pane toggle; `renderBody`'s markup becomes the second pane | `js/app.js` | M |
| 4 | Repoint the three internal `renderBody()` self-re-renders (add weight, CSV import, delete entry - js/app.js:1550, 1556, 1568) at the new pane renderer | `js/app.js` | S |
| 5 | Repoint Home's `data-home-go="body"` arrow (js/app.js:2834) at Progress + the Body pane | `js/app.js` | S |
| 6 | `renderView`: `activeTab==="body"` should still resolve, so an old persisted tab value or a stale link doesn't dead-end | `js/app.js` | S |
| 7 | Guide: rewrite section 5 and 6, which describe Body as its own tab, plus any "five tabs" wording | `js/app.js` (`renderHelp`) | M |
| 8 | `README.md` if it lists the tabs; `docs/PROJECT-STATUS.md` feature list | docs | S |
| 9 | Bump `CACHE_NAME` | `sw.js` | S |

Overall **M**. No data-model change at all - no migration, nothing to sync, nothing that can
corrupt a log. That's what makes it safe despite touching navigation.

## Risks and how they're handled

- **Muscle memory.** Body has been its own tab since the beginning; it moving is the one thing
  here Cerys would notice without being told. Mitigate by keeping the 🏋 Body arrow on Home
  pointing straight at the Body pane, so the Home route is unchanged.
- **Draft capture.** `switchTab` calls `captureDraft()` before every switch and drafts persist to
  their own localStorage key with a 12h expiry, so tabbing away from a half-entered session and
  back is already safe. Adding a tab doesn't change that - but it should be re-verified in the
  browser with a part-filled form, because it's now the common path rather than a rare one.
- **Chart leaks.** Two Chart.js instances on one tab. The toggle renders one pane at a time and
  each path destroys its own chart first (js/app.js:1576, `if(chart) chart.destroy()`), so this is
  covered as long as the pane switch goes through the render functions rather than
  showing/hiding markup.
- **The Guide going stale.** It describes Body as a tab in two sections. Convention says the Guide
  reflects reality, so this is part of the work, not a follow-up.

## Open question for Daniel

**What should the tab be called - "Session" or "Log"?** "Log" matches the verb on Home's button
and the internal key; "Session" matches what the tab actually shows (today's session, whether or
not you log anything). The suggestion says "session tab", so that's the default unless you say
otherwise.
