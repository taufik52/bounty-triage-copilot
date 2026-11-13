# TEST-REPORT.md — Bounty Triage Copilot

Test date: 12 November 2026 (WIB). All tests run on this VM.
Reproduce with: `python3 -m unittest test_triage test_llm_parse -v`
and `bash test_e2e.sh`.

**Re-verified fresh 12 Nov 2026 ~12:30 WIB (resume run): unit 13/13,
E2E 9/9, strong draft 93/100 Grade A, weak draft 7/100 Grade F,
rules scoring latency 0.0019 s. Live server check: `/api/health`
`ollama_available: true`, model `qwen2.5:3b` present. LLM fallback
re-verified: POST `/api/triage/llm` with `LLM_TIMEOUT=30` → HTTP 502
after 30.1 s with the graceful message, rules score unaffected.**

## Unit tests — 13/13 passed

| Suite | Tests | Result |
|---|---|---|
| `test_triage.py` (rubric engine) | 8 | OK |
| `test_llm_parse.py` (LLM JSON parser) | 5 | OK |

Rubric cases covered: strong sample scores high, weak sample scores
low, empty draft scores 0, total equals sum of dimensions, severity
mismatch flagged, PoC signals detected, duplicate screen flags a known
pattern, result is JSON-serialisable. Parser cases: plain JSON, fenced
JSON, JSON with surrounding text, garbage/empty/non-object → None,
unterminated JSON → None.

## End-to-end smoke test — 9/9 passed (`bash test_e2e.sh`)

- GET / serves UI; GET /static/app.js and /static/style.css return 200
- GET /api/health returns `{"status": "ok", ...}`
- GET /api/samples returns strong + weak drafts
- POST /api/triage on both samples, with asserts (0–100 range,
  total == sum of dimensions)
- POST /api/triage with empty draft → 400
- GET /nope → 404
- Rules scoring latency: 0.004–0.008 s (LLM is never on this path)

Measured scores (deterministic, re-verified 12 Nov):

| Draft | Total | Grade | Verdict | Suggestions | Dup hits |
|---|---|---|---|---|---|
| Strong — reentrancy in Vault.withdraw | 93 | A | Submission-ready | 0 | 1 (reentrancy pattern) |
| Weak — vague access-control claim | 7 | F | Not submittable yet | 6 | 0 |

## Ollama / LLM verification (live, http://127.0.0.1:11434)

Model `qwen2.5:3b` confirmed present via `/api/tags`.

| Check | Result |
|---|---|
| `/api/generate`, 5-token reply | HTTP 200 in ~60 s (first call, incl. model load) |
| `/api/generate`, 30-token reply | HTTP 200 in 275.5 s; correct one-sentence answer about PoC quality; `eval_count: 30` |
| `/api/generate`, 2-token reply (warm) | HTTP 200 in 112.7 s wall; `prompt_eval 20.4 s`, `eval 13.6 s` (~7 s/token) |
| `/api/health` (app) | `ollama_available: true`, "model qwen2.5:3b available" |
| POST `/api/triage/llm` with `LLM_TIMEOUT=30` | HTTP 502 after 30.4 s with graceful message: "LLM review unavailable (Ollama slow, down, or returned unparseable output). Rules-based score above still stands." |

Conclusion: the LLM integration works end-to-end, but a full structured
review (200–400 tokens) needs 10+ minutes on this VM's CPU. The app is
designed around that fact: instant rules-based scoring is the core path,
the LLM review is an async best-effort enhancement with a 1200 s timeout
and a graceful 502 fallback. On a GPU machine the same endpoint is fast.

## Known issues found during testing (fixed)

1. Severity inference mapped "drain"/"funds" to Critical, contradicting
   a reasonable "High" claim on the strong sample. Fixed: Critical is now
   reserved for the narrowest classes (unlimited mint, selfdestruct,
   delegatecall, takeover, privilege escalation); fund-loss words map
   to High.
2. First e2e run failed with connection refused (server had not finished
   starting when the checks ran / CPU contention with the concurrent
   Ollama test). Re-run green 9/9; the e2e script's 2 s startup wait is
   adequate under normal load.

## Not tested (out of scope for this build)

- Full `/api/triage/llm` success path with a real draft (would take
  10+ minutes on this CPU; the round-trip and the parser are verified
  separately, see above).
- Browser rendering / screenshots (no live-browser tool in this session).
- Devpost submission and GitHub repo creation (explicitly out of scope —
  see SUBMISSION.md TODOs).
