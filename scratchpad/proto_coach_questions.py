"""Build a LOCAL prototype state for the coach questions card on Home. Pushes nothing.

Newest data-backup-*.json in, scratchpad/proto-coachq-state.json out. Adds made-up questions:

  Daniel  two open (one blocking, one optional) and one already answered
  Cerys   one open safety question and one closed (not shown)

The shared store is never opened.

    python scratchpad/proto_coach_questions.py
"""
import glob, io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
src = sorted(glob.glob(os.path.join(HERE, "data-backup-2*.json")))[-1]
data = json.load(io.open(src, encoding="utf-8"))
print("source:", os.path.basename(src))

NOW = 1793100000000


def question(qid, text, why, priority, status="open", answer="", decision="", day="2026-11-02"):
    return {"id": qid, "question": text, "why": why, "priority": priority, "decision": decision,
            "askedAt": day, "nextFollowUp": "2026-11-09", "reminders": 0, "answer": answer,
            "answeredAt": "2026-11-03" if answer else "", "status": status, "updatedAt": NOW}


data["coachQuestions"] = {
    data["people"][0]: [
        question("Q-20261102-01", "Does the new exercise order on the long day feel manageable?",
                 "It decides whether the order stays or moves next week.", "blocking",
                 decision="D-20261102-01"),
        question("Q-20261102-02", "Would you rather run alone or together on the weekly run?",
                 "It changes how the run is set up, not how long it is.", "optional"),
        question("Q-20261026-01", "Which machine do you use for the seated row?",
                 "The coach needs the smallest weight step on it.", "routine", status="answered",
                 answer="The plate-loaded one, it goes up in 5 kg jumps.", day="2026-10-26"),
    ],
    data["people"][1]: [
        question("Q-20261102-03", "Did the run leave any shin soreness the next morning?",
                 "The coach will not lengthen the run until this is answered.", "safety"),
        question("Q-20261019-01", "Do you want a reminder of the warm-up order?",
                 "Asked once, no longer needed.", "optional", status="closed", day="2026-10-19"),
    ],
}

prog = data["program"]
prog["order"] = [k for k in prog["order"] if k in prog["sessions"]]  # live store has orphan keys (2 Nov)
data["activePerson"] = 0
data["theme"] = "light"
out = os.path.join(HERE, "proto-coachq-state.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(data, indent=1))
print("wrote", os.path.basename(out), "- load it in the browser, nothing pushed")
for person, qs in data["coachQuestions"].items():
    print(person, [(q["id"], q["status"]) for q in qs])
