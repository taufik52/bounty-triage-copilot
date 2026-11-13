#!/usr/bin/env python3
"""Unit tests for the LLM reply parser (llm.parse_llm_json).

The parser is pure string handling, so it is tested without calling
Ollama. The Ollama round-trip itself is verified separately (see
TEST-REPORT.md): two successful /api/generate calls returning HTTP 200.

Run: python3 -m unittest test_llm_parse -v
"""

import unittest

from llm import parse_llm_json


class TestParseLlmJson(unittest.TestCase):
    def test_plain_json(self):
        out = parse_llm_json('{"summary": "Good draft.", "strengths": ["a"]}')
        self.assertEqual(out, {"summary": "Good draft.", "strengths": ["a"]})

    def test_fenced_json(self):
        out = parse_llm_json(
            '```json\n{"summary": "Good draft."}\n```')
        self.assertEqual(out, {"summary": "Good draft."})

    def test_json_with_surrounding_text(self):
        out = parse_llm_json(
            'Here is my review: {"summary": "OK"} Hope this helps!')
        self.assertEqual(out, {"summary": "OK"})

    def test_garbage_returns_none(self):
        self.assertIsNone(parse_llm_json("no json here at all"))
        self.assertIsNone(parse_llm_json(""))
        self.assertIsNone(parse_llm_json("[]"))  # not an object

    def test_unterminated_json_returns_none(self):
        self.assertIsNone(parse_llm_json('{"summary": "never closed"'))


if __name__ == "__main__":
    unittest.main()
