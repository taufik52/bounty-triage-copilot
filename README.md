# Bounty Triage Copilot

**Arbiter Hacks V1 — General Track**

A local-first web app that scores a bug-bounty report draft against a
triage rubric — before a human triager does. Paste a draft, pick a program,
and get an instant score (0–100) across four dimensions, a severity
cross-check, a heuristic duplication screen, and concrete suggestions to
improve the report. An optional local-LLM review (Ollama, `qwen2.5:3b`)
adds a second opinion; it is never required and never blocks the instant
result.

Built for security researchers who write many reports and want fast,
private feedback on draft quality. No accounts, no uploads, no data
leaves the machine, nothing is stored server-side.

## How it works

1. **Rules engine (instant, always available)** — `triage.py` scores the
   draft on four rubric dimensions (25 points each):
   - **PoC evidence** — contract addresses, tx hashes, code blocks,
     test commands, function references, explicit PoC section.
   - **Severity justification** — explicit severity label, claimed vs
     detected impact, concrete impact wording.
   - **Reproducibility** — numbered steps, expected vs actual behaviour,
     environment/prerequisites.
   - **Clarity & completeness** — title, length, structure, fix suggested,
     vague-language penalty.
   It also infers severity from impact keywords and flags a claimed /
   inferred mismatch, and screens the draft against a small built-in list
   of common public issue patterns (labelled as a heuristic, not a
   duplicate database).
2. **Local LLM review (optional, async)** — `llm.py` calls Ollama on
   `http://127.0.0.1:11434` with `qwen2.5:3b` and asks for a structured
   JSON review (summary, strengths, weaknesses, suggestions, severity
   assessment). The UI calls it in the background after the instant score.
   Any failure (server down, timeout, unparseable output) degrades
   gracefully to the rules-based result.

## Run it

Requirements: Python 3.10+ (standard library only — no dependencies).
Ollama is optional; without it, only the LLM button is disabled.

```bash
python3 app.py            # http://127.0.0.1:8080
python3 app.py --port 9000
```

Environment variables: `PORT`, `HOST`, `OLLAMA_URL`
(default `http://127.0.0.1:11434`), `OLLAMA_MODEL` (default `qwen2.5:3b`),
`LLM_TIMEOUT` (default `1200` seconds).

To enable the LLM review, install Ollama and pull the model:

```bash
ollama pull qwen2.5:3b
ollama serve
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Web UI |
| GET | `/api/health` | Status + Ollama availability |
| GET | `/api/samples` | Example drafts (strong + weak) |
| POST | `/api/triage` | Instant rules-based scoring (JSON in/out) |
| POST | `/api/triage/llm` | Optional local-LLM review (slow) |

Example:

```bash
curl -s -X POST http://127.0.0.1:8080/api/triage \
  -H 'Content-Type: application/json' \
  -d '{"title":"Reentrancy in Vault.withdraw","program":"Example Vault",
       "draft":"Severity: High\n\nFunds can be drained..."}'
```

## Tests

```bash
python3 -m unittest test_triage -v   # 8 unit tests for the rubric engine
bash test_e2e.sh                      # end-to-end smoke test (9 checks)
```

See [TEST-REPORT.md](TEST-REPORT.md) for the latest verified results.

## Project layout

```
app.py            HTTP server (stdlib only) + routing
triage.py         rules-based rubric engine
llm.py            Ollama client (optional enhancement)
samples.py        example drafts (strong + weak)
static/           web UI (index.html, style.css, app.js)
test_triage.py    unit tests
test_e2e.sh       end-to-end smoke test
SUBMISSION.md     Devpost submission draft
DEMO-SCRIPT.md    2–3 minute demo video script
```

## Known limitations (honest notes)

- The local LLM (`qwen2.5:3b`) is **very slow on this VM's CPU**:
  measured ~7 s per generated token when warm (13.6 s for 2 tokens) and
  ~275 s for a 30-token reply under load. A full structured review
  therefore takes 10+ minutes here, so the LLM review is a best-effort
  background enhancement, never the core path. On a machine with a GPU,
  or with a smaller/faster local model, it becomes practical.
- The duplication screen is a heuristic over a handful of common
  patterns, not a search over real program issue trackers.
- Severity inference is keyword-based; the app flags disagreements for
  the user to judge, it does not decide severity itself.

## License

MIT — see [LICENSE](LICENSE).
