const $ = (id) => document.getElementById(id);

const DIM_LABELS = {
  poc_evidence: "PoC evidence",
  severity: "Severity justification",
  reproducibility: "Reproducibility",
  clarity: "Clarity & completeness",
};

let lastPayload = null;

async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    const ollama = data.ollama_available
      ? `<span class="ok">Ollama OK (${data.ollama_model})</span>`
      : `<span class="bad">Ollama unavailable</span> — ${data.ollama_detail}. Rules-based scoring still works; LLM review will be disabled.`;
    $("health").innerHTML = `Rules engine: ${data.engine} &nbsp;·&nbsp; ${ollama}`;
    $("llmBtn").disabled = !data.ollama_available;
  } catch (e) {
    $("health").textContent = "Could not reach the app server.";
  }
}

function renderResult(data) {
  $("results").classList.remove("hidden");
  $("grade").textContent = "Grade " + data.grade;
  $("total").textContent = data.total;
  $("verdict").textContent = data.verdict;

  const dims = $("dimensions");
  dims.innerHTML = "";
  for (const [key, dim] of Object.entries(data.dimensions)) {
    const pct = Math.round((dim.score / dim.max) * 100);
    const cls = pct < 50 ? "bar low" : pct < 75 ? "bar mid" : "bar";
    const notes = [...(dim.found || []), ...(dim.notes || [])];
    if (key === "reproducibility") notes.push(`${dim.steps} numbered steps`);
    if (key === "clarity") notes.push(`${dim.words} words`);
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML =
      `<div class="bar-label"><span>${DIM_LABELS[key]}</span><span>${dim.score}/${dim.max}</span></div>` +
      `<div class="${cls}"><div style="width:${pct}%"></div></div>` +
      (notes.length ? `<p class="notes">${notes.join(" · ")}</p>` : "");
    dims.appendChild(row);
  }

  const sev = data.severity;
  $("severity").textContent = sev.claimed
    ? `Claimed: ${sev.claimed} · Detected impact: ${sev.inferred} · ${sev.match ? "Match ✓" : "Mismatch — see suggestions."}`
    : `No severity label found in the draft. Detected impact: ${sev.inferred}.`;

  const dups = data.duplicate_screen || [];
  $("dupWrap").classList.toggle("hidden", dups.length === 0);
  $("duplicates").innerHTML = dups
    .map((d) => `<li><strong>${d.pattern}</strong> — matched: ${d.matched_keywords.join(", ")}</li>`)
    .join("");

  $("suggestions").innerHTML = (data.suggestions.length
    ? data.suggestions
    : ["No major issues found — this draft looks triage-ready."]).map((s) => `<li>${s}</li>`).join("");

  $("llmWrap").classList.add("hidden");
  $("llmNote").classList.add("hidden");
}

async function scoreDraft() {
  const payload = {
    program: $("program").value,
    title: $("title").value,
    draft: $("draft").value,
  };
  if (!payload.draft.trim()) { $("status").textContent = "Paste a draft first."; return; }
  $("status").textContent = "Scoring…";
  $("scoreBtn").disabled = true;
  try {
    const res = await fetch("/api/triage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) { $("status").textContent = data.error || "Scoring failed."; return; }
    lastPayload = payload;
    renderResult(data);
    $("status").textContent = "Scored with the rules engine (instant, local).";
  } catch (e) {
    $("status").textContent = "Request failed: " + e.message;
  } finally {
    $("scoreBtn").disabled = false;
  }
}

async function askLlm() {
  if (!lastPayload) { $("status").textContent = "Score the draft first."; return; }
  $("llmBtn").disabled = true;
  $("status").textContent = "Asking the local LLM (qwen2.5:3b on CPU — this can take 10+ minutes on this machine)…";
  try {
    const res = await fetch("/api/triage/llm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lastPayload),
    });
    const data = await res.json();
    if (!res.ok) {
      const note = $("llmNote");
      note.textContent = "LLM review unavailable: " + (data.error || "unknown error");
      note.classList.remove("hidden");
      $("status").textContent = "LLM review failed — rules-based score still stands.";
      return;
    }
    const llm = data.llm;
    $("llmWrap").classList.remove("hidden");
    $("llmSummary").textContent = llm.summary || "";
    $("llmDetail").innerHTML =
      (llm.strengths && llm.strengths.length ? `<p><strong>Strengths:</strong></p><ul>${llm.strengths.map((s) => `<li>${s}</li>`).join("")}</ul>` : "") +
      (llm.weaknesses && llm.weaknesses.length ? `<p><strong>Weaknesses:</strong></p><ul>${llm.weaknesses.map((s) => `<li>${s}</li>`).join("")}</ul>` : "") +
      (llm.suggestions && llm.suggestions.length ? `<p><strong>LLM suggestions:</strong></p><ul>${llm.suggestions.map((s) => `<li>${s}</li>`).join("")}</ul>` : "") +
      (llm.severity_assessment ? `<p><strong>Severity:</strong> ${llm.severity_assessment}</p>` : "");
    $("llmMeta").textContent = `Model: ${llm.model}` +
      (llm.eval_tokens ? ` · ${llm.eval_tokens} tokens generated` : "") +
      (llm.total_seconds ? ` · ${llm.total_seconds}s total` : "");
    $("status").textContent = "LLM review received.";
  } catch (e) {
    $("status").textContent = "LLM request failed: " + e.message;
  } finally {
    $("llmBtn").disabled = false;
  }
}

async function loadSample(id) {
  try {
    const res = await fetch("/api/samples");
    const data = await res.json();
    const sample = data.samples.find((s) => s.id === id);
    if (!sample) return;
    $("program").value = sample.program;
    $("title").value = sample.title;
    $("draft").value = sample.draft;
    $("status").textContent = `Loaded example: ${sample.label}.`;
  } catch (e) {
    $("status").textContent = "Could not load sample: " + e.message;
  }
}

$("scoreBtn").addEventListener("click", scoreDraft);
$("llmBtn").addEventListener("click", askLlm);
document.querySelectorAll("[data-sample]").forEach((btn) =>
  btn.addEventListener("click", () => loadSample(btn.dataset.sample)));

checkHealth();
