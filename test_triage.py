#!/usr/bin/env python3
"""Unit tests for the rules-based rubric engine (triage.py).

Run: python3 -m unittest test_triage -v
"""

import unittest

from samples import SAMPLES
from triage import score_draft


class TestRubric(unittest.TestCase):
    def test_strong_sample_scores_high(self):
        s = next(x for x in SAMPLES if x["id"] == "strong")
        result = score_draft(s["title"], s["program"], s["draft"])
        self.assertGreaterEqual(result["total"], 70)
        self.assertIn(result["grade"], ("A", "B"))
        self.assertEqual(result["severity"]["claimed"], "high")
        self.assertTrue(result["severity"]["match"])

    def test_weak_sample_scores_low(self):
        s = next(x for x in SAMPLES if x["id"] == "weak")
        result = score_draft(s["title"], s["program"], s["draft"])
        self.assertLessEqual(result["total"], 45)
        self.assertIn(result["grade"], ("D", "F"))
        self.assertTrue(len(result["suggestions"]) >= 3)

    def test_empty_draft_scores_zero(self):
        result = score_draft("", "P", "")
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["grade"], "F")

    def test_total_is_sum_of_dimensions(self):
        result = score_draft("Reentrancy bug", "P",
                             "## Summary\nSome text about reentrancy and funds.")
        expected = sum(d["score"] for d in result["dimensions"].values())
        self.assertEqual(result["total"], expected)
        for dim in result["dimensions"].values():
            self.assertGreaterEqual(dim["score"], 0)
            self.assertLessEqual(dim["score"], dim["max"])

    def test_severity_mismatch_flagged(self):
        draft = (
            "Severity: Critical\n\n"
            "There is a typo in a comment. Just a documentation issue, "
            "nothing else. Steps: 1. Read the code. 2. See the typo."
        )
        result = score_draft("Typo in comment", "P", draft)
        self.assertEqual(result["severity"]["claimed"], "critical")
        self.assertFalse(result["severity"]["match"])
        self.assertTrue(any("mismatch" in s or "re-label" in s
                            for s in result["suggestions"]))

    def test_poc_signals_detected(self):
        draft = (
            "## Summary\nContract 0x1234567890abcdef1234567890abcdef12345678 "
            "has a bug.\n\n```solidity\nfunction foo() {}\n```\n\n"
            "forge test --match-test testFoo\n"
        )
        result = score_draft("Bug", "P", draft)
        found = result["dimensions"]["poc_evidence"]["found"]
        self.assertIn("contract address present", found)
        self.assertIn("code block present", found)
        self.assertGreaterEqual(result["dimensions"]["poc_evidence"]["score"], 10)

    def test_duplicate_screen_flags_known_pattern(self):
        draft = ("The withdraw function has a reentrancy issue: an attacker "
                 "can call withdraw again before the balance updates.")
        result = score_draft("Reentrancy", "P", draft)
        patterns = [d["pattern"] for d in result["duplicate_screen"]]
        self.assertIn("reentrancy in withdraw", patterns)

    def test_result_is_json_serialisable(self):
        import json
        s = next(x for x in SAMPLES if x["id"] == "strong")
        result = score_draft(s["title"], s["program"], s["draft"])
        json.dumps(result)  # must not raise


if __name__ == "__main__":
    unittest.main()
