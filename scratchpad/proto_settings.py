"""Build a LOCAL prototype state for the Settings split (Profile / Admin) and the switches.
Pushes nothing.

Newest data-backup-*.json in, scratchpad/proto-settings-state.json out. Sets:

  Daniel  Food and calories off (his targets and meals stay), Garmin and coach on, Body on
  Cerys   Food and calories on, Tape and body measures off, Garmin and coach off
          (her coach notes, questions and watch data stay in the store, only hidden)
  PIN     a family PIN "1234", with a real random salt and hash

Both people get a coach question, calorie and protein targets and one measurement, so every
switch has something to hide. The shared store is never opened.

    python scratchpad/proto_settings.py
"""
import glob, hashlib, io, json, os, secrets

HERE = os.path.dirname(os.path.abspath(__file__))
src = sorted(glob.glob(os.path.join(HERE, "data-backup-2*.json")))[-1]
data = json.load(io.open(src, encoding="utf-8"))
print("source:", os.path.basename(src))

NOW = 1793100000000
daniel, cerys = data["people"][0], data["people"][1]


def switch(on):
    return {"on": on, "updatedAt": NOW}


data["features"] = {
    daniel: {"food": switch(False), "garmin": switch(True)},
    cerys: {"food": switch(True), "body": switch(False), "garmin": switch(False)},
}

salt = secrets.token_bytes(16)
data["adminPin"] = {"salt": salt.hex(), "hash": hashlib.sha256(salt + b"1234").hexdigest(), "updatedAt": NOW}

data["nutritionTargets"] = {daniel: {"kcal": 2600, "protein": 160, "updatedAt": NOW},
                            cerys: {"kcal": 2000, "protein": 110, "updatedAt": NOW}}
data["measurements"] = [{"person": p, "date": "2026-09-20", "cm": {"waist": 82.0, "chest": 98.5}, "updatedAt": NOW}
                        for p in (daniel, cerys)]


def question(qid, text, why):
    return {"id": qid, "question": text, "why": why, "priority": "routine", "decision": "", "askedAt": "2026-11-02",
            "nextFollowUp": "2026-11-09", "reminders": 0, "answer": "", "answeredAt": "", "status": "open",
            "updatedAt": NOW}


data["coachQuestions"] = {
    daniel: [question("Q-20261102-01", "Does the new exercise order on the long day feel manageable?",
                      "It decides whether the order stays or moves next week.")],
    cerys: [question("Q-20261102-03", "Did the run leave any shin soreness the next morning?",
                     "The coach will not lengthen the run until this is answered.")],
}

prog = data["program"]
prog["order"] = [k for k in prog["order"] if k in prog["sessions"]]  # live store has orphan keys (2 Nov)
data["activePerson"] = 0
data["theme"] = "light"
out = os.path.join(HERE, "proto-settings-state.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(data, indent=1))
print("wrote", os.path.basename(out), "- load it in the browser, nothing pushed")
print("PIN 1234, salt", salt.hex())
for person, f in data["features"].items():
    print(person, {k: v["on"] for k, v in f.items()})
