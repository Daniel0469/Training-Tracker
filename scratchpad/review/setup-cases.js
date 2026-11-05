"use strict";
// Cases for the family setup code in js/app.js: making and reading the code, the address being cleaned
// before anything else runs, a phone connecting from a link or a paste with the password held only in
// memory, a bad or old code being refused, and the sending phone hiding the code again. Run from the
// command line:
//
//   ELECTRON_RUN_AS_NODE=1 "<VS Code>/Code.exe" scratchpad/review/setup-cases.js
//
// Phones are the ones sync-cases.js builds, talking to the JS fake of Supabase. No page opens, no network
// is used, and no real store is read.
const { src, grab } = require("./sync-harness");
const { FakeServer } = require("./sync-fake");
const { makePhone, makeState, connect } = require("./sync-cases");

let failed = 0, passed = 0;
function check(label, ok, detail) {
  if (ok) passed++; else { failed++; console.log("FAIL " + label + (detail !== undefined ? " -> " + JSON.stringify(detail) : "")); }
}
const PASS = "family-pass", FAMILY = { url: "https://x.supabase.co", key: "pk", email: "fam@x.example" };
const codeOf = (extra) => Buffer.from(JSON.stringify(Object.assign({ v: 1, password: PASS }, FAMILY, extra)), "utf8").toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const linkOf = code => "https://fam.example/Training-Tracker/#tt-setup=" + code;
const signedCount = server => (server.signedIn || new Set()).size;
const stored = phone => JSON.stringify(phone.store);

// The form and dialog elements the code reads, as small fakes.
function setupDom(phone) {
  const els = phone.dom.els;
  const ctx = { fills: [], fillStyle: "", fillRect(x, y, w, h) { ctx.fills.push([x, y, w, h, ctx.fillStyle]); } };
  Object.assign(els, {
    setupQr: { width: 0, height: 0, getContext: () => ctx },
    setupDlg: { open: false, showModal() { this.open = true; }, close() { this.open = false; } },
    settingsBtn: { onclick() { phone.counts.opened++; } },
  });
  els.setupPass = { value: "", focus() {} };
  els.setupShow = { hidden: true }; els.setupAsk = { hidden: false };
  return ctx;
}
function fakeQrLib(win) {
  const calls = { texts: [], drew: 0, levels: [] };
  function QRCode(el, opt) { calls.levels.push(opt.correctLevel); this._oDrawing = { draw() { calls.drew++; } }; }
  QRCode.CorrectLevel = { M: 0 };
  QRCode.prototype.makeCode = function (text) { calls.texts.push(text); this._oDrawing.draw({ getModuleCount: () => 21, isDark: (r, c) => (r + c) % 2 === 0 }); };
  win.QRCode = QRCode;
  return calls;
}
async function seconds(phone, n) { for (let i = 0; i < n; i++) { phone.env.clock.t += 1000; await phone.advance(1000); } }

async function main() {
  // ---- making and reading the code ----
  {
    const server = new FakeServer();
    const phone = makePhone(server, makeState(["Alex"]), { password: PASS });
    check("a family phone connects", await connect(phone, PASS));
    const link = phone.ev("setupLink(" + JSON.stringify("p@ss/+=?\u00e9 w") + ")"), code = link.split("#tt-setup=")[1];
    check("the link is the app's own address with the code after a #", link.indexOf("https://fam.example/Training-Tracker/#tt-setup=") === 0 && link.split("#").length === 2, link);
    check("the code is plain base64url", /^[A-Za-z0-9_-]+$/.test(code), code);
    const got = phone.ev("setupDecode(" + JSON.stringify(link) + ")");
    check("the link decodes to the connection and password, odd characters kept",
      JSON.stringify(got) === JSON.stringify({ url: FAMILY.url, key: FAMILY.key, email: FAMILY.email, password: "p@ss/+=?\u00e9 w" }), got);
    check("the bare code decodes the same", JSON.stringify(phone.ev("setupDecode(" + JSON.stringify(code) + ")")) === JSON.stringify(got));
    check("a link copied with spaces and a line break around it decodes", phone.ev("setupDecode(" + JSON.stringify("  \n" + link + "\n ") + ")").password === got.password);
    check("the JSON inside is {v:1, url, key, email, password}", JSON.stringify(Object.keys(JSON.parse(Buffer.from(code.replace(/-/g, "+").replace(/_/g, "/"), "base64").toString("utf8")))) === '["v","url","key","email","password"]');

    const refused = (text, re) => { try { phone.ev("setupDecode(" + JSON.stringify(text) + ")"); return false; } catch (e) { return re.test(e.message); } };
    check("nothing at all is not a code", refused("", /not a setup code/));
    check("random text is not a code", refused("hello there", /not a setup code/));
    check("JSON that is not a setup code is refused", refused(Buffer.from('{"a":1}').toString("base64"), /not a setup code/));
    check("a newer code asks for an update", refused(codeOf({ v: 2 }), /newer version of the app. Tap Update now/));
    check("an older code asks for a new one", refused(codeOf({ v: 0 }), /older version of the app. Make a new one/));
    check("a code with no password is refused and says what is missing", refused(codeOf({ password: "" }), /not complete\. Password is empty/));
    check("a code with a path in the address is refused", refused(codeOf({ url: "https://x.supabase.co/rest/v1" }), /not complete\. Project URL must look like/));
  }

  // ---- the address is cleaned before anything else runs ----
  {
    const replaced = [], loc = hash => ({ hash, pathname: "/Training-Tracker/", search: "?x=1" });
    const run = hash => new Function("location", "history", "const SETUP_PREFIX=" + JSON.stringify("tt-setup=") + ";\n" + grab("takeSetupHash") + "\nreturn takeSetupHash();")(loc(hash), { replaceState: (a, b, url) => replaced.push(url) });
    check("the code is taken from the fragment", run("#tt-setup=abc_-123") === "tt-setup=abc_-123");
    check("the address loses the fragment and keeps the path and query", replaced.length === 1 && replaced[0] === "/Training-Tracker/?x=1", replaced);
    check("another fragment is left alone", run("#top") === "" && run("") === "" && replaced.length === 1);
    const hashAt = src.indexOf("const SETUP_HASH = takeSetupHash();");
    const firstUse = re => src.search(re);
    check("the fragment is taken before the app reads storage or the page",
      hashAt > 0 && hashAt < firstUse(/localStorage\./) && hashAt < firstUse(/document\.(getElementById|querySelector|addEventListener)/) && hashAt < firstUse(/addEventListener\(/), [hashAt, firstUse(/localStorage\./)]);
    check("a setup code in the address is used after the first screen is drawn", src.indexOf("if(SETUP_HASH) setupReceive(SETUP_HASH);") > src.indexOf("\nrenderView();\n"));
  }

  // ---- a phone that receives the link connects with the password in memory only ----
  {
    const server = new FakeServer();
    const phone = makePhone(server, makeState(["Alex"]));
    setupDom(phone);
    const code = codeOf();
    await phone.ev("setupReceive(" + JSON.stringify("tt-setup=" + code) + ")"); await phone.settle();
    check("the phone connected", phone.sb.mode === "supabase", phone.dom.els.fsStatus && phone.dom.els.fsStatus.textContent);
    check("Admin > Family storage was opened", phone.counts.opened === 1 && phone.counts.tab === "admin");
    check("the fields show the address, key and email", phone.dom.els.fsUrl.value === FAMILY.url && phone.dom.els.fsKey.value === FAMILY.key && phone.dom.els.fsEmail.value === FAMILY.email);
    check("the password box was never filled", !phone.dom.els.fsPass || phone.dom.els.fsPass.value === "");
    const everything = stored(phone) + JSON.stringify(phone.sb) + JSON.stringify(phone.state) + JSON.stringify(phone.counts);
    check("neither the password nor the code is stored, logged or in the data", everything.indexOf(PASS) < 0 && everything.indexOf(code) < 0);
    check("every stored value is free of the password", Object.keys(phone.store).every(k => String(phone.store[k]).indexOf(PASS) < 0), Object.keys(phone.store));
    check("no dialog complained", phone.counts.dialogs.length === 0);
  }

  // ---- a bad or old code shows a clear message and connects nothing ----
  {
    const server = new FakeServer(), before = signedCount(server);
    const phone = makePhone(server, makeState(["Alex"]));
    setupDom(phone);
    await phone.ev("setupReceive(" + JSON.stringify("tt-setup=bm90IGEgY29kZQ") + ")"); await phone.settle();
    check("a damaged code opens a dialog that says so", phone.counts.dialogs.length === 1 && phone.counts.dialogs[0][0] === "Setup code not used" && /not a setup code/.test(phone.counts.dialogs[0][1]), phone.counts.dialogs);
    await phone.ev("setupReceive(" + JSON.stringify("tt-setup=" + codeOf({ v: 2 })) + ")"); await phone.settle();
    check("a newer code says to update", phone.counts.dialogs.length === 2 && /newer version/.test(phone.counts.dialogs[1][1]));
    check("nothing was connected or opened", phone.sb.mode === "github" && signedCount(server) === before && phone.counts.opened === 0 && !phone.sb.url);
  }

  // ---- a phone with no account yet keeps the code in memory until it has one ----
  {
    const server = new FakeServer(), before = signedCount(server);
    const phone = makePhone(server, makeState([]));
    setupDom(phone);
    const code = codeOf();
    await phone.ev("setupReceive(" + JSON.stringify("tt-setup=" + code) + ")"); await phone.settle();
    check("the code waits in memory", !!phone.setupPending && phone.setupPending.password === PASS && phone.sb.mode === "github" && signedCount(server) === before);
    check("nothing about the code is stored while it waits", stored(phone).indexOf(PASS) < 0 && stored(phone).indexOf(code) < 0 && !phone.sb.url);
    phone.state.people[0] = "Alex";
    await phone.ev("setupResume()"); await phone.settle();
    check("it connects once an account exists, and the wait is over", phone.sb.mode === "supabase" && phone.setupPending === null && phone.counts.opened === 1);
    check("nothing about the code is stored after it connects", stored(phone).indexOf(PASS) < 0 && stored(phone).indexOf(code) < 0);
  }

  // ---- the paste box takes the whole link or just the code ----
  {
    const server = new FakeServer();
    for (const [name, text] of [["the full link", linkOf(codeOf())], ["the bare code", codeOf()]]) {
      const phone = makePhone(server, makeState(["Alex"]));
      setupDom(phone);
      phone.dom.els.fsSetupPaste = { value: text };
      await phone.ev("setupUse(" + JSON.stringify(text) + ")"); await phone.settle();
      check("pasting " + name + " connects", phone.sb.mode === "supabase", phone.dom.els.fsStatus && phone.dom.els.fsStatus.textContent);
      check("the paste box is emptied after " + name, phone.dom.els.fsSetupPaste.value === "");
      check("the password is not kept after " + name, stored(phone).indexOf(PASS) < 0 && JSON.stringify(phone.sb).indexOf(PASS) < 0);
    }
    const bad = makePhone(server, makeState(["Alex"]));
    setupDom(bad);
    bad.dom.els.fsSetupPaste = { value: "x" };
    await bad.ev("setupUse('not a code')"); await bad.settle();
    check("a bad paste says so under the Connect button and connects nothing", bad.sb.mode === "github" && /^Setup code not used\. This is not a setup code/.test(bad.dom.els.fsConnectMsg.textContent) && bad.dom.els.fsConnectNote.hidden === false && bad.dom.els.fsConnectDot.dataset.s === "bad", bad.dom.els.fsConnectMsg.textContent);
    await bad.ev("setupUse('   ')");
    check("an empty paste asks for the code", /^Setup code not used\. Paste the link or the code first/.test(bad.dom.els.fsConnectMsg.textContent));
    await bad.ev("setupUse(" + JSON.stringify(linkOf(codeOf({ v: 0 }))) + ")");
    check("an old code is named as old", /older version of the app/.test(bad.dom.els.fsConnectMsg.textContent));
    check("a wrong password in a code is a normal sign-in failure", await (async () => {
      const p = makePhone(server, makeState(["Alex"])); setupDom(p);
      await p.ev("setupUse(" + JSON.stringify(codeOf({ password: "wrong" })) + ")"); await p.settle();
      return p.sb.mode === "github" && /Sign-in failed/.test(p.dom.els.fsStatus.textContent);
    })());
    const connected = makePhone(server, makeState(["Alex"]));
    setupDom(connected);
    await connect(connected, PASS);
    await connected.ev("setupUse(" + JSON.stringify(codeOf({ url: "https://other.supabase.co" })) + ")"); await connected.settle();
    check("a connected phone is not switched to another storage", connected.sb.url === FAMILY.url && /^Setup code not used\. This phone is already connected/.test(connected.dom.els.fsConnectMsg.textContent), connected.dom.els.fsConnectMsg.textContent);
  }

  // ---- the sending phone: the password is typed, checked, shown for 60 seconds and never kept ----
  {
    const server = new FakeServer();
    const phone = makePhone(server, makeState(["Alex"]), { password: PASS });
    const ctx = setupDom(phone), qr = fakeQrLib(phone.win);
    check("the sending phone is connected", await connect(phone, PASS));
    phone.dom.els.setupMsg = { hidden: true, textContent: "", className: "" }; phone.dom.els.setupText = { value: "" }; phone.dom.els.setupCount = { textContent: "" };
    phone.nav.clipboard = { writeText: text => { phone.copied = text; return Promise.resolve(); } };

    phone.ev("setupAsk()");
    check("Show setup code opens the dialog on the password step", phone.dom.els.setupDlg.open && phone.dom.els.setupAsk.hidden === false && phone.dom.els.setupShow.hidden === true);
    await phone.ev("setupGo()");
    check("an empty password is refused", /Type the family password/.test(phone.dom.els.setupMsg.textContent) && phone.dom.els.setupShow.hidden === true);
    phone.dom.els.setupPass.value = "wrong";
    await phone.ev("setupGo()"); await phone.settle();
    check("a wrong password shows no code", /not the family password/.test(phone.dom.els.setupMsg.textContent) && phone.dom.els.setupShow.hidden === true && phone.dom.els.setupText.value === "" && phone.dom.els.setupPass.value === "");

    phone.dom.els.setupPass.value = PASS;
    await phone.ev("setupGo()"); await phone.settle();
    const link = phone.dom.els.setupText.value;
    check("the right password shows the code as a link", phone.dom.els.setupShow.hidden === false && phone.dom.els.setupAsk.hidden === true && link.indexOf("https://fam.example/Training-Tracker/#tt-setup=") === 0, link);
    check("the code holds the connection and the password just typed", JSON.stringify(phone.ev("setupDecode(" + JSON.stringify(link) + ")")) === JSON.stringify({ url: FAMILY.url, key: FAMILY.key, email: FAMILY.email, password: PASS }));
    check("the password box is emptied at once", phone.dom.els.setupPass.value === "");
    check("the picture is the same link, drawn by us at the middle error level, and the library drew nothing itself", qr.texts.length === 1 && qr.texts[0] === link && qr.levels[0] === 0 && qr.drew === 0, qr);
    const quiet = 4, n = 21, cell = phone.dom.els.setupQr.width / (n + 2 * quiet);
    check("it is drawn on a canvas with a white border four modules wide", phone.dom.els.setupQr.width > 0 && Number.isInteger(cell) && ctx.fills[0][4] === "#fff" && ctx.fills[0][2] === phone.dom.els.setupQr.width && ctx.fills[1][0] === quiet * cell && ctx.fills[1][4] === "#000");
    check("the countdown is showing", /^Hides in 60 seconds/.test(phone.dom.els.setupCount.textContent), phone.dom.els.setupCount.textContent);
    phone.ev("setupCopy()"); await phone.settle();
    check("Copy puts the same text on the clipboard", phone.copied === link && phone.counts.toasts.pop() === "Setup code copied");
    const everything = stored(phone) + JSON.stringify(phone.sb) + JSON.stringify(phone.state) + JSON.stringify(phone.counts.toasts);
    check("while it is showing, nothing about it is stored", everything.indexOf(PASS) < 0 && everything.indexOf(link.split("#tt-setup=")[1]) < 0);

    await seconds(phone, 30);
    check("the countdown runs down", /^Hides in 30 seconds/.test(phone.dom.els.setupCount.textContent), phone.dom.els.setupCount.textContent);
    await seconds(phone, 30);
    check("after 60 seconds the code, picture and password are gone", phone.dom.els.setupShow.hidden === true && phone.dom.els.setupAsk.hidden === false && phone.dom.els.setupText.value === "" && phone.dom.els.setupQr.width === 0 && phone.dom.els.setupPass.value === "" && /hidden after 60 seconds/.test(phone.dom.els.setupMsg.textContent));
    check("the countdown timer is stopped", !phone.ev("setupTimer"));

    phone.dom.els.setupPass.value = PASS;
    await phone.ev("setupGo()"); await phone.settle();
    check("it can be shown again", phone.dom.els.setupText.value.indexOf("#tt-setup=") > 0);
    phone.ev("setupHide('')");
    check("Hide, a closed dialog and the app going to the background all run setupHide and clear everything", phone.dom.els.setupText.value === "" && phone.dom.els.setupQr.width === 0 && phone.dom.els.setupShow.hidden === true && !phone.ev("setupTimer"));
    check("the dialog close and the background both call setupHide", /setupDlg"\)\.addEventListener\("close", \(\)=>setupHide\(""\)\)/.test(src) && /visibilityState==="hidden"\) setupHide\(""\)/.test(src) && /setupHideBtn"\)\.onclick=\(\)=>setupHide\(""\)/.test(src));

    // the library never arrives: the text code still shows, and a clear message follows the timeout
    const slow = makePhone(server, makeState(["Alex"]), { password: PASS });
    setupDom(slow);
    slow.dom.els.setupMsg = { hidden: true, textContent: "", className: "" }; slow.dom.els.setupText = { value: "" }; slow.dom.els.setupCount = { textContent: "" };
    await connect(slow, PASS);
    slow.dom.els.setupPass.value = PASS;
    const going = slow.ev("setupGo()"); await slow.settle();
    check("without the QR library the text code shows while it waits", slow.dom.els.setupText.value.indexOf("#tt-setup=") > 0 && slow.dom.els.setupQr.width === 0);
    await slow.advance(15000); await going;
    check("the library error names the text code", /Could not load the QR library - use the text code instead/.test(slow.dom.els.setupMsg.textContent) && slow.dom.els.setupMsg.className === "hint pin-err" && slow.dom.els.setupText.value.indexOf("#tt-setup=") > 0, slow.dom.els.setupMsg.textContent);
    check("the pinned library address and a sha512 check are used", /const QR_LIB_URL="https:\/\/cdnjs\.cloudflare\.com\/ajax\/libs\/qrcodejs\/1\.0\.0\/qrcode\.min\.js";/.test(src) && /const QR_LIB_SRI="sha512-[A-Za-z0-9+\/]{86}==";/.test(src));
    check("the service worker caches the same QR library address", require("fs").readFileSync(require("path").join(__dirname, "..", "..", "sw.js"), "utf8").indexOf('"https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"') > 0);
  }
  finished = true;
  console.log((failed ? "FAILED " : "ok ") + passed + " passed, " + failed + " failed");
  process.exit(failed ? 1 : 0);
}
// A promise that never settles ends the run silently, so say so.
let finished = false;
process.on("exit", () => { if (!finished) { console.log("FAILED the run stopped before the end"); process.exitCode = 1; } });
main().catch(e => { console.log("CRASH", e && e.stack || e); process.exit(1); });
