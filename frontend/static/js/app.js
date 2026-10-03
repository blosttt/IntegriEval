/* ======================================================================
   IntegriEval — App Logic v2.0
   ====================================================================== */

let currentToken = localStorage.getItem("token") || null;
let currentUser   = null;
let currentCourseId = null;
let activeTab     = "panel";
let panelData     = null;
let teacherWS     = null;

/* ── Toast system ───────────────────────────────────────────────────── */
function showToast(title, msg = "", type = "info") {
  const icons = { info: "ℹ️", success: "✅", warning: "⚠️", error: "❌" };
  const el = document.createElement("div");
  el.className = "toast";
  el.innerHTML = `
    <div class="toast-icon">${icons[type] || icons.info}</div>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      ${msg ? `<div class="toast-msg">${msg}</div>` : ""}
    </div>`;
  document.getElementById("toast-container").appendChild(el);
  setTimeout(() => {
    el.classList.add("toast-out");
    el.addEventListener("animationend", () => el.remove());
  }, 4000);
}

/* ── API helper ─────────────────────────────────────────────────────── */
async function apiCall(endpoint, method = "GET", body = null, isFormData = false) {
  const headers = {};
  if (currentToken) headers["Authorization"] = `Bearer ${currentToken}`;
  if (!isFormData && body) headers["Content-Type"] = "application/json";

  const resp = await fetch(endpoint, {
    method,
    headers,
    body: isFormData ? body : (body ? JSON.stringify(body) : null)
  });

  if (resp.status === 401) { logout(); throw new Error("Sesión expirada"); }
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "Error desconocido" }));
    throw new Error(err.detail || "Error en la solicitud");
  }
  return resp.json();
}

/* ── Theme ──────────────────────────────────────────────────────────── */
function initTheme() {
  const saved = localStorage.getItem("theme") || "light";
  applyTheme(saved);
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const icon = theme === "dark" ? "☀️" : "🌙";
  document.querySelectorAll("#theme-icon, #headerThemeIcon").forEach(el => el && (el.textContent = icon));
}

function toggleTheme() {
  const cur  = document.documentElement.getAttribute("data-theme");
  const next = cur === "dark" ? "light" : "dark";
  localStorage.setItem("theme", next);
  applyTheme(next);
}

/* ── Init ───────────────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", async () => {
  initTheme();
  if (currentToken) {
    await checkAuth();
  } else {
    showLogin();
  }
});

function showLogin()  {
  document.getElementById("loginScreen").style.display = "";
  document.getElementById("mainApp").style.display = "none";
}

function showApp() {
  document.getElementById("loginScreen").style.display = "none";
  document.getElementById("mainApp").style.display = "";
}

/* ── Auth ───────────────────────────────────────────────────────────── */
async function checkAuth() {
  try {
    currentUser = await apiCall("/api/auth/me");
    applyUserUI();
    showApp();
    await loadCourses();
  } catch { showLogin(); }
}

function applyUserUI() {
  if (!currentUser) return;
  const nameEl = document.getElementById("userDisplay");
  const avatarEl = document.getElementById("userAvatarText");
  const roleBadge = document.getElementById("userRoleBadge");

  if (nameEl) nameEl.textContent = (currentUser.nombre || "Docente").toUpperCase();
  if (avatarEl) {
    const parts = (currentUser.nombre || "Docente").split(" ");
    avatarEl.textContent = (parts[0][0] + (parts[1]?.[0] || "")).toUpperCase();
  }

  // Role badge exact style (Screenshot 2: gold Administrador)
  if (roleBadge) {
    if (currentUser.rol === "admin") {
      roleBadge.className = "role-badge-gold";
      roleBadge.textContent = "Administrador";
    } else if (currentUser.rol === "ayudante") {
      roleBadge.className = "role-badge-blue";
      roleBadge.textContent = "Ayudante";
    } else {
      roleBadge.className = "role-badge-green";
      roleBadge.textContent = "Docente";
    }
  }
}

/* ── UCT UI & Guided Workflow Helpers ──────────────────────────────────── */
function toggleProfLogin() {
  const box = document.getElementById("profOptionsBox");
  if (!box) return;
  const isHidden = box.style.display === "none";
  box.style.display = isHidden ? "block" : "none";
  const btn = document.getElementById("btnProfToggle");
  if (btn) btn.style.borderColor = isHidden ? "var(--brand-blue)" : "";
}

function openStudentDialog() {
  const m = document.getElementById("studentDialogModal");
  if (m) m.style.display = "flex";
}

function goToManualStudentTest() {
  const token = document.getElementById("manualStudentToken")?.value?.trim();
  if (!token) {
    showToast("Aviso", "Por favor ingresa un token válido de Flash Test.", "info");
    return;
  }
  window.open(`/test/${token}`, "_blank");
}

function scrollToWorkflow() {
  switchTab("panel");
  const el = document.getElementById("workflowGuideAnchor");
  if (el) el.scrollIntoView({ behavior: "smooth" });
}

/* Demo quick-fill */
function fillDemo(email, password) {
  document.getElementById("loginEmail").value    = email;
  document.getElementById("loginPassword").value = password;
  // Auto-submit
  handleLogin({ preventDefault: () => {} });
}


async function handleLogin(e) {
  e.preventDefault();
  const btn    = document.getElementById("loginBtn");
  const errEl  = document.getElementById("loginError");
  const errMsg = document.getElementById("loginErrorMsg");
  errEl.style.display = "none";
  if (btn) { btn.textContent = "Iniciando sesión…"; btn.disabled = true; }

  try {
    const res = await apiCall("/api/auth/login", "POST", {
      correo:     document.getElementById("loginEmail").value,
      contrasena: document.getElementById("loginPassword").value
    });
    currentToken = res.access_token;
    localStorage.setItem("token", currentToken);
    currentUser = res.user;
    applyUserUI();
    showApp();
    await loadCourses();
    showToast("Bienvenido", currentUser.nombre, "success");
  } catch (err) {
    errMsg.textContent = err.message;
    errEl.style.display = "flex";
  } finally {
    if (btn) { btn.textContent = "Iniciar sesión"; btn.disabled = false; }
  }
}

function logout() {
  currentToken = null;
  localStorage.removeItem("token");
  if (teacherWS) { teacherWS.close(); teacherWS = null; }
  currentUser = null; currentCourseId = null;
  showLogin();
}

/* ── Courses ─────────────────────────────────────────────────────────  */
async function loadCourses() {
  const courses = await apiCall("/api/asignaturas");
  const select  = document.getElementById("courseSelect");
  if (!select) return;
  select.innerHTML = "";

  if (courses.length === 0) { showNewCourseModal(); return; }

  courses.forEach(c => {
    const opt = document.createElement("option");
    opt.value     = c.id;
    opt.textContent = `${c.nombre} (${c.periodo} ${c.ano})`;
    select.appendChild(opt);
  });

  currentCourseId = courses[0].id;
  connectTeacherWS(currentCourseId);
  switchTab(activeTab);
}

function onCourseChange() {
  const sel = document.getElementById("courseSelect");
  currentCourseId = parseInt(sel.value);
  connectTeacherWS(currentCourseId);
  switchTab(activeTab);
}

/* ── WebSocket Live Updates ──────────────────────────────────────────── */
function connectTeacherWS(courseId) {
  if (teacherWS) { teacherWS.close(); teacherWS = null; }
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  teacherWS = new WebSocket(`${proto}//${location.host}/ws/panel/${courseId}`);

  teacherWS.onopen  = () => {
    const b = document.getElementById("wsStatusBadge");
    if (b) { b.textContent = "● En vivo"; b.className = "badge badge-green"; }
  };
  teacherWS.onclose = () => {
    const b = document.getElementById("wsStatusBadge");
    if (b) { b.textContent = "○ Desconectado"; b.className = "badge badge-gray"; }
    setTimeout(() => connectTeacherWS(courseId), 3000);
  };
  teacherWS.onmessage = e => {
    const data = JSON.parse(e.data);
    if (data.type === "STUDENT_TEST_FINISHED" && activeTab === "panel") {
      loadPanel();
      showToast("Flash Test completado", `Estudiante ID #${data.estudiante_id} finalizó`, "success");
    }
  };
}

/* ── Tabs ────────────────────────────────────────────────────────────── */
function switchTab(tabId) {
  activeTab = tabId;
  document.querySelectorAll(".nav-tab").forEach(btn =>
    btn.classList.toggle("active", btn.dataset.tab === tabId));

  const tabs = ["panel","nomina","materiales","evaluacion","preguntas","auditoria","config"];
  tabs.forEach(t => {
    const el = document.getElementById(`tabContent_${t}`);
    if (el) el.style.display = (t === tabId) ? "" : "none";
  });

  // Highlight current step in the workflow guide
  const stepMap = {
    nomina:     "wfStep1",
    materiales: "wfStep2",
    evaluacion: "wfStep3",
    preguntas:  "wfStep4",
    panel:      "wfStep5"
  };
  [1, 2, 3, 4, 5].forEach(num => {
    const card = document.getElementById(`wfStep${num}`);
    if (card) card.classList.remove("active");
  });
  if (stepMap[tabId]) {
    const activeCard = document.getElementById(stepMap[tabId]);
    if (activeCard) activeCard.classList.add("active");
  }

  const loaders = {
    panel:      loadPanel,
    nomina:     loadNomina,
    materiales: loadMateriales,
    evaluacion: loadEvaluacion,
    preguntas:  loadPreguntas,
    auditoria:  loadAuditoria,
    config:     loadConfig,
  };
  if (loaders[tabId]) loaders[tabId]();
}

/* ══ TAB 1 — Panel ══════════════════════════════════════════════════════ */
async function loadPanel() {
  if (!currentCourseId) return;
  try {
    panelData = await apiCall(`/api/asignaturas/${currentCourseId}/panel`);

    setStatVal("statTotalAlumnos",    panelData.total_alumnos);
    setStatVal("statAnalizados",      panelData.analizados);
    setStatVal("statAlertaIA",        panelData.alerta_ia);
    setStatVal("statReqDefensa",      panelData.requieren_defensa);
    setStatVal("statTestsCompletados",panelData.tests_completados);
    setStatVal("statNotasCerradas",   panelData.notas_cerradas);

    renderPanelTable(panelData.estudiantes);
    updateWorkflowGuide(panelData);
  } catch (err) {
    showToast("Error cargando panel", err.message, "error");
  }
}

function updateWorkflowGuide(data) {
  if (!data) return;
  // Step 1: Nomina
  const b1 = document.getElementById("wfBadge1");
  if (b1) {
    if (data.total_alumnos > 0) {
      b1.className = "wf-step-badge wf-badge-done";
      b1.textContent = `✓ ${data.total_alumnos} inscritos`;
    } else {
      b1.className = "wf-step-badge wf-badge-pending";
      b1.textContent = "0 inscritos";
    }
  }

  // Step 2: Materiales
  const b2 = document.getElementById("wfBadge2");
  if (b2) {
    b2.className = "wf-step-badge wf-badge-done";
    b2.textContent = "✓ Syllabus activo";
  }

  // Step 3: Informes
  const b3 = document.getElementById("wfBadge3");
  if (b3) {
    if (data.analizados > 0) {
      b3.className = "wf-step-badge wf-badge-done";
      b3.textContent = `✓ ${data.analizados} analizados`;
    } else {
      b3.className = "wf-step-badge wf-badge-pending";
      b3.textContent = "0 analizados";
    }
  }

  // Step 4: Flash Tests
  const b4 = document.getElementById("wfBadge4");
  if (b4) {
    if (data.tests_completados > 0) {
      b4.className = "wf-step-badge wf-badge-done";
      b4.textContent = `✓ ${data.tests_completados} respondidos`;
    } else {
      b4.className = "wf-step-badge wf-badge-pending";
      b4.textContent = "0 despachados";
    }
  }

  // Step 5: Panel & % Logro
  const b5 = document.getElementById("wfBadge5");
  if (b5) {
    if (data.notas_cerradas > 0) {
      b5.className = "wf-step-badge wf-badge-done";
      b5.textContent = `✓ ${data.notas_cerradas} confirmados`;
    } else {
      b5.className = "wf-step-badge wf-badge-active";
      b5.textContent = "Monitoreo activo";
    }
  }
}


function setStatVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function renderPanelTable(estudiantes) {
  const tbody  = document.getElementById("panelTableBody");
  const filter = document.getElementById("filterSelect")?.value || "todos";

  const filtered = estudiantes.filter(s => {
    if (filter === "defensa")   return s.requiere_defensa;
    if (filter === "alerta_ia") return s.pct_ia !== null && s.pct_ia >= 40;
    if (filter === "cerradas")  return s.nota_cerrada;
    return true;
  });

  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state">
      <div class="empty-icon">🔍</div>
      <div class="empty-title">Sin estudiantes con ese filtro</div>
    </div></td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(s => {
    /* IA badge */
    let iaBadge = `<span class="badge badge-gray">Pendiente</span>`;
    if (s.pct_ia !== null) {
      if (s.pct_ia >= 50) iaBadge = `<span class="badge badge-red">⚠ ${s.pct_ia}% <span style="opacity:.7;font-weight:400;">${s.confianza_ia}</span></span>`;
      else if (s.pct_ia >= 35) iaBadge = `<span class="badge badge-amber">⚡ ${s.pct_ia}%</span>`;
      else iaBadge = `<span class="badge badge-green">✓ ${s.pct_ia}%</span>`;
    }

    /* Flash badge */
    let flashBadge = `<span class="badge badge-gray">Sin test</span>`;
    if (s.puntaje_flash !== null) {
      if (s.puntaje_flash >= 70)     flashBadge = `<span class="badge badge-green">✓ ${s.puntaje_flash}%</span>`;
      else if (s.puntaje_flash >= 50) flashBadge = `<span class="badge badge-amber">⚡ ${s.puntaje_flash}%</span>`;
      else                            flashBadge = `<span class="badge badge-red">✗ ${s.puntaje_flash}%</span>`;
    }

    /* Decision */
    const defBadge = s.requiere_defensa
      ? `<span class="badge badge-red">Defensa oral</span>`
      : `<span class="badge badge-green">Validado</span>`;

    /* Cita */
    let citaBadge = `<span class="text-xs text-muted">—</span>`;
    if (s.cita_bloque) {
      const estadoColor = { programada: "blue", realizada: "green", ausente: "red", cancelada: "gray" };
      citaBadge = `<span class="badge badge-${estadoColor[s.cita_estado] || "gray"}" title="${s.cita_fecha || ''}">${s.cita_bloque}</span>`;
    }

    /* % de Logro */
    const rawVal = s.nota_cerrada ? (s.pct_logro_final ?? s.pct_logro) : s.pct_logro;
    let logroNum = rawVal != null ? Math.round(Number(rawVal)) : null;
    if (logroNum === null && s.porcentaje_logro) {
      const parsed = parseInt(String(s.porcentaje_logro).replace('%', ''));
      if (!isNaN(parsed)) logroNum = parsed;
    }
    if (logroNum === null && s.nota_preliminar != null) {
      logroNum = s.nota_preliminar >= 4.0
        ? Math.round(60 + (s.nota_preliminar - 4.0) * (40 / 3))
        : Math.round(Math.max(0, (s.nota_preliminar - 1.0) * (60 / 3)));
    }

    let logroDisplay = "—";
    if (logroNum !== null) {
      if (s.nota_cerrada) {
        logroDisplay = `<strong>${logroNum}%</strong> <span class="badge badge-green" style="font-size:.65rem;padding:1px 5px;" title="Evaluación confirmada">✓ Confirmado</span>`;
      } else {
        logroDisplay = `<strong>${logroNum}%</strong>`;
      }
    }

    return `
    <tr>
      <td>
        <div class="font-medium" style="color:var(--text);">${s.estudiante_nombre}</div>
        <div class="text-xs text-muted truncate" style="max-width:180px;">${s.estudiante_correo}</div>
      </td>
      <td>${logroDisplay}</td>
      <td>${iaBadge}</td>
      <td>${flashBadge}</td>
      <td>${defBadge}</td>
      <td>${citaBadge}</td>
      <td>
        <div class="row-actions">
          <button class="btn btn-secondary btn-sm" onclick="openAnexoAModal(${s.estudiante_id})" data-tooltip="Ver Anexo A">🔍</button>
          <button class="btn btn-secondary btn-sm" onclick="openCitaModal(${s.estudiante_id},'${s.estudiante_nombre.replace(/'/g,"\\'")}')" data-tooltip="Citar a defensa">📅</button>
          <button class="btn btn-primary btn-sm"   onclick="openCierreModal(${s.estudiante_id},'${s.estudiante_nombre.replace(/'/g,"\\'")}',${logroNum ?? 60})" data-tooltip="Confirmar % Logro">✍</button>
        </div>
      </td>
    </tr>`;
  }).join("");
}

/* ── Anexo A modal ───────────────────────────────────────────────────── */
async function openAnexoAModal(studentId) {
  try {
    const data = await apiCall(`/api/asignaturas/${currentCourseId}/estudiantes/${studentId}/evaluacion`);
    const d = data.desglose || {};
    const det = d.deteccion_ia || {};
    const fb  = d.feedback || {};
    const dr  = d.desglose_rubrica || {};
    const er  = d.evaluacion_respuestas || {};

    document.getElementById("anexoAContainer").innerHTML = `
      <!-- Metrics row -->
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:1.25rem;">
        <div class="stat-card c-blue" style="margin:0;padding:1rem;">
          <div class="stat-label">Porcentaje de logro</div>
          <div class="stat-value" style="font-size:1.5rem;">${d.porcentaje_logro || "—"}</div>
          <div class="text-xs text-muted">Evaluación de informe</div>
        </div>
        <div class="stat-card c-red" style="margin:0;padding:1rem;">
          <div class="stat-label">Detección IA</div>
          <div class="stat-value" style="font-size:1.5rem;">${det.porcentaje || "—"}</div>
          <div class="text-xs text-muted">Confianza: ${det.nivel_confianza || "—"}</div>
        </div>
        <div class="stat-card ${er.requiere_defensa_oral ? "c-amber" : "c-green"}" style="margin:0;padding:1rem;">
          <div class="stat-label">Coherencia Flash</div>
          <div class="stat-value" style="font-size:1.5rem;">${er.porcentaje_coherencia || "—"}</div>
          <div class="text-xs text-muted">${er.requiere_defensa_oral ? "⚠ Requiere defensa" : "✓ Validado"}</div>
        </div>
      </div>

      <!-- Feedback accordion -->
      <div class="anexo-section">
        <div class="anexo-section-header" onclick="toggleAnexo(this)">
          <span>💬 Feedback Pedagógico Estructurado</span><span>▼</span>
        </div>
        <div class="anexo-section-body">
          <div style="margin-bottom:.75rem;">
            <div class="text-xs font-medium text-muted mb-2" style="text-transform:uppercase;">Fortalezas</div>
            ${(fb.fortalezas||[]).map(f=>`<div class="feedback-item"><span style="color:var(--success);">✓</span><span>${f}</span></div>`).join("")}
          </div>
          <div style="margin-bottom:.75rem;">
            <div class="text-xs font-medium text-muted mb-2" style="text-transform:uppercase;">Debilidades</div>
            ${(fb.debilidades||[]).map(f=>`<div class="feedback-item"><span style="color:var(--warning);">⚠</span><span>${f}</span></div>`).join("")}
          </div>
          <div>
            <div class="text-xs font-medium text-muted mb-2" style="text-transform:uppercase;">Recomendaciones</div>
            ${(fb.recomendaciones||[]).map(f=>`<div class="feedback-item"><span style="color:var(--brand-blue);">💡</span><span>${f}</span></div>`).join("")}
          </div>
        </div>
      </div>

      <!-- IA section -->
      <div class="anexo-section">
        <div class="anexo-section-header" onclick="toggleAnexo(this)">
          <span>🤖 Análisis de Detección IA</span><span>▼</span>
        </div>
        <div class="anexo-section-body">
          <p class="text-sm" style="margin-bottom:.5rem;">${det.justificacion || "Sin observaciones"}</p>
          <p class="text-xs text-muted"><strong>Secciones observadas:</strong> ${(det.secciones_sospechosas||[]).join(", ") || "Ninguna"}</p>
        </div>
      </div>

      <!-- Rúbrica -->
      <div class="anexo-section">
        <div class="anexo-section-header" onclick="toggleAnexo(this)">
          <span>📐 Desglose de Rúbrica</span><span>▼</span>
        </div>
        <div class="anexo-section-body" style="display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;">
          ${Object.entries(dr).map(([k,v])=>`
            <div style="text-align:center;">
              <div class="text-xs text-muted" style="text-transform:uppercase;margin-bottom:.25rem;">${k}</div>
              <div style="font-size:1.25rem;font-weight:800;color:var(--brand-blue);">${v}</div>
            </div>`).join("")}
        </div>
      </div>

      <!-- Evaluación respuestas -->
      <div class="anexo-section">
        <div class="anexo-section-header" onclick="toggleAnexo(this)">
          <span>⚡ Evaluación de Respuestas Flash</span><span>▼</span>
        </div>
        <div class="anexo-section-body">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-bottom:.75rem;">
            <div><span class="text-xs text-muted">Correctas:</span> <strong>${er.respuestas_correctas||"—"}</strong></div>
            <div><span class="text-xs text-muted">Rigor:</span> <strong>${er.nivel_rigor_aplicado||"—"}</strong></div>
          </div>
          <p class="text-sm text-muted">${er.observacion_ia||"Sin observaciones"}</p>
          ${(er.preguntas_falladas||[]).length ? `
            <div style="margin-top:.75rem;">
              <div class="text-xs text-muted font-medium" style="text-transform:uppercase;margin-bottom:.5rem;">Preguntas falladas</div>
              ${er.preguntas_falladas.map(p=>`<div class="feedback-item"><span style="color:var(--danger);">✗</span><span>${p}</span></div>`).join("")}
            </div>` : ""}
        </div>
      </div>
    `;

    document.getElementById("anexoAModal").style.display = "flex";
  } catch {
    showToast("Sin evaluación", "Este estudiante aún no tiene un informe evaluado.", "warning");
  }
}

function toggleAnexo(header) {
  const body = header.nextElementSibling;
  const arrow = header.querySelector("span:last-child");
  body.style.display = body.style.display === "none" ? "" : "none";
  arrow.textContent  = body.style.display === "none" ? "▶" : "▼";
}

/* ── Cita modal ─────────────────────────────────────────────────────── */
function openCitaModal(studentId, studentName) {
  document.getElementById("citaStudentId").value   = studentId;
  document.getElementById("citaStudentName").textContent = studentName;
  document.getElementById("citaDate").value        = new Date().toISOString().split("T")[0];
  document.getElementById("citaBloque").value      = "10:00 - 10:15";
  document.getElementById("citaAcuerdos").value    = "";
  document.getElementById("citaModal").style.display = "flex";
}

async function submitCita(e) {
  e.preventDefault();
  try {
    await apiCall(`/api/asignaturas/${currentCourseId}/citas`, "POST", {
      estudiante_id: parseInt(document.getElementById("citaStudentId").value),
      fecha:  new Date(document.getElementById("citaDate").value).toISOString(),
      bloque: document.getElementById("citaBloque").value,
      acuerdos: document.getElementById("citaAcuerdos").value
    });
    closeModal("citaModal");
    loadPanel();
    showToast("Cita agendada", "La defensa oral fue registrada.", "success");
  } catch (err) { showToast("Error", err.message, "error"); }
}

/* ── Cierre modal (% Logro) ────────────────────────────────────────── */
function openCierreModal(studentId, studentName, currentLogro) {
  document.getElementById("cierreStudentId").value       = studentId;
  document.getElementById("cierreStudentName").textContent = studentName;
  const logroNum = currentLogro != null ? Math.round(Number(currentLogro)) : 60;
  document.getElementById("cierreLogro").value           = logroNum;
  document.getElementById("cierreJustificacion").value   = "Criterio del docente";
  document.getElementById("cierreModal").style.display   = "flex";
}

async function submitCierreNota(e) {
  e.preventDefault();
  try {
    const logroVal = parseFloat(document.getElementById("cierreLogro").value);
    const res = await apiCall(`/api/asignaturas/${currentCourseId}/cerrar-nota`, "POST", {
      estudiante_id: parseInt(document.getElementById("cierreStudentId").value),
      nota_final:    logroVal,
      justificacion: document.getElementById("cierreJustificacion").value
    });
    closeModal("cierreModal");
    loadPanel();
    showToast("Evaluación confirmada", `${logroVal}% de logro registrado con éxito.`, "success");
  } catch (err) { showToast("Error", err.message, "error"); }
}

/* ── Dispatch Flash Tests ────────────────────────────────────────────── */
async function handleDispatchFlashTests() {
  const btn = document.getElementById("dispatchBtn");
  btn.textContent = "Despachando…"; btn.disabled = true;

  try {
    const res = await apiCall(`/api/asignaturas/${currentCourseId}/flash-test/despacho`, "POST");
    btn.textContent = "⚡ Despachar Flash Tests"; btn.disabled = false;

    if (res.total_despachados === 0) {
      showToast("Sin tests para despachar", "Evalúa al menos un informe primero.", "warning");
      return;
    }

    document.getElementById("dispatchLinksContainer").innerHTML = `
      <div class="callout callout-green mb-4">
        <div class="callout-icon">✅</div>
        <div><strong>${res.total_despachados} token(s) UUIDv4</strong> generados con vigencia 48 h. Correos despachados vía Gmail SMTP.</div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Estudiante ID</th><th>Correo</th><th>Enlace tokenizado único</th><th>Email</th></tr></thead>
          <tbody>
            ${res.items.map(item => `
              <tr>
                <td>#${item.estudiante_id}</td>
                <td>${item.correo}</td>
                <td><a href="${item.enlace_test}" target="_blank" style="color:var(--brand-blue);font-size:.75rem;font-family:'JetBrains Mono',monospace;">${item.enlace_test}</a></td>
                <td>${item.correo_enviado ? '<span class="badge badge-green">✓ Enviado</span>' : '<span class="badge badge-gray">Simulado</span>'}</td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>`;
    document.getElementById("dispatchModal").style.display = "flex";
    showToast("Flash Tests despachados", `${res.total_despachados} tokens generados.`, "success");
  } catch (err) {
    btn.textContent = "⚡ Despachar Flash Tests"; btn.disabled = false;
    showToast("Error en despacho", err.message, "error");
  }
}

/* ══ TAB 2 — Nómina ════════════════════════════════════════════════════ */
async function loadNomina() {
  if (!currentCourseId) return;
  const students = await apiCall(`/api/asignaturas/${currentCourseId}/estudiantes`);
  const tbody = document.getElementById("nominaTableBody");
  const countEl = document.getElementById("nominaCount");
  if (countEl) countEl.textContent = `${students.length} registros`;

  if (!students.length) {
    tbody.innerHTML = `<tr><td colspan="5"><div class="empty-state"><div class="empty-icon">👥</div><div class="empty-title">Sin estudiantes</div><div class="empty-sub">Sube el archivo CSV para registrar la nómina</div></div></td></tr>`;
    return;
  }
  tbody.innerHTML = students.map((s, i) => `
    <tr>
      <td>${i + 1}</td>
      <td><strong>${s.nombre}</strong></td>
      <td><span class="text-sm" style="font-family:'JetBrains Mono',monospace;">${s.correo}</span></td>
      <td>${s.rut || "<span class='text-muted'>—</span>"}</td>
      <td>${s.tiene_trabajo
        ? '<span class="badge badge-green">✓ PDF cargado</span>'
        : '<span class="badge badge-gray">Pendiente</span>'}</td>
    </tr>`).join("");
}

async function handleCSVUpload(file) {
  if (!file) return;
  const statusEl = document.getElementById("csvUploadStatus");
  statusEl.innerHTML = `<span class="text-muted">Procesando nómina CSV…</span>`;

  const formData = new FormData();
  formData.append("file", file);
  try {
    const res = await apiCall(`/api/asignaturas/${currentCourseId}/estudiantes/csv`, "POST", formData, true);
    statusEl.innerHTML = `
      <div class="callout callout-green" style="margin-top:.5rem;">
        <div class="callout-icon">✅</div>
        <div>
          <strong>${res.cargados_exitosamente}</strong> estudiantes registrados ·
          ${res.duplicados_omitidos} duplicados omitidos ·
          ${res.errores.length} errores
        </div>
      </div>`;
    loadNomina();
    showToast("CSV importado", `${res.cargados_exitosamente} alumnos cargados.`, "success");
  } catch (err) {
    statusEl.innerHTML = `<div class="callout callout-red"><div class="callout-icon">❌</div><div>${err.message}</div></div>`;
    showToast("Error CSV", err.message, "error");
  }
}

/* ══ TAB 3 — Materiales ════════════════════════════════════════════════ */
async function loadMateriales() {
  if (!currentCourseId) return;
  const mats  = await apiCall(`/api/asignaturas/${currentCourseId}/materiales`);
  const tbody = document.getElementById("materialesTableBody");

  if (!mats.length) {
    tbody.innerHTML = `<tr><td colspan="4"><div class="empty-state"><div class="empty-icon">📚</div><div class="empty-title">Sin materiales aún</div></div></td></tr>`;
    return;
  }
  const typeLabel = { syllabus:"Syllabus", rubrica:"Rúbrica", guia:"Guía", otro:"Otro" };
  const typeBadge = { syllabus:"badge-blue", rubrica:"badge-red", guia:"badge-green", otro:"badge-gray" };
  tbody.innerHTML = mats.map(m => `
    <tr>
      <td><strong>${m.nombre}</strong></td>
      <td><span class="badge ${typeBadge[m.tipo]||'badge-gray'}">${typeLabel[m.tipo]||m.tipo}</span></td>
      <td><span class="text-muted">${m.markdown.length.toLocaleString()} caracteres</span></td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="previewMarkdown(${JSON.stringify(m.markdown.slice(0,3000))})">Ver Markdown</button>
      </td>
    </tr>`).join("");
}

async function handleMaterialUpload(e) {
  e.preventDefault();
  const file   = document.getElementById("materialFile").files[0];
  const nombre = document.getElementById("materialNombre").value;
  const tipo   = document.getElementById("materialTipo").value;
  if (!file || !nombre) return;

  const formData = new FormData();
  formData.append("file", file);
  formData.append("nombre", nombre);
  formData.append("tipo", tipo);

  try {
    await apiCall(`/api/asignaturas/${currentCourseId}/materiales`, "POST", formData, true);
    document.getElementById("materialNombre").value = "";
    document.getElementById("materialFile").value   = "";
    loadMateriales();
    showToast("Material subido", `${nombre} convertido a Markdown.`, "success");
  } catch (err) { showToast("Error", err.message, "error"); }
}

function previewMarkdown(text) {
  document.getElementById("markdownPreviewBody").textContent = text;
  document.getElementById("markdownModal").style.display = "flex";
}

/* ══ TAB 4 — Informes PDF ══════════════════════════════════════════════ */
async function loadEvaluacion() {
  if (!currentCourseId) return;
  const students = await apiCall(`/api/asignaturas/${currentCourseId}/estudiantes`);
  const select   = document.getElementById("singleUploadStudentSelect");
  select.innerHTML = '<option value="">Seleccionar…</option>';
  students.forEach(s => {
    const o = document.createElement("option");
    o.value = s.id; o.textContent = `${s.nombre}`;
    select.appendChild(o);
  });
}

async function handleSinglePDFUpload(e) {
  e.preventDefault();
  const studentId = document.getElementById("singleUploadStudentSelect").value;
  const file      = document.getElementById("singlePDFFile").files[0];
  const statusEl  = document.getElementById("singlePDFStatus");
  if (!studentId || !file) return;

  statusEl.innerHTML = `<span class="text-muted">Extrayendo semántica y evaluando informe…</span>`;
  const fd = new FormData();
  fd.append("estudiante_id", studentId);
  fd.append("file", file);
  try {
    const res = await apiCall(`/api/asignaturas/${currentCourseId}/trabajos/upload`, "POST", fd, true);
    statusEl.innerHTML = `<div class="callout callout-green"><div class="callout-icon">✅</div><div>${res.message}</div></div>`;
    showToast("Evaluación completada", res.message, "success");
  } catch (err) {
    statusEl.innerHTML = `<div class="callout callout-red"><div class="callout-icon">❌</div><div>${err.message}</div></div>`;
    showToast("Error", err.message, "error");
  }
}

async function handleBatchPDFUpload(files) {
  if (!files?.length) return;
  const statusEl = document.getElementById("batchPDFStatus");
  statusEl.innerHTML = `<span class="text-muted">Cargando ${files.length} archivos en lote…</span>`;
  const fd = new FormData();
  for (let i = 0; i < files.length; i++) fd.append("files", files[i]);
  try {
    const res = await apiCall(`/api/asignaturas/${currentCourseId}/trabajos/batch`, "POST", fd, true);
    statusEl.innerHTML = `<div class="callout callout-green"><div class="callout-icon">✅</div><div>Asociados: <strong>${res.asociados_y_evaluados}</strong> de ${res.total_archivos}</div></div>`;
    showToast("Batch completado", `${res.asociados_y_evaluados} informes procesados.`, "success");
  } catch (err) {
    statusEl.innerHTML = `<div class="callout callout-red"><div class="callout-icon">❌</div><div>${err.message}</div></div>`;
    showToast("Error batch", err.message, "error");
  }
}

/* ══ TAB 5 — Preguntas & Despacho ══════════════════════════════════════ */
async function loadPreguntas() {
  if (!currentCourseId) return;
  const students = await apiCall(`/api/asignaturas/${currentCourseId}/estudiantes`);
  const select   = document.getElementById("poolStudentSelect");
  select.innerHTML = '<option value="">Seleccionar…</option>';
  students.filter(s => s.tiene_trabajo).forEach(s => {
    const o = document.createElement("option");
    o.value = s.id; o.textContent = s.nombre;
    select.appendChild(o);
  });
}

async function onPoolStudentChange() {
  const studentId = document.getElementById("poolStudentSelect").value;
  if (!studentId) return;
  const container = document.getElementById("questionsPoolContainer");
  container.innerHTML = `<div class="empty-state"><div class="empty-icon">⏳</div><div class="empty-title">Cargando preguntas…</div></div>`;

  try {
    const evalData  = await apiCall(`/api/asignaturas/${currentCourseId}/estudiantes/${studentId}/evaluacion`);
    const questions = await apiCall(`/api/evaluaciones/${evalData.evaluacion_id}/preguntas`);
    renderPoolQuestions(evalData.evaluacion_id, questions);
  } catch {
    container.innerHTML = `<div class="callout callout-amber"><div class="callout-icon">⚠️</div><div>No se encontraron preguntas generadas. Evalúa el informe primero.</div></div>`;
  }
}

function renderPoolQuestions(evalId, questions) {
  const container = document.getElementById("questionsPoolContainer");
  const selected  = questions.filter(q => q.seleccionada).length;

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <div>
          <h3 class="card-title">Pool de preguntas (${questions.length} generadas)</h3>
          <p class="text-xs text-muted mt-1"><strong>${selected}</strong> seleccionadas para el Flash Test</p>
        </div>
        <button class="btn btn-primary btn-sm" onclick="saveSelectedQuestions(${evalId})">Guardar selección</button>
      </div>
      <div class="card-body" style="display:flex;flex-direction:column;gap:.75rem;">
        ${questions.map(q => `
          <div class="card" style="margin:0;padding:1rem;border-left:3px solid ${q.seleccionada ? "var(--brand-blue)" : "var(--border)"};">
            <label style="display:flex;align-items:flex-start;gap:.75rem;cursor:pointer;">
              <input type="checkbox" class="q-select-check" data-qid="${q.id}" ${q.seleccionada?"checked":""} style="margin-top:3px;width:16px;height:16px;accent-color:var(--brand-blue);">
              <div style="flex:1;">
                <div class="text-sm font-medium" style="color:var(--text);margin-bottom:.5rem;">${q.texto}</div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:.25rem;">
                  ${q.alternativas.map(a => `
                    <div style="display:flex;gap:.4rem;align-items:flex-start;font-size:.75rem;padding:.3rem .5rem;background:${a.es_correcta?"var(--success-light)":"var(--surface-2)"};border-radius:var(--r-sm);">
                      <span style="font-family:'JetBrains Mono',monospace;font-weight:700;color:${a.es_correcta?"var(--success)":"var(--text-muted)"};">${a.id}</span>
                      <span style="color:${a.es_correcta?"var(--success-dark)":"var(--text-muted)"};">${a.texto}</span>
                    </div>`).join("")}
                </div>
                ${q.seccion_origen ? `<div class="text-xs text-muted mt-2">📌 Sección: ${q.seccion_origen}</div>` : ""}
              </div>
            </label>
          </div>`).join("")}
      </div>
    </div>`;
}

async function saveSelectedQuestions(evalId) {
  const ids = [...document.querySelectorAll(".q-select-check:checked")].map(cb => parseInt(cb.dataset.qid));
  try {
    await apiCall(`/api/evaluaciones/${evalId}/seleccionar`, "POST", { pregunta_ids: ids });
    showToast("Selección guardada", `${ids.length} preguntas activas.`, "success");
    onPoolStudentChange();
  } catch (err) { showToast("Error", err.message, "error"); }
}

/* ══ TAB 6 — Auditoría ════════════════════════════════════════════════ */
async function loadAuditoria() {
  const logs  = await apiCall("/api/audit");
  const tbody = document.getElementById("auditTableBody");
  if (!logs.length) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">🛡️</div><div class="empty-title">Sin registros aún</div></div></td></tr>`;
    return;
  }
  const actionColor = {
    LOGIN: "badge-blue", REGISTRO_DOCENTE: "badge-cyan",
    CREAR_ASIGNATURA:"badge-purple", CIERRE_MODIFICACION_NOTA:"badge-red",
    DESPACHO_FLASH_TESTS:"badge-amber", EVALUACION_GENERADA:"badge-green",
    AGENDAR_DEFENSA_ORAL:"badge-amber"
  };
  tbody.innerHTML = logs.map(l => `
    <tr>
      <td class="text-muted">#${l.id}</td>
      <td><span class="badge ${actionColor[l.accion]||"badge-gray"}">${l.accion}</span></td>
      <td><code>${l.tabla}</code></td>
      <td>${l.usuario_nombre || "Sistema"}</td>
      <td class="text-xs text-muted">${new Date(l.timestamp).toLocaleString("es-CL")}</td>
      <td>
        <button class="btn btn-ghost btn-sm" onclick="viewAuditDiff('${encodeURIComponent(JSON.stringify(l.datos_previos))}','${encodeURIComponent(JSON.stringify(l.datos_nuevos))}')">Ver diffs</button>
      </td>
    </tr>`).join("");
}

function viewAuditDiff(prevEnc, nextEnc) {
  const prev = JSON.parse(decodeURIComponent(prevEnc));
  const next = JSON.parse(decodeURIComponent(nextEnc));
  document.getElementById("auditDiffBody").innerHTML = `
    <div class="grid-2">
      <div>
        <p class="text-xs font-medium text-muted mb-2" style="text-transform:uppercase;">Estado previo</p>
        <pre style="background:var(--surface-2);padding:.875rem;border-radius:var(--r-md);font-size:.75rem;overflow-x:auto;">${JSON.stringify(prev,null,2)||"—"}</pre>
      </div>
      <div>
        <p class="text-xs font-medium text-muted mb-2" style="text-transform:uppercase;">Estado nuevo</p>
        <pre style="background:var(--success-light);padding:.875rem;border-radius:var(--r-md);font-size:.75rem;overflow-x:auto;color:var(--success-dark);">${JSON.stringify(next,null,2)||"—"}</pre>
      </div>
    </div>`;
  document.getElementById("auditModal").style.display = "flex";
}

/* ══ TAB 7 — Config ════════════════════════════════════════════════════ */
async function loadConfig() {
  if (!currentCourseId) return;
  const course = await apiCall(`/api/asignaturas/${currentCourseId}`);
  const p = course.parametros || {};
  document.getElementById("configPrompt").value            = p.prompt_custom || "";
  document.getElementById("configRigor").value             = p.nivel_rigor   || "medium";
  document.getElementById("configPoolSize").value          = p.pool_size     || 15;
  document.getElementById("configNumTest").value           = p.num_preguntas_test || 5;
  document.getElementById("configUmbralIA").value          = p.umbral_ia     || 40;
  document.getElementById("configUmbralCoherencia").value  = p.umbral_coherencia || 60;
  document.getElementById("configTiempoTest").value        = p.tiempo_test_segundos || 60;
}

async function handleSaveConfig(e) {
  e.preventDefault();
  try {
    await apiCall(`/api/asignaturas/${currentCourseId}`, "PUT", {
      parametros: {
        prompt_custom:         document.getElementById("configPrompt").value,
        nivel_rigor:           document.getElementById("configRigor").value,
        pool_size:             parseInt(document.getElementById("configPoolSize").value),
        num_preguntas_test:    parseInt(document.getElementById("configNumTest").value),
        umbral_ia:             parseFloat(document.getElementById("configUmbralIA").value),
        umbral_coherencia:     parseFloat(document.getElementById("configUmbralCoherencia").value),
        tiempo_test_segundos:  parseInt(document.getElementById("configTiempoTest").value)
      }
    });
    showToast("Parámetros guardados", "Configuración actualizada.", "success");
  } catch (err) { showToast("Error", err.message, "error"); }
}

/* ── Courses modal ───────────────────────────────────────────────────── */
function showNewCourseModal() {
  document.getElementById("newCourseModal").style.display = "flex";
}

async function handleCreateCourse(e) {
  e.preventDefault();
  try {
    await apiCall("/api/asignaturas", "POST", {
      nombre:  document.getElementById("newCourseNombre").value,
      periodo: document.getElementById("newCoursePeriodo").value,
      ano:     parseInt(document.getElementById("newCourseAno").value)
    });
    closeModal("newCourseModal");
    loadCourses();
    showToast("Asignatura creada", "", "success");
  } catch (err) { showToast("Error", err.message, "error"); }
}

/* ── Modal helper ────────────────────────────────────────────────────── */
function closeModal(id) {
  document.getElementById(id).style.display = "none";
}
