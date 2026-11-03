"use strict";
// Cuts pieces out of js/app.js so sync-parity.js and sync-cases.js can run them without a page:
// whole functions by name, one-line consts, and the Family storage block between its two marker
// comments. Nothing here opens a page or touches a real store.
const fs = require("fs");
const path = require("path");
const src = fs.readFileSync(path.join(__dirname, "..", "..", "js", "app.js"), "utf8");

// A whole `function name(...) {...}` out of the source, by brace matching.
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
// A one-line `const name = ...;` out of the source.
function grabConst(name) {
  const m = new RegExp("^const " + name + "\\s*=.*;\\s*$", "m").exec(src);
  if (!m) throw new Error("const " + name + " not found in js/app.js");
  return m[0].trim();
}
// The Family storage block, marker to marker.
function familyBlock() {
  const a = src.indexOf("// ==== Family storage (Supabase) ====");
  const b = src.indexOf("// ==== end Family storage ====");
  if (a < 0 || b < a) throw new Error("Family storage markers not found in js/app.js");
  return src.slice(a, b);
}

module.exports = { src, grab, grabConst, familyBlock };
