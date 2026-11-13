"""Rules-based rubric engine for Bounty Triage Copilot.

Scores a bug-bounty report draft against four rubric dimensions
(0-25 points each, 100 total). Pure standard library, deterministic,
no network access. The LLM layer (llm.py) is an optional enhancement
on top of this engine, never a requirement for a result.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Keyword / pattern tables
# ---------------------------------------------------------------------------

IMPACT_KEYWORDS = {
    # "Critical" is reserved for the narrowest, highest-impact classes.
    # Fund-loss words (drain, steal, funds) map to High: many programs
    # rate a vault drain High unless it also breaks access control or
    # governance, and the engine must not contradict a reasonable
    # "High" claim on a well-evidenced draft.
    "critical": [
        "unlimited mint", "unauthorized mint", "selfdestruct",
        "delegatecall", "takeover", "privilege escalation",
        "governance takeover",
    ],
    "high": [
        "funds", "fund loss", "loss of funds", "drain", "steal",
        "reentrancy", "re-entrancy",
        "denial of service", "dos", "griefing", "freeze", "locked",
        "lock funds", "incorrect accounting", "price manipulation",
        "oracle manipulation", "front-running", "access control",
        "unauthorized", "undercollateralized",
    ],
    "medium": [
        "rounding", "precision loss", "gas griefing", "event",
        "missing validation", "input validation", "stale",
    ],
    "low": [
        "typo", "documentation", "naming", "gas optimization",
        "code style", "comment",
    ],
}

POC_SIGNALS = [
    (r"0x[0-9a-fA-F]{40}", "contract address present", 4),
    (r"0x[0-9a-fA-F]{64}", "transaction hash present", 4),
    (r"```", "code block present", 4),
    (r"\bforge test\b|\bforge\b.*\btest\b|\bnpx hardhat\b|\bcast\b",
     "test command present", 4),
    (r"\bfunction\s+\w+\s*\(", "function reference present", 3),
    (r"\battacker\b.*\bcall|\bexploit\b.*\bcall|\bcall\s*\(.*\)",
     "attacker call described", 3),
    (r"proof[\s-]?of[\s-]?concept|\bPoC\b", "explicit PoC section", 3),
]

REPRO_SIGNALS = [
    (r"(?m)^\s*(1[.)]|step\s*1|#+\s*steps?)\b", "numbered steps present", 6),
    (r"expected\b.*\bactual\b|actual\b.*\bexpected\b",
     "expected vs actual behaviour", 5),
    (r"\bprerequisite|setup|environment|version\b",
     "environment / prerequisites stated", 4),
    (r"(?m)^\s*\d+[.)]\s+\w+", "step-by-step list", 5),
    (r"\breproduc", "reproduction described", 5),
]

SEVERITY_LABELS = ["critical", "high", "medium", "low", "informational", "info"]

VAGUE_PHRASES = [
    "sometimes", "maybe", "possibly", "might be", "kind of",
    "somehow", "i think", "not sure", "unclear",
]

# Small built-in list of well-known generic issue patterns, used only as a
# *heuristic* duplication screen. This is NOT a real duplicate database;
# the report says so explicitly.
KNOWN_PATTERNS = [
    ("missing access control on admin function",
     ["missing access control", "no access control", "anyone can call"]),
    ("reentrancy in withdraw",
     ["reentrancy", "re-entrancy", "withdraw"]),
    ("unchecked external call return value",
     ["unchecked", "return value", "external call"]),
    ("oracle price manipulation",
     ["oracle", "price manipulation", "flash loan"]),
    ("front-running / sandwich",
     ["front-run", "frontrun", "sandwich", "mev"]),
    ("integer overflow / underflow",
     ["overflow", "underflow"]),
    ("unbounded loop / gas griefing",
     ["unbounded loop", "gas griefing", "out of gas"]),
    ("missing input validation",
     ["missing validation", "no validation", "input validation"]),
]

GRADE_BANDS = [
    (85, "A", "Submission-ready"),
    (70, "B", "Strong — minor fixes"),
    (55, "C", "Needs work"),
    (40, "D", "Weak — major rewrite"),
    (0, "F", "Not submittable yet"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_steps(text: str) -> int:
    return len(re.findall(r"(?m)^\s*\d+[.)]\s+\S", text))


def _has(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE) is not None


def _detect_claimed_severity(text: str) -> str | None:
    m = re.search(
        r"severity\s*[:\-–]\s*(critical|high|medium|low|informational|info)",
        text, re.IGNORECASE,
    )
    if m:
        label = m.group(1).lower()
        return "informational" if label == "info" else label
    return None


def _infer_severity(text: str) -> str:
    lowered = text.lower()
    for level in ("critical", "high", "medium", "low"):
        if any(k in lowered for k in IMPACT_KEYWORDS[level]):
            return level
    return "informational"


def _duplicate_screen(text: str) -> list[dict]:
    lowered = text.lower()
    hits = []
    for name, keywords in KNOWN_PATTERNS:
        matched = [k for k in keywords if k in lowered]
        if len(matched) >= 2 or (len(keywords) == 1 and matched):
            hits.append({
                "pattern": name,
                "matched_keywords": matched,
                "note": (
                    "Heuristic match against a small list of common public "
                    "issue patterns. Check the program's known-issues list "
                    "before submitting — this is not a duplicate database."
                ),
            })
    return hits


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def score_draft(title: str, program: str, draft: str) -> dict:
    """Score a report draft. Returns a JSON-serialisable result dict."""
    text = f"{title}\n{draft}"
    lowered = text.lower()
    word_count = len(re.findall(r"\w+", draft))

    # --- 1. PoC evidence (0-25) -------------------------------------------
    poc_score = 0
    poc_found: list[str] = []
    for pattern, label, points in POC_SIGNALS:
        if _has(pattern, text):
            poc_score += points
            poc_found.append(label)
    poc_score = min(25, poc_score)

    # --- 2. Severity justification (0-25) ----------------------------------
    claimed = _detect_claimed_severity(text)
    inferred = _infer_severity(text)
    sev_score = 0
    sev_notes: list[str] = []
    if claimed:
        sev_score += 8
        sev_notes.append(f"claimed severity: {claimed}")
        if claimed == inferred:
            sev_score += 9
            sev_notes.append("claimed severity matches detected impact")
        else:
            sev_notes.append(
                f"claimed severity ({claimed}) does not match detected "
                f"impact ({inferred}) — justify or re-label"
            )
    else:
        sev_notes.append("no explicit severity label found")
    impact_hits = sum(
        1 for level in IMPACT_KEYWORDS
        for k in IMPACT_KEYWORDS[level] if k in lowered
    )
    if impact_hits >= 3:
        sev_score += 8
        sev_notes.append("concrete impact described")
    elif impact_hits >= 1:
        sev_score += 4
        sev_notes.append("some impact described, but thin")
    sev_score = min(25, sev_score)

    # --- 3. Reproducibility (0-25) -----------------------------------------
    repro_score = 0
    repro_found: list[str] = []
    for pattern, label, points in REPRO_SIGNALS:
        if _has(pattern, text):
            repro_score += points
            repro_found.append(label)
    steps = _count_steps(draft)
    if steps >= 4:
        repro_score += 5
    elif steps >= 2:
        repro_score += 2
    repro_score = min(25, repro_score)

    # --- 4. Clarity & completeness (0-25) ----------------------------------
    clarity_score = 0
    clarity_notes: list[str] = []
    if len(title.strip()) >= 10:
        clarity_score += 5
        clarity_notes.append("descriptive title")
    else:
        clarity_notes.append("title is missing or too short")
    if word_count >= 150:
        clarity_score += 6
    elif word_count >= 80:
        clarity_score += 3
    else:
        clarity_notes.append(f"draft is short ({word_count} words)")
    headings = len(re.findall(r"(?m)^#{1,3}\s+\S", draft))
    sections = len(re.findall(
        r"(?im)^(summary|impact|proof of concept|poc|steps? to reproduce|"
        r"recommendation|fix|mitigation)\b", draft))
    if headings >= 2 or sections >= 3:
        clarity_score += 7
        clarity_notes.append("structured with sections/headings")
    elif sections >= 1:
        clarity_score += 3
    if _has(r"recommend|suggest|fix|mitigat", draft):
        clarity_score += 4
        clarity_notes.append("fix / mitigation suggested")
    else:
        clarity_notes.append("no fix or mitigation suggested")
    vague = [p for p in VAGUE_PHRASES if p in lowered]
    if vague:
        clarity_score = max(0, clarity_score - 3)
        clarity_notes.append(f"vague language found: {', '.join(vague)}")
    clarity_score = min(25, clarity_score)

    # --- Total, grade, verdict ---------------------------------------------
    dimensions = {
        "poc_evidence": {"score": poc_score, "max": 25,
                         "found": poc_found},
        "severity": {"score": sev_score, "max": 25,
                     "notes": sev_notes},
        "reproducibility": {"score": repro_score, "max": 25,
                            "found": repro_found, "steps": steps},
        "clarity": {"score": clarity_score, "max": 25,
                    "notes": clarity_notes, "words": word_count},
    }
    total = sum(d["score"] for d in dimensions.values())
    grade, verdict = next(
        (g, v) for threshold, g, v in GRADE_BANDS if total >= threshold
    )

    # --- Suggestions --------------------------------------------------------
    suggestions: list[str] = []
    if poc_score < 15:
        suggestions.append(
            "Add a runnable proof-of-concept: contract address, attacker "
            "call sequence in a code block, and (if possible) a Foundry/Hardhat "
            "test command that reproduces the issue."
        )
    if not claimed:
        suggestions.append(
            "State the severity explicitly (e.g. 'Severity: High') and "
            "justify it with the concrete impact."
        )
    elif claimed != inferred:
        suggestions.append(
            f"Your claimed severity ({claimed}) disagrees with the impact "
            f"keywords detected ({inferred}). Either strengthen the impact "
            "evidence or re-label the severity — triagers penalise mismatch."
        )
    if repro_score < 15:
        suggestions.append(
            "Add numbered reproduction steps: prerequisites, exact calls, "
            "and expected vs actual behaviour for each step."
        )
    if clarity_score < 15:
        suggestions.append(
            "Structure the report with sections (Summary, Impact, PoC, "
            "Steps to Reproduce, Recommended Fix) and remove vague wording."
        )
    if word_count < 150:
        suggestions.append(
            f"Expand the draft (currently {word_count} words). A triage-ready "
            "report usually needs at least 150 words of substance."
        )
    if not _has(r"recommend|suggest|fix|mitigat", draft):
        suggestions.append(
            "Add a 'Recommended Fix' section — even a one-paragraph "
            "mitigation shows the issue is understood, not just observed."
        )

    return {
        "program": program,
        "title": title,
        "total": total,
        "grade": grade,
        "verdict": verdict,
        "engine": "rules",
        "dimensions": dimensions,
        "severity": {
            "claimed": claimed,
            "inferred": inferred,
            "match": claimed == inferred if claimed else None,
        },
        "duplicate_screen": _duplicate_screen(text),
        "suggestions": suggestions,
    }
