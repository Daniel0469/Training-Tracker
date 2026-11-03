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
  "prChanges", "applyPrChanges", "recheckPrs"];
const CONSTS = ["clone", "byDateThenId"];

// The app's own functions, bound to `state` and to the given stand-ins for the page.
function makeApi(src, state, env) {
  const body = "let progExIndex=null, bwIndex={}, personIndex={}, progIndex={};\n"
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
