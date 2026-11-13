"""Optional local-LLM enhancement for Bounty Triage Copilot.

Talks to Ollama on http://127.0.0.1:11434 (model qwen2.5:3b).
Any failure — server down, model not loaded, timeout, bad JSON —
returns ``None`` so the caller can fall back to the rules engine.
Never raises for expected failure modes.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
# qwen2.5:3b on this VM's CPU runs at roughly 0.15 tokens/s (measured:
# 13.6 s to generate 2 tokens when warm, 275 s for 30 tokens under load),
# so a full structured review needs a very generous timeout. The UI calls
# this endpoint asynchronously and never blocks the instant rules-based
# result on it. On a GPU machine this is seconds, not minutes.
TIMEOUT_SECONDS = int(os.environ.get("LLM_TIMEOUT", "1200"))

PROMPT_TEMPLATE = """You are a senior bug-bounty triage reviewer. Review the draft report below for the program "{program}".

Title: {title}

Draft:
{draft}

Reply with ONLY a JSON object (no markdown fences, no extra text) with these keys:
- "summary": one sentence on the overall quality of the draft.
- "strengths": list of up to 3 short strings.
- "weaknesses": list of up to 3 short strings.
- "suggestions": list of up to 3 short, actionable strings.
- "severity_assessment": one sentence on whether the claimed severity looks justified.
"""


def ollama_available(timeout: float = 5.0) -> tuple[bool, str]:
    """Check whether Ollama answers and the model is present."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = [m.get("name", "") for m in data.get("models", [])]
        if MODEL in models or any(m.startswith(MODEL.split(":")[0]) for m in models):
            return True, f"model {MODEL} available"
        return False, f"model {MODEL} not in Ollama ({', '.join(models) or 'none'})"
    except Exception as exc:  # noqa: BLE001 - availability check must not raise
        return False, f"Ollama unreachable: {exc}"


def parse_llm_json(raw: str) -> dict | None:
    """Parse the LLM's reply into a dict, tolerating fences and junk.

    Returns None when no JSON object can be recovered.
    """
    text = (raw or "").strip()
    if not text:
        return None
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Last resort: salvage the first {...} block.
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            parsed = json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def llm_review(program: str, title: str, draft: str) -> dict | None:
    """Ask the local LLM to review a draft. Returns parsed JSON or None."""
    prompt = PROMPT_TEMPLATE.format(program=program, title=title, draft=draft)
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 400},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 - any LLM failure means fallback
        return None
    raw = (data.get("response") or "").strip()
    parsed = parse_llm_json(raw)
    if parsed is None:
        return None
    return {
        "model": MODEL,
        "summary": str(parsed.get("summary", ""))[:500],
        "strengths": [str(s)[:200] for s in parsed.get("strengths", [])][:3],
        "weaknesses": [str(s)[:200] for s in parsed.get("weaknesses", [])][:3],
        "suggestions": [str(s)[:200] for s in parsed.get("suggestions", [])][:3],
        "severity_assessment": str(parsed.get("severity_assessment", ""))[:500],
        "eval_tokens": data.get("eval_count"),
        "total_seconds": round(data.get("total_duration", 0) / 1e9, 1),
    }
