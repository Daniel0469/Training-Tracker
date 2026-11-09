"use strict";
// Cases for a session's weekdays: daysOf, setSessionDays, orderedKeys and sessionForDate with
// `days`, `autoPick` and old sessions that only have `day`. Run from the command line:
//
//   ELECTRON_RUN_AS_NODE=1 "<VS Code>/Code.exe" scratchpad/review/days-cases.js
//
// It reads the source text of js/app.js and runs the functions on small fixture stores.
const fs = require("fs");
const path = require("path");
const src = fs.readFileSync(path.join(__dirname, "..", "..", "js", "app.js"), "utf8");

function grab(name) {
  const at = src.indexOf("function " + name + "(");
  if (at < 0) throw new Error("function " + name + " not found in js/app.js");
  let depth = 0;
  for (let i = src.indexOf("{", at); i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}" && --depth === 0) return src.slice(at, i + 1);
  }
  throw new Error("unbalanced braces in " + name);
}
function grabConst(name) {
  const m = new RegExp("^const " + name + "\\s*=.*;\\s*$", "m").exec(src);
  if (!m) throw new Error("const " + name + " not found in js/app.js");
  return m[0].trim();
}

const FUNCTIONS = ["daysOf", "setSessionDays", "orderedKeys", "ownsSession", "sessionForDate", "alternatedKey"];
const CONSTS = ["DOW", "DAY_NAMES", "dayText", "isOptional"];
function makeApi(state, env) {
  const body = "const curDate='';\nfunction progOf(){ return state.programs.p; }\nfunction liveSessionSwap(){ return env.swap||null; }\n"
    + "function liveNextCardio(){ return null; }\nfunction sessionKeyByName(n){ return Object.keys(state.programs.p.sessions).find(k=>state.programs.p.sessions[k].name===n); }\n"
    + "function isCardioSession(s){ return !!s.cardio; }\n"
    + CONSTS.map(grabConst).join("\n") + "\n" + FUNCTIONS.map(grab).join("\n")
    + "\nreturn { " + FUNCTIONS.concat(CONSTS).join(", ") + " };";
  return new Function("state", "env", body)(state, env || {});
}

const ex = name => ({ name, warmup: "", target: "3x8", sets: 3, cols: ["Weight (kg)", "Reps"] });
const sess = (name, extra) => Object.assign({ name, exercises: [ex("A")] }, extra || {});
function store(sessions, logs, env) {
  const order = Object.keys(sessions);
  const state = { people: ["Daniel", "Cerys"], activePerson: 0, logs: logs || [], programs: { p: { id: "p", members: ["Daniel", "Cerys"], order, sessions } }, programIds: {} };
  return { state, api: makeApi(state, env) };
}
// 2026-11-09 is a Monday, 2026-11-10 a Tuesday, 2026-11-11 a Wednesday, 2026-11-15 a Sunday.
const MON = "2026-11-09", TUE = "2026-11-10", WED = "2026-11-11", SUN = "2026-11-15";

const cases = [];
const t = (name, fn) => cases.push([name, fn]);
const eq = (a, b) => { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error("got " + JSON.stringify(a) + ", wanted " + JSON.stringify(b)); };

t("daysOf: a days list, in week order and only weekdays", () => {
  const { api } = store({});
  eq(api.daysOf({ day: "Friday", days: ["Friday", "Monday", "Nowhere"] }), ["Monday", "Friday"]);
  eq(api.daysOf({ day: "Optional", days: [] }), []);
});
t("daysOf: an old session has just its day, in any case", () => {
  const { api } = store({});
  eq(api.daysOf({ day: "tuesday" }), ["Tuesday"]);
  eq(api.daysOf({ day: "Optional" }), []);
  eq(api.daysOf({}), []);
});
t("setSessionDays: day is the first of them, Optional when none, and autoPick keeps only those days", () => {
  const { api } = store({});
  const s = { autoPick: { Monday: true, Thursday: true } };
  api.setSessionDays(s, ["Thursday", "Sunday"]);
  eq(s, { autoPick: { Thursday: true }, days: ["Thursday", "Sunday"], day: "Thursday" });
  api.setSessionDays(s, []);
  eq(s, { days: [], day: "Optional" });
});
t("dayText and isOptional", () => {
  const { api } = store({});
  eq(api.dayText({ days: ["Monday", "Thursday"], day: "Monday" }), "Monday, Thursday");
  eq(api.dayText({ day: "Optional", days: [] }), "Optional");
  eq(api.isOptional({ day: "Optional", days: [] }), true);
  eq(api.isOptional({ day: "Monday", days: ["Monday"] }), false);
  eq(api.isOptional({ day: "Optional" }), true);
});
t("orderedKeys: sorted by the first weekday, optional last", () => {
  const { api, state } = store({ opt: sess("Opt", { day: "Optional", days: [] }), thu: sess("T", { day: "Thursday", days: ["Thursday"] }), mon: sess("M", { day: "Monday", days: ["Monday", "Friday"] }), old: sess("O", { day: "Wednesday" }) });
  eq(api.orderedKeys(state.programs.p), ["mon", "old", "thu", "opt"]);
});
t("orderedKeys: an order key whose session was deleted is skipped", () => {
  const { api, state } = store({ mon: sess("M", { day: "Monday", days: ["Monday"] }) });
  state.programs.p.order.push("gone");
  eq(api.orderedKeys(state.programs.p), ["mon"]);
});
t("sessionForDate: a session on several days opens on each of them", () => {
  const { api } = store({ a: sess("A", { day: "Monday", days: ["Monday", "Thursday"] }), b: sess("B", { day: "Tuesday", days: ["Tuesday"] }) });
  eq(api.sessionForDate(MON), "a");
  eq(api.sessionForDate(TUE), "b");
  eq(api.sessionForDate("2026-11-12"), "a");
  eq(api.sessionForDate(WED), undefined);
});
t("sessionForDate: an old session with only a day still opens on it", () => {
  const { api } = store({ a: sess("A", { day: "Sunday" }) });
  eq(api.sessionForDate(SUN), "a");
});
t("sessionForDate: an optional session is never opened", () => {
  const { api } = store({ a: sess("A", { day: "Optional", days: [] }) });
  eq(api.sessionForDate(MON), undefined);
});
t("sessionForDate: the auto-pick for that weekday wins over program order", () => {
  const { api } = store({
    a: sess("A", { day: "Tuesday", days: ["Tuesday", "Friday"] }),
    b: sess("B", { day: "Tuesday", days: ["Tuesday"], autoPick: { Tuesday: true } })
  });
  eq(api.sessionForDate(TUE), "b");
  eq(api.sessionForDate("2026-11-13"), "a");
});
t("sessionForDate: auto-pick is per weekday, and an unmarked day falls back to the old rules", () => {
  const logs = [{ person: "Daniel", date: "2026-11-03", sessionName: "A" }, { person: "Daniel", date: "2026-11-04", sessionName: "B" }];
  const { api } = store({
    a: sess("A", { day: "Tuesday", days: ["Tuesday", "Friday"], autoPick: { Friday: true } }),
    b: sess("B", { day: "Tuesday", days: ["Tuesday", "Friday"] })
  }, logs);
  eq(api.sessionForDate("2026-11-13"), "a");
  eq(api.sessionForDate(TUE), "a");
});
t("sessionForDate: lift before cardio still applies with no auto-pick", () => {
  const logs = [{ person: "Daniel", date: TUE, sessionKey: "lift", sessionName: "Lift" }];
  const { api } = store({ lift: sess("Lift", { day: "Tuesday", days: ["Tuesday"] }), run: sess("Run", { day: "Tuesday", days: ["Tuesday"], cardio: true }) }, logs);
  eq(api.sessionForDate(TUE), "run");
});
t("sessionForDate: the coach swap beats an auto-pick", () => {
  const { api } = store({ a: sess("A", { day: "Tuesday", days: ["Tuesday"], autoPick: { Tuesday: true } }), b: sess("B", { day: "Tuesday", days: ["Tuesday"] }), m: sess("M", { day: "Optional", days: [] }) }, [], { swap: { day: "Tuesday", session: "M" } });
  eq(api.sessionForDate(TUE), "m");
});
t("sessionForDate: a session for one person is not offered to the other", () => {
  const { api } = store({ d: sess("D", { day: "Tuesday", days: ["Tuesday"], person: "Cerys" }), u: sess("U", { day: "Tuesday", days: ["Tuesday"] }) });
  eq(api.sessionForDate(TUE), "u");
});

let failed = 0;
cases.forEach(([name, fn]) => {
  try { fn(); console.log("pass  " + name); } catch (e) { failed++; console.log("FAIL  " + name + "\n      " + e.message); }
});
console.log(failed ? failed + " failed" : "all " + cases.length + " passed");
process.exit(failed ? 1 : 0);
