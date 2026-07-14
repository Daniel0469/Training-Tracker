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
          "warmup": "70x10, then 110x5",
          "target": "4x8-12",
          "sets": 4,
          "cols": [
            "Weight (kg)",
            "Reps"
          ]
        },
        {
          "name": "Romanian deadlift",
          "warmup": "light x8",
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
          "warmup": "empty x10, then ~60% x5",
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
          "warmup": "10x10, then 14x5",
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
          "target": "20-25 min",
          "sets": 1,
          "cols": [
            "Pace",
            "Time"
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
let activeTab = "log";
let curSession = state.program.order[0];
let curDate = new Date().toISOString().slice(0,10);
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
      return s;
    }
  }catch(e){}
  return { people:["Daniel","Cerys"], weights:["",""], activePerson:0, program:clone(DEFAULT_PROGRAM), logs:[] };
}
function save(){ localStorage.setItem(KEY, JSON.stringify(state)); }

function toast(msg){
  const t=document.getElementById("toast"); t.textContent=msg; t.classList.add("show");
  clearTimeout(t._t); t._t=setTimeout(()=>t.classList.remove("show"),1800);
}
const esc = s => String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const possessive = n => /s$/i.test(n) ? n+"'" : n+"'s";
const todayStr = ()=> new Date().toISOString().slice(0,10);
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
function parseRange(target){
  const m=String(target).match(/(\d+)\s*[-]\s*(\d+)/);
  return m? {low:+m[1],high:+m[2]} : null;
}
function loadStep(w){ return w>=60?"5 kg":w>=20?"2.5 kg":"1-2 kg"; }
function suggestNext(ex, entry, lastEntry){
  if(!isLifting(ex)) return "Beat last time - add a little time, distance, or pace.";
  const sets=entry.rows.map(r=>({w:parseFloat(r[0]),reps:parseInt(r[1],10)})).filter(s=>!isNaN(s.reps));
  if(!sets.length) return "Enter weight and reps to get a recommendation.";
  const range=parseRange(ex.target);
  const minReps=Math.min(...sets.map(s=>s.reps));
  const maxReps=Math.max(...sets.map(s=>s.reps));
  const ws=sets.map(s=>s.w).filter(w=>!isNaN(w));
  const topW=ws.length?Math.max(...ws):null;
  let txt;
  if(range){
    if(minReps>=range.high)
      txt = topW!=null ? "Hit the top of the range on every set - add "+loadStep(topW)+" next time and aim for "+range.low+"+ reps."
                       : "Hit the top of the range - increase the difficulty next time.";
    else if(maxReps<range.low)
      txt = topW!=null ? "Below target reps - keep "+topW+" kg and push for "+range.low+"+ reps next time."
                       : "Below target reps - aim for "+range.low+"+ next time.";
    else
      txt = "In range - add a rep per set toward "+range.high+", then add "+(topW!=null?loadStep(topW):"weight")+".";
  } else {
    txt = "Aim to add a rep or a little load vs this session.";
  }
  if(lastEntry){
    const ls=lastEntry.rows.map(r=>({w:parseFloat(r[0]),reps:parseInt(r[1],10)})).filter(s=>!isNaN(s.reps));
    if(ls.length){
      const vol=a=>a.reduce((t,s)=>t+(isNaN(s.w)?s.reps:s.w*s.reps),0);
      const lastTop=Math.max(...ls.map(s=>s.w).filter(w=>!isNaN(w)),-Infinity);
      if(topW!=null && lastTop>-Infinity){
        if(topW>lastTop || vol(sets)>vol(ls)) txt="✅ Up from last session. "+txt;
        else if(vol(sets)<vol(ls)) txt="⚠️ Down vs last - repeat and beat it. "+txt;
      }
    }
  }
  return txt;
}

function renderPeople(){
  const el=document.getElementById("ptoggle");
  el.innerHTML = state.people.map((n,i)=>
    '<button data-p="'+i+'" class="'+(state.activePerson===i?'active':'')+'">'+esc(n)+'</button>').join("");
  el.querySelectorAll("button").forEach(b=>b.onclick=()=>{
    if(+b.dataset.p===state.activePerson) return;
    captureDraft();
    state.activePerson=+b.dataset.p; save(); renderPeople(); renderView();
    if(activeTab==="log" && formDrafts[draftKey()])
      toast("Restored "+possessive(state.people[state.activePerson])+" unsaved entry");
  });
  const w=state.weights[state.activePerson];
  document.getElementById("sub").textContent =
    w ? state.people[state.activePerson]+" · "+w+" kg" : "Tap the gear to set bodyweight";
}
document.getElementById("tabs").querySelectorAll("button").forEach(b=>{
  b.onclick=()=>{ captureDraft(); activeTab=b.dataset.tab;
    document.querySelectorAll("#tabs button").forEach(x=>x.classList.toggle("active",x===b));
    renderView();
  };
});

function latestLog(person, sessionKey){
  return state.logs.filter(l=>l.person===person && l.sessionKey===sessionKey)
    .sort((a,b)=> (a.date<b.date?1:a.date>b.date?-1: (a.id<b.id?1:-1)))[0];
}
function bestWeightSoFar(person, exerciseName){
  var best=-Infinity;
  state.logs.filter(function(l){return l.person===person;}).forEach(function(l){
    var e=l.entries.find(function(x){return x.name===exerciseName;}); if(!e) return;
    e.rows.forEach(function(r){ var w=parseFloat(r[0]); if(!isNaN(w)&&w>best) best=w; });
  });
  return best;
}
function latestEntryAnywhere(person, exName){
  var bestLog=null, bestEntry=null;
  state.logs.forEach(function(l){
    if(l.person!==person) return;
    var e=l.entries.find(function(x){return x.name===exName;}); if(!e) return;
    if(!bestLog || l.date>bestLog.date || (l.date===bestLog.date && l.id>bestLog.id)){ bestLog=l; bestEntry=e; }
  });
  return bestLog ? {log:bestLog, entry:bestEntry} : null;
}
function daysAgo(dateStr){
  return Math.round((new Date() - new Date(dateStr+"T12:00:00"))/86400000);
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
    const rows=[], done=[];
    card.querySelectorAll("tbody tr").forEach(tr=>{
      const w=tr.querySelector('[data-c="0"]').value;
      const r=tr.querySelector('[data-c="1"]').value;
      const dn=tr.querySelector('[data-done]').checked;
      rows.push([w,r]); done.push(dn);
      if(w!==""||r!==""||dn) any=true;
    });
    entries[ei]={rows,done};
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
    d.rows.forEach((r,i)=>{
      const tr=tb.rows[i]; if(!tr) return;
      tr.querySelector('[data-c="0"]').value=r[0];
      tr.querySelector('[data-c="1"]').value=r[1];
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
  const planFor = name => { if(prev&&prev.suggestions){const s=prev.suggestions.find(x=>x.name===name); return s?s.text:"";} return ""; };
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
    + '<span class="hint" style="margin:0">Workout time &mdash; saved with the session.</span>'
    + '</div></div>';

  html += '<div id="exForm">';
  sess.exercises.forEach((ex,ei)=>{
    const last = prev && prev.entries.find(e=>e.name===ex.name);
    html += renderExForm(ex,ei,last,prev?prev.date:"",planFor(ex.name),recentNote(p,ex,prev));
  });
  html += '</div>';

  html += '<div class="card"><div class="sec-title">How did the session feel?</div>'
    + '<div class="row" style="margin-bottom:10px"><div class="grow">'
    + '<div class="hint" style="margin-bottom:4px">Difficulty (1 easy &middot; 10 max effort)</div>'
    + '<div class="diff" id="diff">'+[1,2,3,4,5,6,7,8,9,10].map(n=>'<button data-d="'+n+'">'+n+'</button>').join("")+'</div>'
    + '</div></div>'
    + '<label class="fld">Your own notes (optional)<textarea id="feedback" placeholder="e.g. Right knee tight on squats. Felt strong today."></textarea></label>'
    + '<div class="hint">A per-exercise plan for next session is generated automatically when you save.</div></div>'
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
  updateTimerUI();
  if(getTimer().running) ensureTimerTick();
}

function setRowHtml(n,ex,prevCell){
  const lifting = isLifting(ex);
  const im0 = lifting ? ' inputmode="decimal"' : '';
  const im1 = lifting ? ' inputmode="numeric"' : '';
  return '<tr><td class="setno">'+n+'</td>'
    + '<td><input data-c="0"'+im0+' value="" placeholder="'+esc(ex.cols[0])+'"></td>'
    + '<td><input data-c="1"'+im1+' value="" placeholder="'+esc(ex.cols[1])+'"></td>'
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
function renderExForm(ex,ei,last,prevDate,plan,recent){
  const rows = Math.max(ex.sets, last? last.rows.length:0);
  const fmt = r => esc(r[0])+(r[1]!==""&&r[1]!=null?" x "+esc(r[1]):"");
  let body="";
  for(let i=0;i<rows;i++){
    const r = last && last.rows[i] ? last.rows[i] : null;
    body += setRowHtml(i+1, ex, r?fmt(r):"-");
  }
  return '<div class="card ex" data-ei="'+ei+'" data-name="'+esc(ex.name)+'">'
    + '<div class="ex-head"><div class="ex-name">'+esc(ex.name)+'</div><div class="ex-meta">'+esc(ex.target)+'</div></div>'
    + (ex.warmup?'<div class="warmup">Warm-up: '+esc(ex.warmup)+'</div>':"")
    + (recent?'<div class="recent">🕑 '+recent+'</div>':"")
    + (plan?'<div class="plan">🎯 Plan: '+esc(plan)+'</div>':"")
    + '<table class="sets"><thead><tr><th></th><th>'+esc(ex.cols[0])+'</th><th>'+esc(ex.cols[1])+'</th>'
    + '<th class="prev" title="'+esc(prevDate)+'">Last'+(prevDate?' · '+relTime(prevDate):"")+'</th><th class="done-cell"></th></tr></thead><tbody>'+body+'</tbody></table>'
    + '<div class="row" style="margin-top:8px"><button class="mini" data-addset>+ set</button>'
    + '<button class="mini" data-delset>- set</button></div></div>';
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
  medal.hidden = !(isLifting(ex) && !isNaN(w) && best>-Infinity && w>best);
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
}
function wireExCard(card, ex){
  const tbody=card.querySelector("tbody");
  const best=cardBestWeight(ex);
  Array.from(tbody.rows).forEach(tr=>wireSetRow(tr, ex, best));
  const firstWeight = tbody.rows[0] && tbody.rows[0].querySelector('[data-c="0"]');
  if(firstWeight && isLifting(ex)){
    firstWeight.addEventListener("input", ()=>{
      const val=firstWeight.value;
      if(!val) return;
      Array.from(tbody.rows).slice(1).forEach(tr=>{
        const w=tr.querySelector('[data-c="0"]');
        if(w && !w.value) w.value=val;
      });
    });
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
    const name=card.dataset.name;
    const ex=sess.exercises.find(e=>e.name===name) || {cols:["Weight (kg)","Reps"]};
    const rows=[];
    card.querySelectorAll("tbody tr").forEach(tr=>{
      const a=tr.querySelector('[data-c="0"]').value.trim();
      const b=tr.querySelector('[data-c="1"]').value.trim();
      if(a!==""||b!=="") rows.push([a,b]);
    });
    if(rows.length) entries.push({name,cols:ex.cols.slice(),rows});
  });
  if(!entries.length && !feedback){ toast("Nothing entered yet"); return; }
  const suggestions=entries.map(en=>{
    const ex=sess.exercises.find(e=>e.name===en.name)||{cols:en.cols,target:""};
    const lastEn=prev && prev.entries.find(e=>e.name===en.name);
    return {name:en.name, text:suggestNext(ex,en,lastEn)};
  });
  var volume=0;
  entries.forEach(function(en){ en.rows.forEach(function(r){ var w=parseFloat(r[0]), reps=parseInt(r[1],10); if(!isNaN(w)&&!isNaN(reps)) volume+=w*reps; }); });
  volume=Math.round(volume);
  var prs=[];
  entries.forEach(function(en){
    if(!isLifting(en)) return; // col-0 is only a weight (kg) for lifting entries
    var ws=en.rows.map(function(r){return parseFloat(r[0]);}).filter(function(v){return !isNaN(v);});
    if(!ws.length) return;
    var thisMax=Math.max.apply(null,ws);
    var prevBest=bestWeightSoFar(person,en.name);
    if(prevBest>-Infinity && thisMax>prevBest){ en.pr=thisMax; prs.push({name:en.name,weight:thisMax}); }
  });
  const durationSec = timerElapsed(getTimer());
  const log={ id:Date.now(), date, person, sessionKey:curSession, sessionName:sess.name,
    entries, feedback, difficulty, suggestions, volume, durationSec };
  state.logs.push(log); save();
  delete formDrafts[draftKey()];
  delete sessionTimers[draftKey()];
  justSavedId=log.id;
  activeTab="history";
  document.querySelectorAll("#tabs button").forEach(x=>x.classList.toggle("active",x.dataset.tab==="history"));
  renderView();
  showSaveSummary(volume, prs, entries);
}

function renderHistory(){
  const logs=[...state.logs].sort((a,b)=> (a.date<b.date?1:a.date>b.date?-1:b.id-a.id));
  let html='<div class="card"><div class="flex-between">'
    + '<div class="sec-title" style="margin:0">History - '+logs.length+' session'+(logs.length===1?"":"s")+'</div>'
    + '<select id="histFilter"><option value="all">Everyone</option>'
    + state.people.map(p=>'<option value="'+esc(p)+'">'+esc(p)+'</option>').join("")
    + '</select></div></div>';
  if(!logs.length){
    html+='<div class="card empty">No sessions logged yet.<br>Head to the <b>Log</b> tab to record your first one.</div>';
    document.getElementById("view").innerHTML=html; return;
  }
  html+='<div id="histList"></div>';
  document.getElementById("view").innerHTML=html;
  const filter=document.getElementById("histFilter");
  filter.onchange=()=>drawHist(filter.value);
  drawHist("all");
}
function drawHist(who){
  let logs=[...state.logs].sort((a,b)=> (a.date<b.date?1:a.date>b.date?-1:b.id-a.id));
  if(who!=="all") logs=logs.filter(l=>l.person===who);
  const pc=p=> state.people[0]===p?"me":"partner";
  document.getElementById("histList").innerHTML = logs.map(l=>{
    const open = l.id===justSavedId;
    const rows=l.entries.map(e=>'<tr><td><b>'+esc(e.name)+(e.pr?' 🥇':'')+'</b></td><td>'
      + e.rows.map(r=>esc(r[0])+(r[1]!==""?" x "+esc(r[1]):"")).join(" · ")+'</td></tr>').join("");
    const plan=(l.suggestions&&l.suggestions.length)
      ? '<div class="planbox"><div class="sec-title" style="margin:0 0 5px">Plan for next '+esc(l.sessionName)+'</div>'
        + l.suggestions.map(s=>'<div class="planrow"><b>'+esc(s.name)+':</b> '+esc(s.text)+'</div>').join("")+'</div>'
      : "";
    return '<div class="log-item"><div class="log-row"><div>'
      + '<h3>'+esc(l.sessionName)+' <span class="pill '+pc(l.person)+'">'+esc(l.person)+'</span></h3>'
      + '<div class="ex-meta">'+esc(l.date)+(l.difficulty?' · difficulty '+l.difficulty+'/10':"")+(l.volume?' · '+l.volume.toLocaleString()+' kg':"")+(l.durationSec?' · ⏱ '+fmtDuration(l.durationSec):"")+'</div></div>'
      + '<div class="row"><button class="mini" data-toggle="'+l.id+'">'+(open?"Hide":"View")+'</button>'
      + '<button class="mini" data-del="'+l.id+'" style="color:var(--bad)">Delete</button></div></div>'
      + '<div class="log-detail '+(open?"open":"")+'" id="d'+l.id+'"><table>'
      + (rows||'<tr><td class="ex-meta">No set data</td></tr>')+'</table>'
      + (l.feedback?'<div class="fb">📝 '+esc(l.feedback)+'</div>':"")+plan+'</div></div>';
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
  const allEx=[...new Set(state.logs.flatMap(l=>l.entries.map(e=>e.name)))].sort();
  if(!allEx.length){
    document.getElementById("view").innerHTML='<div class="card empty">Log a few sessions and your progress charts will appear here.</div>';
    return;
  }
  document.getElementById("view").innerHTML='<div class="card">'
    + '<div class="flex-between" style="margin-bottom:12px">'
    + '<label class="fld grow" style="max-width:340px">Exercise<select id="progEx">'
    + allEx.map(n=>'<option>'+esc(n)+'</option>').join("")+'</select></label></div>'
    + '<div class="hint" style="margin-bottom:10px">Tracks the highest value in the first column (e.g. top-set weight) per session, for both people.</div>'
    + '<div class="chart-box"><canvas id="progChart"></canvas></div></div>';
  document.getElementById("progEx").onchange=drawChart;
  drawChart();
}
function drawChart(){
  const name=document.getElementById("progEx").value;
  const series=state.people.map((p,i)=>{
    const pts=state.logs.filter(l=>l.person===p)
      .map(l=>{ const e=l.entries.find(x=>x.name===name); if(!e) return null;
        const vals=e.rows.map(r=>parseFloat(r[0])).filter(v=>!isNaN(v));
        if(!vals.length) return null; return {x:l.date,y:Math.max(...vals)}; })
      .filter(Boolean).sort((a,b)=>a.x<b.x?-1:1);
    return {label:p,data:pts,borderColor:i===0?"#2f6df0":"#e0633a",
      backgroundColor:i===0?"#2f6df0":"#e0633a",tension:.25,spanGaps:true};
  });
  if(chart) chart.destroy();
  chart=new Chart(document.getElementById("progChart"),{
    type:"line", data:{datasets:series},
    options:{responsive:true,maintainAspectRatio:false,parsing:false,
      scales:{x:{type:"category",labels:[...new Set(state.logs.map(l=>l.date))].sort()},
        y:{beginAtZero:false,title:{display:true,text:"Top value"}}},
      plugins:{legend:{position:"top"}}}
  });
}

function renderEdit(){
  let html='<div class="card"><div class="hint">Edit any session below - rename exercises, change targets, add warm-up notes, add or remove movements. Changes apply to future logging; past history is untouched.</div></div>';
  orderedKeys().forEach(k=>{
    const s=state.program.sessions[k];
    html+='<div class="card"><div class="flex-between" style="margin-bottom:10px"><div>'
      + '<h3>'+esc(s.name)+'</h3><div class="ex-meta">'+esc(s.day)+'</div></div>'
      + '<button class="mini" data-addex="'+k+'">+ exercise</button></div>';
    s.exercises.forEach((ex,ei)=>{
      html+='<div class="ex"><div class="ex-head"><div><div class="ex-name">'+esc(ex.name)+'</div>'
        + '<div class="ex-meta">'+esc(ex.target)+(ex.warmup?' · warm-up: '+esc(ex.warmup):"")+'</div></div>'
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
}
function move(ref,dir){
  const a=ref.split(":"); const arr=state.program.sessions[a[0]].exercises;
  const i=+a[1], j=i+dir; if(j<0||j>=arr.length) return;
  const t=arr[i]; arr[i]=arr[j]; arr[j]=t; save(); renderEdit();
}

let exDlgCtx=null;
const exDlg=document.getElementById("exDlg");
function openExDlg(sessionKey,ei){
  exDlgCtx={sessionKey,ei};
  const editing = ei!=null;
  const ex = editing? state.program.sessions[sessionKey].exercises[ei]
    : {name:"",warmup:"",target:"3x8-12",cols:["Weight (kg)","Reps"],sets:3};
  document.getElementById("exDlgTitle").textContent= editing?"Edit exercise":"Add exercise";
  document.getElementById("exName").value=ex.name;
  document.getElementById("exWarmup").value=ex.warmup||"";
  document.getElementById("exTarget").value=ex.target||"";
  document.getElementById("exSets").value=ex.sets||3;
  document.getElementById("exCol0").value=ex.cols[0];
  document.getElementById("exCol1").value=ex.cols[1];
  exDlg.showModal();
}
document.getElementById("exCancel").onclick=()=>exDlg.close();
document.getElementById("exSave").onclick=()=>{
  const name=document.getElementById("exName").value.trim();
  if(!name){ toast("Name required"); return; }
  const ex={ name, warmup:document.getElementById("exWarmup").value.trim(),
    target:document.getElementById("exTarget").value.trim()||"-",
    sets:Math.max(1,Math.min(12,+document.getElementById("exSets").value||3)),
    cols:[document.getElementById("exCol0").value.trim()||"Weight (kg)",
          document.getElementById("exCol1").value.trim()||"Reps"] };
  const arr=state.program.sessions[exDlgCtx.sessionKey].exercises;
  if(exDlgCtx.ei!=null) arr[exDlgCtx.ei]=ex; else arr.push(ex);
  save(); exDlg.close(); renderEdit(); toast("Saved");
};

const setDlg=document.getElementById("settingsDlg");
document.getElementById("settingsBtn").onclick=()=>{
  document.getElementById("name0").value=state.people[0];
  document.getElementById("name1").value=state.people[1];
  document.getElementById("weight0").value=state.weights[0];
  document.getElementById("weight1").value=state.weights[1];
  document.getElementById("wlab0").childNodes[0].nodeValue=possessive(state.people[0])+" bodyweight (kg)";
  document.getElementById("wlab1").childNodes[0].nodeValue=possessive(state.people[1])+" bodyweight (kg)";
  setDlg.showModal();
};
document.getElementById("settingsCancel").onclick=()=>setDlg.close();
document.getElementById("settingsSave").onclick=()=>{
  const n0=document.getElementById("name0").value.trim()||"Daniel";
  const n1=document.getElementById("name1").value.trim()||"Cerys";
  state.people=[n0,n1];
  state.weights=[document.getElementById("weight0").value.trim(),
                 document.getElementById("weight1").value.trim()];
  save(); setDlg.close(); renderPeople(); renderView(); toast("Saved");
};
document.getElementById("resetProgram").onclick=()=>{
  if(confirm("Reset all workouts to the default program? Your logged history stays.")){
    state.program=clone(DEFAULT_PROGRAM); curSession=state.program.order[0];
    save(); setDlg.close(); renderView(); toast("Program reset");
  }
};

const importDlg=document.getElementById("importDlg");
function exportData(){
  const payload={version:1, exportedAt:new Date().toISOString(),
    people:state.people, weights:state.weights, program:state.program, logs:state.logs};
  const text=JSON.stringify(payload,null,2);
  const fname="training-data-"+todayStr()+".json";
  try{
    const blob=new Blob([text],{type:"application/json"});
    const url=URL.createObjectURL(blob);
    const a=document.createElement("a"); a.href=url; a.download=fname;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),2000);
    toast("Exported "+fname);
  }catch(e){
    setDlg.close();
    document.getElementById("importText").value=text;
    importDlg.showModal();
    toast("Download blocked - copy this text to transfer");
  }
}
document.getElementById("exportBtn").onclick=exportData;
document.getElementById("importBtn").onclick=()=>{
  document.getElementById("importText").value="";
  document.getElementById("importAdopt").checked=false;
  importDlg.showModal();
};
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
  var byId={}; state.logs.forEach(function(l,i){ byId[l.id]=i; });
  let added=0, updated=0;
  data.logs.forEach(function(l){ if(!l) return; if(byId[l.id]!=null){ state.logs[byId[l.id]]=l; updated++; } else { byId[l.id]=state.logs.length; state.logs.push(l); added++; } });
  if(document.getElementById("importAdopt").checked){
    if(data.program&&data.program.sessions) state.program=clone(data.program);
    if(Array.isArray(data.people)&&data.people.length) state.people=data.people.slice(0,2);
    if(Array.isArray(data.weights)) state.weights=data.weights.slice(0,2);
    curSession=sessionForDate(curDate)||state.program.order[0];
  }
  save(); importDlg.close(); setDlg.close(); renderPeople(); renderView();
  toast(added+" added, "+updated+" updated");
};

function renderHelp(){
  function card(title, body){ return '<div class="card"><div class="sec-title">'+title+'</div>'+body+'</div>'; }
  function p(t){ return '<p style="margin:0 0 9px">'+t+'</p>'; }
  var h='';
  h+='<div class="card"><h3 style="margin-bottom:6px">How to use this tracker</h3>'
    +'<div class="hint" style="margin-bottom:0">A shared training log for two people. Pick who you are, log each workout, and it tells you what to aim for next time. Everything saves automatically on this device - no account or internet needed.</div></div>';

  h+=card('1 &middot; Pick who you are',
      p('Use the toggle at the top right to switch between the two of you (blue and orange). Every set you log and every suggestion belongs to whoever is selected, so check it before you start.')
     +p('Tap the gear icon to set both <b>names</b> and each person\'s <b>bodyweight</b>. The selected person\'s bodyweight shows under the title - update it whenever it changes.'));

  h+=card('2 &middot; Log a workout',
      p('Open the <b>Log</b> tab and choose the session (Lower 1, Upper 1, etc.) and the date. Each exercise shows its target reps and any warm-up note.')
     +p('Type your <b>weight</b> and <b>reps</b> for each set. Use <b>+ set</b> / <b>- set</b> to change how many sets you do.')
     +p('Boxes start <b>blank on purpose</b>. The grey <b>Last</b> column on the right shows exactly what that person did last time, set by set - your job is to match or beat it.'));

  h+=card('3 &middot; Rate it and save',
      p('At the bottom, tap a <b>difficulty</b> from 1 (easy) to 10 (max effort), and add any personal <b>notes</b> (optional).')
     +p('Hit <b>Save session</b>. The app instantly writes a <b>plan for next time</b> for every exercise - e.g. "hit the top of the range, add 2.5 kg" or "below target reps, chase more reps", and whether you went up or down versus last session.'));

  h+=card('4 &middot; The next-session plan',
      p('Your saved plan appears in <b>History</b> right after saving, and again as a green <b>Plan</b> line on each exercise the next time you log that session. Follow it to keep adding weight or reps gradually (progressive overload).'));

  h+=card('5 &middot; History',
      p('The <b>History</b> tab lists every saved session, newest first. Filter by person, tap <b>View</b> to expand the full set data, notes and plan, or <b>Delete</b> to remove a session.'));

  h+=card('6 &middot; Progress',
      p('The <b>Progress</b> tab charts your best set (top weight) for any exercise over time, with both people on the same graph - a quick way to see who is moving up and where things have stalled.'));

  h+=card('7 &middot; Edit the program',
      p('The <b>Edit Program</b> tab lets you change the workouts: rename an exercise, change its target, add a warm-up note, add/remove/reorder movements, or relabel the input columns (handy for cardio fields like Min or Pace).')
     +p('Changes only affect future logging - your past history is never altered. To start over, use <b>Reset program to default</b> in the gear menu (your logs stay).'));

  h+=card('8 &middot; Where your data lives',
      p('Everything is stored <b>on this device, in this browser</b>. There is no cloud sync, so your phone copy and your computer copy keep <b>separate</b> logs. Pick one main place to log each day (most people use their phone).'));

  h+=card('9 &middot; Move data between devices (sync)',
      p('In the gear menu under <b>Data</b>: <b>Export</b> saves a file with everything; send it to the other device (email, Drive, AirDrop).')
     +p('On the other device, tap <b>Import / merge</b>, pick the file, and its sessions are <b>added in</b>. Merging is by unique ID, so nothing is overwritten or duplicated - you can import in either direction as often as you like.')
     +p('Tick "Also replace program &amp; names" only if you want to copy the other device\'s program too; leave it off to merge logs only.'));

  h+=card('10 &middot; Put it on your phone',
      p('Open the file in your phone browser, then add it to your home screen (Share &rarr; Add to Home Screen on iPhone; menu &rarr; Add to Home screen on Android). Always open it from that icon so it uses the same saved data.'));

  h+=card('Quick tips',
      p('&bull; Beat the grey <b>Last</b> numbers - even one extra rep counts.')
     +p('&bull; Save every session so the plans and charts stay accurate.')
     +p('&bull; Export now and then as a backup, and to keep both of you in sync.'));

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
  if(!c||!max) return "#e9edf2";
  var t=c/max, l=[190,222,255], d=[10,52,130];
  return "rgb("+lerp(l[0],d[0],t)+","+lerp(l[1],d[1],t)+","+lerp(l[2],d[2],t)+")";
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
  var muscleSets={};
  (entries||[]).forEach(function(en){
    var ms=classifyMuscles(en.name||""); var sets=(en.rows&&en.rows.length)||0;
    ms.forEach(function(mk){ muscleSets[mk]=(muscleSets[mk]||0)+sets; });
  });
  var maxc=0; for(var k in muscleSets){ if(muscleSets[k]>maxc) maxc=muscleSets[k]; }
  var wrap=document.getElementById("muscleWrap");
  if(maxc>0){
    wrap.style.display="";
    document.querySelectorAll("#muscleSvg .musc").forEach(function(el){
      var mk=el.getAttribute("data-muscle"); var cval=muscleSets[mk]||0;
      el.setAttribute("fill", muscleColor(cval,maxc));
      var ti=el.querySelector("title");
      if(ti){ var base=ti.textContent.replace(/:.*$/,""); ti.textContent=base+": "+cval+" set"+(cval===1?"":"s"); }
    });
  } else { wrap.style.display="none"; }
  document.getElementById("savePRs").innerHTML=prHtml;
  document.getElementById("saveDlg").showModal();
}
document.getElementById("saveDlgOk").onclick=function(){ document.getElementById("saveDlg").close(); };

function renderView(){
  if(!state.program.sessions[curSession]) curSession=state.program.order[0];
  if(activeTab==="log") renderLog();
  else if(activeTab==="history") renderHistory();
  else if(activeTab==="progress") renderProgress();
  else if(activeTab==="edit") renderEdit();
  else if(activeTab==="help") renderHelp();
}
curSession = sessionForDate(curDate) || curSession;
renderPeople();
renderView();

if("serviceWorker" in navigator){
  window.addEventListener("load", ()=>{ navigator.serviceWorker.register("sw.js"); });
}
