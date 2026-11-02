#!/usr/bin/env python3
"""Runs progression_cases.json against progression.py. The same file is run against
the JS copies in js/app.js by scratchpad/review/progression-cases.html.

    python mcp-coach/test_progression.py
"""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import progression as P

FUNCS = {
    "parseStepLines": lambda i: P.parse_step_lines(i["text"]),
    "progLadder": lambda i: P.prog_ladder(i["weights"]),
    "stepCore": lambda i: P.step_for(i["ex"], i["w"], i.get("override"), i.get("pool") or []),
    "progCore": lambda i: P.prog_core(i["entries"], i["ex"], i.get("ctx") or {}),
}


def matches(actual, want):
    """Every key in `want` must equal the same key in `actual`; lists must match whole."""
    if isinstance(want, dict):
        return isinstance(actual, dict) and all(k in actual and matches(actual[k], v) for k, v in want.items())
    if isinstance(want, list):
        return isinstance(actual, list) and len(actual) == len(want) and all(map(matches, actual, want))
    if isinstance(want, (int, float)) and not isinstance(want, bool):
        return isinstance(actual, (int, float)) and abs(actual - want) < 1e-9
    return actual == want


class ProgressionCases(unittest.TestCase):
    def test_cases(self):
        with open(os.path.join(HERE, "progression_cases.json"), encoding="utf-8") as f:
            cases = json.load(f)
        for case in cases:
            with self.subTest(case["name"]):
                got = FUNCS[case["fn"]](case["in"])
                exact = not case.get("exact") or len(got) == len(case["out"])
                self.assertTrue(matches(got, case["out"]) and exact,
                                "got %s\nwant %s" % (json.dumps(got), json.dumps(case["out"])))


if __name__ == "__main__":
    unittest.main()
