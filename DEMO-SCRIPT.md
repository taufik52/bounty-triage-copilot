# DEMO-SCRIPT.md — Demo video script (2–3 minutes)

> Re-verified 12 Nov 2026: weak draft scores 7/100 Grade F, strong draft
> scores 93/100 Grade A (fresh E2E run, 9/9). Ollama `qwen2.5:3b`
> confirmed running on this VM — health line shows "Ollama OK".
> LLM review is slow on this CPU (~7 s/token); keep the LLM click for
> last and do not wait for its full reply on camera (see Scene 4).

Target length: ~2:30. Record the screen with voice-over in English.
One continuous take per scene; cut between scenes.

## Scene 1 — The problem (0:00–0:25)

> "Bug-bounty hunters lose rewards to preventable triage rejections:
> missing proof-of-concept, severity that doesn't match the impact,
> steps nobody can reproduce. You only find out days after submitting.
> Bounty Triage Copilot gives you that feedback in under a second —
> before you submit."

(On screen: title slide / app home page.)

## Scene 2 — Weak draft, instant verdict (0:25–1:15)

1. Click **"weak draft"** example.
2. Click **"Score my draft"**.
3. Point at the result: **7/100, Grade F, "Not submittable yet"**.
4. Read two suggestions aloud: "Add a runnable proof-of-concept" and
   "State the severity explicitly and justify it."
5. Say: "This is the exact feedback a triager would give — but now, not
   in three days."

## Scene 3 — Strong draft (1:15–1:55)

1. Click **"strong draft"** example (reentrancy in Vault.withdraw).
2. Click **"Score my draft"**.
3. Point at the result: **93/100, Grade A, "Submission-ready"**,
   rubric bars nearly full, severity check "Claimed: High · Detected
   impact: High · Match ✓", and the duplication screen flagging the
   well-known reentrancy pattern as a reminder to check known issues.
4. Say: "Same tool, same rubric — the difference is evidence."

## Scene 4 — Local LLM, privacy (1:55–2:25)

1. Point at the health line: "Ollama OK (qwen2.5:3b)".
2. Click **"Ask local LLM"** and explain while it loads: "The second
   opinion comes from a model running on this machine — the draft never
   leaves it. That's important when a draft describes an unpublished
   vulnerability."
3. Be honest on camera: "On this CPU the model is slow, so it's an
   optional background review — the instant score never waits for it."

## Scene 5 — Close (2:25–2:35)

> "Bounty Triage Copilot: instant, private, local triage feedback.
> Built with Python, plain HTML and JavaScript, and a local Ollama model.
> Try it — paste a draft, fix what it flags, submit with confidence."

(On screen: repo URL + `python3 app.py`.)

## Recording checklist

- [ ] App running on http://127.0.0.1:8080, browser zoom 100%
- [ ] Ollama running (`ollama serve`) so the health line shows OK
- [ ] Score the weak draft first (7/100), then the strong draft (93/100)
- [ ] Keep the LLM click for last; do not wait for its full reply on camera
- [ ] Total runtime 2:00–3:00
