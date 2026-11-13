# SUBMISSION.md — Devpost draft (English)

> Status: DRAFT — not submitted. Fill in the repo URL and video URL
> before submitting. Deadline: 21 December 2026, 12:00 WIB
> (20 Dec 2026, 9:00 PM PST / 21 Dec 05:00 UTC — verified 12 Nov 2026).
> Hackathon page: https://arbiter-hacks-v1.devpost.com
> Prize pool: $7,800 (5 cash prizes). Eligibility: students only, 13+.
> Tests re-verified fresh 13 Nov 2026 ~18:47 WIB: unit 13/13, E2E 9/9.

## Project title

**Bounty Triage Copilot**

## Track

General Track

## Tagline

Score your bug-bounty draft against a triage rubric before a human triager does — instantly, privately, locally.

## Description

Bug-bounty hunters lose time and rewards to preventable triage rejections:
missing proof-of-concept, severity that does not match the impact, steps
that cannot be reproduced, reports too vague to act on. Triagers see the
same mistakes every day — but hunters get that feedback only after
submitting, days later, if at all.

**Bounty Triage Copilot** gives that feedback in under a second, before
submission. Paste a draft report, pick the program, and the app scores it
0–100 against a four-dimension rubric — PoC evidence, severity
justification, reproducibility, and clarity — cross-checks the claimed
severity against the impact described, screens for common duplicate
patterns, and returns concrete, actionable suggestions ("Add numbered
reproduction steps", "Your claimed severity disagrees with the detected
impact — justify or re-label").

Everything runs locally: the scoring engine is a deterministic
rules-based system in pure Python (standard library only, no
dependencies), and the optional second opinion comes from a local LLM
(Ollama, `qwen2.5:3b`) on localhost. No accounts, no uploads, no data
leaves the machine — important when drafts describe unpublished
vulnerabilities. If the LLM is slow or unavailable, the app degrades
gracefully to the instant rules-based score instead of failing.

### What we built

- Web app (Python stdlib HTTP server + plain HTML/CSS/JS, zero
  dependencies) with live rubric bars, severity cross-check, duplication
  screen, and suggestions.
- Rules-based rubric engine (13 unit tests: 8 rubric + 5 LLM-parser)
  with two built-in example drafts: a strong reentrancy report (scores
  93/100, Grade A) and a vague access-control claim (scores 7/100,
  Grade F).
- Optional local-LLM review endpoint with strict JSON parsing and
  graceful fallback.
- End-to-end smoke test covering every endpoint (9 checks, all passing).

### What we learned

- A small local model on CPU is honest but slow: a 30-token reply took
  ~275 s on the demo VM, so the LLM must be an async enhancement, never
  on the critical path. Designing for graceful degradation mattered more
  than the model itself.
- Triage quality is mostly checkable mechanically: presence of a PoC,
  numbered steps, and severity/impact agreement already separate strong
  drafts from weak ones without any AI.

### What's next

- Per-program rubric profiles (severity tables and required evidence
  differ by program).
- Real duplicate search against public disclosure databases.
- A browser-extension "check before submit" flow and support for faster
  local models / GPU inference.

## How to run

```bash
python3 app.py            # http://127.0.0.1:8080
```

Optional, for the LLM review: `ollama pull qwen2.5:3b && ollama serve`.

## Links (fill in before submitting)

- Public code repository: _TODO — create public GitHub repo and paste URL_
- Demo video (2–3 min): _TODO — record per DEMO-SCRIPT.md and paste URL_
- Hackathon page: https://arbiter-hacks-v1.devpost.com

## Built with

Python (standard library only), HTML/CSS/JavaScript, Ollama (qwen2.5:3b, local).
