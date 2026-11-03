"use strict";
// Cases for editing saved sessions: the PR recheck, applyLogEdit and the undo steps. Shared by
// edit-cases.html (in the browser) and the command line:
//
//   ELECTRON_RUN_AS_NODE=1 "<VS Code>/Code.exe" scratchpad/review/edit-cases.js
//   ELECTRON_RUN_AS_NODE=1 "<VS Code>/Code.exe" scratchpad/review/edit-cases.js --dryrun <state.json>
//
// It reads the source text of js/app.js, cuts out the functions it needs and runs them on small
// fixture stores, so it opens no page and reads and writes no real store. --dryrun reports how many
// stored pr flags a full recompute of a store copy would flip with no edit at all.

// A whole `function name(...) {...}` out of the source, by brace matching.
function grab(src, name) {
  const at = src.indexOf("function " + name + "(");
  if (at < 0) throw new Error("function " + name + " not found in js/app.js");
  let depth = 0;
  for (let i = src.indexOf("{", at); i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}" && --depth === 0) return src.slice(at, i + 1);
  }
  throw new Error("unbalanced braces in " + name);
}
// A one-line `const name = ...;` out of the source.
function grabConst(src, name) {
  const m = new RegExp("^const " + name + "\\s*=.*;\\s*$", "m").exec(src);
  if (!m) throw new Error("const " + name + " not found in js/app.js");
  return m[0].trim();
}

const FUNCTIONS = ["isLoadCol", "isLifting", "isTimed", "isRunning", "workRows", "holdWeight", "parseRest",
  "colIndex", "loadTypeOf", "loadPctOf", "programExerciseByName", "clearCaches", "bwFor", "bodyweightOn",
  "setLoad", "logVolume", "newLogIndex", "indexLog", "logIndex", "prevBestLookup", "entryPr", "findPrs",
  "prChanges", "applyPrChanges", "recheckPrs", "isSetRow", "setIndexList", "editedEntry", "applyLogEdit",
  "commitLogEdit", "editToast"];
const CONSTS = ["clone", "byDateThenId", "sameJson", "trimRow", "numSort", "shortDate"];

// The app's own functions, bound to `state` and to the given stand-ins for the page.
function makeApi(src, state, env) {
  const body = "let progExIndex=null, bwIndex={}, personIndex={}, progIndex={};\n"
    + "function save(){ clearCaches(); env.saved=(env.saved||0)+1; }\nfunction syncNow(){ env.synced=(env.synced||0)+1; }\n"
    + CONSTS.map(n => grabConst(src, n)).join("\n") + "\n"
    + FUNCTIONS.map(n => grab(src, n)).join("\n")
    + "\nreturn { " + FUNCTIONS.concat(CONSTS).join(", ") + " };";
  return new Function("state", "env", body)(state, env || {});
}

// ---- fixtures ----
const lift = (name, rows, extra) => Object.assign({ name, cols: ["Weight (kg)", "Reps"], rows: rows.map(r => r.map(String)) }, extra || {});
const hold = (name, rows, extra) => Object.assign({ name, cols: ["Weight (kg)", "Time (s)"], timed: true, rows: rows.map(r => r.map(String)) }, extra || {});
const mkLog = (id, date, person, entries, extra) => Object.assign({ id, updatedAt: id, date, person, sessionKey: "upper1",
  sessionName: "Upper A", entries, feedback: "", difficulty: null, volume: 0 }, extra || {});
const mkState = logs => ({ people: ["Daniel", "Cerys"], weights: ["", ""], program: { order: [], sessions: {} }, bodyweights: [], logs, deletedLogs: [] });

// ---- cases ----
// Each case builds its own store, so none depends on another. t.eq compares by JSON.
const CASES = [];
const add = (name, fn) => CASES.push({ name, fn });

add("findPrs: a lift above the earlier best is a PR, the first ever and a tie are not", (A, t) => {
  const state = mkState([mkLog(1, "2026-11-01", "Daniel", [lift("Bench press", [[60, 8]])])]);
  const api = A(state);
  const en = [lift("Bench press", [[62.5, 8]]), lift("Squat", [[100, 5]]), lift("Bench press", [[60, 8]])];
  t.eq(api.findPrs(en, "Daniel", "2026-11-05").map(p => p.name + ":" + p.weight), ["Bench press:62.5"]);
  t.eq([en[0].pr, en[1].pr, en[2].pr], [62.5, undefined, undefined]);
});
add("findPrs: a timed hold is a PR only above the earlier hold at that weight", (A, t) => {
  const state = mkState([mkLog(1, "2026-11-01", "Daniel", [hold("Plank", [[0, 40], [5, 30]])])]);
  const api = A(state);
  const longer = [hold("Plank", [[0, 50]])], newWeight = [hold("Plank", [[10, 90]])];
  t.eq(api.findPrs(longer, "Daniel", "2026-11-05"), [{ name: "Plank", weight: 0, hold: 50 }]);
  t.eq(api.findPrs(newWeight, "Daniel", "2026-11-05"), []);
});
add("findPrs: a given previous-best lookup replaces the saved logs", (A, t) => {
  const api = A(mkState([]));
  const prev = { best: () => 50, hold: () => 0 };
  t.eq(api.findPrs([lift("Bench press", [[60, 8]])], "Daniel", "2026-11-05", prev).length, 1);
});

const benchLogs = () => [
  mkLog(1, "2026-11-01", "Daniel", [lift("Bench press", [[60, 8]])]),
  mkLog(2, "2026-11-05", "Daniel", [lift("Bench press", [[62.5, 8]], { pr: 62.5 })]),
  mkLog(3, "2026-11-09", "Daniel", [lift("Bench press", [[65, 8]], { pr: 65 })]),
];
add("prChanges: raising an earlier session removes the later PRs it now beats", (A, t) => {
  const state = mkState(benchLogs());
  const api = A(state);
  state.logs[0].entries[0].rows = [["70", "8"]];
  const ch = api.prChanges("Daniel", ["Bench press"], state.logs[0]);
  t.eq(ch.map(c => c.log.id + ":" + c.was + ">" + c.now), ["2:62.5>null", "3:65>null"]);
});
add("prChanges: lowering an earlier session gives a later session its PR", (A, t) => {
  const logs = benchLogs();
  logs[2].entries[0].rows = [["62.5", "8"]]; delete logs[2].entries[0].pr;
  const state = mkState(logs);
  const api = A(state);
  state.logs[1].entries[0].rows = [["60", "8"]];
  const ch = api.prChanges("Daniel", ["Bench press"], state.logs[1]);
  t.eq(ch.map(c => c.log.id + ":" + c.was + ">" + c.now), ["2:62.5>null", "3:null>62.5"]);
});
add("prChanges: writes nothing, applyPrChanges writes the flags and stamps only the logs that flipped", (A, t) => {
  const state = mkState(benchLogs().concat([mkLog(4, "2026-11-10", "Daniel", [lift("Squat", [[100, 5]])])]));
  const api = A(state);
  state.logs[0].entries[0].rows = [["70", "8"]];
  const ch = api.prChanges("Daniel", ["Bench press"], state.logs[0]);
  t.eq(state.logs[1].entries[0].pr, 62.5);
  api.applyPrChanges(ch, 999);
  t.eq(state.logs.map(l => l.updatedAt), [1, 999, 999, 4]);
  t.eq(state.logs.map(l => l.entries[0].pr), [undefined, undefined, undefined, undefined]);
});
add("prChanges: only the named exercises are looked at", (A, t) => {
  const logs = benchLogs();
  logs[1].entries.push(lift("Squat", [[90, 5]], { pr: 90 }));
  logs[0].entries.push(lift("Squat", [[100, 5]]));
  const state = mkState(logs);
  const api = A(state);
  state.logs[0].entries[0].rows = [["70", "8"]];
  const ch = api.prChanges("Daniel", ["Bench press"], state.logs[0]);
  t.eq(ch.map(c => c.name), ["Bench press", "Bench press"]);
  t.eq(api.prChanges("Daniel", [], state.logs[0]), []);
});
add("prChanges: runs in date then id order whatever the array order, and skips the other person", (A, t) => {
  const logs = benchLogs().reverse();
  logs.push(mkLog(7, "2026-11-02", "Cerys", [lift("Bench press", [[100, 5]])]));
  const state = mkState(logs);
  const api = A(state);
  const first = state.logs.find(l => l.id === 1);
  first.entries[0].rows = [["70", "8"]];
  const ch = api.prChanges("Daniel", ["Bench press"], first);
  t.eq(ch.map(c => c.log.id).sort(), [2, 3]);
});
add("prChanges: nothing before the edited session is touched", (A, t) => {
  const state = mkState(benchLogs());
  const api = A(state);
  state.logs[1].entries[0].rows = [["59", "8"]];
  const ch = api.prChanges("Daniel", ["Bench press"], state.logs[1]);
  t.eq(ch.map(c => c.log.id + ":" + c.was + ">" + c.now), ["2:62.5>null"]);
});
add("prChanges: the edited session's PR value follows its new top set", (A, t) => {
  const state = mkState(benchLogs());
  const api = A(state);
  state.logs[2].entries[0].rows = [["66", "8"]];
  const ch = api.prChanges("Daniel", ["Bench press"], state.logs[2]);
  t.eq(ch.map(c => c.log.id + ":" + c.was + ">" + c.now), ["3:65>66"]);
});
add("prChanges: warm-up sets never set a record", (A, t) => {
  const logs = benchLogs();
  const state = mkState(logs);
  const api = A(state);
  state.logs[2].entries[0].rows = [["100", "3"], ["65", "8"]];
  state.logs[2].entries[0].warmup = [0];
  t.eq(api.prChanges("Daniel", ["Bench press"], state.logs[2]), []);
});
add("prChanges: a second entry of the same name in a session does not raise the running best", (A, t) => {
  const state = mkState([
    mkLog(1, "2026-11-01", "Daniel", [lift("Bench press", [[60, 8]]), lift("Bench press", [[80, 3]])]),
    mkLog(2, "2026-11-05", "Daniel", [lift("Bench press", [[70, 8]])]),
  ]);
  const api = A(state);
  const ch = api.prChanges("Daniel", ["Bench press"], state.logs[0]);
  t.eq(ch.map(c => c.log.id + ":" + c.now), ["2:70"]);
});
add("prChanges: holds are compared at the same weight", (A, t) => {
  const state = mkState([
    mkLog(1, "2026-11-01", "Daniel", [hold("Plank", [[0, 40]])]),
    mkLog(2, "2026-11-05", "Daniel", [hold("Plank", [[0, 50], [5, 30]])]),
  ]);
  const api = A(state);
  const ch0 = api.prChanges("Daniel", ["Plank"], state.logs[0]);
  t.eq(ch0.map(c => c.log.id + ":" + c.now), ["2:50"]);
  state.logs[0].entries[0].rows = [["0", "60"]];
  state.logs[1].entries[0].pr = 50;
  const ch1 = api.prChanges("Daniel", ["Plank"], state.logs[0]);
  t.eq(ch1.map(c => c.log.id + ":" + c.was + ">" + c.now), ["2:50>null"]);
});
add("prChanges: a stale PR on a first-ever set is removed", (A, t) => {
  const state = mkState([mkLog(1, "2026-11-01", "Daniel", [lift("Bench press", [[60, 8]], { pr: 60 })])]);
  const api = A(state);
  const ch = api.prChanges("Daniel", ["Bench press"], state.logs[0]);
  t.eq(ch.map(c => c.was + ">" + c.now), ["60>null"]);
});

// ---- applyLogEdit ----
const run = (rows, extra) => Object.assign({ name: "Treadmill run", cols: ["Distance (km)", "Time (mm:ss)", "Pace (min/km)"], rows: rows.map(r => r.map(String)) }, extra || {});
const single = en => mkState([mkLog(10, "2026-11-05", "Daniel", [en], { garmin: { avg_hr: 150, rows_from: "reps" }, garminActivityId: 77, corrections: [{ at: "x" }] })]);

add("applyLogEdit: replaces the sets and keeps every other key on the entry and the log", (A, t) => {
  const en = lift("Bench press", [[60, 8], [60, 7]], { done: [0, 1], rpe: "8", load: "bw", bwPct: 65, muscles: ["chest"], smith: true, extraKey: 1 });
  const state = single(en), api = A(state), log = state.logs[0];
  const r = api.applyLogEdit(log, { entries: [{ rows: [["62.5", "8"], ["62.5", "7"]], warmup: [], done: [0, 1] }] }, 555);
  t.eq(r, { changed: true, names: ["Bench press"] });
  t.eq(log.entries[0], { name: "Bench press", cols: ["Weight (kg)", "Reps"], rows: [["62.5", "8"], ["62.5", "7"]], done: [0, 1], rpe: "8", load: "bw", bwPct: 65, muscles: ["chest"], smith: true, extraKey: 1 });
  t.eq([log.id, log.date, log.sessionKey, log.sessionName, log.garmin, log.garminActivityId, log.corrections], [10, "2026-11-05", "upper1", "Upper A", { avg_hr: 150, rows_from: "reps" }, 77, [{ at: "x" }]]);
  t.eq([log.editedAt, log.updatedAt], [555, 555]);
});
add("applyLogEdit: the volume is worked out again from the new sets", (A, t) => {
  const state = single(lift("Bench press", [[60, 8]])), api = A(state);
  api.applyLogEdit(state.logs[0], { entries: [{ rows: [["62.5", "8"], ["62.5", "7"]], warmup: [], done: [] }] }, 1);
  t.eq(state.logs[0].volume, Math.round(62.5 * 8 + 62.5 * 7));
});
add("applyLogEdit: removing a set renumbers the warm-up and done marks", (A, t) => {
  const en = lift("Squat", [[40, 5], [100, 8], [100, 8], [100, 7]], { warmup: [0], done: [1, 2, 3] });
  const state = single(en), api = A(state);
  api.applyLogEdit(state.logs[0], { entries: [{ rows: [["40", "5"], ["100", "8"], ["100", "7"]], warmup: [0], done: [1, 2] }] }, 1);
  t.eq([state.logs[0].entries[0].rows.length, state.logs[0].entries[0].warmup, state.logs[0].entries[0].done], [3, [0], [1, 2]]);
});
add("applyLogEdit: a removed warm-up row drops the warmup key, and so do emptied done marks", (A, t) => {
  const en = lift("Squat", [[40, 5], [100, 8]], { warmup: [0], done: [0] });
  const state = single(en), api = A(state);
  api.applyLogEdit(state.logs[0], { entries: [{ rows: [["100", "8"]], warmup: [], done: [] }] }, 1);
  t.eq(Object.keys(state.logs[0].entries[0]).sort(), ["cols", "name", "rows"]);
});
add("applyLogEdit: blank rows and a load with no reps drop out like a save, and the marks follow", (A, t) => {
  const en = lift("Bench press", [[60, 8], [60, 8], [60, 8]], { done: [0, 1, 2] });
  const state = single(en), api = A(state);
  api.applyLogEdit(state.logs[0], { entries: [{ rows: [["60", "8"], ["", ""], ["60", ""], ["60", "9"]], warmup: [], done: [0, 3] }] }, 1);
  t.eq([state.logs[0].entries[0].rows, state.logs[0].entries[0].done], [[["60", "8"], ["60", "9"]], [0, 1]]);
});
add("applyLogEdit: an added set counts as done when the exercise has a done list, and not otherwise", (A, t) => {
  const ticked = lift("Bench press", [[60, 8]], { done: [0] }), plain = lift("Row", [[40, 10]]);
  const state = mkState([mkLog(10, "2026-11-05", "Daniel", [ticked, plain])]), api = A(state);
  api.applyLogEdit(state.logs[0], { entries: [{ rows: [["60", "8"], ["60", "8"]], warmup: [], done: [0, 1] }, { rows: [["40", "10"], ["40", "9"]], warmup: [], done: [] }] }, 1);
  t.eq([state.logs[0].entries[0].done, state.logs[0].entries[1].done], [[0, 1], undefined]);
});
add("applyLogEdit: an exercise left with no sets goes, a run stays", (A, t) => {
  const state = mkState([mkLog(10, "2026-11-05", "Daniel", [lift("Bench press", [[60, 8]]), lift("Row", [[40, 10]]), run([[5, "30:00", "6:00"]])])]), api = A(state);
  const r = api.applyLogEdit(state.logs[0], { entries: [{ rows: [["", ""]], warmup: [], done: [] }, undefined, { rows: [["", "", ""]], warmup: [], done: [] }] }, 1);
  t.eq(state.logs[0].entries.map(e => e.name + ":" + e.rows.length), ["Row:1", "Treadmill run:0"]);
  t.eq(r.names.sort(), ["Bench press", "Treadmill run"]);
});
add("applyLogEdit: edited run rows the watch sync wrote are marked edited in the app", (A, t) => {
  ["reps", "laps", "reps (replaced lap-derived rows)"].forEach(from => {
    const state = single(run([[5, "30:00", "6:00"]])), api = A(state);
    state.logs[0].garmin.rows_from = from;
    api.applyLogEdit(state.logs[0], { entries: [{ rows: [["4", "30:00", "7:30"]], warmup: [], done: [] }] }, 1);
    t.eq(state.logs[0].garmin.rows_from, "edited in app");
  });
});
add("applyLogEdit: rows_from is left alone for typed rows, for a run not edited, and when there is no garmin block", (A, t) => {
  const state = single(run([[5, "30:00", "6:00"]])), api = A(state), log = state.logs[0];
  log.garmin.rows_from = "manual";
  api.applyLogEdit(log, { entries: [{ rows: [["4", "30:00", "7:30"]], warmup: [], done: [] }] }, 1);
  t.eq(log.garmin.rows_from, "manual");
  log.garmin.rows_from = "reps";
  api.applyLogEdit(log, { entries: [{ rows: [["4", "30:00", "7:30"]], warmup: [], done: [], rpe: "6" }] }, 2);
  t.eq(log.garmin.rows_from, "reps");
  const bare = mkState([mkLog(11, "2026-11-05", "Daniel", [run([[5, "30:00", "6:00"]])])]);
  A(bare).applyLogEdit(bare.logs[0], { entries: [{ rows: [["4", "30:00", "7:30"]], warmup: [], done: [] }] }, 1);
  t.eq(bare.logs[0].garmin, undefined);
});
add("applyLogEdit: RPE, difficulty and the note change on their own, and cleared values are kept as empty", (A, t) => {
  const state = single(lift("Bench press", [[60, 8]], { rpe: "8" })), api = A(state), log = state.logs[0];
  log.difficulty = 7; log.feedback = "tired";
  const r = api.applyLogEdit(log, { entries: [{ rows: [["60", "8"]], warmup: [], done: [], rpe: "" }], difficulty: null, feedback: "  " }, 9);
  t.eq(r, { changed: true, names: [] });
  t.eq([log.entries[0].rpe, log.difficulty, log.feedback], [undefined, null, ""]);
  api.applyLogEdit(log, { entries: [{ rows: [["60", "8"]], warmup: [], done: [], rpe: "9" }], difficulty: 6, feedback: "better" }, 10);
  t.eq([log.entries[0].rpe, log.difficulty, log.feedback], ["9", 6, "better"]);
});
add("applyLogEdit: an edit that changes nothing leaves the log exactly as it was", (A, t) => {
  const state = single(lift("Bench press", [[60, 8]], { rpe: 8, done: [0] })), api = A(state), log = state.logs[0];
  const before = JSON.stringify(log);
  const r = api.applyLogEdit(log, { entries: [{ rows: [["60", "8"]], warmup: [], done: [0], rpe: "8" }], difficulty: null, feedback: "" }, 5);
  t.eq(r, { changed: false, names: [] });
  t.eq(JSON.stringify(log), before);
});
add("applyLogEdit: an untouched exercise keeps odd saved rows, an edited one drops them", (A, t) => {
  const odd = lift("Bench press", [[60, ""], [60, 8]]);
  const state = mkState([mkLog(10, "2026-11-05", "Daniel", [odd, lift("Row", [[40, 10]])])]), api = A(state);
  const r = api.applyLogEdit(state.logs[0], { entries: [{ rows: [["60", ""], ["60", "8"]], warmup: [], done: [] }, { rows: [["40", "10"], ["40", "9"]], warmup: [], done: [] }] }, 5);
  t.eq(r.names, ["Row"]);
  t.eq(state.logs[0].entries[0].rows, [["60", ""], ["60", "8"]]);
  api.applyLogEdit(state.logs[0], { entries: [{ rows: [["60", ""], ["60", "9"]], warmup: [], done: [] }] }, 6);
  t.eq(state.logs[0].entries[0].rows, [["60", "9"]]);
});
add("applyLogEdit: making a set a warm-up set counts as a change to the exercise", (A, t) => {
  const state = single(lift("Bench press", [[40, 8], [60, 8]])), api = A(state);
  t.eq(api.applyLogEdit(state.logs[0], { entries: [{ rows: [["40", "8"], ["60", "8"]], warmup: [0], done: [] }] }, 5), { changed: true, names: ["Bench press"] });
  t.eq(state.logs[0].entries[0].warmup, [0]);
});
add("commitLogEdit: rechecks the later sessions, saves and syncs once, and reports the flags that moved", (A, t) => {
  const env = {};
  const state = mkState(benchLogs()), api = A(state, env);
  const flips = api.commitLogEdit(state.logs[0], { entries: [{ rows: [["70", "8"]], warmup: [], done: [] }] });
  t.eq(flips.map(c => c.log.id + ":" + c.was + ">" + c.now), ["2:62.5>null", "3:65>null"]);
  t.eq([env.saved, env.synced], [1, 1]);
  t.eq(api.commitLogEdit(state.logs[0], { entries: [{ rows: [["70", "8"]], warmup: [], done: [] }] }), null);
  t.eq([env.saved, env.synced], [1, 1]);
});
add("editToast: says which sessions gained or lost a PR", (A, t) => {
  const api = A(mkState([])), c = (date, name, was, now) => ({ log: { date }, name, was, now });
  t.eq(api.editToast([]), "Saved");
  t.eq(api.editToast([c("2026-11-02", "Bench press", null, 60), c("2026-11-09", "Bench press", 65, null)]), "Saved - PR now on 2 Nov Bench press, removed from 9 Nov Bench press");
  t.eq(api.editToast([c("2026-11-09", "Squat", 65, null)]), "Saved - PR removed from 9 Nov Squat");
  t.eq(api.editToast([1, 2, 3, 4, 5].map(n => c("2026-11-0" + n, "Row", 1, null))), "Saved - PR removed from 1 Nov Row, 2 Nov Row, 3 Nov Row and 2 more");
});

// ---- runners ----
function runCases(src) {
  const results = [];
  for (const c of CASES) {
    const t = { eq(got, want) {
      const g = JSON.stringify(got), w = JSON.stringify(want);
      if (g !== w) throw new Error("got  " + g + "\nwant " + w);
    } };
    try { c.fn((state, env) => makeApi(src, state, env), t); results.push({ name: c.name, ok: true }); }
    catch (e) { results.push({ name: c.name, ok: false, why: String(e.message || e) }); }
  }
  return results;
}

// How many stored pr flags a full recompute would flip with no edit at all, per person.
function dryRun(src, store) {
  const state = JSON.parse(JSON.stringify(store));
  state.bodyweights = state.bodyweights || [];
  state.weights = state.weights || [];
  state.program = state.program || { order: [], sessions: {} };
  const api = makeApi(src, state, {});
  const out = { flagFlips: 0, valueOnly: 0, logs: 0, detail: [] };
  const flipped = new Set();
  state.people.filter(Boolean).forEach(person => {
    const mine = state.logs.filter(l => l.person === person).sort(api.byDateThenId);
    if (!mine.length) return;
    const names = new Set();
    mine.forEach(l => (l.entries || []).forEach(e => names.add(e.name)));
    const ch = api.prChanges(person, Array.from(names), mine[0]);
    ch.forEach(c => {
      // The first log is walked as the edited one, so its value-only moves are reported apart.
      if ((c.was === null) !== (c.now === null)) {
        out.flagFlips++; flipped.add(c.log.id);
        out.detail.push(person + " " + c.log.date + " " + c.name + " " + c.was + " -> " + c.now);
      } else out.valueOnly++;
    });
  });
  out.logs = flipped.size;
  return out;
}

if (typeof module !== "undefined" && require.main === module) {
  const fs = require("fs"), path = require("path");
  const src = fs.readFileSync(path.join(__dirname, "..", "..", "js", "app.js"), "utf8");
  const dry = process.argv.indexOf("--dryrun");
  if (dry >= 0) {
    console.log(JSON.stringify(dryRun(src, JSON.parse(fs.readFileSync(process.argv[dry + 1], "utf8")))));
  } else {
    const res = runCases(src);
    res.forEach(r => console.log((r.ok ? "pass  " : "FAIL  ") + r.name + (r.ok ? "" : "\n      " + r.why.replace(/\n/g, "\n      "))));
    const bad = res.filter(r => !r.ok).length;
    console.log(bad ? bad + " of " + res.length + " cases FAIL" : "All " + res.length + " cases pass");
    process.exitCode = bad ? 1 : 0;
  }
} else if (typeof window !== "undefined") {
  window.EditCases = { runCases, dryRun };
}
