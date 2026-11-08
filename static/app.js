/**
 * CV Optimizer - Interactive Frontend Controller
 */

let currentSessionId = null;
let currentInitialDiagnosis = null;
let currentPostDiagnosis = null;
let currentComparison = null;

document.addEventListener("DOMContentLoaded", () => {
  initUpload();
  initOptimization();
  initManualReview();
});

// -------------------------------------------------------------
// SECTION A: UPLOAD HANDLING
// -------------------------------------------------------------
function initUpload() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  });
}

async function handleFileUpload(file) {
  const validExts = [".pdf", ".docx"];
  const filename = file.name;
  const isDocx = filename.toLowerCase().endsWith(".docx");
  const isPdf = filename.toLowerCase().endsWith(".pdf");

  if (!isDocx && !isPdf) {
    alert("Formato não suportado. Por favor, envie um arquivo .pdf ou .docx");
    return;
  }

  // Update file info display in Section A
  const fileInfoBar = document.getElementById("file-info-bar");
  const fileFormatBadge = document.getElementById("file-format-badge");
  const fileNameDisplay = document.getElementById("file-name-display");
  const fileStatsDisplay = document.getElementById("file-stats-display");

  fileNameDisplay.textContent = filename;
  fileFormatBadge.textContent = isDocx ? "DOCX" : "PDF";
  fileStatsDisplay.textContent = `Carregando... (${(file.size / 1024).toFixed(1)} KB)`;
  fileInfoBar.classList.remove("hidden");

  // Reset downstream sections if replacing document
  resetDownstreamSections();

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/upload", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Erro no processamento do arquivo.");
    }

    const data = await res.json();
    currentSessionId = data.session_id;
    currentInitialDiagnosis = data.initial_diagnosis;

    fileStatsDisplay.textContent = `Identificado como ${data.format} | ${data.word_count} palavras extraídas`;

    // Render Section B: Diagnóstico Inicial
    renderInitialDiagnosis(data.initial_diagnosis);

    // Show Section C: Botão Melhorar CV
    document.getElementById("section-cta").classList.remove("hidden");

  } catch (err) {
    alert("Falha no upload: " + err.message);
  }
}

function resetDownstreamSections() {
  document.getElementById("section-diagnosis").classList.add("hidden");
  document.getElementById("section-cta").classList.add("hidden");
  document.getElementById("section-post-inspection").classList.add("hidden");
  document.getElementById("section-comparison").classList.add("hidden");
  document.getElementById("section-recommendations").classList.add("hidden");
  document.getElementById("section-manual-review").classList.add("hidden");
  document.getElementById("section-export").classList.add("hidden");
  document.getElementById("steps-container").style.display = "none";
}

// -------------------------------------------------------------
// SECTION B: RENDER INITIAL DIAGNOSIS
// -------------------------------------------------------------
function renderInitialDiagnosis(diag) {
  const section = document.getElementById("section-diagnosis");
  section.classList.remove("hidden");

  // Overall Score
  document.getElementById("init-score-val").textContent = diag.overall_score;
  document.getElementById("init-score-percent").textContent = `${diag.overall_score}%`;
  
  const fill = document.getElementById("init-progress-fill");
  fill.style.width = `${diag.overall_score}%`;
  if (diag.overall_score >= 80) fill.style.backgroundColor = "var(--success)";
  else if (diag.overall_score >= 60) fill.style.backgroundColor = "var(--warning)";
  else fill.style.backgroundColor = "var(--danger)";

  // Criteria Grid
  const grid = document.getElementById("init-criteria-grid");
  grid.innerHTML = "";
  diag.criteria.forEach((c) => {
    const card = document.createElement("div");
    card.className = "criterion-card";
    const statusColor = c.percentage >= 80 ? "var(--success)" : (c.percentage >= 60 ? "var(--warning)" : "var(--danger)");
    card.innerHTML = `
      <div class="criterion-top">
        <span class="criterion-name">${c.name}</span>
        <span class="criterion-val" style="color: ${statusColor}">${c.score}/${c.max_score}</span>
      </div>
      <div class="progress-bar-bg" style="height: 6px;">
        <div class="progress-bar-fill" style="width: ${c.percentage}%; background-color: ${statusColor}"></div>
      </div>
      <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 6px;">
        Status: <strong style="color: ${statusColor}">${c.status}</strong> (${c.percentage}%)
      </div>
    `;
    grid.appendChild(card);
  });

  // Issues
  const issuesList = document.getElementById("init-issues-list");
  issuesList.innerHTML = "";
  if (diag.key_issues && diag.key_issues.length > 0) {
    diag.key_issues.forEach((iss) => {
      const li = document.createElement("li");
      li.textContent = iss;
      issuesList.appendChild(li);
    });
  } else {
    issuesList.innerHTML = "<li>Nenhum problema grave detectado.</li>";
  }

  // Positives
  const positivesList = document.getElementById("init-positives-list");
  positivesList.innerHTML = "";
  if (diag.positive_points && diag.positive_points.length > 0) {
    diag.positive_points.forEach((pos) => {
      const li = document.createElement("li");
      li.textContent = pos;
      positivesList.appendChild(li);
    });
  } else {
    positivesList.innerHTML = "<li>A estrutura requer melhorias substanciais para leitura ATS.</li>";
  }

  // Recommendations
  const recsList = document.getElementById("init-recs-list");
  recsList.innerHTML = "";
  if (diag.initial_recommendations && diag.initial_recommendations.length > 0) {
    diag.initial_recommendations.forEach((rec) => {
      const li = document.createElement("li");
      li.textContent = rec;
      recsList.appendChild(li);
    });
  } else {
    recsList.innerHTML = "<li>Otimize a formatação e inclua palavras-chave estratégicas.</li>";
  }
}

// -------------------------------------------------------------
// SECTION C: OPTIMIZATION WORKFLOW
// -------------------------------------------------------------
function initOptimization() {
  const btn = document.getElementById("btn-improve-cv");
  btn.addEventListener("click", runOptimizationFlow);
}

async function runOptimizationFlow() {
  if (!currentSessionId) return;

  const btn = document.getElementById("btn-improve-cv");
  btn.disabled = true;
  btn.innerHTML = `<span class="step-spinner"></span> Otimizando seu currículo...`;

  const stepsContainer = document.getElementById("steps-container");
  stepsContainer.style.display = "block";
  const stepsList = document.getElementById("steps-list");
  stepsList.innerHTML = "";

  const plannedSteps = [
    "1. Leitura e extração estrutural da fonte da verdade",
    "2. Higienização e remoção de dados desencorajados pelo ATS",
    "3. Reorganização em seções padronizadas",
    "4. Refatoração de descrições com verbos de ação",
    "5. Mapeamento de competências e palavras-chave sustentadas",
    "6. Inspeção posterior com os mesmos critérios objetivos",
    "7. Validação estrita de preservação factual",
    "8. Geração da nova versão estruturada"
  ];

  // Animate real progress
  for (let i = 0; i < plannedSteps.length - 1; i++) {
    const item = document.createElement("div");
    item.className = "step-item";
    item.innerHTML = `<span class="step-check">✔</span> <span>${plannedSteps[i]}</span>`;
    stepsList.appendChild(item);
    await new Promise((r) => setTimeout(r, 220));
  }

  try {
    const res = await fetch("/api/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: currentSessionId })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Erro durante otimização.");
    }

    const data = await res.json();
    currentPostDiagnosis = data.post_diagnosis;
    currentComparison = data.comparison;

    // Final step complete
    const finalItem = document.createElement("div");
    finalItem.className = "step-item";
    finalItem.innerHTML = `<span class="step-check">✔</span> <span>${plannedSteps[plannedSteps.length - 1]}</span>`;
    stepsList.appendChild(finalItem);

    // Section D: Inspeção posterior à otimização
    renderPostInspection(data.post_diagnosis, data.preservation);

    // Section E: Comparação antes e depois
    renderComparison(data.comparison);

    // Section F: Recomendações finais
    renderFinalRecommendations(data.comparison.human_recommendations);

    // Section H: Revisão manual (carrega texto no editor)
    renderManualReview(data.optimized_text);

    // Section G: Exportação dos documentos
    setupExportLinks(currentSessionId);

    // Scroll smoothly to Post Inspection
    document.getElementById("section-post-inspection").scrollIntoView({ behavior: "smooth" });

  } catch (err) {
    alert("Erro na otimização: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>✨ Melhorar CV (Executado)</span>`;
  }
}

// -------------------------------------------------------------
// SECTION D: POST INSPECTION
// -------------------------------------------------------------
function renderPostInspection(postDiag, preservation) {
  const sec = document.getElementById("section-post-inspection");
  sec.classList.remove("hidden");

  // Preservation bullet update
  const presBullet = document.getElementById("preservation-check-bullet");
  if (preservation && preservation.is_valid) {
    presBullet.innerHTML = `✔ <strong>Preservação factual comprovada:</strong> ${preservation.details.join("; ")}`;
  } else if (preservation && preservation.hallucination_warnings.length > 0) {
    presBullet.innerHTML = `⚠️ <strong>Avisos de preservação:</strong> ${preservation.hallucination_warnings.join("; ")}`;
  }

  // Criteria Grid for Post Inspection
  const grid = document.getElementById("post-criteria-grid");
  grid.innerHTML = "";
  postDiag.criteria.forEach((c) => {
    const card = document.createElement("div");
    card.className = "criterion-card";
    const statusColor = c.percentage >= 80 ? "var(--success)" : (c.percentage >= 60 ? "var(--warning)" : "var(--danger)");
    card.innerHTML = `
      <div class="criterion-top">
        <span class="criterion-name">${c.name}</span>
        <span class="criterion-val" style="color: ${statusColor}">${c.score}/${c.max_score}</span>
      </div>
      <div class="progress-bar-bg" style="height: 6px;">
        <div class="progress-bar-fill" style="width: ${c.percentage}%; background-color: ${statusColor}"></div>
      </div>
      <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 6px;">
        Status: <strong style="color: ${statusColor}">${c.status}</strong> (${c.percentage}%)
      </div>
    `;
    grid.appendChild(card);
  });
}

// -------------------------------------------------------------
// SECTION E: COMPARISON BEFORE & AFTER
// -------------------------------------------------------------
function renderComparison(comp) {
  const sec = document.getElementById("section-comparison");
  sec.classList.remove("hidden");

  document.getElementById("comp-score-before").textContent = comp.original_score;
  document.getElementById("comp-score-after").textContent = comp.optimized_score;
  const deltaVal = comp.absolute_delta;
  const deltaBadge = document.getElementById("comp-score-delta");
  deltaBadge.textContent = `${deltaVal >= 0 ? "+" : ""}${deltaVal} pts`;
  deltaBadge.style.color = deltaVal > 0 ? "var(--accent)" : "var(--text-muted)";

  // Criteria Comparison Table
  const tbody = document.getElementById("comp-table-body");
  tbody.innerHTML = "";

  comp.criteria_comparison.forEach((c) => {
    const tr = document.createElement("tr");
    const deltaStr = c.delta > 0 ? `+${c.delta}` : `${c.delta}`;
    const deltaClass = c.delta > 0 ? "delta-positive" : "delta-neutral";

    tr.innerHTML = `
      <td><strong>${c.name}</strong></td>
      <td>${c.before_score} / ${c.max_score}</td>
      <td><strong>${c.after_score}</strong> / ${c.max_score}</td>
      <td><span class="delta-badge ${deltaClass}">${deltaStr}</span></td>
      <td style="min-width: 140px;">
        <div class="progress-bar-bg" style="height: 8px; margin-top: 0;">
          <div class="progress-bar-fill" style="width: ${c.progress_percentage}%; background-color: var(--success);"></div>
        </div>
        <span style="font-size: 0.75rem; color: var(--text-muted);">${c.progress_percentage}% atingido</span>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Issue Resolution Box
  const resContainer = document.getElementById("comp-issues-resolution");
  resContainer.innerHTML = "";

  // Resolved
  if (comp.resolved_issues && comp.resolved_issues.length > 0) {
    comp.resolved_issues.forEach((r) => {
      const d = document.createElement("div");
      d.style.padding = "10px 14px";
      d.style.background = "#f0fdf4";
      d.style.border = "1px solid #bbf7d0";
      d.style.borderRadius = "var(--radius-sm)";
      d.innerHTML = `
        <span class="issue-status-badge status-resolved">Resolvido</span>
        <strong style="margin-left: 8px; font-size: 0.9rem;">${r.issue}</strong>
        <p style="font-size: 0.85rem; color: #166534; margin-top: 4px;">${r.explanation}</p>
      `;
      resContainer.appendChild(d);
    });
  }

  // Partially resolved
  if (comp.partially_resolved_issues && comp.partially_resolved_issues.length > 0) {
    comp.partially_resolved_issues.forEach((p) => {
      const d = document.createElement("div");
      d.style.padding = "10px 14px";
      d.style.background = "#fffbeb";
      d.style.border = "1px solid #fde68a";
      d.style.borderRadius = "var(--radius-sm)";
      d.innerHTML = `
        <span class="issue-status-badge status-partial">Parcialmente Resolvido</span>
        <strong style="margin-left: 8px; font-size: 0.9rem;">${p.issue}</strong>
        <p style="font-size: 0.85rem; color: #92400e; margin-top: 4px;">${p.explanation}</p>
      `;
      resContainer.appendChild(d);
    });
  }

  // Unresolved (preservation / missing original data)
  if (comp.unresolved_issues && comp.unresolved_issues.length > 0) {
    comp.unresolved_issues.forEach((u) => {
      const d = document.createElement("div");
      d.style.padding = "10px 14px";
      d.style.background = "#f8fafc";
      d.style.border = "1px solid #cbd5e1";
      d.style.borderRadius = "var(--radius-sm)";
      d.innerHTML = `
        <span class="issue-status-badge status-unresolved">Ação Humana Necessária</span>
        <strong style="margin-left: 8px; font-size: 0.9rem;">${u.issue}</strong>
        <p style="font-size: 0.85rem; color: #475569; margin-top: 4px;">${u.explanation}</p>
      `;
      resContainer.appendChild(d);
    });
  }
}

// -------------------------------------------------------------
// SECTION F: FINAL RECOMMENDATIONS (HUMAN INTERVENTION)
// -------------------------------------------------------------
function renderFinalRecommendations(recs) {
  const sec = document.getElementById("section-recommendations");
  sec.classList.remove("hidden");

  const container = document.getElementById("final-recs-container");
  container.innerHTML = "";

  if (!recs || recs.length === 0) {
    container.innerHTML = "<p>Nenhuma pendência crítica identificada.</p>";
    return;
  }

  const priorities = [
    { key: "alta", title: "1. Alta Prioridade — Informações Importantes Ausentes / Confirmação Necessária", badgeBg: "#fee2e2", badgeCol: "#b91c1c" },
    { key: "media", title: "2. Média Prioridade — Melhorias de Conteúdo e Detalhamento", badgeBg: "#fef3c7", badgeCol: "#b45309" },
    { key: "baixa", title: "3. Baixa Prioridade — Refinamentos de Escrita e Organização", badgeBg: "#e0f2fe", badgeCol: "#0369a1" }
  ];

  priorities.forEach((pGroup) => {
    const items = recs.filter((r) => r.priority === pGroup.key);
    if (items.length > 0) {
      const gTitle = document.createElement("h4");
      gTitle.style.margin = "18px 0 10px";
      gTitle.style.color = "var(--primary)";
      gTitle.textContent = pGroup.title;
      container.appendChild(gTitle);

      items.forEach((item) => {
        const card = document.createElement("div");
        card.className = `rec-card p-${item.priority}`;
        card.innerHTML = `
          <div class="rec-header">
            <span class="rec-title">${item.title}</span>
            <span class="rec-priority-badge" style="background: ${pGroup.badgeBg}; color: ${pGroup.badgeCol};">
              ${item.priority.toUpperCase()}
            </span>
          </div>
          <div class="rec-detail-row">
            <span class="rec-label">Qual é o problema:</span> ${item.problem}
          </div>
          <div class="rec-detail-row">
            <span class="rec-label">Por que importa:</span> ${item.why_matters}
          </div>
          <div class="rec-detail-row">
            <span class="rec-label">O que você pode fazer:</span> ${item.what_to_do}
          </div>
          ${item.example ? `
            <div class="rec-example">
              <strong>Exemplo prático de melhoria:</strong> "${item.example}"
            </div>
          ` : ""}
        `;
        container.appendChild(card);
      });
    }
  });
}

// -------------------------------------------------------------
// SECTION H: MANUAL REVIEW & LIVE RE-ANALYSIS
// -------------------------------------------------------------
function renderManualReview(optText) {
  const sec = document.getElementById("section-manual-review");
  sec.classList.remove("hidden");

  const editor = document.getElementById("cv-editor");
  editor.value = optText;
  document.getElementById("editor-status").textContent = "";
}

function initManualReview() {
  const reanalyzeBtn = document.getElementById("btn-reanalyze");
  reanalyzeBtn.addEventListener("click", async () => {
    if (!currentSessionId) return;

    const editor = document.getElementById("cv-editor");
    const editedText = editor.value.trim();
    if (!editedText) {
      alert("O texto do currículo não pode estar vazio.");
      return;
    }

    reanalyzeBtn.disabled = true;
    reanalyzeBtn.textContent = "Reavaliando...";

    try {
      const res = await fetch("/api/manual-edit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentSessionId,
          edited_text: editedText
        })
      });

      if (!res.ok) {
        throw new Error("Erro ao salvar alterações manuais.");
      }

      const data = await res.json();
      currentPostDiagnosis = data.post_diagnosis;
      currentComparison = data.comparison;

      // Dynamically update Post Inspection (D) & Comparison (E)
      renderPostInspection(data.post_diagnosis, data.preservation);
      renderComparison(data.comparison);
      renderFinalRecommendations(data.comparison.human_recommendations);

      const statusEl = document.getElementById("editor-status");
      statusEl.textContent = `✔ Alterações salvas com sucesso! Nova pontuação recalculada: ${data.post_diagnosis.overall_score}/100`;

      setTimeout(() => {
        statusEl.textContent = "";
      }, 5000);

    } catch (err) {
      alert(err.message);
    } finally {
      reanalyzeBtn.disabled = false;
      reanalyzeBtn.innerHTML = "🔄 Salvar e Reavaliar Pontuação";
    }
  });
}

// -------------------------------------------------------------
// SECTION G: EXPORT DOWNLOAD BUTTONS
// -------------------------------------------------------------
function setupExportLinks(sessionId) {
  const sec = document.getElementById("section-export");
  sec.classList.remove("hidden");

  document.getElementById("btn-download-docx").href = `/api/export/docx?session_id=${sessionId}`;
  document.getElementById("btn-download-pdf").href = `/api/export/pdf?session_id=${sessionId}`;
  document.getElementById("btn-download-report").href = `/api/export/report?session_id=${sessionId}`;
  document.getElementById("btn-download-checklist").href = `/api/export/checklist?session_id=${sessionId}`;
}
