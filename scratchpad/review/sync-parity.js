"use strict";
// Proves the app's toRecords / fromRecords give exactly the rows and payload that
// mcp-coach/tt_records.py gives, on the shared fixture sync-parity.json. Run from the command line:
//
//   ELECTRON_RUN_AS_NODE=1 "<VS Code>/Code.exe" scratchpad/review/sync-parity.js [more-fixture.json ...]
//
// Make a fixture from a copy of the real store with
//   python scratchpad/review/sync-fixture.py --input <data.json> --out <fixture.json>
// and pass its path to run on that as well.
const fs = require("fs");
const path = require("path");
const { grab, grabConst, familyBlock } = require("./sync-harness");

const FUNCTIONS = ["slugify", "programSlug", "wrapProgram"];
const body = "const localStorage = { getItem() { return null; }, setItem() {} };\n" + grabConst("KEY") + "\n" + grabConst("clone") + "\n" + FUNCTIONS.map(grab).join("\n") + "\n" + familyBlock()
  + "\nreturn { toRecords, fromRecords, recMs, rowHash };";
const api = new Function(body)();

let failed = 0, passed = 0;
function check(label, ok, detail) {
  if (ok) passed++; else { failed++; console.log("FAIL " + label + (detail !== undefined ? " -> " + detail : "")); }
}
const json = JSON.stringify;
// Plain objects with sorted keys, so key order never counts as a difference.
const canon = v => Array.isArray(v) ? v.map(canon)
  : v && typeof v === "object" ? Object.keys(v).sort().reduce((o, k) => (o[k] = canon(v[k]), o), {}) : v;
const same = (a, b) => json(canon(a)) === json(canon(b));
const firstDiff = (a, b) => {
  for (let i = 0; i < Math.max(a.length, b.length); i++) if (!same(a[i], b[i])) return i + ": js " + json(a[i]) + " py " + json(b[i]);
  return "";
};

const files = [path.join(__dirname, "sync-parity.json")].concat(process.argv.slice(2));
files.forEach(file => {
  JSON.parse(fs.readFileSync(file, "utf8")).cases.forEach(c => {
    const prev = {};
    (c.prev || []).forEach(r => { prev[r.kind + "|" + r.key] = r; });
    const rows = api.toRecords(JSON.parse(json(c.input)), c.now, prev);
    check(c.name + ": same rows (" + rows.length + ")", same(rows, c.rows), firstDiff(rows, c.rows));
    check(c.name + ": same order", json(rows.map(r => r.kind + "|" + r.key)) === json(c.rows.map(r => r.kind + "|" + r.key)));
    const payload = api.fromRecords(c.rows);
    check(c.name + ": same payload", same(payload, c.payload), Object.keys(c.payload).filter(k => !same(payload[k], c.payload[k])).join(","));
    check(c.name + ": row hash ignores key order and a program's version", rows.every(r => api.rowHash(r) === api.rowHash(JSON.parse(json(r)))));
  });
});

// recMs against tt_records._ms on the same values
const fixture = JSON.parse(fs.readFileSync(files[0], "utf8"));
const badMs = fixture.ms.filter(m => api.recMs(m[0]) !== m[1]);
check("recMs on " + fixture.ms.length + " times", !badMs.length, json(badMs.slice(0, 3).map(m => [m[0], m[1], api.recMs(m[0])])));

console.log((failed ? "FAILED " : "ok ") + passed + " passed, " + failed + " failed");
process.exit(failed ? 1 : 0);
