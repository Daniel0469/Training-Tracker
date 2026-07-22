"use strict";
const KEY = "flLiveTracker_v1";

const DEFAULT_PROGRAM = {
  "order": [
    "lower1",
    "cardioSpeed",
    "upper1",
    "lower2",
    "cardioEndurance",
    "upper2"
  ],
  "sessions": {
    "lower1": {
      "name": "Lower 1",
      "day": "Monday",
      "exercises": [
        {
          "name": "Leg press",
          "warmup": "50%x10, then 75%x5",
          "target": "4x8-12",
          "sets": 4,
          "cols": [
            "Weight (kg)",
            "Reps"
          ]
        },
        {
          "name": "Romanian deadlift",
          "warmup": "50%x8",
          "target": "3x8-12",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        },
        {
          "name": "Leg extension",
          "warmup": "",
          "target": "3x10-15",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        },
        {
          "name": "Seated leg curl",
          "warmup": "",
          "target": "3x8-12",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        },
        {
          "name": "Standing calf raise",
          "warmup": "",
          "target": "4x10-15",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 4
        },
        {
          "name": "Back extension",
          "warmup": "",
          "target": "3x10-15",
          "sets": 3,
          "cols": [
            "Weight (kg)",
            "Reps"
          ]
        }
      ]
    },
    "upper1": {
      "name": "Upper 1",
      "day": "Thursday",
      "exercises": [
        {
          "name": "Flat press (DB)",
          "warmup": "",
          "target": "3x6-10",
          "sets": 4,
          "cols": [
            "Weight (kg)",
            "Reps"
          ]
        },
        {
          "name": "Lat pulldown",
          "warmup": "",
          "target": "3x8-12",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        },
        {
          "name": "Incline DB press",
          "warmup": "",
          "target": "3x8-12",
          "sets": 3,
          "cols": [
            "Weight (kg)",
            "Reps"
          ]
        },
        {
          "name": "Seated cable row",
          "warmup": "",
          "target": "3x8-12",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        },
        {
          "name": "Triceps pushdown",
          "warmup": "",
          "target": "3x8-12",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        },
        {
          "name": "Lateral raise",
          "warmup": "",
          "target": "3x12-15",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        },
        {
          "name": "Bicep curl",
          "warmup": "",
          "target": "3x8-12",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        }
      ]
    },
    "lower2": {
      "name": "Lower 2",
      "day": "Friday",
      "exercises": [
        {
          "name": "Squat",
          "warmup": "empty x10, then 60%x5",
          "target": "4x6-10",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 4
        },
        {
          "name": "Walking/sandbag lunges",
          "warmup": "",
          "target": "3 sets",
          "sets": 3,
          "cols": [
            "Weight (kg)",
            "Distance (m)"
          ]
        },
        {
          "name": "Seated leg curl",
          "warmup": "",
          "target": "3x8-12",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        },
        {
          "name": "Hip abduction",
          "warmup": "",
          "target": "3x12-15",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        },
        {
          "name": "Hip adduction",
          "warmup": "",
          "target": "3x12-15",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        },
        {
          "name": "Calf raise",
          "warmup": "",
          "target": "3x12-15",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        },
        {
          "name": "Back extension",
          "warmup": "",
          "target": "3x10-15",
          "sets": 3,
          "cols": [
            "Weight (kg)",
            "Reps"
          ]
        }
      ]
    },
    "upper2": {
      "name": "Upper 2",
      "day": "Sunday",
      "exercises": [
        {
          "name": "Pull-ups (assisted to weighted)",
          "warmup": "",
          "target": "4x4-8",
          "sets": 4,
          "cols": [
            "Added/Assist (kg)",
            "Reps"
          ]
        },
        {
          "name": "Incline bench",
          "warmup": "50%x10, then 75%x5",
          "target": "3x8-12",
          "sets": 3,
          "cols": [
            "Weight (kg)",
            "Reps"
          ]
        },
        {
          "name": "Seated row",
          "warmup": "",
          "target": "3x8-12",
          "sets": 3,
          "cols": [
            "Weight (kg)",
            "Reps"
          ]
        },
        {
          "name": "Cable crossover",
          "warmup": "",
          "target": "3x10-15",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        },
        {
          "name": "Face pull",
          "warmup": "",
          "target": "3x12-15",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        },
        {
          "name": "triceps ext",
          "warmup": "",
          "target": "3x8-12",
          "sets": 3,
          "cols": [
            "Weight (kg)",
            "Reps"
          ]
        },
        {
          "name": "Lateral raise",
          "warmup": "",
          "target": "3x10-15",
          "sets": 3,
          "cols": [
            "Weight (kg)",
            "Reps"
          ]
        },
        {
          "name": "Hammer curl",
          "warmup": "",
          "target": "3x8-12",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        }
      ]
    },
    "cardioSpeed": {
      "name": "Cardio: Speed + Core",
      "day": "Wednesday",
      "exercises": [
        {
          "name": "Warm-up jog",
          "warmup": "",
          "target": "8 min easy",
          "cols": [
            "Min",
            "Notes"
          ],
          "sets": 1
        },
        {
          "name": "Treadmill intervals",
          "warmup": "",
          "target": "6x1 min hard / 2 min easy",
          "sets": 1,
          "cols": [
            "Hard pace",
            "Easy pace"
          ]
        },
        {
          "name": "Cooldown",
          "warmup": "",
          "target": "5 min easy",
          "cols": [
            "Min",
            "Notes"
          ],
          "sets": 1
        },
        {
          "name": "Core: Leg raise",
          "warmup": "",
          "target": "3x10-15",
          "cols": [
            "Weight (kg)",
            "Reps"
          ],
          "sets": 3
        },
        {
          "name": "Russian Twists",
          "warmup": "",
          "target": "3x10-15",
          "sets": 3,
          "cols": [
            "Kg",
            "reps"
          ]
        }
      ]
    },
    "cardioEndurance": {
      "name": "Cardio: Endurance + Core",
      "day": "Saturday",
      "exercises": [
        {
          "name": "Warm-up",
          "warmup": "",
          "target": "5 min easy",
          "cols": [
            "Min",
            "Notes"
          ],
          "sets": 1
        },
        {
          "name": "Easy run (Zone 2)",
          "warmup": "",
          "target": "5 km",
          "sets": 1,
          "cols": [
            "Distance (km)",
            "Time (mm:ss)",
            "Pace"
          ]
        },
        {
          "name": "Cooldown",
          "warmup": "",
          "target": "5 min easy",
          "cols": [
            "Min",
            "Notes"
          ],
          "sets": 1
        },
        {
          "name": "Leg raise",
          "warmup": "",
          "target": "3x10-15",
          "sets": 3,
          "cols": [
            "Weight (kg)",
            "Reps"
          ]
        },
        {
          "name": "Russian twists",
          "warmup": "",
          "target": "3x10-15",
          "sets": 3,
          "cols": [
            "Weight (kg)",
            "Reps"
          ]
        }
      ]
    }
  }
};

const clone = o => JSON.parse(JSON.stringify(o));
let state = load();
if(!state.namesSet){ if(state.people[0]==="Me") state.people[0]="Daniel"; if(state.people[1]==="Partner") state.people[1]="Cerys"; state.namesSet=true; try{save();}catch(e){} }
let activeTab = "home";
let curSession = state.program.order[0];
let curDate = trainingDateStr();
let justSavedId = null;
// In-memory, per person+session drafts of the in-progress log form, so
// switching person (or session) mid-entry doesn't wipe unsaved sets. Lets
// both people log from one phone. Not persisted: a page reload clears them.
let formDrafts = {};
// Per person+session workout timers (same keying as formDrafts). Also
// in-memory: a page reload clears them.
let sessionTimers = {};
let timerInterval = null;

function load(){
  try{
    const s = JSON.parse(localStorage.getItem(KEY));
    if(s && s.program && s.program.sessions){
      if(!Array.isArray(s.weights)) s.weights=["",""];
      if(!Array.isArray(s.goals)) s.goals=["",""];
      // Existing installs get the exact colours they already look like today
      // (Daniel navy, Cerys purple) - no visual change from adding this feature.
      if(!Array.isArray(s.colors)) s.colors=["navy","purple"];
      if(!s.coaching || typeof s.coaching!=="object") s.coaching={};
      if(!Array.isArray(s.coachingLog)) s.coachingLog=[];
      if(!Array.isArray(s.suggestions)) s.suggestions=[];
      if(!Array.isArray(s.meals)) s.meals=[];
      if(!Array.isArray(s.bodyweights)){
        // Migrate: seed history from each person's current single weight.
        s.bodyweights=[];
        var today=new Date().toISOString().slice(0,10);
        s.weights.forEach(function(w,i){
          var kg=parseFloat(w);
          if(!isNaN(kg)) s.bodyweights.push({person:s.people[i], date:today, kg:kg});
        });
      }
      // Migrate: the default warm-ups were fixed kg, so Daniel and Cerys both saw
      // the same numbers. Percentages resolve against each person's own last top
      // set, so convert — but only where the text still matches the old default,
      // leaving anything edited in Edit Program alone.
      if(!s.warmupPct){
        var WU={ "70x10, then 110x5":"50%x10, then 75%x5",
                 "light x8":"50%x8",
                 "empty x10, then ~60% x5":"empty x10, then 60%x5",
                 "10x10, then 14x5":"50%x10, then 75%x5" };
        Object.keys(s.program.sessions).forEach(function(k){
          (s.program.sessions[k].exercises||[]).forEach(function(ex){
            var repl=WU[(ex.warmup||"").trim()];
            if(repl) ex.warmup=repl;
          });
        });
        s.warmupPct=true;
      }
      return s;
    }
  }catch(e){}
  // Genuinely blank install: no accounts, no program - see renderCreateAccount().
  return { people:["",""], weights:["",""], goals:["",""], colors:["",""], coaching:{}, coachingLog:[], suggestions:[], meals:[], bodyweights:[], activePerson:0, program:{order:[], sessions:{}}, logs:[] };
}
function save(){ localStorage.setItem(KEY, JSON.stringify(state)); }

function toast(msg){
  const t=document.getElementById("toast"); t.textContent=msg; t.classList.add("show");
  clearTimeout(t._t); t._t=setTimeout(()=>t.classList.remove("show"),1800);
}
const esc = s => String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const possessive = n => /s$/i.test(n) ? n+"'" : n+"'s";
const todayStr = ()=> new Date().toISOString().slice(0,10);
// The training day rolls over at ~5am, not midnight: a session logged at 1am
// Friday still belongs to Thursday's workout. Subtract the cutoff (in local
// time) before reading the date, so the default log date + auto-selected
// session both land on the right training day. `now` is injectable for tests.
function trainingDateStr(now){
  var d = now ? new Date(now) : new Date();
  d.setHours(d.getHours()-5);
  var m=d.getMonth()+1, day=d.getDate();
  return d.getFullYear()+"-"+(m<10?"0":"")+m+"-"+(day<10?"0":"")+day;
}
const DOW={monday:1,tuesday:2,wednesday:3,thursday:4,friday:5,saturday:6,sunday:7};
function orderedKeys(){
  return state.program.order.slice().sort(function(a,b){
    var da=DOW[String(state.program.sessions[a].day||"").toLowerCase()]||99;
    var db=DOW[String(state.program.sessions[b].day||"").toLowerCase()]||99;
    return da-db;
  });
}

function sessionForDate(dstr){
  var wd=new Date(dstr+"T12:00:00").getDay();
  var names=["sunday","monday","tuesday","wednesday","thursday","friday","saturday"];
  var target=names[wd];
  return state.program.order.filter(function(k){return String(state.program.sessions[k].day||"").toLowerCase()===target;})[0];
}
function isLifting(ex){ return /kg|assist/i.test(ex.cols[0]) && /rep/i.test(ex.cols[1]); }
// A running exercise carries both a distance and a time column (any order),
// which lets us auto-compute pace. Rows are splits.
function isRunning(ex){ return ex.cols.some(c=>/dist/i.test(c)) && ex.cols.some(c=>/time/i.test(c)); }
function colIndex(ex, re){ for(var i=0;i<ex.cols.length;i++){ if(re.test(ex.cols[i])) return i; } return -1; }
function parseTimeToMin(s){
  s=String(s).trim(); if(!s) return NaN;
  if(s.indexOf(":")>=0){ var p=s.split(":"); return (parseFloat(p[0])||0) + (parseFloat(p[1])||0)/60; }
  return parseFloat(s); // bare number = decimal minutes
}
function fmtPace(minPerKm){
  if(!isFinite(minPerKm)||minPerKm<=0) return "";
  var m=Math.floor(minPerKm), s=Math.round((minPerKm-m)*60);
  if(s===60){ m++; s=0; }
  return m+":"+(s<10?"0":"")+s;
}
// Fill a running row's pace column (min/km) from its distance + time.
function updatePace(tr, ex){
  var di=colIndex(ex,/dist/i), ti=colIndex(ex,/time/i), pi=colIndex(ex,/pace/i);
  if(di<0||ti<0||pi<0) return;
  var dInp=tr.querySelector('[data-c="'+di+'"]'), tInp=tr.querySelector('[data-c="'+ti+'"]'), pInp=tr.querySelector('[data-c="'+pi+'"]');
  if(!dInp||!tInp||!pInp) return;
  var dist=parseFloat(dInp.value), tmin=parseTimeToMin(tInp.value);
  pInp.value = (!isNaN(dist)&&dist>0&&!isNaN(tmin)&&tmin>0) ? fmtPace(tmin/dist) : "";
}
function fmtMmSs(sec){ sec=Math.round(sec); var m=Math.floor(sec/60), s=sec%60; return m+":"+(s<10?"0":"")+s; }
// Parse a Garmin/Strava TCX: each <Lap> -> one split {km, sec}.
function parseTcx(doc){
  const laps=[], nodes=doc.getElementsByTagName("Lap");
  for(let i=0;i<nodes.length;i++){
    const dm=nodes[i].getElementsByTagName("DistanceMeters")[0];
    const tt=nodes[i].getElementsByTagName("TotalTimeSeconds")[0];
    const km=dm?parseFloat(dm.textContent)/1000:NaN, sec=tt?parseFloat(tt.textContent):NaN;
    if(!isNaN(km)&&!isNaN(sec)) laps.push({km, sec});
  }
  return laps;
}
function haversineM(la1,lo1,la2,lo2){
  const R=6371000, rad=x=>x*Math.PI/180;
  const dLa=rad(la2-la1), dLo=rad(lo2-lo1);
  const a=Math.sin(dLa/2)**2+Math.cos(rad(la1))*Math.cos(rad(la2))*Math.sin(dLo/2)**2;
  return 2*R*Math.asin(Math.sqrt(a));
}
// Parse a GPX: no laps, so sum trackpoint legs into one summary {km, sec}.
function parseGpx(doc){
  const pts=doc.getElementsByTagName("trkpt");
  if(pts.length<2) return [];
  let dist=0, t0=null, t1=null, prev=null;
  for(let i=0;i<pts.length;i++){
    const lat=parseFloat(pts[i].getAttribute("lat")), lon=parseFloat(pts[i].getAttribute("lon"));
    if(isNaN(lat)||isNaN(lon)) continue;
    if(prev) dist+=haversineM(prev.lat,prev.lon,lat,lon);
    prev={lat,lon};
    const te=pts[i].getElementsByTagName("time")[0];
    if(te){ const t=new Date(te.textContent); if(!isNaN(t)){ if(!t0)t0=t; t1=t; } }
  }
  const km=dist/1000; if(km<=0) return [];
  return [{km, sec:(t0&&t1)?(t1-t0)/1000:0}];
}
// Fill a running exercise's rows (splits) on the log form from a TCX/GPX file.
function importRunIntoCard(text, ex, card){
  let doc;
  try{ doc=new DOMParser().parseFromString(text, "application/xml"); }catch(e){ toast("Couldn't read that file"); return; }
  if(doc.getElementsByTagName("parsererror").length){ toast("That file isn't valid TCX/GPX"); return; }
  let laps=parseTcx(doc); if(!laps.length) laps=parseGpx(doc);
  if(!laps.length){ toast("No run data found in file"); return; }
  const di=colIndex(ex,/dist/i), ti=colIndex(ex,/time/i);
  const tb=card.querySelector("tbody");
  while(tb.rows.length<laps.length){
    tb.insertAdjacentHTML("beforeend", setRowHtml(tb.rows.length+1, ex, "-"));
    wireSetRow(tb.rows[tb.rows.length-1], ex, cardBestWeight(ex));
  }
  laps.forEach((lap,i)=>{
    const inputs=tb.rows[i].querySelectorAll('[data-c]');
    if(di>=0&&inputs[di]) inputs[di].value=Math.round(lap.km*100)/100;
    if(ti>=0&&inputs[ti]) inputs[ti].value=fmtMmSs(lap.sec);
    updatePace(tb.rows[i], ex);
  });
  startTimerIfIdle();
  toast(laps.length+" split"+(laps.length>1?"s":"")+" imported");
}
function parseRange(target){
  const m=String(target).match(/(\d+)\s*[-]\s*(\d+)/);
  return m? {low:+m[1],high:+m[2]} : null;
}

function renderPeople(){
  // Self-heal: if the active slot has no account but the other one does (e.g.
  // right after a skip, or stale data), point activePerson at the real one.
  if(!state.people[state.activePerson] && state.people[1-state.activePerson]) state.activePerson=1-state.activePerson;
  // Drive the app accent (via CSS --brand) and chrome colour off the active person's chosen swatch.
  document.documentElement.setAttribute("data-color", (state.colors&&state.colors[state.activePerson])||"navy");
  updateMeta();
  const el=document.getElementById("ptoggle");
  let html="";
  state.people.forEach((n,i)=>{
    if(n) html+='<button data-p="'+i+'" class="'+(state.activePerson===i?'active':'')+'">'+esc(n)+'</button>';
  });
  const emptySlot=state.people.findIndex(n=>!n);
  if(emptySlot>=0 && state.people.some(n=>n)) html+='<button class="mini" data-addperson="'+emptySlot+'">+ Add</button>';
  el.innerHTML=html;
  el.querySelectorAll("[data-p]").forEach(b=>b.onclick=()=>{
    if(+b.dataset.p===state.activePerson) return;
    captureDraft();
    state.activePerson=+b.dataset.p; save(); renderPeople(); renderView();
    if(activeTab==="log" && formDrafts[draftKey()])
      toast("Restored "+possessive(state.people[state.activePerson])+" unsaved entry");
  });
  el.querySelectorAll("[data-addperson]").forEach(b=>b.onclick=()=>renderCreateAccount(+b.dataset.addperson));
  const w=state.weights[state.activePerson];
  document.getElementById("sub").textContent =
    w ? state.people[state.activePerson]+" · "+w+" kg" : "Tap the gear to set bodyweight";
}
// Full-screen-ish onboarding card: no account exists yet (slotIndex 0), or an
// existing account is offering to add a second (slotIndex 1, skippable).
function renderCreateAccount(slotIndex){
  document.getElementById("tabs").style.display="none";
  document.getElementById("ptoggle").style.display="none";
  document.getElementById("settingsBtn").style.display="none";
  const isSecond = slotIndex===1 && state.people[0];
  let html='<div class="card">'
    + '<div class="sec-title" style="margin:0 0 4px">'+(isSecond?"Add a second account":"Welcome - create your account")+'</div>'
    + '<div class="hint" style="margin-bottom:16px">'+(isSecond
        ?"Optional - this device can be shared by up to two people."
        :"Give your tracker a name and a colour to get started. Nothing is sent anywhere; it's saved on this device.")+'</div>'
    + '<label class="fld" style="margin-bottom:14px">Name<input id="caName" type="text" placeholder="e.g. Alex" autocomplete="off"></label>'
    + '<label class="fld" style="margin-bottom:18px">Colour<div class="swatchpick" id="caColor"></div></label>'
    + '<div class="row" style="justify-content:flex-end">'
    + (isSecond?'<button class="btn btn-ghost" id="caSkip">Skip - just me for now</button>':"")
    + '<button class="btn btn-primary" id="caCreate">Create account</button>'
    + '</div></div>';
  document.getElementById("view").innerHTML=html;
  const colorEl=document.getElementById("caColor");
  renderSwatchPicker(colorEl, slotIndex===1?"purple":"navy");
  wireSwatchPicker(colorEl);
  const reveal=()=>{
    document.getElementById("tabs").style.display="";
    document.getElementById("ptoggle").style.display="";
    document.getElementById("settingsBtn").style.display="";
  };
  document.getElementById("caCreate").onclick=()=>{
    const nm=(document.getElementById("caName").value||"").trim();
    if(!nm){ toast("Enter a name"); return; }
    state.people[slotIndex]=nm;
    state.colors[slotIndex]=readSwatchPicker(colorEl);
    state.activePerson=slotIndex;
    save(); reveal(); renderPeople(); renderView();
    toast("Welcome, "+nm+"!");
  };
  if(isSecond){
    document.getElementById("caSkip").onclick=()=>{ reveal(); renderPeople(); renderView(); };
  }
}
document.getElementById("tabs").querySelectorAll("button").forEach(b=>{
  b.onclick=()=>switchTab(b.dataset.tab);
});

function latestLog(person, sessionKey){
  return state.logs.filter(l=>l.person===person && l.sessionKey===sessionKey)
    .sort((a,b)=> (a.date<b.date?1:a.date>b.date?-1: (a.id<b.id?1:-1)))[0];
}
function bestWeightSoFar(person, exerciseName){
  var best=-Infinity;
  state.logs.filter(function(l){return l.person===person;}).forEach(function(l){
    var e=(l.entries||[]).find(function(x){return x.name===exerciseName;}); if(!e) return;
    var wu=e.warmup||[];
    e.rows.forEach(function(r,ri){ if(wu.indexOf(ri)>=0) return; var w=parseFloat(r[0]); if(!isNaN(w)&&w>best) best=w; });
  });
  return best;
}
function latestEntryAnywhere(person, exName){
  var bestLog=null, bestEntry=null;
  state.logs.forEach(function(l){
    if(l.person!==person) return;
    var e=(l.entries||[]).find(function(x){return x.name===exName;}); if(!e) return;
    if(!bestLog || l.date>bestLog.date || (l.date===bestLog.date && l.id>bestLog.id)){ bestLog=l; bestEntry=e; }
  });
  return bestLog ? {log:bestLog, entry:bestEntry} : null;
}
// Escaped display of one logged row across its columns. Lifting reads
// "weight x reps"; anything else (cardio/running) joins its filled cells.
function fmtRow(cols, r){
  cols = cols||[];
  const lift = /kg|assist/i.test(cols[0]||"") && /rep/i.test(cols[1]||"");
  const n = Math.max(cols.length, r.length);
  const vals=[]; for(let i=0;i<n;i++){ vals.push(r[i]==null?"":String(r[i]).trim()); }
  if(lift) return esc(vals[0])+(vals[1]!==""?" x "+esc(vals[1]):"");
  const ne=vals.filter(v=>v!=="");
  return ne.length ? ne.map(esc).join(" / ") : "-";
}
function daysAgo(dateStr){
  return Math.round((new Date() - new Date(dateStr+"T12:00:00"))/86400000);
}
// Monday (ISO week start) of the week containing dateStr, as YYYY-MM-DD.
function weekMonday(dateStr){
  var d=new Date(dateStr+"T12:00:00");
  var off=(d.getDay()+6)%7; // 0 = Monday
  d.setDate(d.getDate()-off);
  var m=d.getMonth()+1, day=d.getDate();
  return d.getFullYear()+"-"+(m<10?"0":"")+m+"-"+(day<10?"0":"")+day;
}
function weeklyVolumes(person){
  var map={};
  state.logs.filter(function(l){return l.person===person;}).forEach(function(l){ var wk=weekMonday(l.date); map[wk]=(map[wk]||0)+(l.volume||0); });
  return Object.keys(map).sort().map(function(wk){ return {week:wk, volume:map[wk]}; });
}
function relTime(dateStr){
  var d=daysAgo(dateStr);
  if(d<=0) return "today";
  if(d===1) return "yesterday";
  if(d<7) return d+" days ago";
  var w=Math.round(d/7);
  if(d<56) return w+(w===1?" week":" weeks")+" ago";
  var m=Math.round(d/30.44);
  if(d<700) return m+(m===1?" month":" months")+" ago";
  var y=Math.round(d/365.25);
  return y+(y===1?" year":" years")+" ago";
}

function draftKey(){ return state.people[state.activePerson]+"|"+curSession; }
// Read the live log form into formDrafts under the current person+session,
// or drop the draft if nothing has been entered. Call before any action that
// re-renders the form (person/session/date change, tab switch).
function captureDraft(){
  if(activeTab!=="log") return;
  const form=document.getElementById("exForm");
  if(!form) return;
  const entries=[]; let any=false;
  form.querySelectorAll(".ex").forEach(card=>{
    const ei=+card.dataset.ei;
    const rows=[], done=[], warm=[];
    card.querySelectorAll("tbody tr").forEach(tr=>{
      const vals=[]; let rowHas=false;
      tr.querySelectorAll('[data-c]').forEach(inp=>{ vals.push(inp.value); if(inp.value!=="") rowHas=true; });
      const dn=tr.querySelector('[data-done]').checked;
      const wu=tr.classList.contains("wset");
      rows.push(vals); done.push(dn); warm.push(wu);
      if(rowHas||dn||wu) any=true;
    });
    entries[ei]={rows,done,warm};
    // A changed set count is worth persisting on its own, so sets you add or
    // remove survive a re-render even before anything has been typed.
    const exDef=((state.program.sessions[curSession]||{}).exercises||[])[ei];
    if(exDef && rows.length!==Math.max(1, exDef.sets||1)) any=true;
  });
  const sel=document.querySelector("#diff button.sel");
  const difficulty=sel?+sel.dataset.d:null;
  const fb=document.getElementById("feedback");
  const feedback=fb?fb.value:"";
  if(difficulty!=null||feedback.trim()!=="") any=true;
  const key=draftKey();
  if(any) formDrafts[key]={entries,difficulty,feedback}; else delete formDrafts[key];
}
// Re-apply a saved draft onto the freshly-rendered form. Returns true if one
// was restored. Runs after the form is wired so added rows get their handlers.
function restoreDraft(){
  const draft=formDrafts[draftKey()];
  if(!draft) return false;
  const sess=state.program.sessions[curSession];
  document.querySelectorAll("#exForm .ex").forEach(card=>{
    const ei=+card.dataset.ei;
    const d=draft.entries[ei]; if(!d) return;
    const ex=sess.exercises[ei]; if(!ex) return;
    const tb=card.querySelector("tbody");
    const best=cardBestWeight(ex);
    while(tb.rows.length<d.rows.length){
      tb.insertAdjacentHTML("beforeend", setRowHtml(tb.rows.length+1, ex, "-"));
      wireSetRow(tb.rows[tb.rows.length-1], ex, best);
    }
    // ...and drop extras, so sets you removed stay removed across a re-render
    // (leaving/returning to the tab used to add them straight back).
    while(tb.rows.length>d.rows.length && tb.rows.length>1) tb.deleteRow(tb.rows.length-1);
    d.rows.forEach((r,i)=>{
      const tr=tb.rows[i]; if(!tr) return;
      const inputs=tr.querySelectorAll('[data-c]');
      (r||[]).forEach((v,ci)=>{ if(inputs[ci]) inputs[ci].value=v; });
      if(isRunning(ex)) updatePace(tr, ex);
      if(d.warm && d.warm[i]){
        tr.classList.add("wset");
        const sn=tr.querySelector("[data-setno]"); if(sn) sn.textContent="W";
      }
      if(d.done[i]){
        const cb=tr.querySelector('[data-done]');
        cb.checked=true; tr.classList.add("done");
        updateSetMedal(tr, ex, best);
      }
    });
  });
  if(draft.difficulty!=null){
    const b=document.querySelector('#diff button[data-d="'+draft.difficulty+'"]');
    if(b) b.classList.add("sel");
  }
  if(draft.feedback){ const f=document.getElementById("feedback"); if(f) f.value=draft.feedback; }
  return true;
}

function getTimer(){ return sessionTimers[draftKey()] || {elapsedSec:0, running:false, lastStart:0}; }
function timerElapsed(t){ return Math.floor(t.elapsedSec + (t.running ? (Date.now()-t.lastStart)/1000 : 0)); }
function fmtDuration(sec){
  sec=Math.max(0,Math.floor(sec));
  const h=Math.floor(sec/3600), m=Math.floor((sec%3600)/60), s=sec%60;
  const two=n=>(n<10?"0":"")+n;
  return h>0 ? h+":"+two(m)+":"+two(s) : m+":"+two(s);
}
function startTimer(){
  const key=draftKey();
  const t=sessionTimers[key] || {elapsedSec:0, running:false, lastStart:0};
  if(!t.running){ t.running=true; t.lastStart=Date.now(); sessionTimers[key]=t; }
  ensureTimerTick(); updateTimerUI();
}
function pauseTimer(){
  const t=sessionTimers[draftKey()]; if(!t||!t.running) return;
  t.elapsedSec += (Date.now()-t.lastStart)/1000; t.running=false;
  updateTimerUI();
}
function toggleTimer(){ const t=sessionTimers[draftKey()]; if(t&&t.running) pauseTimer(); else startTimer(); }
function resetTimer(){ delete sessionTimers[draftKey()]; updateTimerUI(); }
// Auto-start on the first bit of data entered, but never fight a deliberate
// pause: only starts when no timer has ever been created for this key.
function startTimerIfIdle(){ if(!sessionTimers[draftKey()]) startTimer(); }
function ensureTimerTick(){
  if(timerInterval) return;
  timerInterval=setInterval(()=>{
    const t=sessionTimers[draftKey()];
    if(!document.getElementById("timerDisplay") || !t || !t.running){
      clearInterval(timerInterval); timerInterval=null; return;
    }
    updateTimerUI();
  },1000);
}
function updateTimerUI(){
  const el=document.getElementById("timerDisplay"); if(!el) return;
  const t=getTimer();
  el.textContent=fmtDuration(timerElapsed(t));
  el.classList.toggle("running", t.running);
  const btn=document.getElementById("timerToggle");
  if(btn) btn.textContent = t.running ? "Pause" : (t.elapsedSec>0 ? "Resume" : "Start");
}

function renderLog(){
  const p = state.people[state.activePerson];
  const opts = orderedKeys().map(k=>{
    const s=state.program.sessions[k];
    return '<option value="'+k+'" '+(k===curSession?'selected':'')+'>'+esc(s.name)+' · '+esc(s.day)+'</option>';
  }).join("");
  const sess = state.program.sessions[curSession];
  const prev = latestLog(p, curSession);
  const coach = (state.coaching && state.coaching[p]) || {};
  const coachFor = name => (coach.byExercise && coach.byExercise[name]) || "";
  const prevNote = prev
    ? "Inputs start blank. "+esc(possessive(p))+" last session ("+relTime(prev.date)+") is shown in the <b>Last</b> column - beat it."
    : "No previous "+esc(p)+" log for this session yet - today sets the baseline.";

  let html = '<div class="card">'
    + '<div class="flex-between" style="margin-bottom:12px">'
    + '<label class="fld grow" style="max-width:340px">Session<select id="sessionSel">'+opts+'</select></label>'
    + '<label class="fld" style="width:160px">Date<input id="logDate" type="date" value="'+curDate+'"></label>'
    + '</div><div class="hint" style="margin-top:-4px">Logging for <b>'+esc(p)+'</b>. '+prevNote+'</div>'
    + '<div class="row" style="margin-top:11px;gap:8px;align-items:center">'
    + '<span class="timer" id="timerDisplay">0:00</span>'
    + '<button class="mini" id="timerToggle">Start</button>'
    + '<button class="mini" id="timerReset">Reset</button>'
    + '<span class="hint" style="margin:0">Workout time - saved with the session.</span>'
    + '</div></div>';

  const sessNote = (coach.bySession && sess && coach.bySession[sess.name]) || "";
  if(sessNote){
    html += '<div class="card coach-card"><div class="sec-title">🧠 Coach'+(coach.updated?' &middot; '+relTime(coach.updated):"")+'</div>'
      + '<div style="white-space:pre-wrap"><b>'+esc(sess.name)+':</b> '+esc(sessNote)+'</div>'
      + '</div>';
  }

  // Cardio day: the run auto-fills from Garmin, so tell them to just save.
  if((sess.exercises||[]).some(e=>isRunning(e))){
    html += '<div class="cardio-note">⌚ <b>Cardio day.</b> If you wear your Garmin, just <b>log &amp; save</b> - the run\'s distance, splits, pace &amp; ♥ HR fill in automatically once it syncs. Otherwise type the splits below, or <b>⬆ import</b> a file.</div>';
  }

  html += '<div id="exForm">';
  sess.exercises.forEach((ex,ei)=>{
    const last = prev && (prev.entries||[]).find(e=>e.name===ex.name);
    const lastRun = (last && isRunning(ex)) ? runSummaryFromEntry(last, prev&&prev.garmin) : "";
    html += renderExForm(ex,ei,last,prev?prev.date:"",recentNote(p,ex,prev),coachFor(ex.name),lastRun);
  });
  html += '</div>';

  html += '<div class="card"><div class="sec-title">How did the session feel?</div>'
    + '<div class="row" style="margin-bottom:10px"><div class="grow">'
    + '<div class="hint" style="margin-bottom:4px">Difficulty (1 easy &middot; 10 max effort)</div>'
    + '<div class="diff" id="diff">'+[1,2,3,4,5,6,7,8,9,10].map(n=>'<button data-d="'+n+'">'+n+'</button>').join("")+'</div>'
    + '</div></div>'
    + '<label class="fld">Your own notes (optional)<textarea id="feedback" placeholder="e.g. Right knee tight on squats. Felt strong today."></textarea></label>'
    + '<div class="hint">🧠 Coaching notes show at the top and on each exercise after a sync.</div></div>'
    + '<div class="row" style="justify-content:flex-end;margin-bottom:30px">'
    + '<button class="btn btn-ghost" id="clearForm">Clear</button>'
    + '<button class="btn btn-primary" id="saveSession">Save session &check;</button></div>';

  document.getElementById("view").innerHTML = html;

  document.getElementById("sessionSel").onchange=e=>{ captureDraft(); curSession=e.target.value; renderView(); };
  document.getElementById("logDate").onchange=e=>{ captureDraft(); curDate=e.target.value; var sk=sessionForDate(curDate); if(sk) curSession=sk; renderView(); };
  document.getElementById("diff").querySelectorAll("button").forEach(b=>b.onclick=()=>{
    document.querySelectorAll("#diff button").forEach(x=>x.classList.remove("sel"));
    b.classList.add("sel");
  });
  document.getElementById("view").querySelectorAll("[data-addset]").forEach(b=>b.onclick=()=>addSetRow(b));
  document.getElementById("view").querySelectorAll("[data-delset]").forEach(b=>b.onclick=()=>{
    const tb=b.closest(".ex").querySelector("tbody");
    if(tb.rows.length>1){ tb.deleteRow(tb.rows.length-1); }
  });
  document.getElementById("exForm").querySelectorAll(".ex").forEach(card=>{
    const ex=sess.exercises[+card.dataset.ei];
    if(ex) wireExCard(card, ex);
  });
  document.getElementById("saveSession").onclick=saveSession;
  document.getElementById("clearForm").onclick=()=>{ delete formDrafts[draftKey()]; renderView(); };
  document.getElementById("timerToggle").onclick=toggleTimer;
  document.getElementById("timerReset").onclick=resetTimer;
  const startOnEntry=()=>startTimerIfIdle();
  const form=document.getElementById("exForm");
  form.addEventListener("input", startOnEntry);
  form.addEventListener("change", startOnEntry);
  restoreDraft();
  document.querySelectorAll("#exForm .ex").forEach(card=>{
    const ex=sess.exercises[+card.dataset.ei];
    if(ex) updateWarmup(card, ex);
  });
  updateTimerUI();
  if(getTimer().running) ensureTimerTick();
}

function setRowHtml(n,ex,prevCell){
  const lifting = isLifting(ex);
  const paceIdx = isRunning(ex) ? colIndex(ex,/pace/i) : -1;
  let cells="";
  ex.cols.forEach((c,ci)=>{
    let attr="";
    if(lifting) attr = (ci===0 ? ' inputmode="decimal"' : ' inputmode="numeric"');
    if(ci===paceIdx) attr += ' readonly';
    cells += '<td><input data-c="'+ci+'"'+attr+' value="" placeholder="'+esc(c)+'"></td>';
  });
  return '<tr><td class="setno" data-setno data-n="'+n+'" title="Tap to mark as a warm-up set">'+n+'</td>'+cells
    + '<td class="prev">'+prevCell+'</td>'
    + '<td class="done-cell"><input type="checkbox" data-done title="Mark set done"><span class="medal" data-medal hidden>&#129351;</span></td></tr>';
}
// "Most recent for this movement in ANY session" note; empty when the most
// recent occurrence is the log already shown in the Last column.
function recentNote(person, ex, prev){
  if(!isLifting(ex)) return "";
  const rec=latestEntryAnywhere(person, ex.name);
  if(!rec || (prev && rec.log.id===prev.id)) return "";
  let top=null, tw=-Infinity;
  rec.entry.rows.forEach(r=>{ const w=parseFloat(r[0]); if(!isNaN(w)&&w>tw){tw=w;top=r;} });
  if(!top) return "";
  return 'Most recent: <b>'+esc(top[0])+' kg'+(top[1]!==""&&top[1]!=null?' × '+esc(top[1]):"")+'</b> · '
    + relTime(rec.log.date)+' ('+esc(rec.log.sessionName)+')';
}
// Warm-up notes may use "NN%" tokens; resolve them to kg from a reference
// weight (the top set entered so far, else last session's top set).
function warmupBase(card){
  let top=-Infinity;
  card.querySelectorAll('tbody tr [data-c="0"]').forEach(inp=>{ const w=parseFloat(inp.value); if(!isNaN(w)&&w>top) top=w; });
  if(top===-Infinity){ const lt=parseFloat(card.dataset.lasttop); if(!isNaN(lt)) top=lt; }
  return top>-Infinity ? top : null;
}
function computeWarmupText(warmup, base){
  // Once a reference weight is known, show the resolved kg in place of the
  // "NN%" token (e.g. "40%x8" -> "40kg x8"); before then, keep the raw %.
  return warmup.replace(/(\d+(?:\.\d+)?)\s*%/g, function(m,pct){
    if(base==null) return m;
    var kg=Math.round((base*parseFloat(pct)/100)/2.5)*2.5;
    return kg+"kg";
  });
}
function updateWarmup(card, ex){
  if(!ex.warmup || ex.warmup.indexOf("%")<0) return;
  const span=card.querySelector("[data-warmup]"); if(!span) return;
  span.textContent=computeWarmupText(ex.warmup, warmupBase(card));
}
function renderExForm(ex,ei,last,prevDate,recent,coach,lastRun){
  const running = isRunning(ex);
  // Runs get a single blank split row — the watch (or the importer) fills the
  // real splits in. Other exercises take their set count from the program only
  // (it used to be max(program, last log), which permanently inflated it).
  const rows = running ? 1 : Math.max(1, ex.sets||1);
  const fmt = r => fmtRow(ex.cols, r);
  let body="";
  for(let i=0;i<rows;i++){
    // Per-set "Last" only makes sense for lifting; a run's km-by-km splits don't
    // line up session to session, so runs show a single "Last run" line instead.
    const r = !running && last && last.rows[i] ? last.rows[i] : null;
    body += setRowHtml(i+1, ex, r?fmt(r):"-");
  }
  let lastTop=-Infinity;
  if(last && isLifting(ex)) last.rows.forEach(r=>{ const w=parseFloat(r[0]); if(!isNaN(w)&&w>lastTop) lastTop=w; });
  const lastTopAttr = lastTop>-Infinity ? ' data-lasttop="'+lastTop+'"' : '';
  const warmupHtml = ex.warmup
    ? '<div class="warmup">Warm-up: <span data-warmup>'+esc(computeWarmupText(ex.warmup, lastTop>-Infinity?lastTop:null))+'</span></div>'
    : "";
  return '<div class="card ex" data-ei="'+ei+'" data-name="'+esc(ex.name)+'"'+lastTopAttr+'>'
    + '<div class="ex-head"><div class="ex-name">'+esc(ex.name)
      + '<button type="button" class="wrench'+(ex.notes?' has':'')+'" data-exnotes-toggle aria-expanded="false" title="Machine settings">&#128295;</button>'
      + '</div><div class="ex-meta">'+esc(ex.target)+'</div></div>'
    + warmupHtml
    + (running && lastRun ? '<div class="recent">🏃 Last run: <b>'+esc(lastRun)+'</b></div>' : "")
    + '<div class="notes-wrap" data-notes-wrap hidden>'
      + '<textarea class="notes" data-exnotes rows="2" placeholder="Seat height, pins, machine settings…">'+esc(ex.notes||"")+'</textarea>'
      + '</div>'
    + (coach?'<div class="coach">🧠 Coach: '+esc(coach)+'</div>':"")
    + (recent?'<div class="recent">🕑 '+recent+'</div>':"")
    + '<div class="sets-wrap"><table class="sets"><thead><tr><th></th>'+ex.cols.map(c=>'<th>'+esc(c)+'</th>').join("")
    + '<th class="prev" title="'+esc(prevDate)+'">Last'+(prevDate?' · '+relTime(prevDate):"")+'</th><th class="done-cell"></th></tr></thead><tbody>'+body+'</tbody></table></div>'
    + '<div class="row" style="margin-top:8px"><button class="mini" data-addset>+ set</button>'
    + '<button class="mini" data-delset>- set</button>'
    + (isRunning(ex)?'<button class="mini" data-runimport style="margin-left:auto">⬆ Import run (TCX/GPX)</button><input type="file" data-runfile accept=".tcx,.gpx,.xml" style="display:none">':'')
    + '</div></div>';
}
function addSetRow(btn){
  const card=btn.closest(".ex"); const ei=+card.dataset.ei;
  const ex=state.program.sessions[curSession].exercises[ei];
  const tb=card.querySelector("tbody");
  tb.insertAdjacentHTML("beforeend", setRowHtml(tb.rows.length+1, ex, "-"));
  const tr=tb.rows[tb.rows.length-1];
  wireSetRow(tr, ex, cardBestWeight(ex));
  if(isLifting(ex)){
    const firstWeight=tb.rows[0].querySelector('[data-c="0"]');
    const w=tr.querySelector('[data-c="0"]');
    if(firstWeight && firstWeight.value && w && !w.value) w.value=firstWeight.value;
  }
}

// Best saved weight is only recomputed once per card render/added row, not
// per keystroke — it can't change until the session is saved.
function cardBestWeight(ex){
  return isLifting(ex) ? bestWeightSoFar(state.people[state.activePerson], ex.name) : -Infinity;
}
function updateSetMedal(tr, ex, best){
  const medal=tr.querySelector("[data-medal]");
  if(!medal) return;
  const w=parseFloat(tr.querySelector('[data-c="0"]').value);
  // Warm-up sets never earn a PR medal.
  medal.hidden = !(isLifting(ex) && !tr.classList.contains("wset") && !isNaN(w) && best>-Infinity && w>best);
}
function wireSetRow(tr, ex, best){
  const cb=tr.querySelector("[data-done]");
  const weightInput=tr.querySelector('[data-c="0"]');
  const repsInput=tr.querySelector('[data-c="1"]');
  if(!cb) return;
  cb.addEventListener("change", ()=>{
    tr.classList.toggle("done", cb.checked);
    if(cb.checked){
      if(isLifting(ex) && repsInput && !repsInput.value.trim()){
        const range=parseRange(ex.target);
        if(range) repsInput.value=range.high;
      }
      updateSetMedal(tr, ex, best);
    } else {
      tr.querySelector("[data-medal]").hidden=true;
    }
  });
  if(weightInput) weightInput.addEventListener("input", ()=>{ if(cb.checked) updateSetMedal(tr, ex, best); });
  if(isRunning(ex)){
    const upd=()=>updatePace(tr, ex);
    tr.querySelectorAll('[data-c]').forEach(inp=>inp.addEventListener("input", upd));
  }
  const setno=tr.querySelector("[data-setno]");
  if(setno) setno.addEventListener("click", ()=>{
    const wu=tr.classList.toggle("wset");
    setno.textContent = wu ? "W" : setno.dataset.n;
    updateSetMedal(tr, ex, best); // warm-up rows show no medal
  });
}
function wireExCard(card, ex){
  const tbody=card.querySelector("tbody");
  const best=cardBestWeight(ex);
  Array.from(tbody.rows).forEach(tr=>wireSetRow(tr, ex, best));
  const firstWeight = tbody.rows[0] && tbody.rows[0].querySelector('[data-c="0"]');
  if(firstWeight && isLifting(ex)){
    // Mirror the first set's weight into rows the user hasn't set themselves.
    // Track the last mirrored value so multi-digit entry keeps updating: typing
    // "6" then "0" fills every row with "60", not stuck at "6" (the old check
    // only filled empty rows, so after the first digit they were never updated).
    let mirrored=firstWeight.value||"";
    firstWeight.addEventListener("input", ()=>{
      const val=firstWeight.value;
      Array.from(tbody.rows).slice(1).forEach(tr=>{
        const w=tr.querySelector('[data-c="0"]');
        if(w && (!w.value || w.value===mirrored)) w.value=val;
      });
      mirrored=val;
    });
  }
  if(ex.warmup && ex.warmup.indexOf("%")>=0){
    updateWarmup(card, ex);
    tbody.addEventListener("input", ()=>updateWarmup(card, ex));
  }
  // Machine settings are editable mid-session: `ex` is the live program object,
  // so changes stick for next time too. Saved on blur to avoid writing on every
  // keystroke; autoSync on change so the other phone picks the settings up.
  const notesEl=card.querySelector("[data-exnotes]");
  const notesWrap=card.querySelector("[data-notes-wrap]");
  const notesBtn=card.querySelector("[data-exnotes-toggle]");
  if(notesBtn && notesWrap){
    notesBtn.onclick=()=>{
      const opening=notesWrap.hasAttribute("hidden");
      if(opening){ notesWrap.removeAttribute("hidden"); if(notesEl) notesEl.focus(); }
      else notesWrap.setAttribute("hidden","");
      notesBtn.setAttribute("aria-expanded", opening?"true":"false");
    };
  }
  if(notesEl){
    notesEl.addEventListener("change", ()=>{
      const v=notesEl.value.trim();
      if(v===(ex.notes||"")) return;
      ex.notes=v; save(); autoSync();
      if(notesBtn) notesBtn.classList.toggle("has", !!v); // wrench stays lit when settings are saved
      toast("Machine settings saved");
    });
  }
  const runBtn=card.querySelector("[data-runimport]");
  if(runBtn){
    const fileInp=card.querySelector("[data-runfile]");
    runBtn.onclick=()=>fileInp.click();
    fileInp.onchange=e=>{
      const f=e.target.files[0]; if(!f) return;
      const rd=new FileReader();
      rd.onload=()=>importRunIntoCard(rd.result, ex, card);
      rd.readAsText(f);
      fileInp.value="";
    };
  }
}

function saveSession(){
  const sess=state.program.sessions[curSession];
  const person=state.people[state.activePerson];
  const prev=latestLog(person,curSession);
  const date=document.getElementById("logDate").value || todayStr();
  const sel=document.querySelector("#diff button.sel");
  const difficulty = sel? +sel.dataset.d : null;
  const feedback=document.getElementById("feedback").value.trim();
  const entries=[];
  document.querySelectorAll("#exForm .ex").forEach(card=>{
    const ex=sess.exercises[+card.dataset.ei] || {cols:["Weight (kg)","Reps"], name:card.dataset.name};
    const name=ex.name || card.dataset.name;
    const rows=[], warmup=[];
    card.querySelectorAll("tbody tr").forEach(tr=>{
      const vals=[]; let has=false;
      tr.querySelectorAll('[data-c]').forEach(inp=>{ const v=inp.value.trim(); vals.push(v); if(v!=="") has=true; });
      if(has){ if(tr.classList.contains("wset")) warmup.push(rows.length); rows.push(vals); }
    });
    if(rows.length){ const en={name,cols:ex.cols.slice(),rows}; if(warmup.length) en.warmup=warmup;
      if(ex.muscles&&ex.muscles.length) en.muscles=ex.muscles.slice(); entries.push(en); }
  });
  if(!entries.length && !feedback){ toast("Nothing entered yet"); return; }
  var volume=0;
  entries.forEach(function(en){ var wu=en.warmup||[]; en.rows.forEach(function(r,ri){ if(wu.indexOf(ri)>=0) return; var w=parseFloat(r[0]), reps=parseInt(r[1],10); if(!isNaN(w)&&!isNaN(reps)) volume+=w*reps; }); });
  volume=Math.round(volume);
  var prs=[];
  entries.forEach(function(en){
    if(!isLifting(en)) return; // col-0 is only a weight (kg) for lifting entries
    var wu=en.warmup||[];
    var ws=en.rows.map(function(r,ri){return wu.indexOf(ri)>=0?NaN:parseFloat(r[0]);}).filter(function(v){return !isNaN(v);});
    if(!ws.length) return;
    var thisMax=Math.max.apply(null,ws);
    var prevBest=bestWeightSoFar(person,en.name);
    if(prevBest>-Infinity && thisMax>prevBest){ en.pr=thisMax; prs.push({name:en.name,weight:thisMax}); }
  });
  const durationSec = timerElapsed(getTimer());
  const log={ id:Date.now(), date, person, sessionKey:curSession, sessionName:sess.name,
    entries, feedback, difficulty, volume, durationSec };
  // Cardio/running session: flag it so the Garmin sync (laptop) can link the run's
  // extra data (HR, cadence, elevation, splits…). Cleared once linked; see mcp-garmin.
  if(entries.some(en=>isRunning(en))) log.garminWanted=true;
  state.logs.push(log); save();
  delete formDrafts[draftKey()];
  delete sessionTimers[draftKey()];
  justSavedId=log.id;
  switchTab("history", true); // draft just cleared above — don't re-capture it
  showSaveSummary(volume, prs, entries);
  autoSync(); // push this session to the shared store automatically (if sync is set up)
}

function renderHistory(){
  const logs=[...state.logs].sort((a,b)=> (a.date<b.date?1:a.date>b.date?-1:b.id-a.id));
  let html='<div class="card"><div class="flex-between">'
    + '<div class="sec-title" style="margin:0">History - '+logs.length+' session'+(logs.length===1?"":"s")+'</div>'
    + '<select id="histFilter"><option value="all">Everyone</option>'
    + state.people.map(p=>'<option value="'+esc(p)+'">'+esc(p)+'</option>').join("")
    + '</select></div></div>';
  if(!logs.length){
    html+='<div class="card empty">No sessions logged yet.<br>Tap <b>Log it</b> on <b>Home</b> to record your first one.</div>';
    document.getElementById("view").innerHTML=html; return;
  }
  // This-week summary for the active person (volume, sessions, muscle heatmap).
  const p=state.people[state.activePerson];
  const pc = personSwatch(p);
  const thisWk=weekMonday(trainingDateStr());
  const wkLogs=state.logs.filter(l=>l.person===p && weekMonday(l.date)===thisWk);
  const wkVol=wkLogs.reduce((t,l)=>t+(l.volume||0),0);
  html+='<div class="card"><div class="sec-title">📅 This week - '+esc(p)+' <span class="pill" data-sw="'+pc+'">'+wkLogs.length+' session'+(wkLogs.length===1?"":"s")+'</span></div>'
    + '<div class="row" style="align-items:center;gap:16px">'
    + '<div><div style="font-size:22px;font-weight:800">'+wkVol.toLocaleString()+' kg</div><div class="hint" style="margin:0">volume this week</div></div>'
    + '<div id="weekMap" style="flex:1;min-width:180px;max-width:280px"></div>'
    + '</div>'
    + '<div class="hint" style="margin:10px 0 4px">Weekly volume</div><div class="chart-box" style="height:150px"><canvas id="weekChart"></canvas></div></div>';
  html+='<div id="histList"></div>';
  document.getElementById("view").innerHTML=html;
  // Weekly muscle heatmap: clone the (styled) save-dialog map and shade it.
  const src=document.getElementById("muscleSvg");
  if(src && wkLogs.length){
    const clone=src.cloneNode(true); clone.removeAttribute("id"); clone.style.maxWidth="280px";
    paintMuscleMap(clone, muscleSetsForLogs(wkLogs));
    document.getElementById("weekMap").appendChild(clone);
  } else if(document.getElementById("weekMap")){
    document.getElementById("weekMap").innerHTML='<div class="hint" style="margin:0">No sessions yet this week.</div>';
  }
  drawWeekChart(p);
  const filter=document.getElementById("histFilter");
  filter.onchange=()=>drawHist(filter.value);
  drawHist("all");
}
let weekChart=null;
function drawWeekChart(person){
  const canvas=document.getElementById("weekChart"); if(!canvas) return;
  const weeks=weeklyVolumes(person).slice(-10);
  const i=state.people.indexOf(person);
  const dark=document.documentElement.getAttribute("data-theme")==="dark";
  const col=swatchColor(state.colors[i],dark);
  const tickCol=dark?"#9aa3b2":"#697086", gridCol=dark?"rgba(255,255,255,.09)":"rgba(20,30,55,.08)";
  if(weekChart) weekChart.destroy();
  weekChart=new Chart(canvas,{
    type:"bar",
    data:{labels:weeks.map(w=>w.week.slice(5)), datasets:[{label:person+" weekly kg", data:weeks.map(w=>w.volume), backgroundColor:col}]},
    options:{responsive:true, maintainAspectRatio:false,
      scales:{x:{ticks:{color:tickCol},grid:{color:gridCol}}, y:{beginAtZero:true, ticks:{color:tickCol}, grid:{color:gridCol}}},
      plugins:{legend:{display:false}}}
  });
}
// The extra info Garmin adds to a linked cardio session (see mcp-garmin). Themed box.
function garminLine(l){
  const g=l.garmin; if(!g) return "";
  const bits=[];
  if(g.avg_hr!=null) bits.push("avg HR "+g.avg_hr);
  if(g.max_hr!=null) bits.push("max "+g.max_hr);
  if(g.cadence_spm!=null) bits.push("cadence "+g.cadence_spm+" spm");
  if(g.elevation_gain_m!=null) bits.push("+"+g.elevation_gain_m+" m");
  if(g.calories!=null) bits.push(g.calories+" kcal");
  if(g.moving_time) bits.push("moving "+g.moving_time);
  if(g.training_effect!=null) bits.push("TE "+g.training_effect);
  if(g.vo2max!=null) bits.push("VO₂ "+g.vo2max);
  return bits.length? '<div class="garminbox">⌚ Garmin · '+bits.map(esc).join(" · ")+'</div>' : "";
}
function garminStatus(l){
  if(l.garminActivityId) return ' · ⌚ Garmin';
  if(l.garminWanted) return ' · ⌚ awaiting run…';
  return "";
}
// Parse "m:ss" / "h:mm:ss" to seconds; blank/invalid -> null.
function parseClock(s){
  if(s==null) return null; s=String(s).trim(); if(!s) return null;
  const p=s.split(":").map(Number); if(p.some(isNaN)) return null;
  return p.reduce((t,n)=>t*60+n,0);
}
// One-line summary of a session's run for the collapsed History row: total
// distance, time, average pace, and avg HR from the linked Garmin data.
// A real running split has distance. Garmin logs rest/auto laps at 0 km, which
// aren't splits and skew pace/totals — drop those (but keep blank-distance rows
// from manual entry). Used by both the collapsed summary and the splits table.
function isSplitRow(r, di){ const d=parseFloat(r[di]); return isNaN(d) || d>0; }
// Distance · time · avg pace · ♥ HR for one run entry (0-distance laps skipped).
function runSummaryFromEntry(e, garmin){
  if(!e) return "";
  const di=colIndex(e,/dist/i), ti=colIndex(e,/time/i);
  let km=0, sec=0;
  (e.rows||[]).forEach(r=>{ const d=parseFloat(r[di]); if(isNaN(d)||d<=0) return;
    km+=d; const t=parseClock(r[ti]); if(t!=null) sec+=t; });
  const bits=[];
  if(km>0) bits.push((Math.round(km*100)/100)+" km");
  if(sec>0) bits.push(fmtMmSs(sec));
  if(km>0&&sec>0) bits.push(fmtPace((sec/60)/km)+"/km");
  const g=garmin||{}; if(g.avg_hr!=null) bits.push("♥ "+g.avg_hr);
  return bits.join(" · ");
}
function runSummary(l){
  const e=(l.entries||[]).find(x=>isRunning(x)); if(!e) return null;
  return runSummaryFromEntry(e, l.garmin) || null;
}
// One entry's detail row. Runs render as a proper splits table (per-lap
// distance/time/pace/HR) with a totals line; everything else stays a compact
// dot-joined list.
function entryDetailHtml(e){
  if(isRunning(e) && (e.rows||[]).length){
    const cols=e.cols||[];
    const di=colIndex(e,/dist/i), ti=colIndex(e,/time/i), pi=colIndex(e,/pace/i), hi=colIndex(e,/hr/i);
    const splitRows=e.rows.filter(r=>isSplitRow(r, di)); // drop 0-distance rest laps
    if(!splitRows.length) return '<tr><td colspan="2"><b>'+esc(e.name)+(e.pr?' 🥇':'')+'</b></td></tr>';
    const head='<tr><th class="spl">#</th>'+cols.map(c=>'<th class="spl">'+esc(c)+'</th>').join("")+'</tr>';
    const body=splitRows.map((r,ri)=>'<tr><td class="spl">'+(ri+1)+'</td>'
      + cols.map((c,ci)=>'<td class="spl">'+esc(r[ci]!=null&&String(r[ci]).trim()!==""?String(r[ci]):"-")+'</td>').join("")+'</tr>').join("");
    let km=0, sec=0, hrSum=0, hrN=0;
    splitRows.forEach(r=>{ const d=parseFloat(r[di]); if(!isNaN(d)) km+=d;
      const t=parseClock(r[ti]); if(t!=null) sec+=t;
      if(hi>=0){ const h=parseFloat(r[hi]); if(!isNaN(h)){ hrSum+=h; hrN++; } } });
    const tot=cols.map((c,ci)=>{
      let v="";
      if(ci===di && km>0) v=Math.round(km*100)/100;
      else if(ci===ti && sec>0) v=fmtMmSs(sec);
      else if(ci===pi && km>0 && sec>0) v=fmtPace((sec/60)/km)+"/km";
      else if(ci===hi && hrN) v=Math.round(hrSum/hrN);
      return '<td class="spl">'+esc(String(v))+'</td>';
    }).join("");
    const totals=(km>0||sec>0)?'<tr class="tot"><td class="spl">Σ</td>'+tot+'</tr>':"";
    return '<tr><td colspan="2"><b>'+esc(e.name)+(e.pr?' 🥇':'')+'</b>'
      + '<div class="splits-wrap"><table class="splits">'+head+body+totals+'</table></div></td></tr>';
  }
  return '<tr><td><b>'+esc(e.name)+(e.pr?' 🥇':'')+'</b></td><td>'
    + e.rows.map((r,ri)=>{ const s=fmtRow(e.cols||[], r); return (e.warmup&&e.warmup.indexOf(ri)>=0)?'<span class="wu-tag">'+s+' (w)</span>':s; }).join(" · ")+'</td></tr>';
}
function drawHist(who){
  let logs=[...state.logs].sort((a,b)=> (a.date<b.date?1:a.date>b.date?-1:b.id-a.id));
  if(who!=="all") logs=logs.filter(l=>l.person===who);
  const pc=personSwatch;
  document.getElementById("histList").innerHTML = logs.map(l=>{
    const open = l.id===justSavedId;
    const rows=(l.entries||[]).map(entryDetailHtml).join("");
    const rs=runSummary(l);
    return '<div class="log-item"><div class="log-row"><div>'
      + '<h3>'+esc(l.sessionName)+' <span class="pill" data-sw="'+pc(l.person)+'">'+esc(l.person)+'</span></h3>'
      + '<div class="ex-meta">'+esc(l.date)+(rs?' · '+esc(rs):"")+(l.difficulty?' · difficulty '+l.difficulty+'/10':"")+(l.volume?' · '+l.volume.toLocaleString()+' kg':"")+(l.durationSec?' · ⏱ '+fmtDuration(l.durationSec):"")+garminStatus(l)+'</div></div>'
      + '<div class="row"><button class="mini" data-toggle="'+l.id+'">'+(open?"Hide":"View")+'</button>'
      + '<button class="mini" data-del="'+l.id+'" style="color:var(--bad)">Delete</button></div></div>'
      + '<div class="log-detail '+(open?"open":"")+'" id="d'+l.id+'"><table>'
      + (rows||'<tr><td class="ex-meta">No set data</td></tr>')+'</table>'
      + (l.feedback?'<div class="fb">📝 '+esc(l.feedback)+'</div>':"")+garminLine(l)+'</div></div>';
  }).join("");
  justSavedId=null;
  document.querySelectorAll("[data-toggle]").forEach(b=>b.onclick=()=>{
    const d=document.getElementById("d"+b.dataset.toggle);
    d.classList.toggle("open"); b.textContent=d.classList.contains("open")?"Hide":"View";
  });
  document.querySelectorAll("[data-del]").forEach(b=>b.onclick=()=>{
    if(confirm("Delete this session?")){
      state.logs=state.logs.filter(l=>l.id!=b.dataset.del); save(); drawHist(who); toast("Deleted");
    }
  });
}

let chart=null;
function renderProgress(){
  const allEx=[...new Set(state.logs.flatMap(l=>(l.entries||[]).map(e=>e.name)))].sort();
  if(!allEx.length){
    document.getElementById("view").innerHTML='<div class="card empty">Log a few sessions and your progress charts will appear here.</div>';
    return;
  }
  const p=state.people[state.activePerson];
  const pc = personSwatch(p);
  const recs=personRecords(p);
  const recNames=Object.keys(recs).sort();
  let recTable;
  if(recNames.length){
    recTable='<div class="sets-wrap"><table class="rec"><thead><tr><th>Exercise</th><th>Best</th><th>Reps</th><th>e1RM</th><th>When</th></tr></thead><tbody>'
      + recNames.map(function(n){ const r=recs[n]; const e=epley(r.kg, r.reps);
          return '<tr><td>'+esc(n)+'</td><td><b>'+r.kg+' kg</b></td><td>'+(r.reps!=null?r.reps:"–")+'</td><td>'+(isNaN(e)?"–":Math.round(e)+" kg")+'</td><td class="ex-meta">'+relTime(r.date)+'</td></tr>'; }).join("")
      + '</tbody></table></div>';
  } else {
    recTable='<div class="hint">No lifting bests for '+esc(p)+' yet.</div>';
  }
  document.getElementById("view").innerHTML='<div class="card">'
    + '<div class="sec-title">🏅 Records - '+esc(p)+' <span class="pill" data-sw="'+pc+'">current bests</span></div>'
    + recTable + '</div>'
    + '<div class="card">'
    + '<div class="row" style="margin-bottom:12px">'
    + '<label class="fld grow" style="max-width:280px">Exercise chart<select id="progEx">'
    + allEx.map(n=>'<option>'+esc(n)+'</option>').join("")+'</select></label>'
    + '<label class="fld" style="width:150px">Metric<select id="progMetric"><option value="weight">Top-set weight</option><option value="e1rm">Est. 1RM</option></select></label></div>'
    + '<div class="hint" style="margin-bottom:10px">Per session, for both people. Warm-up sets are excluded.</div>'
    + '<div class="chart-box"><canvas id="progChart"></canvas></div></div>';
  document.getElementById("progEx").onchange=drawChart;
  document.getElementById("progMetric").onchange=drawChart;
  drawChart();
}
function drawChart(){
  const name=document.getElementById("progEx").value;
  const metric=(document.getElementById("progMetric")||{}).value||"weight";
  const dark=document.documentElement.getAttribute("data-theme")==="dark";
  const series=state.people.map((p,i)=>{
    const pts=state.logs.filter(l=>l.person===p)
      .map(l=>{ const e=(l.entries||[]).find(x=>x.name===name); if(!e) return null;
        const wu=e.warmup||[]; const vals=[];
        e.rows.forEach((r,ri)=>{ if(wu.indexOf(ri)>=0) return; const w=parseFloat(r[0]); if(isNaN(w)) return;
          if(metric==="e1rm"){ const v=epley(w,parseInt(r[1],10)); if(!isNaN(v)) vals.push(v); } else vals.push(w); });
        if(!vals.length) return null; return {x:l.date,y:Math.round(Math.max.apply(null,vals)*10)/10}; })
      .filter(Boolean).sort((a,b)=>a.x<b.x?-1:1);
    return {label:p,data:pts,borderColor:swatchColor(state.colors[i],dark),
      backgroundColor:swatchColor(state.colors[i],dark),tension:.25,spanGaps:true};
  });
  if(chart) chart.destroy();
  const tickCol=dark?"#9aa3b2":"#697086";
  const gridCol=dark?"rgba(255,255,255,.09)":"rgba(20,30,55,.08)";
  chart=new Chart(document.getElementById("progChart"),{
    type:"line", data:{datasets:series},
    options:{responsive:true,maintainAspectRatio:false,parsing:false,
      scales:{x:{type:"category",labels:[...new Set(state.logs.map(l=>l.date))].sort(),
          ticks:{color:tickCol},grid:{color:gridCol}},
        y:{beginAtZero:false,title:{display:true,text:metric==="e1rm"?"Est. 1RM (kg)":"Top-set weight",color:tickCol},
          ticks:{color:tickCol},grid:{color:gridCol}}},
      plugins:{legend:{position:"top",labels:{color:tickCol}}}}
  });
}

function bwFor(person){
  return state.bodyweights.filter(b=>b.person===person)
    .slice().sort((a,b)=> a.date<b.date?-1: a.date>b.date?1:0);
}
function latestBw(person){ const a=bwFor(person); return a.length? a[a.length-1] : null; }
// Add or replace a person's bodyweight for a date; keeps weights[] (the
// "current" value shown in the header/settings) in sync with the newest entry.
function addBodyweight(person, date, kg){
  if(isNaN(kg)) return;
  const existing=state.bodyweights.find(b=>b.person===person && b.date===date);
  if(existing) existing.kg=kg; else state.bodyweights.push({person, date, kg});
  const pi=state.people.indexOf(person);
  if(pi>=0){ const lb=latestBw(person); if(lb) state.weights[pi]=String(lb.kg); }
}
// Tolerant CSV parse: split on comma/semicolon/tab, honouring simple quotes.
function parseCsv(text){
  return text.replace(/\r/g,"").split("\n").filter(l=>l.trim()!=="").map(line=>{
    const out=[]; let cur="", q=false;
    for(let i=0;i<line.length;i++){
      const c=line[i];
      if(q){ if(c==='"'){ if(line[i+1]==='"'){cur+='"';i++;} else q=false; } else cur+=c; }
      else if(c==='"') q=true;
      else if(c===","||c===";"||c==="\t"){ out.push(cur); cur=""; }
      else cur+=c;
    }
    out.push(cur);
    return out.map(s=>s.trim());
  });
}
function parseAnyDate(s){
  s=String(s).trim(); if(!s) return null;
  let m=s.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/); // ISO-ish
  if(m) return m[1]+"-"+("0"+m[2]).slice(-2)+"-"+("0"+m[3]).slice(-2);
  m=s.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})/); // D/M/Y or M/D/Y — assume D/M/Y
  if(m){ let d=+m[1], mo=+m[2]; if(d>12){/*keep*/} else if(mo>12){ const t=d;d=mo;mo=t; }
    return m[3]+"-"+("0"+mo).slice(-2)+"-"+("0"+d).slice(-2); }
  const t=new Date(s); if(!isNaN(t)) return t.toISOString().slice(0,10);
  return null;
}
// Import a bodyweight CSV (e.g. from the 1byone Health app export). Auto-detects
// the date and weight columns from the header; converts lb→kg if the header says so.
function importBodyweightCsv(text, person){
  const rows=parseCsv(text);
  if(!rows.length) return {added:0, msg:"Empty file"};
  const header=rows[0].map(h=>h.toLowerCase());
  let di=header.findIndex(h=>/date|time|day/.test(h));
  let wi=header.findIndex(h=>/weight|mass|\bkg\b|\blb\b|lbs|pounds/.test(h));
  let start=1;
  if(di<0 || wi<0){ // no recognisable header — assume col0=date, col1=weight, no header
    di=0; wi=1; start=0;
  }
  const isLb=wi>=0 && /lb|pound/.test(header[wi]||"");
  let added=0;
  for(let r=start;r<rows.length;r++){
    const cells=rows[r]; if(!cells || cells.length<=Math.max(di,wi)) continue;
    const date=parseAnyDate(cells[di]);
    let kg=parseFloat(String(cells[wi]).replace(/[^\d.]/g,""));
    if(!date || isNaN(kg)) continue;
    if(isLb) kg=Math.round(kg*0.453592*10)/10;
    addBodyweight(person, date, kg); added++;
  }
  return {added, msg: added? added+" entries imported" : "No date+weight rows found"};
}

let bwChart=null;
function renderBody(){
  const p=state.people[state.activePerson];
  const hist=bwFor(p).slice().reverse(); // newest first for the list
  const latest=latestBw(p);
  const pc = personSwatch(p);
  const goal=(state.goals&&state.goals[state.activePerson])||"";
  let html='<div class="card"><div class="sec-title">🎯 '+esc(possessive(p))+' goals</div>'
    + (goal ? '<div style="white-space:pre-wrap">'+esc(goal)+'</div>'
            : '<div class="hint" style="margin:0">No goals set yet - add them via the gear menu.</div>')
    + '</div>';
  html+='<div class="card">'
    + '<div class="flex-between" style="margin-bottom:10px"><div>'
    + '<h3>'+esc(p)+' <span class="pill" data-sw="'+pc+'">bodyweight</span></h3>'
    + '<div class="ex-meta">'+(latest? latest.kg+' kg · '+relTime(latest.date) : 'No entries yet')+'</div></div></div>'
    + '<div class="row" style="align-items:flex-end;gap:8px">'
    + '<label class="fld"><span>Weight (kg)</span><input id="bwKg" type="number" inputmode="decimal" step="0.1" placeholder="e.g. 76" style="width:120px"></label>'
    + '<label class="fld"><span>Date</span><input id="bwDate" type="date" value="'+trainingDateStr()+'" style="width:150px"></label>'
    + '<button class="btn btn-primary" id="bwAdd">Add</button>'
    + '<button class="mini" id="bwImport" style="margin-left:auto">⬆ Import from scale (CSV)</button>'
    + '<input id="bwFile" type="file" accept=".csv,text/csv,text/plain" style="display:none">'
    + '</div>'
    + '<div class="hint" style="margin-top:6px">Import a CSV exported from your scale app (e.g. 1byone Health). Date + weight columns are detected automatically.</div>'
    + '</div>';
  if(hist.length){
    html+='<div class="card"><div class="sec-title">Trend</div><div class="chart-box"><canvas id="bwChart"></canvas></div></div>';
    html+='<div class="card"><div class="sec-title">History - '+hist.length+' entr'+(hist.length===1?"y":"ies")+'</div><div id="bwList"></div></div>';
  } else {
    html+='<div class="card empty">No bodyweight logged for '+esc(p)+' yet.<br>Add one above, or import from your scale app.</div>';
  }
  document.getElementById("view").innerHTML=html;

  document.getElementById("bwAdd").onclick=()=>{
    const kg=parseFloat(document.getElementById("bwKg").value);
    const date=document.getElementById("bwDate").value||todayStr();
    if(isNaN(kg)){ toast("Enter a weight"); return; }
    addBodyweight(p, date, kg); save(); renderPeople(); renderBody(); toast("Saved");
  };
  document.getElementById("bwImport").onclick=()=>document.getElementById("bwFile").click();
  document.getElementById("bwFile").onchange=e=>{
    const f=e.target.files[0]; if(!f) return;
    const rd=new FileReader();
    rd.onload=()=>{ const res=importBodyweightCsv(rd.result, p); if(res.added){ save(); renderPeople(); } renderBody(); toast(res.msg); };
    rd.readAsText(f);
  };
  if(hist.length){
    const list=document.getElementById("bwList");
    list.innerHTML=hist.map(b=>'<div class="log-row" style="padding:4px 0;border-bottom:1px solid var(--line)">'
      + '<div><b>'+b.kg+' kg</b> <span class="ex-meta">'+esc(b.date)+' · '+relTime(b.date)+'</span></div>'
      + '<button class="mini" data-bwdel="'+esc(b.person)+'|'+esc(b.date)+'" style="color:var(--bad)">Delete</button></div>').join("");
    list.querySelectorAll("[data-bwdel]").forEach(btn=>btn.onclick=()=>{
      const a=btn.dataset.bwdel.split("|");
      state.bodyweights=state.bodyweights.filter(b=>!(b.person===a[0] && b.date===a[1]));
      const pi=state.people.indexOf(p); if(pi>=0){ const lb=latestBw(p); state.weights[pi]=lb?String(lb.kg):""; }
      save(); renderPeople(); renderBody(); toast("Deleted");
    });
    drawBwChart(p);
  }
}
function drawBwChart(person){
  const pts=bwFor(person).map(b=>({x:b.date, y:b.kg}));
  const i=state.people.indexOf(person);
  if(bwChart) bwChart.destroy();
  const dark=document.documentElement.getAttribute("data-theme")==="dark";
  const col=swatchColor(state.colors[i],dark);
  const tickCol=dark?"#9aa3b2":"#697086", gridCol=dark?"rgba(255,255,255,.09)":"rgba(20,30,55,.08)";
  bwChart=new Chart(document.getElementById("bwChart"),{
    type:"line", data:{datasets:[{label:person+" (kg)", data:pts, borderColor:col, backgroundColor:col, tension:.25, spanGaps:true}]},
    options:{responsive:true, maintainAspectRatio:false, parsing:false,
      scales:{x:{type:"category", labels:[...new Set(bwFor(person).map(b=>b.date))].sort(), ticks:{color:tickCol}, grid:{color:gridCol}},
        y:{beginAtZero:false, title:{display:true, text:"kg", color:tickCol}, ticks:{color:tickCol}, grid:{color:gridCol}}},
      plugins:{legend:{position:"top", labels:{color:tickCol}}}}
  });
}

function renderEdit(){
  let html='<div class="card"><div class="hint">Edit any session below - rename exercises, change targets, add warm-up notes, add or remove movements. Changes apply to future logging; past history is untouched.</div>'
    + '<div class="row" style="margin-top:10px"><button class="mini" id="addSessionBtn">&#10133; Add session</button>'
    + '<button class="mini" id="importSessionBtn">&#128229; Import shared session</button></div></div>';
  if(!orderedKeys().length){
    html+='<div class="card empty">No sessions yet.<br>Tap <b>+ Add session</b> above to create your first workout day.</div>';
  }
  orderedKeys().forEach(k=>{
    const s=state.program.sessions[k];
    html+='<div class="card"><div class="flex-between" style="margin-bottom:10px"><div>'
      + '<h3>'+esc(s.name)+'</h3><div class="ex-meta">'+esc(s.day)+'</div></div>'
      + '<div class="row"><button class="mini" data-shareex="'+k+'">&#128279; Share</button>'
      + '<button class="mini" data-addex="'+k+'">+ exercise</button></div></div>';
    s.exercises.forEach((ex,ei)=>{
      html+='<div class="ex"><div class="ex-head"><div><div class="ex-name">'+esc(ex.name)+'</div>'
        + '<div class="ex-meta">'+esc(ex.target)+(ex.warmup?' · warm-up: '+esc(ex.warmup):"")+(ex.notes?' · 🔧 setup':"")+'</div></div>'
        + '<div class="row"><button class="mini" data-editex="'+k+':'+ei+'">Edit</button>'
        + '<button class="mini" data-upex="'+k+':'+ei+'">&uarr;</button>'
        + '<button class="mini" data-downex="'+k+':'+ei+'">&darr;</button>'
        + '<button class="mini" data-delex="'+k+':'+ei+'" style="color:var(--bad)">&times;</button>'
        + '</div></div></div>';
    });
    html+='</div>';
  });
  document.getElementById("view").innerHTML=html;
  document.querySelectorAll("[data-addex]").forEach(b=>b.onclick=()=>openExDlg(b.dataset.addex,null));
  document.querySelectorAll("[data-editex]").forEach(b=>b.onclick=()=>{ const a=b.dataset.editex.split(":"); openExDlg(a[0],+a[1]); });
  document.querySelectorAll("[data-delex]").forEach(b=>b.onclick=()=>{
    const a=b.dataset.delex.split(":");
    if(confirm("Remove this exercise from the program?")){
      state.program.sessions[a[0]].exercises.splice(+a[1],1); save(); renderEdit(); toast("Removed");
    }
  });
  document.querySelectorAll("[data-upex]").forEach(b=>b.onclick=()=>move(b.dataset.upex,-1));
  document.querySelectorAll("[data-downex]").forEach(b=>b.onclick=()=>move(b.dataset.downex,1));
  document.querySelectorAll("[data-shareex]").forEach(b=>b.onclick=()=>shareSession(b.dataset.shareex));
  document.getElementById("importSessionBtn").onclick=()=>importSessionDlg.showModal();
  document.getElementById("addSessionBtn").onclick=()=>{
    document.getElementById("sessName").value="";
    document.getElementById("sessDay").value="Monday";
    sessionDlg.showModal();
  };
}
function move(ref,dir){
  const a=ref.split(":"); const arr=state.program.sessions[a[0]].exercises;
  const i=+a[1], j=i+dir; if(j<0||j>=arr.length) return;
  const t=arr[i]; arr[i]=arr[j]; arr[j]=t; save(); renderEdit();
}

let exDlgCtx=null;
const exDlg=document.getElementById("exDlg");
// Unique exercise names seen anywhere (program + logged history), so the Add/
// Edit dialog can offer them as pick-from-list suggestions and avoid the
// spelling variants that fragment history for the same movement.
function exerciseLibrary(){
  const set={};
  Object.keys(state.program.sessions).forEach(k=>{
    state.program.sessions[k].exercises.forEach(e=>{ if(e.name) set[e.name]=true; });
  });
  state.logs.forEach(l=>(l.entries||[]).forEach(e=>{ if(e.name) set[e.name]=true; }));
  return Object.keys(set).sort((a,b)=>a.toLowerCase()<b.toLowerCase()?-1:1);
}
function openExDlg(sessionKey,ei){
  exDlgCtx={sessionKey,ei};
  const editing = ei!=null;
  const ex = editing? state.program.sessions[sessionKey].exercises[ei]
    : {name:"",warmup:"",target:"3x8-12",cols:["Weight (kg)","Reps"],sets:3};
  document.getElementById("exNameList").innerHTML =
    exerciseLibrary().map(n=>'<option value="'+esc(n)+'"></option>').join("");
  document.getElementById("exDlgTitle").textContent= editing?"Edit exercise":"Add exercise";
  document.getElementById("exName").value=ex.name;
  document.getElementById("exWarmup").value=ex.warmup||"";
  document.getElementById("exNotes").value=ex.notes||"";
  document.getElementById("exTarget").value=ex.target||"";
  document.getElementById("exSets").value=ex.sets||3;
  document.getElementById("exCol0").value=ex.cols[0];
  document.getElementById("exCol1").value=ex.cols[1];
  document.getElementById("exCol2").value=ex.cols[2]||"";
  exMusclesTouched = false;
  renderMuscleTags(document.getElementById("exMuscles"),
    (ex.muscles&&ex.muscles.length) ? ex.muscles : classifyMuscles(ex.name));
  exDlg.showModal();
}
// Tracks whether the user has manually touched the muscle pills for the
// exercise currently open in the dialog, so re-guessing on name changes
// doesn't clobber a deliberate choice.
let exMusclesTouched = false;
document.getElementById("exMuscles").onclick=e=>{
  const b=e.target.closest("button"); if(!b) return;
  exMusclesTouched = true;
  b.classList.toggle("sel");
};
document.getElementById("exName").oninput=()=>{
  if(exMusclesTouched) return;
  renderMuscleTags(document.getElementById("exMuscles"),
    classifyMuscles(document.getElementById("exName").value));
};
document.getElementById("exCancel").onclick=()=>exDlg.close();
document.getElementById("exPresetLift").onclick=()=>{
  document.getElementById("exCol0").value="Weight (kg)";
  document.getElementById("exCol1").value="Reps";
  document.getElementById("exCol2").value="";
};
document.getElementById("exPresetRun").onclick=()=>{
  document.getElementById("exCol0").value="Distance (km)";
  document.getElementById("exCol1").value="Time (mm:ss)";
  document.getElementById("exCol2").value="Pace";
};
document.getElementById("exSave").onclick=()=>{
  const name=document.getElementById("exName").value.trim();
  if(!name){ toast("Name required"); return; }
  const cols=[document.getElementById("exCol0").value.trim()||"Weight (kg)",
              document.getElementById("exCol1").value.trim()||"Reps"];
  const c2=document.getElementById("exCol2").value.trim();
  if(c2) cols.push(c2);
  const ex={ name, warmup:document.getElementById("exWarmup").value.trim(),
    notes:document.getElementById("exNotes").value.trim(),
    target:document.getElementById("exTarget").value.trim()||"-",
    sets:Math.max(1,Math.min(12,+document.getElementById("exSets").value||3)),
    cols, muscles:readMuscleTags(document.getElementById("exMuscles")) };
  const arr=state.program.sessions[exDlgCtx.sessionKey].exercises;
  if(exDlgCtx.ei!=null) arr[exDlgCtx.ei]=ex; else arr.push(ex);
  save(); exDlg.close(); renderEdit(); toast("Saved");
};

const setDlg=document.getElementById("settingsDlg");
document.getElementById("settingsBtn").onclick=()=>{
  // Settings are person-specific: edit the selected person; switch person to edit the other.
  const i=state.activePerson;
  document.getElementById("setWho").textContent="· "+(state.people[i]||"");
  document.getElementById("pName").value=state.people[i]||"";
  renderSwatchPicker(document.getElementById("pColor"), (state.colors&&state.colors[i])||"navy");
  wireSwatchPicker(document.getElementById("pColor"));
  document.getElementById("pWeight").value=(state.weights&&state.weights[i])||"";
  document.getElementById("pGoals").value=(state.goals&&state.goals[i])||"";
  document.getElementById("pWeightLab").childNodes[0].nodeValue=possessive(state.people[i])+" bodyweight (kg)";
  document.getElementById("pGoalsLab").childNodes[0].nodeValue=possessive(state.people[i])+" goals";
  const sc=loadSync();
  document.getElementById("ghRepo").value=sc.repo||"";
  document.getElementById("ghPath").value=sc.path||"";
  document.getElementById("ghToken").value=sc.token||"";
  setSyncStatus(sc.repo&&sc.token ? "Configured for "+sc.repo+(sc.sha?" · last synced OK":"") : "Not configured.");
  document.getElementById("sugText").value="";
  renderSuggestions();
  showAppVersion();
  setDlg.showModal();
};
function renderSuggestions(){
  const list=document.getElementById("sugList"); if(!list) return;
  const open=(state.suggestions||[]).filter(s=>s&&s.status!=="done").slice().reverse();
  list.innerHTML = open.length
    ? '<div class="hint" style="margin:0 0 4px">'+open.length+' pending - synced for the dev/coach chat to action</div>'
      + open.map(s=>'<div class="log-row" style="padding:3px 0;border-bottom:1px solid var(--line);gap:8px">'
        + '<div style="font-size:13px"><b class="pill" data-sw="'+personSwatch(s.person)+'">'+esc(s.person||"?")+'</b> '+esc(s.text)+'</div>'
        + '<button class="mini" data-sugdel="'+s.id+'" title="Mark as done" style="color:var(--good)">&#10003;</button></div>').join("")
    : '<div class="hint" style="margin:0">No suggestions yet.</div>';
  list.querySelectorAll("[data-sugdel]").forEach(b=>b.onclick=()=>{
    // Mark done rather than deleting. A deleted row was resurrected by the very
    // next sync — mergeInData unions in any remote suggestion missing locally —
    // so dismissals never stuck. A local "done" is the tombstone: it hides the
    // row, blocks the re-add, and is re-asserted on every push, so it stays
    // cleared even if another device pushed an older "open" copy.
    const s=(state.suggestions||[]).find(x=>String(x.id)===b.dataset.sugdel);
    if(s){ s.status="done"; s.doneAt=new Date().toISOString(); }
    save(); renderSuggestions(); autoSync();
  });
}
document.getElementById("sugSend").onclick=()=>{
  const t=document.getElementById("sugText").value.trim();
  if(!t){ toast("Type a suggestion first"); return; }
  if(!Array.isArray(state.suggestions)) state.suggestions=[];
  state.suggestions.push({id:Date.now(), person:state.people[state.activePerson], date:todayStr(), text:t, status:"open"});
  save(); document.getElementById("sugText").value=""; renderSuggestions(); autoSync(); toast("Suggestion added");
};
// Auto-save the selected person's name / bodyweight / goals whenever the
// dialog closes (X, Done, Esc or backdrop) — no explicit Save button.
function saveSettingsPerson(){
  // Preserve any in-progress log entry: closing settings re-renders the view, and
  // without capturing first the half-filled form was wiped (“going into settings
  // then back to log clears the log”).
  captureDraft();
  const i=state.activePerson;
  if(!Array.isArray(state.weights)) state.weights=["",""];
  if(!Array.isArray(state.goals)) state.goals=["",""];
  if(!Array.isArray(state.colors)) state.colors=["",""];
  const nm=(document.getElementById("pName").value||"").trim();
  if(nm) state.people[i]=nm;
  state.colors[i]=readSwatchPicker(document.getElementById("pColor"));
  state.weights[i]=(document.getElementById("pWeight").value||"").trim();
  state.goals[i]=(document.getElementById("pGoals").value||"").trim();
  const kg=parseFloat(state.weights[i]); if(!isNaN(kg)) addBodyweight(state.people[i], todayStr(), kg);
  save(); renderPeople(); renderView();
}
setDlg.addEventListener("close", saveSettingsPerson);
document.getElementById("settingsClose").onclick=()=>setDlg.close();
document.getElementById("settingsClose2").onclick=()=>setDlg.close();
document.getElementById("guideBtn").onclick=()=>{ setDlg.close(); switchTab("help"); };
document.getElementById("ghSaveCfg").onclick=()=>{
  const cfg=loadSync();
  cfg.repo=document.getElementById("ghRepo").value.trim();
  cfg.path=document.getElementById("ghPath").value.trim()||"data.json";
  cfg.token=document.getElementById("ghToken").value.trim();
  saveSyncCfg(cfg);
  setSyncStatus(cfg.repo&&cfg.token ? "Saved. Ready to sync "+cfg.repo : "Saved (repo + token needed to sync).");
  toast("Sync settings saved");
};
document.getElementById("ghSyncBtn").onclick=()=>{
  // Persist whatever's in the fields first, then sync.
  document.getElementById("ghSaveCfg").click();
  syncNow();
};
document.getElementById("resetProgram").onclick=()=>{
  if(confirm("Reset all workouts to the default program? Your logged history stays.")){
    state.program=clone(DEFAULT_PROGRAM); curSession=state.program.order[0];
    save(); setDlg.close(); renderView(); toast("Program reset");
  }
};

const importDlg=document.getElementById("importDlg");
function exportPayload(){
  return {version:1, exportedAt:new Date().toISOString(),
    people:state.people, weights:state.weights, goals:state.goals, coaching:state.coaching,
    coachingLog:state.coachingLog, suggestions:state.suggestions, meals:state.meals,
    bodyweights:state.bodyweights, program:state.program, logs:state.logs};
}
// Merge an exported/synced payload into local state. Logs upsert by id and
// bodyweights by person+date (both idempotent). Config (program/people/
// weights/goals) is only replaced when adopting; otherwise empty goals are
// filled from the incoming copy so each person's goal propagates.
function mergeInData(data, adoptConfig){
  let added=0, updated=0;
  if(Array.isArray(data.logs)){
    var byId={}; state.logs.forEach((l,i)=>{ byId[l.id]=i; });
    data.logs.forEach(function(l){ if(!l) return; if(byId[l.id]!=null){ state.logs[byId[l.id]]=l; updated++; } else { byId[l.id]=state.logs.length; state.logs.push(l); added++; } });
  }
  if(Array.isArray(data.bodyweights)) data.bodyweights.forEach(function(b){ if(b&&b.person&&b.date&&!isNaN(parseFloat(b.kg))) addBodyweight(b.person, b.date, parseFloat(b.kg)); });
  // Coaching is authored centrally (by the MCP coach), so incoming notes win per person.
  if(data.coaching && typeof data.coaching==="object"){ if(!state.coaching) state.coaching={}; Object.keys(data.coaching).forEach(function(p){ state.coaching[p]=data.coaching[p]; }); }
  // Coaching history: union by id (every past coach write, so improvement can be tracked).
  if(Array.isArray(data.coachingLog)){ if(!Array.isArray(state.coachingLog)) state.coachingLog=[]; var cid={}; state.coachingLog.forEach(function(e){ cid[e.id]=true; }); data.coachingLog.forEach(function(e){ if(e&&e.id!=null&&!cid[e.id]){ state.coachingLog.push(e); cid[e.id]=true; } }); }
  // Improvement suggestions: union by id, and a "done" status wins from either
  // side — so resolving one in the coach/dev chat clears it on every device on
  // the next sync. (A plain union kept the local "open" copy and ignored the
  // incoming "done", so resolved suggestions stayed pending in the app.)
  if(Array.isArray(data.suggestions)){
    if(!Array.isArray(state.suggestions)) state.suggestions=[];
    var byS={}; state.suggestions.forEach(function(s){ if(s&&s.id!=null) byS[s.id]=s; });
    data.suggestions.forEach(function(s){
      if(!s||s.id==null) return;
      var cur=byS[s.id];
      if(!cur){ state.suggestions.push(s); byS[s.id]=s; }
      else if(s.status==="done" && cur.status!=="done"){ cur.status="done"; updated++; }
    });
  }
  // Meals: upsert by id, same as logs. Written by the Home Hub app (barcode /
  // camera capture) into the shared store; this app displays them. Unknown
  // fields are kept as-is so the hub can add some without a change here.
  // See docs/home-hub-link.md for the agreed shape.
  if(Array.isArray(data.meals)){
    if(!Array.isArray(state.meals)) state.meals=[];
    var byM={}; state.meals.forEach(function(m,i){ if(m&&m.id!=null) byM[m.id]=i; });
    data.meals.forEach(function(m){
      if(!m||m.id==null) return;
      if(byM[m.id]!=null){ state.meals[byM[m.id]]=m; updated++; }
      else { byM[m.id]=state.meals.length; state.meals.push(m); added++; }
    });
  }
  if(adoptConfig){
    if(data.program&&data.program.sessions) state.program=clone(data.program);
    if(Array.isArray(data.people)&&data.people.length) state.people=data.people.slice(0,2);
    if(Array.isArray(data.weights)) state.weights=data.weights.slice(0,2);
    if(Array.isArray(data.goals)) state.goals=data.goals.slice(0,2);
    curSession=sessionForDate(curDate)||state.program.order[0];
  } else if(Array.isArray(data.goals)){
    data.goals.forEach(function(g,i){ if(g && !((state.goals[i]||"").trim())) state.goals[i]=g; });
  }
  return {added, updated};
}
// One-pass current bests (max top-set weight) per lifting exercise for a person.
function personPRs(person){
  const best={};
  state.logs.filter(l=>l.person===person).forEach(function(l){
    (l.entries||[]).forEach(function(e){
      if(!isLifting(e)) return;
      const wu=e.warmup||[];
      let top=-Infinity; e.rows.forEach(function(r,ri){ if(wu.indexOf(ri)>=0) return; const w=parseFloat(r[0]); if(!isNaN(w)&&w>top) top=w; });
      if(top>-Infinity && (!(e.name in best) || top>best[e.name].kg)) best[e.name]={kg:top, date:l.date};
    });
  });
  return best;
}
// Epley estimated 1RM.
function epley(w, reps){ return (isNaN(w)||isNaN(reps)||reps<1) ? NaN : w*(1+reps/30); }
// Per-exercise current bests for a person: heaviest working set, the reps on
// it, its estimated 1RM, and when. Warm-up sets excluded.
function personRecords(person){
  const best={};
  state.logs.filter(l=>l.person===person).forEach(function(l){
    (l.entries||[]).forEach(function(e){
      if(!isLifting(e)) return;
      const wu=e.warmup||[];
      e.rows.forEach(function(r,ri){
        if(wu.indexOf(ri)>=0) return;
        const w=parseFloat(r[0]), reps=parseInt(r[1],10);
        if(isNaN(w)) return;
        if(!(e.name in best) || w>best[e.name].kg) best[e.name]={kg:w, reps:isNaN(reps)?null:reps, date:l.date};
      });
    });
  });
  return best;
}
function rowPlain(cols, r){
  cols=cols||[];
  const lift=/kg|assist/i.test(cols[0]||"") && /rep/i.test(cols[1]||"");
  const n=Math.max(cols.length, r.length), vals=[];
  for(let i=0;i<n;i++) vals.push(r[i]==null?"":String(r[i]).trim());
  if(lift) return vals[0]+(vals[1]!==""?" x "+vals[1]:"");
  const ne=vals.filter(v=>v!==""); return ne.length?ne.join(" / "):"-";
}
// Markdown coaching brief for one person: goals + bodyweight + PRs + recent
// sessions, with a coach preamble. Paste into Claude, or drop into Obsidian.
function coachBrief(person){
  const i=state.people.indexOf(person);
  const goal=((state.goals&&state.goals[i])||"").trim();
  const bw=bwFor(person), latest=bw.length?bw[bw.length-1]:null;
  const logs=state.logs.filter(l=>l.person===person)
    .sort((a,b)=> a.date<b.date?1:a.date>b.date?-1:(b.id-a.id));
  const prs=personPRs(person);
  let md="# Coaching brief - "+person+"\n\n";
  md+="> You are "+possessive(person)+" strength & conditioning coach. Review the training below "
    + "against the goals and give specific, actionable feedback and the next session's focus.\n\n";
  md+="## Goals\n"+(goal||"_none set_")+"\n\n";
  md+="## Bodyweight\n"+(latest?("Latest **"+latest.kg+" kg** ("+relTime(latest.date)+")"
    + (bw.length>1?"; "+bw.length+" entries logged":"")):"_none logged_")+"\n\n";
  const prNames=Object.keys(prs).sort();
  md+="## Current bests\n"+(prNames.length? prNames.map(n=>"- **"+n+"** - "+prs[n].kg+" kg ("+relTime(prs[n].date)+")").join("\n") : "_none yet_")+"\n\n";
  md+="## Recent sessions (latest "+Math.min(8,logs.length)+")\n";
  if(!logs.length) md+="_none logged_\n";
  logs.slice(0,8).forEach(function(l){
    const meta=[l.date]; if(l.difficulty) meta.push("difficulty "+l.difficulty+"/10");
    if(l.volume) meta.push(l.volume.toLocaleString()+" kg"); if(l.durationSec) meta.push(fmtDuration(l.durationSec));
    md+="\n### "+l.sessionName+" - "+meta.join(" · ")+"\n";
    (l.entries||[]).forEach(function(e){ var wu=e.warmup||[];
      md+="- "+e.name+(e.pr?" 🥇":"")+": "+(e.rows||[]).map(function(r,ri){ var s=rowPlain(e.cols||[],r); return wu.indexOf(ri)>=0?s+" (warm-up)":s; }).join(", ")+"\n"; });
    if(l.feedback) md+="- _Note:_ "+l.feedback+"\n";
  });
  return md;
}
function exportCoachBrief(){
  const person=state.people[state.activePerson];
  const md=coachBrief(person);
  const fname="coach-brief-"+person.replace(/\s+/g,"-")+"-"+todayStr()+".md";
  try{
    const blob=new Blob([md],{type:"text/markdown"});
    const url=URL.createObjectURL(blob);
    const a=document.createElement("a"); a.href=url; a.download=fname;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),2000);
  }catch(e){}
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(md).then(()=>toast("Coach brief copied + saved"), ()=>toast("Coach brief saved"));
  } else toast("Coach brief saved");
}
function exportData(){
  const text=JSON.stringify(exportPayload(),null,2);
  const fname="training-data-"+todayStr()+".json";
  try{
    const blob=new Blob([text],{type:"application/json"});
    const url=URL.createObjectURL(blob);
    const a=document.createElement("a"); a.href=url; a.download=fname;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),2000);
    state.lastExportAt=new Date().toISOString(); save();
    toast("Exported "+fname);
  }catch(e){
    setDlg.close();
    document.getElementById("importText").value=text;
    importDlg.showModal();
    toast("Download blocked - copy this text to transfer");
  }
}
document.getElementById("importCancel").onclick=()=>importDlg.close();
document.getElementById("importFile").onchange=e=>{
  const f=e.target.files[0]; if(!f) return;
  const r=new FileReader();
  r.onload=()=>{ document.getElementById("importText").value=r.result; };
  r.readAsText(f);
};
document.getElementById("importConfirm").onclick=()=>{
  let data; try{ data=JSON.parse(document.getElementById("importText").value); }
  catch(e){ toast("Couldn't read that data"); return; }
  if(!data || !Array.isArray(data.logs)){ toast("No logs found in import"); return; }
  const res=mergeInData(data, document.getElementById("importAdopt").checked);
  save(); importDlg.close(); setDlg.close(); renderPeople(); renderView();
  toast(res.added+" added, "+res.updated+" updated");
};
document.getElementById("exportBtn").onclick=()=>exportData();
document.getElementById("importBtn").onclick=()=>{ setDlg.close(); importDlg.showModal(); };
document.getElementById("coachBriefBtn").onclick=()=>exportCoachBrief();

// ---- Share a session (routine only - no personal numbers) ----
// Travels as plain text through the phone's native share sheet, since there's
// no backend connecting separate installs. Recipient pastes it back in via
// Import shared session, which decodes and adds it as a new program session.
function slugify(s){ return String(s).toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/(^-+|-+$)/g,"") || "session"; }
function sessionShareCode(sessionKey){
  const s=state.program.sessions[sessionKey];
  const payload={type:"tt-session", v:1, name:s.name, day:s.day||"", exercises:clone(s.exercises)};
  return b64encode(JSON.stringify(payload));
}
function shareSession(sessionKey){
  const s=state.program.sessions[sessionKey];
  const text="🏋️ "+s.name+" workout - paste this into Training Tracker → Program → Import shared session:\n\n"+sessionShareCode(sessionKey);
  if(navigator.share){
    navigator.share({text}).catch(()=>{}); // user cancelling the share sheet isn't an error
  } else if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(text).then(()=>toast("Share code copied - paste it to them"), ()=>toast("Couldn't copy"));
  } else toast("Sharing isn't supported in this browser");
}
const importSessionDlg=document.getElementById("importSessionDlg");
document.getElementById("importSessionCancel").onclick=()=>importSessionDlg.close();
document.getElementById("importSessionConfirm").onclick=()=>{
  // The pasted text may be the whole shared message (friendly intro line +
  // code), not just the code itself - the code is always the last token.
  const raw=document.getElementById("importSessionText").value.trim();
  const tokens=raw.split(/\s+/).filter(Boolean);
  const candidate=tokens.length?tokens[tokens.length-1]:raw;
  let payload;
  try{ payload=JSON.parse(b64decode(candidate)); }
  catch(e){ toast("Couldn't read that code"); return; }
  if(!payload || payload.type!=="tt-session" || !Array.isArray(payload.exercises)){ toast("Not a valid shared session"); return; }
  let key=slugify(payload.name), n=2;
  while(state.program.sessions[key]){ key=slugify(payload.name)+"-"+n; n++; }
  state.program.sessions[key]={name:payload.name||"Shared session", day:payload.day||"", exercises:payload.exercises};
  state.program.order.push(key);
  save(); document.getElementById("importSessionText").value=""; importSessionDlg.close(); renderEdit();
  toast("Added "+(payload.name||"session"));
};
const sessionDlg=document.getElementById("sessionDlg");
document.getElementById("sessCancel").onclick=()=>sessionDlg.close();
document.getElementById("sessSave").onclick=()=>{
  const name=(document.getElementById("sessName").value||"").trim();
  if(!name){ toast("Name required"); return; }
  const day=document.getElementById("sessDay").value;
  let key=slugify(name), n=2;
  while(state.program.sessions[key]){ key=slugify(name)+"-"+n; n++; }
  state.program.sessions[key]={name, day, exercises:[]};
  state.program.order.push(key);
  save(); sessionDlg.close(); renderEdit();
  toast("Added "+name);
};

// ---- Cloud sync (GitHub Contents API) ----
const SYNC_KEY="flLiveTracker_sync_v1";
function loadSync(){ try{ return JSON.parse(localStorage.getItem(SYNC_KEY))||{}; }catch(e){ return {}; } }
function saveSyncCfg(s){ localStorage.setItem(SYNC_KEY, JSON.stringify(s)); }
function ghHeaders(token){ return {"Authorization":"Bearer "+token, "Accept":"application/vnd.github+json", "X-GitHub-Api-Version":"2022-11-28"}; }
function b64encode(str){ return btoa(unescape(encodeURIComponent(str))); }
function b64decode(str){ return decodeURIComponent(escape(atob(String(str).replace(/\s/g,"")))); }
function ghUrl(cfg){ return "https://api.github.com/repos/"+cfg.repo+"/contents/"+cfg.path; }
function ghGetFile(cfg){
  return fetch(ghUrl(cfg), {headers:ghHeaders(cfg.token)}).then(function(r){
    if(r.status===404) return {exists:false};
    if(!r.ok) throw new Error("read "+r.status);
    return r.json().then(function(j){ return {exists:true, sha:j.sha, json:JSON.parse(b64decode(j.content))}; });
  });
}
function ghPutFile(cfg, payloadStr, sha){
  const body={message:"Sync training data "+new Date().toISOString(), content:b64encode(payloadStr)};
  if(sha) body.sha=sha;
  return fetch(ghUrl(cfg), {method:"PUT", headers:ghHeaders(cfg.token), body:JSON.stringify(body)}).then(function(r){
    if(!r.ok) return r.text().then(function(t){ throw new Error("write "+r.status); });
    return r.json();
  });
}
function setSyncStatus(msg){ const el=document.getElementById("ghStatus"); if(el) el.textContent=msg; }
// Pull remote -> merge (logs+bodyweights union) -> push merged local back.
// quiet=true for automatic syncs (on save / on open): no toasts, best-effort.
function syncNow(quiet){
  const cfg=loadSync();
  if(!cfg.repo || !cfg.token){ if(!quiet) toast("Add your GitHub repo + token first"); return Promise.resolve(); }
  cfg.path=cfg.path||"data.json";
  setSyncStatus("Syncing…");
  return ghGetFile(cfg).then(function(remote){
    let merged={added:0,updated:0};
    if(remote.exists && remote.json){ merged=mergeInData(remote.json, false); save(); } // keep pulled data even if the push fails
    return ghPutFile(cfg, JSON.stringify(exportPayload(),null,2), remote.exists?remote.sha:null)
      .then(function(res){
        cfg.sha=res&&res.content&&res.content.sha; saveSyncCfg(cfg);
        save(); renderPeople(); renderView();
        setSyncStatus("Synced "+new Date().toLocaleTimeString()+" · +"+merged.added+" new, "+merged.updated+" updated");
        if(!quiet) toast("Synced"); else if(merged.added||merged.updated) toast("Synced · "+(merged.added+merged.updated)+" update"+(merged.added+merged.updated===1?"":"s")+" pulled");
      });
  }).catch(function(e){
    const m=String(e.message||e);
    setSyncStatus("Sync failed ("+(m.indexOf("401")>=0||m.indexOf("403")>=0?"check token/repo access":m)+")");
    if(!quiet) toast("Sync failed"); // stay quiet on auto-sync (e.g. offline) — it retries next time
  });
}
// Best-effort background sync — only if configured. Used after save and on open.
function autoSync(){ const c=loadSync(); if(c.repo && c.token) syncNow(true); }

function renderHelp(){
  function card(title, body){ return '<div class="card"><div class="sec-title">'+title+'</div>'+body+'</div>'; }
  function p(t){ return '<p style="margin:0 0 9px">'+t+'</p>'; }
  var h='';
  h+='<div class="card"><h3 style="margin-bottom:6px">How to use this tracker</h3>'
    +'<div class="hint" style="margin-bottom:0">A training + health log for up to two people sharing a device. Log each workout and it tells you what to aim for next time. Works offline, saves only on this device - nothing sent anywhere.</div></div>';

  h+=card('Home',
      p('The app opens on <b>Home</b> - your at-a-glance hub for the selected person: <b>today\'s session</b> (with a <b>Log it</b> shortcut), any <b>🧠 Coach</b> note, quick tiles (sessions &amp; volume this week, latest bodyweight with its trend, total sessions), your <b>last session</b> and <b>last run</b>, a <b>bodyweight trend</b> mini-chart, and your <b>goals</b>. The arrows jump to the full <b>History</b>, <b>Body</b> etc.'));

  h+=card('1 &middot; Pick who you are',
      p('A brand-new install starts blank - no accounts, no program. <b>Create your account</b> with a name and a colour swatch to get going; nothing else is needed. A second person can join the same device later via <b>+ Add</b> next to the name toggle (or skip it and stay solo).')
     +p('Use the <b>name toggle</b> top-right to switch. Each account has its own colour, chosen at creation (or changed later in Settings) - the whole app\'s accent follows whoever\'s selected. Everything you log and every suggestion belongs to that person. You can switch person <b>mid-entry without losing</b> what you\'ve typed - handy for logging both of you from one phone; a toast confirms when your part is restored.')
     +p('The <b>⚙️ gear</b> (top-right) opens <b>Settings</b> - switch <b>dark / light</b> theme, open this <b>Guide</b>, change your <b>name, colour</b> and <b>bodyweight</b>, and manage export / import / cloud sync. The selected person\'s latest weight shows under the title.'));

  h+=card('2 &middot; Log a workout',
      p('From <b>Home</b>, tap <b>Log it →</b> to open the log, then choose the session and date. The date auto-picks the right session for that weekday - and a late-night session (before ~5am) counts as the <b>previous</b> training day.')
     +p('Type <b>weight</b> and <b>reps</b> per set (phones show a number pad). Enter the first set\'s weight and the rest auto-fill to match. Tick a set\'s <b>checkbox</b> when done: it fills empty reps to the top of the target range, and shows a gold <b>🥇 medal</b> right away if that weight beats your best. Use <b>+ set</b> / <b>- set</b> to change set count.')
     +p('The <b>Last</b> column shows what that person did last time (as "3 days ago" - hover for the date). A <b>🕑 Most recent</b> chip appears when you did that movement more recently in another session. Warm-ups written as a percentage (e.g. "40%x8") show the actual kg for <b>you</b> - worked out from your own last top set for that exercise (and from today\'s weight once you type one), so Daniel and Cerys each get their own warm-up numbers.')
     +p('Tap the <b>🔧</b> next to an exercise name to open its <b>machine settings</b> (seat height, pins). You can edit them <b>mid-session</b> and they\'re saved to the program for next time; the wrench stays highlighted when settings are stored.')
     +p('<b>Tap a set number</b> to mark that set as a <b>warm-up</b> (it shows <b>W</b>). Warm-up sets are excluded from your volume total, PRs and the muscle map - so they don\'t inflate your numbers.'));

  h+=card('3 &middot; Time it, rate it, save',
      p('The <b>timer</b> at the top starts when you begin entering (or tap Start), and is saved with the session; Pause/Reset as needed.')
     +p('Tap a <b>difficulty</b> 1-10 and add any <b>notes</b>. Hit <b>Save session</b>: you get total volume (with a fun comparison), any <b>PRs</b>, and a <b>muscle map</b> of what you worked. Guidance for next time comes from your <b>🧠 Coach</b> notes rather than an auto-generated plan.'));

  h+=card('4 &middot; Cardio &amp; running',
      p('On a <b>cardio day</b> the easiest thing is to just <b>log &amp; save</b> - a banner reminds you. If you wear your <b>Garmin</b>, the run\'s distance, per-km <b>splits</b>, pace and ♥ HR fill in automatically once it syncs; the run starts as a single blank row and shows a <b>🏃 Last run</b> summary to beat. Prefer to enter it yourself? Type the splits (pace is computed for you) or import a file.')
     +p('On a running exercise, <b>⬆ Import run (TCX/GPX)</b> pulls a run exported from Garmin or Strava straight into the splits - export the file on your laptop, then import.')
     +p('<b>Garmin auto-link (⌚):</b> when you save a cardio session it\'s tagged <i>⌚ awaiting run…</i>; the Garmin sync on the laptop then finds that day\'s run and adds the extra info - <b>heart rate, cadence, elevation, calories, moving time, training effect</b>, and per-km splits if you left them blank - shown as a <b>⌚ Garmin</b> line in History. It never overwrites what you typed. (Set up in <code>mcp-garmin</code>; needs the laptop.)'));

  h+=card('5 &middot; History, Progress &amp; Records',
      p('<b>History</b> opens with a <b>This week</b> summary for the selected person - total volume, session count, a muscle heatmap of what you\'ve hit, and a weekly-volume bar chart - then lists every saved session (newest first); filter by person, tap <b>View</b> for full detail, or delete. <b>Runs</b> show their <b>distance, time, pace and ♥ heart rate</b> right on the row, and open to a <b>splits table</b> (each lap\'s pace and HR, with a totals line) plus the <b>⌚ Garmin</b> extras (cadence, elevation, calories, training effect, VO₂).')
     +p('<b>Progress</b> shows the selected person\'s <b>current bests</b> (weight, reps and estimated 1RM per exercise) at the top, then charts your top set for any exercise over time with both people on one graph.'));

  h+=card('6 &middot; Body, goals &amp; bodyweight',
      p('The <b>Body</b> tab tracks each person\'s bodyweight over time with a trend chart. Add a weight by hand, or <b>⬆ Import from scale (CSV)</b> a file exported from your scale app (e.g. 1byone Health) - it finds the date and weight columns automatically.')
     +p('Set your <b>goals</b> in the gear menu; they show at the top of the Body tab and travel with your data, so a coach (or Claude) can see what you\'re working toward.')
     +p('For AI coaching, the gear menu\'s <b>Coach brief (Markdown)</b> button bundles the selected person\'s goals, PRs, bodyweight and recent sessions into a summary you can paste into Claude (or drop into Obsidian).')
     +p('When a coach sends you notes, they show as teal <b>🧠 Coach</b> cards on <b>Home</b> and at the top of the <b>Log</b> tab: a note for <b>today’s session</b>, an optional <b>general</b> note, and a <b>🧠 Coach</b> cue with a next step on each exercise. Every past note is kept under <b>🧠 Coaching history</b> on Home, so you (and the coach) can see how the advice has changed and whether it worked. Tap <b>Sync now</b> to pull the latest coaching.'));

  h+=card('7 &middot; Edit the program',
      p('<b>Edit Program</b> lets you add / edit / reorder / remove exercises. Pick a name from the <b>suggestions list</b> to avoid duplicate spellings (start typing to search, or just type a new one). Set a <b>target</b>, a <b>warm-up</b> (a <b>%</b> is best - it scales to each person\'s own last top set; a fixed weight is the same for both of you), and <b>setup notes</b> (seat height, pins - editable straight from the log form too). Use the <b>Lifting</b> / <b>Running</b> presets for the column labels, or add a 3rd column.')
     +p('<b>&#10133; Add session</b> creates a brand-new workout day (name + weekday) - a blank account starts with no sessions at all, so this is the first thing to do there.')
     +p('<b>Works</b> tags which muscles an exercise counts toward on the heatmap - guessed from the name automatically, but tap to add/remove any that got missed (handy for oddly-named exercises).')
     +p('<b>&#128279; Share</b> on a session sends its exercise list (no personal numbers) through your phone\'s share sheet - useful if someone else you know is using their own copy of the app. They paste the code back in via <b>&#128229; Import shared session</b> at the top of this tab to add it as a new session on their program.')
     +p('Program edits only affect future logging; past history is untouched. <b>Reset program to default</b> (gear menu) restores the default workouts and keeps your logs.'));

  h+=card('8 &middot; Your data, backups &amp; sync',
      p('Everything saves <b>on this device</b>. Gear menu &rarr; <b>Export</b> saves a file with everything; <b>Import / merge</b> on another device adds it in, merged by unique ID so nothing duplicates.')
     +p('<b>Cloud sync (GitHub)</b> is optional and free: set a private repo + access token in the gear menu once. After that it syncs <b>automatically</b> - when you open the app and after every save - so both of you stay up to date and your coach sees new sessions without you doing anything. (<b>Sync now</b> is still there for a manual pull.) It doubles as an off-device <b>backup</b>; the token is stored only on this device and never included in exports.')
     +p('It\'s an installable app: open in your phone browser and <b>Add to Home Screen</b>, then always open it from that icon. It works <b>offline</b>.'));

  h+=card('Quick tips',
      p('&bull; Beat the <b>Last</b> numbers - even one extra rep counts.')
     +p('&bull; Tick sets as you go to catch PRs live and auto-fill reps.')
     +p('&bull; Export regularly as a backup, and to keep both of you in sync.')
     +p('&bull; Spotted a bug or have an idea? Jot it in the gear menu under <b>💡 Improve the app</b> - it syncs to the dev backlog so it isn\'t forgotten.'));

  document.getElementById("view").innerHTML=h;
}

const VOL_REFS=[
  {n:"house cats",w:4.5,e:"🐱"},
  {n:"bulldogs",w:25,e:"🐶"},
  {n:"baby elephants",w:110,e:"🐘"},
  {n:"grizzly bears",w:360,e:"🐻"},
  {n:"grand pianos",w:480,e:"🎹"},
  {n:"horses",w:550,e:"🐴"},
  {n:"dairy cows",w:750,e:"🐄"},
  {n:"compact cars",w:1300,e:"🚗"},
  {n:"hippos",w:1500,e:"🦛"},
  {n:"rhinos",w:2300,e:"🦏"},
  {n:"African elephants",w:6000,e:"🐘"},
  {n:"T. rexes",w:8000,e:"🦖"},
  {n:"London buses",w:12000,e:"🚌"},
  {n:"whale sharks",w:19000,e:"🐋"}
];
function volCompare(total){
  var refs=VOL_REFS.slice().sort(function(a,b){return a.w-b.w;});
  var pick=refs[0];
  for(var i=0;i<refs.length;i++){ if(total/refs[i].w>=1.2) pick=refs[i]; }
  var count=total/pick.w;
  var cstr = count>=10? String(Math.round(count)) : String(Math.round(count*10)/10);
  return {text:"about "+cstr+" "+pick.n, emoji:pick.e};
}
function lerp(a,b,t){return Math.round(a+(b-a)*t);}
function muscleColor(c,max){
  if(!c||!max) return ""; // unworked: clear inline fill, fall back to CSS --musc-base
  // Neutral intensity heat ramp (warm amber -> hot red as the set count rises).
  // Person-independent on purpose: the map reads as "how hard" not "who", so it
  // doesn't clash with the per-person accents. Endpoints suit light + dark cards.
  var t=c/max, lo=[255,206,110], hi=[222,60,45];
  return "rgb("+lerp(lo[0],hi[0],t)+","+lerp(lo[1],hi[1],t)+","+lerp(lo[2],hi[2],t)+")";
}
const MUSCLE_LABELS = {quads:"Quads",glutes:"Glutes",hamstrings:"Hamstrings",adductors:"Adductors",
  calves:"Calves",chest:"Chest",delts:"Delts",triceps:"Triceps",lats:"Lats",traps:"Traps",
  biceps:"Biceps",forearms:"Forearms",abs:"Abs",lowerback:"Lower back"};
// Renders the exercise-dialog muscle-tag pills with `selected` pre-toggled.
function renderMuscleTags(container, selected){
  container.innerHTML = Object.keys(MUSCLE_LABELS).map(function(k){
    return '<button type="button" data-m="'+k+'" class="'+(selected.indexOf(k)>=0?"sel":"")+'">'+MUSCLE_LABELS[k]+'</button>';
  }).join("");
}
function readMuscleTags(container){
  return Array.prototype.slice.call(container.querySelectorAll("button.sel")).map(function(b){ return b.dataset.m; });
}
function classifyMuscles(name){
  var n=String(name).toLowerCase(), m=[];
  function add(){for(var i=0;i<arguments.length;i++){if(m.indexOf(arguments[i])<0)m.push(arguments[i]);}}
  if(/squat|leg press|lunge/.test(n)) add("quads","glutes");
  if(/leg extension/.test(n)) add("quads");
  if(/(lying|seated|leg)\s*curl/.test(n) || /hamstring/.test(n)) add("hamstrings");
  if(/deadlift|romanian|rdl|good ?morning/.test(n)) add("hamstrings","glutes");
  if(/abduction|glute|hip thrust/.test(n)) add("glutes");
  if(/adduction|adductor/.test(n)) add("adductors");
  if(/calf|calves/.test(n)) add("calves");
  if(/bench|incline|crossover|fly|pec|push.?up/.test(n) || (/chest/.test(n) && !/row/.test(n))) add("chest");
  if(/press/.test(n) && !/overhead|shoulder|leg|ohp|military|chest/.test(n)) add("chest");
  if(/overhead press|shoulder press|ohp|military/.test(n)) add("delts");
  if(/lateral raise|side raise|rear delt|face pull|reverse fly/.test(n)) add("delts");
  if(/tricep|pushdown|skull|overhead ext/.test(n)) add("triceps");
  if(/pulldown|pull.?up|chin.?up/.test(n)) add("lats");
  if(/row/.test(n)) add("traps");
  if(/curl/.test(n) && !/leg|lying|seated/.test(n)) add("biceps");
  if(/hammer|forearm|wrist/.test(n)) add("forearms");
  if(/crunch|plank|sit.?up|leg raise|hanging/.test(n)) add("abs");
  if(/back extension|hyperextension|lower back/.test(n)) add("lowerback");
  return m;
}
// Muscle set-counts (warm-ups excluded) from a list of entries, and from logs.
function muscleSetsFromEntries(entries){
  var m={};
  (entries||[]).forEach(function(en){
    var ms=(en.muscles&&en.muscles.length) ? en.muscles : classifyMuscles(en.name||"");
    var sets=((en.rows&&en.rows.length)||0)-((en.warmup&&en.warmup.length)||0);
    ms.forEach(function(mk){ m[mk]=(m[mk]||0)+sets; });
  });
  return m;
}
function muscleSetsForLogs(logs){
  var m={};
  logs.forEach(function(l){ var mm=muscleSetsFromEntries(l.entries); for(var k in mm){ m[k]=(m[k]||0)+mm[k]; } });
  return m;
}
// Shade an SVG muscle map (by data-muscle) from a set-count map; returns the max.
function paintMuscleMap(svgEl, museSets){
  var maxc=0; for(var k in museSets){ if(museSets[k]>maxc) maxc=museSets[k]; }
  svgEl.querySelectorAll(".musc").forEach(function(el){
    var mk=el.getAttribute("data-muscle"); var cval=museSets[mk]||0;
    el.style.fill = muscleColor(cval,maxc);
    var ti=el.querySelector("title");
    if(ti){ var base=ti.textContent.replace(/:.*$/,""); ti.textContent=base+": "+cval+" set"+(cval===1?"":"s"); }
  });
  return maxc;
}
function showSaveSummary(volume, prs, entries){
  var prHtml = prs.length
    ? prs.map(function(pr){return '<div style="background:#fff7e0;border:1px solid #f0dca0;border-radius:8px;padding:6px 10px;margin:6px 0;font-size:13.5px;font-weight:700;color:#8a6d1a">🥇 New PR &middot; '+esc(pr.name)+' &middot; '+pr.weight+' kg</div>';}).join("")
    : '';
  if(volume>0){
    var c=volCompare(volume);
    document.getElementById("saveEmoji").textContent=c.emoji;
    document.getElementById("saveVol").textContent=volume.toLocaleString()+" kg moved";
    document.getElementById("saveCompare").textContent="That's "+c.text+"!";
  } else {
    document.getElementById("saveEmoji").textContent="🏃";
    document.getElementById("saveVol").textContent="Session saved";
    document.getElementById("saveCompare").textContent="Great conditioning work!";
  }
  var muscleSets=muscleSetsFromEntries(entries);
  var wrap=document.getElementById("muscleWrap");
  if(paintMuscleMap(document.getElementById("muscleSvg"), muscleSets)>0) wrap.style.display="";
  else wrap.style.display="none";
  document.getElementById("savePRs").innerHTML=prHtml;
  document.getElementById("saveDlg").showModal();
}
document.getElementById("saveDlgOk").onclick=function(){ document.getElementById("saveDlg").close(); };

// Home dashboard — the hub landing: greeting + today's session, coach card,
// this-week stat tiles, last session, last run, bodyweight trend, goals.
// Reuses existing helpers; links out to the detailed tabs.
let homeChart=null;
function renderHome(){
  const p=state.people[state.activePerson];
  const pc = personSwatch(p);
  const thisWk=weekMonday(trainingDateStr());
  const pLogs=[...state.logs].filter(l=>l.person===p).sort((a,b)=> (a.date<b.date?1:a.date>b.date?-1:b.id-a.id));
  const wkLogs=pLogs.filter(l=>weekMonday(l.date)===thisWk);
  const wkVol=wkLogs.reduce((t,l)=>t+(l.volume||0),0);
  const last=pLogs[0];
  const lastRun=pLogs.find(l=>(l.entries||[]).some(e=>isRunning(e)));
  const bw=bwFor(p);
  const latest=bw.length? bw[bw.length-1] : null;
  let bwDelta="";
  if(bw.length>=2){ const d=Math.round((bw[bw.length-1].kg-bw[bw.length-2].kg)*10)/10; bwDelta = d>0?'▲ '+d:d<0?'▼ '+Math.abs(d):'-'; }
  const coach=(state.coaching&&state.coaching[p])||{};
  const goal=(state.goals&&state.goals[state.activePerson])||"";
  const sess=state.program.sessions[curSession];
  let niceDate; try{ niceDate=new Date().toLocaleDateString(undefined,{weekday:"long",day:"numeric",month:"long"}); }catch(e){ niceDate=todayStr(); }

  let html='<div class="card">'
    + '<div class="sec-title" style="margin:0">👋 '+esc(possessive(p))+' hub</div>'
    + '<div class="home-greet">'+esc(niceDate)+'</div>'
    + '<div class="flex-between" style="align-items:center;gap:10px;flex-wrap:wrap;margin-top:10px">'
    + '<div>Today’s session: <b>'+esc(sess?sess.name:"-")+'</b>'+(sess?' <span class="hint" style="margin:0">· '+esc(sess.day)+'</span>':"")+'</div>'
    + '<button class="btn btn-primary" id="homeLogBtn">Log it →</button>'
    + '</div></div>';

  const coachSessNote=(coach.bySession && sess && coach.bySession[sess.name])||"";
  if(coachSessNote){
    html+='<div class="card coach-card"><div class="sec-title">🧠 Coach · '+esc(sess.name)+(coach.updated?' &middot; '+relTime(coach.updated):"")+'</div>'
      + '<div style="white-space:pre-wrap">'+esc(coachSessNote)+'</div></div>';
  }
  if(coach.overall){
    html+='<div class="card coach-card"><div class="sec-title">🧠 Coach'+(coach.updated?' &middot; '+relTime(coach.updated):"")+'</div>'
      + '<div style="white-space:pre-wrap">'+esc(coach.overall)+'</div></div>';
  }

  html+='<div class="tiles">'
    + '<div class="tile"><div class="big">'+wkLogs.length+'</div><div class="lbl">sessions this week</div></div>'
    + '<div class="tile"><div class="big">'+wkVol.toLocaleString()+'</div><div class="lbl">kg volume this week</div></div>'
    + '<div class="tile"><div class="big">'+(latest? latest.kg+'<span class="sub"> kg</span>':'-')+'</div><div class="lbl">bodyweight'+(bwDelta?' · '+bwDelta:'')+'</div></div>'
    + '<div class="tile"><div class="big">'+pLogs.length+'</div><div class="lbl">sessions logged</div></div>'
    + '</div>';

  if(last){
    const pr=(last.entries||[]).some(e=>e.pr);
    html+='<div class="card"><div class="flex-between"><div class="sec-title" style="margin:0">Last session</div>'
      + '<button class="mini" data-home-go="history">History →</button></div>'
      + '<h3 style="margin:8px 0 2px">'+esc(last.sessionName)+(pr?' 🥇':'')+' <span class="pill" data-sw="'+pc+'">'+relTime(last.date)+'</span></h3>'
      + '<div class="ex-meta">'+esc(last.date)+(last.difficulty?' · difficulty '+last.difficulty+'/10':"")+(last.volume?' · '+last.volume.toLocaleString()+' kg':"")+(last.durationSec?' · ⏱ '+fmtDuration(last.durationSec):"")+garminStatus(last)+'</div>'
      + '</div>';
  } else {
    html+='<div class="card empty">No sessions logged yet.<br>Tap <b>Log it</b> on <b>Home</b> to record your first one.</div>';
  }

  if(lastRun){
    const runEntry=(lastRun.entries||[]).find(e=>isRunning(e));
    const km=(runEntry.rows||[]).reduce((t,r)=>t+(parseFloat(r[0])||0),0);
    const g=lastRun.garmin||{};
    const bits=[];
    if(km) bits.push((Math.round(km*100)/100)+' km');
    if(lastRun.durationSec) bits.push('⏱ '+fmtDuration(lastRun.durationSec));
    if(g.avg_hr!=null) bits.push('❤ '+g.avg_hr);
    html+='<div class="card"><div class="flex-between"><div class="sec-title" style="margin:0">🏃 Last run</div>'
      + '<button class="mini" data-home-go="history">History →</button></div>'
      + '<h3 style="margin:8px 0 2px">'+esc(lastRun.sessionName)+' <span class="pill" data-sw="'+pc+'">'+relTime(lastRun.date)+'</span></h3>'
      + '<div class="ex-meta">'+(bits.length?bits.map(esc).join(' · '):'-')+garminStatus(lastRun)+'</div></div>';
  }

  if(bw.length>=2){
    html+='<div class="card"><div class="flex-between"><div class="sec-title" style="margin:0">⚖️ Bodyweight trend</div>'
      + '<button class="mini" data-home-go="body">Body →</button></div>'
      + '<div class="chart-box" style="height:150px"><canvas id="homeBwChart"></canvas></div></div>';
  }

  html+='<div class="card"><div class="sec-title">🎯 '+esc(possessive(p))+' goals</div>'
    + (goal ? '<div style="white-space:pre-wrap">'+esc(goal)+'</div>'
            : '<div class="hint" style="margin:0">No goals set yet - add them via the gear menu so coaching can target them.</div>')
    + '</div>';

  // Coaching history — every past coach write, so improvement can be tracked over time.
  const chist=(state.coachingLog||[]).filter(e=>e&&e.person===p).sort((a,b)=> (a.id<b.id?1:a.id>b.id?-1:0));
  if(chist.length){
    html+='<details class="card coach-hist"><summary class="sec-title">🧠 Coaching history · '+chist.length+'</summary>'
      + chist.slice(0,15).map(e=>{
          const parts=[];
          if(e.overall) parts.push('<div><b>Overall:</b> '+esc(e.overall)+'</div>');
          if(e.bySession) Object.keys(e.bySession).forEach(k=> parts.push('<div><b>'+esc(k)+':</b> '+esc(e.bySession[k])+'</div>'));
          if(e.byExercise) Object.keys(e.byExercise).forEach(k=> parts.push('<div>'+esc(k)+' - '+esc(e.byExercise[k])+'</div>'));
          return '<div class="hist-entry"><div class="ex-meta">'+esc(e.date||"")+'</div>'+(parts.join('')||'<div class="hint" style="margin:0">(no note)</div>')+'</div>';
        }).join('')
      + '</details>';
  }

  document.getElementById("view").innerHTML=html;

  const go=tab=>switchTab(tab);
  const lb=document.getElementById("homeLogBtn"); if(lb) lb.onclick=()=>go("log");
  document.querySelectorAll("[data-home-go]").forEach(b=>b.onclick=()=>go(b.dataset.homeGo));

  if(bw.length>=2){
    const i=state.people.indexOf(p);
    const dark=document.documentElement.getAttribute("data-theme")==="dark";
    const col=swatchColor(state.colors[i],dark);
    const tickCol=dark?"#9aa3b2":"#697086", gridCol=dark?"rgba(255,255,255,.09)":"rgba(20,30,55,.08)";
    if(homeChart) homeChart.destroy();
    homeChart=new Chart(document.getElementById("homeBwChart"),{
      type:"line",
      data:{labels:bw.map(b=>b.date), datasets:[{data:bw.map(b=>b.kg), borderColor:col, backgroundColor:col, tension:.25, pointRadius:2, spanGaps:true}]},
      options:{responsive:true, maintainAspectRatio:false,
        scales:{x:{ticks:{color:tickCol,maxTicksLimit:6}, grid:{color:gridCol}}, y:{beginAtZero:false, ticks:{color:tickCol}, grid:{color:gridCol}}},
        plugins:{legend:{display:false}}}
    });
  }
}

function renderView(){
  if(!state.people[0] && !state.people[1]){ renderCreateAccount(0); return; }
  // No sessions yet: force Program, since Home/Log/History/Progress all assume
  // a real curSession. Self-corrects the moment a first session is added.
  if(!state.program.order.length) activeTab="edit";
  if(!state.program.sessions[curSession]) curSession=state.program.order[0];
  if(activeTab==="home") renderHome();
  else if(activeTab==="log") renderLog();
  else if(activeTab==="history") renderHistory();
  else if(activeTab==="progress") renderProgress();
  else if(activeTab==="body") renderBody();
  else if(activeTab==="edit") renderEdit();
  else if(activeTab==="help") renderHelp();
}

// Switch section. Works even for views without a bottom-bar tab (Log, Guide):
// Log is reached via Home's "Log it", Guide via Settings. skipCapture is used
// right after saving, when the draft has just been cleared on purpose.
function switchTab(tab, skipCapture){
  if(!skipCapture) captureDraft();
  activeTab=tab;
  document.querySelectorAll("#tabs button").forEach(function(x){ x.classList.toggle("active", x.dataset.tab===tab); });
  renderView();
}

// Preset account colours - hex values mirror the CSS vars in css/styles.css
// (--me/--partner/--sw-*) so charts + the theme-color meta tag (which Chart.js
// and <meta> need as raw hex, not var()) stay in step with the app's --brand.
const SWATCHES = {
  navy:{light:"#1e3a8a",dark:"#7d9bf5"}, purple:{light:"#7a1fe0",dark:"#b57cff"},
  teal:{light:"#0d7d72",dark:"#4fd8c9"}, rose:{light:"#be185d",dark:"#f472b6"},
  amber:{light:"#a15c00",dark:"#f2b84b"}, green:{light:"#15803d",dark:"#5fd88a"}
};
function swatchColor(key,dark){ const s=SWATCHES[key]||SWATCHES.navy; return dark?s.dark:s.light; }
// Renders/reads a single-select colour-swatch picker (.swatchpick, styled in
// css/styles.css). Shared by the Settings dialog and account creation.
function renderSwatchPicker(container, selected){
  container.innerHTML = Object.keys(SWATCHES).map(function(k){
    return '<button type="button" data-c="'+k+'" class="'+(k===selected?"sel":"")+'" title="'+k.charAt(0).toUpperCase()+k.slice(1)+'"></button>';
  }).join("");
}
function readSwatchPicker(container){ const b=container.querySelector("button.sel"); return b?b.dataset.c:"navy"; }
// Swatch key for a person by name, used to colour their "pill" badges throughout.
function personSwatch(name){ const i=state.people.indexOf(name); return (i>=0 && state.colors[i]) || "navy"; }
function wireSwatchPicker(container){
  container.onclick=e=>{
    const b=e.target.closest("button"); if(!b) return;
    container.querySelectorAll("button").forEach(x=>x.classList.remove("sel"));
    b.classList.add("sel");
  };
}
// Address-bar / PWA chrome colour: active person's accent in light, app bg in dark.
function updateMeta(){
  const meta=document.querySelector('meta[name="theme-color"]');
  if(!meta) return;
  const dark=document.documentElement.getAttribute("data-theme")==="dark";
  meta.setAttribute("content", dark ? "#12151c" : swatchColor(state.colors[state.activePerson],false));
}
function applyTheme(t){
  document.documentElement.setAttribute("data-theme", t);
  updateMeta();
  const btn=document.getElementById("themeToggleBtn");
  if(btn){ btn.textContent = t==="dark" ? "☀️ Light mode" : "🌙 Dark mode"; }
}
function initTheme(){
  let t=state.theme;
  if(t!=="light" && t!=="dark"){
    t=(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
  }
  applyTheme(t);
}
function toggleTheme(){
  if(activeTab==="log") captureDraft(); // preserve unsaved entry across the re-render
  const next = document.documentElement.getAttribute("data-theme")==="dark" ? "light" : "dark";
  state.theme=next; save(); applyTheme(next);
  renderView(); // re-render so the themed chart + surfaces refresh
}
document.getElementById("themeToggleBtn").onclick=toggleTheme;

curSession = sessionForDate(curDate) || curSession;
initTheme();
renderPeople();
renderView();
autoSync(); // on open: pull the latest (partner's logs, coach notes) automatically

// Ask the browser to protect this site's storage from automatic eviction under
// storage pressure — relevant for anyone not using cloud sync, since local data
// is the only copy. Best-effort; no UI, nothing to do if unsupported/denied.
if(navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(()=>{});

// Nudge toward a manual backup if it's been a long time (or never) since the
// last Export and there's actually something to lose. Delayed so it doesn't
// collide with the sync-status toast from autoSync() above.
setTimeout(function(){
  if(!state.logs || !state.logs.length) return;
  var last = state.lastExportAt ? new Date(state.lastExportAt).getTime() : 0;
  var daysSince = (Date.now()-last)/86400000;
  if(daysSince>30) toast("Haven't exported in a while - back up via gear → Export");
}, 4000);

if("serviceWorker" in navigator){
  // Auto-apply new versions. sw.js calls skipWaiting()+clients.claim(), so a
  // freshly deployed version activates instead of waiting for every tab to
  // close; controllerchange then reloads the page so the phone actually runs
  // the new code (an installed PWA otherwise keeps stale JS in memory for
  // ages — which is why fixes seemed not to land). Guarded so the initial
  // claim on a first visit doesn't trigger a reload loop.
  let hadController = !!navigator.serviceWorker.controller, reloadingForUpdate=false;
  navigator.serviceWorker.addEventListener("controllerchange", ()=>{
    if(!hadController){ hadController=true; return; }
    if(reloadingForUpdate) return; reloadingForUpdate=true; window.location.reload();
  });
  window.addEventListener("load", ()=>{
    navigator.serviceWorker.register("sw.js").then(reg=>{ if(reg) reg.update(); });
  });
}

// Show the running app version (the shell cache name, e.g. "tt-v47") in Settings.
function showAppVersion(){
  const el=document.getElementById("appVersion"); if(!el) return;
  if(!window.caches){ el.textContent="-"; return; }
  caches.keys().then(keys=>{
    const v=keys.filter(k=>/^tt-v/.test(k)).sort((a,b)=>
      (parseInt(a.replace(/\D/g,""),10)||0)-(parseInt(b.replace(/\D/g,""),10)||0));
    el.textContent = v.length ? v[v.length-1] : "-";
  }).catch(()=>{ el.textContent="-"; });
}
// Force the newest deployed version: drop the service worker + every cache, then
// reload from the network. This is the reliable escape hatch for an installed
// PWA that keeps serving stale files.
function forceUpdate(){
  const btn=document.getElementById("updateNow"); if(btn){ btn.disabled=true; btn.textContent="Updating…"; }
  const reload=()=>window.location.reload();
  const jobs=[];
  if(navigator.serviceWorker && navigator.serviceWorker.getRegistrations)
    jobs.push(navigator.serviceWorker.getRegistrations().then(rs=>Promise.all(rs.map(r=>r.unregister()))));
  if(window.caches)
    jobs.push(caches.keys().then(ks=>Promise.all(ks.map(k=>caches.delete(k)))));
  Promise.all(jobs).then(reload).catch(reload);
}
const updBtn=document.getElementById("updateNow");
if(updBtn) updBtn.onclick=forceUpdate;
