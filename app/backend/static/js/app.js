// ── State ──────────────────────────────────────────────────────
const state = {
  meta: null,
  filters: { institution: new Set(), source: new Set(), area: new Set(), subtema: new Set(), year: new Set(), status: "all", favorite: "0" },
  queue: [],
  queueIdx: -1,
  current: null,
  answered: false,
  mockExam: false,
  mockCorrect: 0,
  mockWrong: 0,
  timerInterval: null,
  startTime: null,
  totalSeconds: 0,
  // ★ per-question timer
  qTimerInterval: null,
  qStartTime: null,
  qElapsedSeconds: 0,
  // ★ session strip
  sessionCorrect: 0,
  sessionWrong: 0,
  sessionQTimes: [],
  sessionStripInterval: null,
  sessionStripStart: null,
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`API ${path} -> ${res.status}`);
  return res.json();
}

// ── Navegação entre abas ─────────────────────────────────────

$$(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    $$(".tab").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    $$(".view").forEach((v) => v.classList.remove("active"));
    const view = $(`#view-${btn.dataset.view}`);
    if (view) view.classList.add("active");
    if (btn.dataset.view === "stats") loadStats();
    if (btn.dataset.view === "planner") loadPlanner();
    if (btn.dataset.view === "coverage") loadCoverage();
  });
});

// ── Filtros ──────────────────────────────────────────────────

function chip(value, label, active = false) {
  const b = document.createElement("button");
  b.className = "chip" + (active ? " active" : "");
  b.dataset.value = value;
  b.innerHTML = label;
  return b;
}

async function initFilters() {
  try {
    state.meta = await api("/api/meta");
  } catch (err) {
    console.error("Failed to load meta:", err);
    return;
  }

  const instBox = $("#f-institution");
  if (instBox && state.meta.institutions) {
    state.meta.institutions.forEach((inst) => {
      const c = chip(inst.institution_code, `${inst.institution_code} <span class="n">${inst.n}</span>`);
      c.addEventListener("click", () => {
        c.classList.toggle("active");
        toggleSetValue(state.filters.institution, inst.institution_code);
        refreshLiveCount();
      });
      instBox.appendChild(c);
    });
  }

  const areaBox = $("#f-area");
  if (areaBox) {
    (state.meta.areas || []).forEach((a) => {
      const c = chip(a.area, `${a.area} <span class="n">${a.n}</span>`);
      c.addEventListener("click", () => {
        c.classList.toggle("active");
        toggleSetValue(state.filters.area, a.area);
        refreshSubtemaSuggestions();
        refreshLiveCount();
      });
      areaBox.appendChild(c);
    });
    if (!state.meta.areas || state.meta.areas.length === 0) {
      areaBox.innerHTML = '<span class="muted small">Classificação por área ainda não gerada.</span>';
    }
  }

  wireGroupActions("f-institution");
  wireGroupActions("f-area");
  wireGroupActions("f-year");

  const fSubtemaInput = $("#f-subtema-input");
  if (fSubtemaInput) {
    fSubtemaInput.addEventListener("input", debounce(refreshSubtemaSuggestions, 250));
    fSubtemaInput.addEventListener("change", () => {
      const val = fSubtemaInput.value.trim();
      if (val) addSubtemaChip(val);
      fSubtemaInput.value = "";
    });
    refreshSubtemaSuggestions();
  }

  const yearBox = $("#f-year");
  if (yearBox && state.meta.years) {
    state.meta.years.forEach((y) => {
      const c = chip(y, String(y));
      c.addEventListener("click", () => {
        c.classList.toggle("active");
        toggleSetValue(state.filters.year, y);
        refreshLiveCount();
      });
      yearBox.appendChild(c);
    });
  }

  $$("#f-status .chip").forEach((c) => {
    c.addEventListener("click", () => {
      $$("#f-status .chip").forEach((x) => x.classList.remove("active"));
      c.classList.add("active");
      state.filters.status = c.dataset.value;
      refreshLiveCount();
    });
  });

  const fFav = $("#f-favorite");
  if (fFav) {
    fFav.addEventListener("click", () => {
      fFav.classList.toggle("active");
      state.filters.favorite = fFav.classList.contains("active") ? "1" : "0";
      refreshLiveCount();
    });
  }

  const fMockExam = $("#f-mock-exam");
  const fMockOptions = $("#mock-exam-options");
  if (fMockExam) {
    fMockExam.addEventListener("change", () => {
      if (fMockOptions) fMockOptions.classList.toggle("hidden", !fMockExam.checked);
    });
  }

  const filtersSummary = $("#filters-summary");
  if (filtersSummary && state.meta) {
    filtersSummary.textContent = `${state.meta.total_questions || 0} questões no banco · ${state.meta.answered_questions || 0} já respondidas`;
  }

  // ★ Presets
  renderPresets();
  const btnSavePreset = $("#btn-save-preset");
  if (btnSavePreset) {
    btnSavePreset.addEventListener("click", () => {
      const name = prompt("Nome do preset:");
      if (name && name.trim()) savePreset(name.trim());
    });
  }

  checkResumeSession();
  refreshLiveCount();
}

function wireGroupActions(groupId) {
  $$(`.link-btn[data-select="${groupId}"]`).forEach((btn) => {
    btn.addEventListener("click", () => {
      const mode = btn.dataset.mode;
      const targets = mode === "all"
        ? $$(`#${groupId} .chip:not(.active)`)
        : $$(`#${groupId} .chip.active`);
      targets.forEach((c) => c.click());
    });
  });
}

function toggleSetValue(set, value) {
  if (set.has(value)) set.delete(value);
  else set.add(value);
}

function debounce(fn, ms) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

async function refreshSubtemaSuggestions() {
  const q = $("#f-subtema-input").value.trim();
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  const areaSel = state.filters.area.values().next().value;
  if (areaSel) params.set("area", areaSel);
  const rows = await api(`/api/subtemas?${params.toString()}`);
  const list = $("#f-subtema-list");
  list.innerHTML = "";
  rows.forEach((r) => {
    const opt = document.createElement("option");
    opt.value = r.subtema;
    opt.label = `${r.subtema} (${r.n})`;
    list.appendChild(opt);
  });
}

function addSubtemaChip(value) {
  if (state.filters.subtema.has(value)) return;
  state.filters.subtema.add(value);
  renderSubtemaChips();
  refreshLiveCount();
}

function removeSubtemaChip(value) {
  state.filters.subtema.delete(value);
  renderSubtemaChips();
  refreshLiveCount();
}

// ── Contagem ao vivo ──────────────────────────────────────────

function buildFilterParams() {
  const params = new URLSearchParams();
  state.filters.institution.forEach((v) => params.append("institution", v));
  state.filters.source.forEach((v) => params.append("source", v));
  state.filters.area.forEach((v) => params.append("area", v));
  state.filters.subtema.forEach((v) => params.append("subtema", v));
  state.filters.year.forEach((v) => params.append("year", v));
  params.set("status", state.filters.status);
  params.set("favorite", state.filters.favorite);
  return params;
}

const refreshLiveCount = debounce(async () => {
  const el = $("#filters-live-count");
  if (!el) return;
  try {
    const res = await api(`/api/questions/count?${buildFilterParams().toString()}`);
    el.textContent = `${res.count} questão(ões) encontrada(s) com os filtros atuais`;
  } catch (err) {
    console.error("Failed to refresh live count:", err);
  }
}, 200);

function renderSubtemaChips() {
  const box = $("#f-subtema-chips");
  box.innerHTML = "";
  state.filters.subtema.forEach((v) => {
    const c = document.createElement("button");
    c.className = "chip active";
    c.innerHTML = `${escapeHtml(v)} <i class="ph ph-x" style="margin-left: 4px; opacity: 0.7;"></i>`;
    c.addEventListener("click", () => removeSubtemaChip(v));
    box.appendChild(c);
  });
}

// ── Sessão ────────────────────────────────────────────────────

const startSessionBtn = $("#start-session");
if (startSessionBtn) startSessionBtn.addEventListener("click", startSession);

const quizExitBtn = $("#quiz-exit");
if (quizExitBtn) {
  quizExitBtn.addEventListener("click", () => {
    stopTimer();
    stopQuestionTimer();
    stopSessionStrip();
    const qPanel = $("#quiz-panel");
    const fPanel = $("#filters-panel");
    if (qPanel) qPanel.classList.add("hidden");
    if (fPanel) fPanel.classList.remove("hidden");
  });
}

const btnSummaryExit = $("#btn-summary-exit");
if (btnSummaryExit) {
  btnSummaryExit.addEventListener("click", () => {
    stopTimer();
    stopQuestionTimer();
    stopSessionStrip();
    clearSessionState();
    $("#quiz-summary").classList.add("hidden");
    $("#quiz-panel").classList.add("hidden");
    $("#filters-panel").classList.remove("hidden");
  });
}

async function startSession() {
  const params = buildFilterParams();

  state.mockExam = $("#f-mock-exam")?.checked || false;
  // reset session strip counters
  state.sessionCorrect = 0;
  state.sessionWrong = 0;
  state.sessionQTimes = [];

  if (state.mockExam) {
    params.set("limit", $("#f-mock-limit").value || 20);
    state.mockCorrect = 0;
    state.mockWrong = 0;
    startTimer();
    // hide session strip in mock mode (timer handles progress)
    $("#session-strip")?.classList.add("hidden");
  } else {
    $("#quiz-timer")?.classList.add("hidden");
    stopTimer();
    // show session strip
    $("#session-strip")?.classList.remove("hidden");
    startSessionStrip();
  }

  const questions = await api(`/api/questions?${params.toString()}`);
  state.queue = questions;
  state.queueIdx = -1;

  $("#filters-panel").classList.add("hidden");
  $("#quiz-panel").classList.remove("hidden");

  if (questions.length === 0) {
    $("#question-card").classList.add("hidden");
    $("#quiz-empty").classList.remove("hidden");
    $("#quiz-progress").textContent = "";
    return;
  }
  $("#question-card").classList.remove("hidden");
  $("#quiz-empty").classList.add("hidden");
  const quizSummary = $("#quiz-summary");
  if (quizSummary) quizSummary.classList.add("hidden");
  const startBar = $("#quiz-progress-bar");
  if (startBar) startBar.style.width = "0%";
  nextQuestion();
}

const qNextBtn = $("#q-next");
if (qNextBtn) qNextBtn.addEventListener("click", nextQuestion);

async function nextQuestion() {
  state.queueIdx++;
  if (state.queueIdx >= state.queue.length) {
    stopQuestionTimer();
    $("#question-card").classList.add("hidden");
    if (state.mockExam) {
      const total = state.mockCorrect + state.mockWrong;
      const pct = total > 0 ? Math.round((state.mockCorrect / total) * 100) : 0;
      const summaryScore = $("#summary-score");
      if (summaryScore) summaryScore.textContent = pct + "%";
      const summaryCorrect = $("#summary-correct");
      if (summaryCorrect) summaryCorrect.textContent = state.mockCorrect;
      const summaryWrong = $("#summary-wrong");
      if (summaryWrong) summaryWrong.textContent = state.mockWrong;
      const summaryTime = $("#summary-time");
      if (summaryTime) summaryTime.textContent = formatTime(state.totalSeconds);
      const summaryAvgTime = $("#summary-avg-time");
      if (summaryAvgTime) {
        const avg = total > 0 ? Math.round(state.totalSeconds / total) : 0;
        summaryAvgTime.textContent = formatAvgTime(avg);
      }
      const quizSummary = $("#quiz-summary");
      if (quizSummary) quizSummary.classList.remove("hidden");
    } else {
      // populate summary with session strip data
      const total = state.sessionCorrect + state.sessionWrong;
      const pct = total > 0 ? Math.round((state.sessionCorrect / total) * 100) : 0;
      const stripTime = state.sessionStripStart ? Math.floor((Date.now() - state.sessionStripStart) / 1000) : 0;
      const avgSecs = state.sessionQTimes.length > 0
        ? Math.round(state.sessionQTimes.reduce((a, b) => a + b, 0) / state.sessionQTimes.length)
        : 0;
      const summaryScore = $("#summary-score");
      if (summaryScore) summaryScore.textContent = pct + "%";
      const summaryCorrect = $("#summary-correct");
      if (summaryCorrect) summaryCorrect.textContent = state.sessionCorrect;
      const summaryWrong = $("#summary-wrong");
      if (summaryWrong) summaryWrong.textContent = state.sessionWrong;
      const summaryTime = $("#summary-time");
      if (summaryTime) summaryTime.textContent = formatTime(stripTime);
      const summaryAvgTime = $("#summary-avg-time");
      if (summaryAvgTime) summaryAvgTime.textContent = formatAvgTime(avgSecs);
      const quizSummary = $("#quiz-summary");
      if (quizSummary) quizSummary.classList.remove("hidden");
    }
    $("#quiz-progress").textContent = "";
    const doneBar = $("#quiz-progress-bar");
    if (doneBar) doneBar.style.width = "100%";
    stopTimer();
    stopSessionStrip();
    clearSessionState();
    return;
  }
  $("#quiz-progress").textContent = `${state.queueIdx + 1} / ${state.queue.length}`;
  const progressBar = $("#quiz-progress-bar");
  if (progressBar) progressBar.style.width = `${((state.queueIdx + 1) / state.queue.length) * 100}%`;
  const qsummary = state.queue[state.queueIdx];
  const q = await api(`/api/questions/${qsummary.id}`);
  state.current = q;
  state.answered = false;
  renderQuestion(q);
  saveSessionState();
}

function renderQuestion(q) {
  $("#q-area").textContent = q.area || q.source_file;
  $("#q-institution").textContent = q.institution_code;
  $("#q-year").textContent = q.year ?? "—";
  const subtema = q.subtema || q.topic;
  $("#q-subtema").textContent = subtema || "—";
  $("#q-subtema").classList.toggle("hidden", !subtema);

  // ★ nota dot indicator
  const noteDot = $("#q-note-dot");
  if (noteDot) {
    const note = loadNote(q.id);
    noteDot.classList.toggle("hidden", !note);
  }

  const btnFav = $("#btn-favorite");
  if (btnFav) {
    const starIcon = (fav) => `<i class="${fav ? "ph-fill" : "ph"} ph-star"></i>`;
    btnFav.innerHTML = starIcon(q.is_favorite);
    btnFav.classList.toggle("active", q.is_favorite);
    const newBtn = btnFav.cloneNode(true);
    btnFav.parentNode.replaceChild(newBtn, btnFav);
    newBtn.addEventListener("click", async () => {
      const res = await api(`/api/questions/${q.id}/favorite`, { method: "POST" });
      newBtn.innerHTML = starIcon(res.is_favorite);
      newBtn.classList.toggle("active", res.is_favorite);
    });
  }

  $("#q-stem").textContent = q.stem;

  const imgBox = $("#q-images");
  imgBox.innerHTML = "";
  q.images.forEach((path) => {
    const img = document.createElement("img");
    img.src = "/" + path;
    img.loading = "lazy";
    imgBox.appendChild(img);
  });

  const altBox = $("#q-alternatives");
  altBox.innerHTML = "";
  q.alternatives.forEach((alt) => {
    const btn = document.createElement("button");
    btn.className = "alt-btn";
    btn.innerHTML = `<span class="alt-letter">${alt.letter}</span><span>${escapeHtml(alt.text)}</span>`;
    btn.addEventListener("click", () => {
      if (btn.classList.contains("eliminated")) {
        btn.classList.remove("eliminated");
        return;
      }
      submitAnswer(alt.letter);
    });
    btn.addEventListener("contextmenu", (e) => {
      e.preventDefault();
      if (!state.answered) btn.classList.toggle("eliminated");
    });
    altBox.appendChild(btn);
  });

  // hide feedback
  $("#q-feedback").classList.add("hidden");
  // hide time-taken badge until answered
  const timeTakenBadge = $("#q-time-taken");
  if (timeTakenBadge) timeTakenBadge.classList.add("hidden");

  // ★ start per-question timer
  startQuestionTimer();
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

async function submitAnswer(letter) {
  if (state.answered) return;
  state.answered = true;

  // ★ stop per-question timer and capture elapsed
  const elapsed = stopQuestionTimer();
  state.sessionQTimes.push(elapsed);

  const result = await api(`/api/questions/${state.current.id}/attempt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selected_letter: letter }),
  });

  $$("#q-alternatives .alt-btn").forEach((btn) => {
    btn.disabled = true;
    const btnLetter = btn.querySelector(".alt-letter").textContent;
    if (btnLetter === result.correct_letter) btn.classList.add("correct");
    else if (btnLetter === letter) btn.classList.add("wrong");
  });

  if (state.mockExam) {
    if (result.is_correct) state.mockCorrect++;
    else state.mockWrong++;
    saveSessionState();
    setTimeout(nextQuestion, 500);
    return;
  }

  // ★ update session strip counters
  if (result.is_correct) state.sessionCorrect++;
  else state.sessionWrong++;
  updateSessionStripCounts();

  const banner = $("#q-feedback-banner");
  banner.textContent = result.is_correct ? "✓ Você acertou!" : `✗ Você errou. Resposta correta: ${result.correct_letter}`;
  banner.className = "feedback-banner " + (result.is_correct ? "correct" : "wrong");

  const expBox = $("#q-explanation");
  if (result.explanation) {
    expBox.textContent = result.explanation;
    expBox.classList.remove("pending");
  } else {
    expBox.textContent = "Explicação ainda não gerada para esta questão — em breve.";
    expBox.classList.add("pending");
  }

  // ★ show time taken badge
  const timeTakenEl = $("#q-time-taken");
  const timeTakenVal = $("#q-time-taken-val");
  if (timeTakenEl && timeTakenVal) {
    timeTakenVal.textContent = formatAvgTime(elapsed);
    timeTakenEl.classList.remove("hidden");
  }

  // ★ populate notes textarea
  const notesArea = $("#q-notes");
  const qId = state.current.id;
  if (notesArea) {
    notesArea.value = loadNote(qId) || "";
    // debounced auto-save
    notesArea.oninput = debounce(() => {
      saveNote(qId, notesArea.value);
      const noteDot = $("#q-note-dot");
      if (noteDot) noteDot.classList.toggle("hidden", !notesArea.value.trim());
      const savedMsg = $("#notes-saved-msg");
      if (savedMsg) {
        savedMsg.classList.remove("hidden");
        setTimeout(() => savedMsg.classList.add("hidden"), 2000);
      }
    }, 600);
  }

  $("#q-feedback").classList.remove("hidden");
}

// ── Persistência de sessão ────────────────────────────────────

const SESSION_STORAGE_KEY = "medquest_session_v1";

function saveSessionState() {
  if (!state.queue.length) { clearSessionState(); return; }
  const data = {
    filters: {
      institution: [...state.filters.institution],
      area: [...state.filters.area],
      subtema: [...state.filters.subtema],
      year: [...state.filters.year],
      status: state.filters.status,
      favorite: state.filters.favorite,
    },
    queueIds: state.queue.map((q) => q.id),
    queueIdx: state.queueIdx,
    mockExam: state.mockExam,
    mockLimit: $("#f-mock-limit")?.value || 20,
    mockCorrect: state.mockCorrect,
    mockWrong: state.mockWrong,
    totalSeconds: state.totalSeconds,
  };
  try { localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(data)); }
  catch (err) { console.error("Failed to save session state:", err); }
}

function clearSessionState() {
  try { localStorage.removeItem(SESSION_STORAGE_KEY); }
  catch (err) { console.error("Failed to clear session state:", err); }
  $("#resume-banner")?.classList.add("hidden");
}

function loadSessionState() {
  try {
    const raw = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (!data.queueIds || !data.queueIds.length) return null;
    if (data.queueIdx >= data.queueIds.length - 1) return null;
    return data;
  } catch (err) { return null; }
}

function checkResumeSession() {
  const banner = $("#resume-banner");
  if (!banner) return;
  const data = loadSessionState();
  if (!data) { banner.classList.add("hidden"); return; }
  const remaining = data.queueIds.length - (data.queueIdx + 1);
  const detail = $("#resume-detail");
  if (detail) {
    detail.textContent = `${Math.max(remaining, 0)} de ${data.queueIds.length} questão(ões) restantes` +
      (data.mockExam ? " · Modo Simulado" : "");
  }
  banner.classList.remove("hidden");
  const continueBtn = $("#resume-continue");
  if (continueBtn) continueBtn.onclick = () => resumeSession(data);
  const discardBtn = $("#resume-discard");
  if (discardBtn) discardBtn.onclick = () => clearSessionState();
}

function syncFilterChipsUI() {
  $$("#f-institution .chip").forEach((c) => c.classList.toggle("active", state.filters.institution.has(c.dataset.value)));
  $$("#f-area .chip").forEach((c) => c.classList.toggle("active", state.filters.area.has(c.dataset.value)));
  $$("#f-year .chip").forEach((c) => {
    const match = [...state.filters.year].some((v) => String(v) === c.dataset.value);
    c.classList.toggle("active", match);
  });
  $$("#f-status .chip").forEach((c) => c.classList.toggle("active", c.dataset.value === state.filters.status));
  $("#f-favorite")?.classList.toggle("active", state.filters.favorite === "1");
  renderSubtemaChips();
  const fMockExam = $("#f-mock-exam");
  if (fMockExam) fMockExam.checked = state.mockExam;
  $("#mock-exam-options")?.classList.toggle("hidden", !state.mockExam);
}

async function resumeSession(data) {
  state.filters.institution = new Set(data.filters.institution);
  state.filters.area = new Set(data.filters.area);
  state.filters.subtema = new Set(data.filters.subtema);
  state.filters.year = new Set(data.filters.year);
  state.filters.status = data.filters.status;
  state.filters.favorite = data.filters.favorite;
  syncFilterChipsUI();

  state.queue = data.queueIds.map((id) => ({ id }));
  state.queueIdx = data.queueIdx - 1;
  state.mockExam = data.mockExam;
  state.mockCorrect = data.mockCorrect || 0;
  state.mockWrong = data.mockWrong || 0;
  state.sessionCorrect = 0;
  state.sessionWrong = 0;
  state.sessionQTimes = [];

  $("#resume-banner")?.classList.add("hidden");
  $("#filters-panel").classList.add("hidden");
  $("#quiz-panel").classList.remove("hidden");
  $("#question-card").classList.remove("hidden");
  $("#quiz-empty").classList.add("hidden");
  $("#quiz-summary")?.classList.add("hidden");

  if (state.mockExam) {
    state.totalSeconds = data.totalSeconds || 0;
    startTimer(true);
    $("#session-strip")?.classList.add("hidden");
  } else {
    $("#quiz-timer")?.classList.add("hidden");
    stopTimer();
    $("#session-strip")?.classList.remove("hidden");
    startSessionStrip();
  }

  await nextQuestion();
}

// ── Atalhos de teclado ────────────────────────────────────────

document.addEventListener("keydown", (e) => {
  const activeTag = document.activeElement?.tagName;
  if (activeTag === "INPUT" || activeTag === "TEXTAREA") return;

  const quizPanel = $("#quiz-panel");
  if (!quizPanel || quizPanel.classList.contains("hidden")) return;
  const questionCard = $("#question-card");
  if (!questionCard || questionCard.classList.contains("hidden")) return;

  if (!state.answered) {
    const letterMap = { "1": "A", "2": "B", "3": "C", "4": "D", "5": "E" };
    const key = e.key.length === 1 ? e.key.toUpperCase() : e.key;
    const letter = ["A", "B", "C", "D", "E"].includes(key) ? key : letterMap[e.key];
    if (letter) {
      const btn = $$("#q-alternatives .alt-btn").find((b) => b.querySelector(".alt-letter")?.textContent === letter);
      if (btn && !btn.disabled) { e.preventDefault(); btn.click(); }
    }
  } else if ((e.key === "Enter" || e.key === "ArrowRight") && !state.mockExam) {
    const nextBtn = $("#q-next");
    if (nextBtn && !$("#q-feedback").classList.contains("hidden")) { e.preventDefault(); nextBtn.click(); }
  }
});

// ── Análise de desempenho ─────────────────────────────────────

async function loadStats() {
  const overview = await api("/api/stats/overview");
  renderTiles(overview);
  const [byArea, byInst, byYear, timeline, weak, recommendations] = await Promise.all([
    api("/api/stats/breakdown?by=area"),
    api("/api/stats/breakdown?by=institution"),
    api("/api/stats/breakdown?by=year"),
    api("/api/stats/timeline"),
    api("/api/stats/weak-topics"),
    api("/api/stats/recommendations"),
  ]);
  renderBarChart($("#chart-area"), byArea);
  renderBarChart($("#chart-institution"), byInst);
  renderBarChart($("#chart-year"), byYear.sort((a, b) => a.label - b.label));
  renderLineChart($("#chart-timeline"), timeline);
  renderWeakTopics(weak);
  renderRecommendations(recommendations);
}

function trendInfo(o) {
  if (o.accuracy_last7 == null || o.accuracy_prev7 == null) return null;
  const diff = Math.round((o.accuracy_last7 - o.accuracy_prev7) * 100);
  if (diff === 0) return null;
  return { dir: diff > 0 ? "up" : "down", text: `${diff > 0 ? "+" : ""}${diff}pp em 7 dias` };
}

function renderTiles(o) {
  const trend = trendInfo(o);
  const tiles = [
    { value: o.total_questions, label: "Questões no banco", icon: "ph-stack" },
    { value: o.distinct_answered, label: "Já respondidas", icon: "ph-check-circle" },
    {
      value: o.accuracy_latest_attempt != null ? Math.round(o.accuracy_latest_attempt * 100) + "%" : "—",
      label: "Acurácia (última tentativa)", icon: "ph-target", trend,
    },
    { value: o.total_attempts, label: "Tentativas totais", icon: "ph-arrows-clockwise" },
    { value: o.coverage_pct != null ? Math.round(o.coverage_pct * 100) + "%" : "—", label: "Cobertura do banco", icon: "ph-chart-donut" },
    { value: o.streak_days || 0, label: "Dias seguidos estudando", icon: "ph-fire" },
    {
      value: o.srs_due_count || 0, label: "Revisões pendentes", icon: "ph-alarm",
      action: o.srs_due_count ? () => applyRecommendationAndStudy({ status: "srs_due" }) : null,
    },
  ];
  const box = $("#stat-tiles");
  box.innerHTML = "<h2><i class='ph ph-activity'></i> Visão Geral</h2>";
  tiles.forEach((t) => {
    const d = document.createElement("div");
    d.className = "tile" + (t.action ? " tile-clickable" : "");
    const trendHtml = t.trend
      ? `<span class="trend ${t.trend.dir}"><i class="ph-bold ph-trend-${t.trend.dir}"></i> ${t.trend.text}</span>`
      : "";
    d.innerHTML = `<div class="value">${t.value}</div><div class="label"><i class="ph ${t.icon}"></i> ${t.label}</div>${trendHtml}`;
    if (t.action) d.addEventListener("click", t.action);
    box.appendChild(d);
  });
}

function renderRecommendations(recs) {
  const box = $("#recommendations-list");
  if (!box) return;
  box.innerHTML = "";
  if (!recs || !recs.length) {
    box.innerHTML = '<div class="empty-note">Continue respondendo questões para receber recomendações personalizadas.</div>';
    return;
  }
  recs.forEach((r) => {
    const card = document.createElement("div");
    card.className = "rec-card rec-" + r.type;
    card.innerHTML = `
      <div class="rec-icon"><i class="ph-fill ${r.icon}"></i></div>
      <div class="rec-body">
        <div class="rec-title">${escapeHtml(r.title)}</div>
        <div class="rec-desc">${escapeHtml(r.description)}</div>
      </div>
      <button class="btn-primary rec-cta"><i class="ph ph-arrow-right"></i> ${escapeHtml(r.cta)}</button>
    `;
    card.querySelector(".rec-cta").addEventListener("click", () => applyRecommendationAndStudy(r.filters || {}));
    box.appendChild(card);
  });
}

function clickChipByValue(containerSel, value) {
  const c = $$(`${containerSel} .chip`).find((el) => el.dataset.value === String(value));
  if (c) c.click();
}

function resetFilters() {
  state.filters.institution.clear();
  state.filters.area.clear();
  state.filters.subtema.clear();
  state.filters.year.clear();
  state.filters.status = "all";
  state.filters.favorite = "0";
  $$("#f-institution .chip, #f-area .chip, #f-year .chip").forEach((c) => c.classList.remove("active"));
  $$("#f-status .chip").forEach((c) => c.classList.remove("active"));
  $('#f-status .chip[data-value="all"]')?.classList.add("active");
  $("#f-favorite")?.classList.remove("active");
  renderSubtemaChips();
  const fMockExam = $("#f-mock-exam");
  if (fMockExam) fMockExam.checked = false;
  $("#mock-exam-options")?.classList.add("hidden");
  state.mockExam = false;
}

function goToStudyTab() {
  $$(".tab").forEach((b) => b.classList.remove("active"));
  $$(".tab").find((b) => b.dataset.view === "study")?.classList.add("active");
  $$(".view").forEach((v) => v.classList.remove("active"));
  $("#view-study")?.classList.add("active");
}

async function applyRecommendationAndStudy(filters) {
  resetFilters();
  if (filters.institution) clickChipByValue("#f-institution", filters.institution);
  if (filters.area) clickChipByValue("#f-area", filters.area);
  if (filters.subtema) { state.filters.subtema.add(filters.subtema); renderSubtemaChips(); }
  if (filters.status) clickChipByValue("#f-status", filters.status);
  goToStudyTab();
  if (Object.keys(filters).length === 0) {
    $("#filters-panel")?.classList.remove("hidden");
    $("#quiz-panel")?.classList.add("hidden");
    return;
  }
  await startSession();
}

function renderWeakTopics(rows) {
  const box = $("#weak-topics");
  box.innerHTML = "";
  if (!rows.length) {
    box.innerHTML = '<div class="empty-note">Responda pelo menos 3 questões de um mesmo tópico para começar a ver seus pontos fracos aqui.</div>';
    return;
  }
  rows.forEach((r) => {
    const row = document.createElement("div");
    row.className = "weak-topic-row";
    row.innerHTML = `
      <div class="name">${escapeHtml(r.topic)}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.round(r.accuracy * 100)}%"></div></div>
      <div class="pct">${Math.round(r.accuracy * 100)}%</div>
    `;
    box.appendChild(row);
  });
}

const btnReset = $("#btn-reset-stats");
if (btnReset) {
  btnReset.addEventListener("click", async () => {
    if (confirm("ATENÇÃO: Você tem certeza que deseja APAGAR TODO o seu histórico de desempenho e progresso de revisão espaçada? Esta ação não pode ser desfeita.")) {
      try {
        await api("/api/stats/reset", { method: "DELETE" });
        alert("Desempenho resetado com sucesso.");
        loadStats();
      } catch (e) {
        alert("Erro ao resetar desempenho.");
      }
    }
  });
}

// ── Cronômetro global (simulado) ──────────────────────────────

function startTimer(isResume = false) {
  stopTimer();
  const timerEl = $("#quiz-timer");
  if (timerEl) {
    timerEl.classList.remove("hidden");
    timerEl.innerHTML = `<i class="ph ph-clock"></i> 00:00`;
  }
  if (!isResume) {
    state.totalSeconds = 0;
    state.startTime = Date.now();
  } else {
    state.startTime = Date.now() - (state.totalSeconds * 1000);
  }
  state.timerInterval = setInterval(() => {
    state.totalSeconds = Math.floor((Date.now() - state.startTime) / 1000);
    if (timerEl) timerEl.innerHTML = `<i class="ph ph-clock"></i> ${formatTime(state.totalSeconds)}`;
  }, 1000);
}

function stopTimer() {
  if (state.timerInterval) { clearInterval(state.timerInterval); state.timerInterval = null; }
}

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function formatAvgTime(seconds) {
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s`;
}

// ── ★ Timer por questão ───────────────────────────────────────

function startQuestionTimer() {
  stopQuestionTimer();
  state.qStartTime = Date.now();
  state.qElapsedSeconds = 0;
  const badge = $("#q-timer-badge");
  if (badge) badge.classList.remove("hidden");
  const val = $("#q-timer-val");
  state.qTimerInterval = setInterval(() => {
    state.qElapsedSeconds = Math.floor((Date.now() - state.qStartTime) / 1000);
    if (val) val.textContent = formatTime(state.qElapsedSeconds);
  }, 1000);
}

function stopQuestionTimer() {
  if (state.qTimerInterval) { clearInterval(state.qTimerInterval); state.qTimerInterval = null; }
  const badge = $("#q-timer-badge");
  if (badge) badge.classList.add("hidden");
  const elapsed = state.qElapsedSeconds;
  state.qElapsedSeconds = 0;
  return elapsed;
}

// ── ★ Strip de sessão ao vivo ─────────────────────────────────

function startSessionStrip() {
  stopSessionStrip();
  state.sessionStripStart = Date.now();
  updateSessionStripCounts();
  state.sessionStripInterval = setInterval(() => {
    const secs = Math.floor((Date.now() - state.sessionStripStart) / 1000);
    const el = $("#ss-time");
    if (el) el.textContent = formatTime(secs);
  }, 1000);
}

function stopSessionStrip() {
  if (state.sessionStripInterval) { clearInterval(state.sessionStripInterval); state.sessionStripInterval = null; }
}

function updateSessionStripCounts() {
  const total = state.sessionCorrect + state.sessionWrong;
  const pct = total > 0 ? Math.round((state.sessionCorrect / total) * 100) : null;
  const avgSecs = state.sessionQTimes.length > 0
    ? Math.round(state.sessionQTimes.reduce((a, b) => a + b, 0) / state.sessionQTimes.length)
    : null;
  const ssCorrect = $("#ss-correct");
  const ssWrong = $("#ss-wrong-count");
  const ssPct = $("#ss-pct");
  const ssAvg = $("#ss-avg");
  if (ssCorrect) ssCorrect.textContent = state.sessionCorrect;
  if (ssWrong) ssWrong.textContent = state.sessionWrong;
  if (ssPct) ssPct.textContent = pct !== null ? pct + "%" : "—";
  if (ssAvg) ssAvg.textContent = avgSecs !== null ? formatAvgTime(avgSecs) : "—";
}

// ── ★ Notas pessoais ──────────────────────────────────────────

const NOTES_KEY = "medquest_notes_v1";

function loadNote(questionId) {
  try {
    const all = JSON.parse(localStorage.getItem(NOTES_KEY) || "{}");
    return all[questionId] || "";
  } catch { return ""; }
}

function saveNote(questionId, text) {
  try {
    const all = JSON.parse(localStorage.getItem(NOTES_KEY) || "{}");
    if (text.trim()) all[questionId] = text;
    else delete all[questionId];
    localStorage.setItem(NOTES_KEY, JSON.stringify(all));
  } catch (err) { console.error("Failed to save note:", err); }
}

// ── ★ Presets de filtros ──────────────────────────────────────

const PRESETS_KEY = "medquest_presets_v1";

function loadPresets() {
  try { return JSON.parse(localStorage.getItem(PRESETS_KEY) || "[]"); }
  catch { return []; }
}

function savePreset(name) {
  const presets = loadPresets();
  const filters = {
    institution: [...state.filters.institution],
    area: [...state.filters.area],
    subtema: [...state.filters.subtema],
    year: [...state.filters.year],
    status: state.filters.status,
    favorite: state.filters.favorite,
  };
  const existing = presets.findIndex((p) => p.name === name);
  if (existing >= 0) presets[existing].filters = filters;
  else presets.push({ name, filters });
  try { localStorage.setItem(PRESETS_KEY, JSON.stringify(presets)); }
  catch (err) { console.error("Failed to save presets:", err); }
  renderPresets();
}

function deletePreset(name) {
  const presets = loadPresets().filter((p) => p.name !== name);
  try { localStorage.setItem(PRESETS_KEY, JSON.stringify(presets)); }
  catch (err) { console.error("Failed to save presets:", err); }
  renderPresets();
}

function applyPreset(filters) {
  resetFilters();
  state.filters.institution = new Set(filters.institution || []);
  state.filters.area = new Set(filters.area || []);
  state.filters.subtema = new Set(filters.subtema || []);
  state.filters.year = new Set(filters.year || []);
  state.filters.status = filters.status || "all";
  state.filters.favorite = filters.favorite || "0";
  syncFilterChipsUI();
  refreshLiveCount();
}

function renderPresets() {
  const container = $("#presets-list");
  if (!container) return;
  const presets = loadPresets();
  container.innerHTML = "";
  if (!presets.length) {
    container.innerHTML = '<span class="presets-empty">Nenhum preset salvo ainda.</span>';
    return;
  }
  presets.forEach((p) => {
    const wrap = document.createElement("div");
    wrap.className = "preset-chip-wrap";

    const btn = document.createElement("button");
    btn.className = "chip preset-chip";
    btn.innerHTML = `<i class="ph ph-bookmark-simple"></i> ${escapeHtml(p.name)}`;
    btn.addEventListener("click", () => applyPreset(p.filters));

    const del = document.createElement("button");
    del.className = "preset-del";
    del.title = "Excluir preset";
    del.innerHTML = '<i class="ph ph-x"></i>';
    del.addEventListener("click", (e) => {
      e.stopPropagation();
      if (confirm(`Excluir preset "${p.name}"?`)) deletePreset(p.name);
    });

    wrap.appendChild(btn);
    wrap.appendChild(del);
    container.appendChild(wrap);
  });
}

// ── ★ Planejador Anual de Estudos Inteligente ─────────────────

// Metadados das áreas: mapeia o rótulo do currículo -> área do banco (p/ filtrar),
// classe do badge e nome curto. Corrige o casamento de G.O. e Cirurgia.
const AREA_META = {
  "Medicina Preventiva":       { db: "Medicina Preventiva e Social", cls: "spec-medicinapreventiva", short: "Preventiva" },
  "Pediatria":                 { db: "Pediatria",                    cls: "spec-pediatria",          short: "Pediatria" },
  "Ginecologia e Obstetrícia": { db: "Ginecologia e Obstetrícia",   cls: "spec-ginecologiaeobstetricia", short: "G.O." },
  "Cirurgia Geral":            { db: "Cirurgia",                     cls: "spec-cirurgiageral",      short: "Cirurgia" },
  "Clínica Médica":            { db: "Clínica Médica",               cls: "spec-clinicamedica",      short: "Clínica" },
};
function areaMeta(area) {
  return AREA_META[area] || { db: area, cls: "spec-clinicamedica", short: area };
}

// Datas (tratadas como locais, sem fuso)
function parseISODate(s) {
  if (!s) return null;
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y, m - 1, d);
}
function toISODate(dt) {
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, "0")}-${String(dt.getDate()).padStart(2, "0")}`;
}
function startOfDay(dt) { return new Date(dt.getFullYear(), dt.getMonth(), dt.getDate()); }
function addDays(dt, n) { const r = new Date(dt); r.setDate(r.getDate() + n); return r; }
function daysBetween(a, b) { return Math.round((startOfDay(b) - startOfDay(a)) / 86400000); }
function fmtBR(dt) { return dt.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }); }

// Encaixa os N temas do currículo no calendário real entre início e prova.
// Comprime (vários temas/semana) ou expande conforme o tempo disponível.
function computePlannerSchedule(cfg, weeks) {
  if (!cfg || !cfg.exam_date) return null;
  const today = startOfDay(new Date());
  const start = cfg.start_date ? parseISODate(cfg.start_date) : today;
  const exam = parseISODate(cfg.exam_date);
  const n = weeks.length;
  const totalDays = Math.max(n, daysBetween(start, exam));
  // Reserva de "reta final" (revisão/simulados): ~12% do tempo, entre 7 e 42 dias.
  const buffer = Math.min(42, Math.max(7, Math.round(totalDays * 0.12)));
  const studyDays = Math.max(n, totalDays - buffer);
  const daysPerTopic = studyDays / n;

  const items = weeks.map((w, i) => ({
    week: w.week,
    start: addDays(start, Math.round(i * daysPerTopic)),
    end: addDays(start, Math.max(Math.round(i * daysPerTopic), Math.round((i + 1) * daysPerTopic) - 1)),
  }));

  // Índice do tema atual (intervalo contém hoje); antes do início -> 0; depois -> último.
  let currentIndex = 0;
  if (today < items[0].start) currentIndex = 0;
  else if (today > items[n - 1].end) currentIndex = n - 1;
  else currentIndex = items.findIndex((it) => today >= it.start && today <= it.end);
  if (currentIndex < 0) currentIndex = n - 1;

  const daysToExam = daysBetween(today, exam);
  return { items, start, exam, today, totalDays, buffer, daysPerTopic, currentIndex, daysToExam };
}

async function loadPlanner() {
  try {
    const [progress, cfg, areaBreak] = await Promise.all([
      api("/api/planner"),
      api("/api/planner/config").catch(() => ({})),
      api("/api/stats/breakdown?by=area").catch(() => []),
    ]);

    state.plannerProgress = progress || {};
    window.PLANNER_WEEKS.forEach((w) => {
      if (!state.plannerProgress[w.week]) {
        state.plannerProgress[w.week] = { studied: false, studied_at: null, rev24h: false, rev7d: false, rev30d: false };
      }
    });

    state.plannerConfig = cfg && cfg.exam_date ? cfg : null;

    // Área mais fraca (mín. de tentativas para significância) para priorização.
    let weak = null;
    (areaBreak || []).forEach((a) => {
      if (a.attempts >= 3 && a.accuracy < 0.7 && (!weak || a.accuracy < weak.accuracy)) weak = a;
    });
    state.plannerWeakArea = weak;

    state.plannerSchedule = computePlannerSchedule(state.plannerConfig, window.PLANNER_WEEKS);

    if (state.viewedPlannerWeek === undefined) {
      if (state.plannerSchedule) {
        state.viewedPlannerWeek = window.PLANNER_WEEKS[state.plannerSchedule.currentIndex].week;
      } else {
        state.viewedPlannerWeek = parseInt(localStorage.getItem("medquest_last_viewed_week") || "1", 10);
      }
    }

    renderPlanner();
  } catch (err) {
    console.error("Failed to load planner:", err);
  }
}

function renderPlanner() {
  const container = $("#view-planner");
  if (!container) return;

  const viewedWeek = state.viewedPlannerWeek;
  const currentWeekData = window.PLANNER_WEEKS.find((w) => w.week === viewedWeek);
  if (!currentWeekData) return;

  const progress = state.plannerProgress[viewedWeek] || { studied: false, studied_at: null, rev24h: false, rev7d: false, rev30d: false };

  // Calcular progresso anual
  const totalWeeks = window.PLANNER_WEEKS.length;
  const studiedWeeks = Object.values(state.plannerProgress).filter((p) => p.studied).length;
  const annualPercentage = Math.round((studiedWeeks / totalWeeks) * 100);

  const sched = state.plannerSchedule;
  const cfg = state.plannerConfig;
  const weak = state.plannerWeakArea;

  // Formulário de configuração (data da prova, ritmo). Prefill com valores atuais.
  const todayISO = toISODate(startOfDay(new Date()));
  const setupForm = `
    <div class="planner-setup ${sched ? "collapsed" : ""}" id="planner-setup">
      <div class="setup-grid">
        <label>Data da prova
          <input type="date" id="cfg-exam-date" value="${cfg?.exam_date || ""}">
        </label>
        <label>Início dos estudos
          <input type="date" id="cfg-start-date" value="${cfg?.start_date || todayISO}">
        </label>
        <label>Dias de estudo / semana
          <input type="number" id="cfg-days-week" min="1" max="7" value="${cfg?.days_per_week || 6}">
        </label>
        <label>Questões / dia
          <input type="number" id="cfg-questions-day" min="5" max="200" step="5" value="${cfg?.questions_per_day || 30}">
        </label>
      </div>
      <button class="btn-primary btn-glow" id="cfg-save"><i class="ph-fill ph-magic-wand"></i> Gerar cronograma</button>
    </div>`;

  let heroHTML;
  if (!sched) {
    heroHTML = `
      <div class="planner-hero panel glass-panel">
        <div class="planner-header-info">
          <h2><i class="ph-fill ph-calendar-star"></i> Monte seu plano anual</h2>
          <p class="muted">Informe a data da prova e seu ritmo. O MedQuest encaixa os ${totalWeeks} temas no seu calendário, reserva a reta final e calcula sua cota de questões.</p>
        </div>
        ${setupForm}
      </div>`;
  } else {
    const curWeek = window.PLANNER_WEEKS[sched.currentIndex];
    const curItem = sched.items[sched.currentIndex];
    const meta = areaMeta(curWeek.area);
    const qPerWeek = (cfg.questions_per_day || 30) * (cfg.days_per_week || 6);
    const behind = studiedWeeks < sched.currentIndex;
    const urgency = sched.daysToExam <= 30 ? "urgent" : sched.daysToExam <= 90 ? "warn" : "ok";
    heroHTML = `
      <div class="planner-hero panel glass-panel">
        <div class="hero-top">
          <div class="hero-countdown ${urgency}">
            <span class="hc-num">${Math.max(0, sched.daysToExam)}</span>
            <span class="hc-lbl">dias até a prova<br><b>${sched.exam.toLocaleDateString("pt-BR")}</b></span>
          </div>
          <div class="hero-metrics">
            <div class="hero-metric"><span class="hm-val">${annualPercentage}%</span><span class="hm-lbl">${studiedWeeks}/${totalWeeks} temas</span></div>
            <div class="hero-metric"><span class="hm-val">${qPerWeek}</span><span class="hm-lbl">questões/semana</span></div>
            <div class="hero-metric"><span class="hm-val ${behind ? "behind" : "ontrack"}">${behind ? "Atrasado" : "Em dia"}</span><span class="hm-lbl">ritmo</span></div>
          </div>
          <button class="btn-ghost btn-sm" id="cfg-toggle"><i class="ph ph-gear"></i> Ajustar</button>
        </div>
        <div class="progress-bar-container"><div class="progress-bar-fill" style="width:${annualPercentage}%;"></div></div>
        ${setupForm}
        <div class="hero-week-card">
          <div class="hwc-head">
            <span class="area-badge ${meta.cls}">${meta.short}</span>
            <span class="hwc-when"><i class="ph ph-calendar-dots"></i> Esta semana · ${fmtBR(curItem.start)}–${fmtBR(curItem.end)}</span>
            ${curWeek.highYield ? '<span class="hy-badge" title="Alto rendimento">🔥</span>' : ""}
          </div>
          <h3 class="hwc-title">Tema ${curWeek.week}: ${escapeHtml(curWeek.theme)}</h3>
          <div class="hero-actions">
            <button class="btn-primary btn-sm" id="hero-study"><i class="ph ph-book-open-text"></i> Ver conteúdo</button>
            <button class="btn-primary btn-sm" id="hero-practice"><i class="ph ph-exam"></i> Fazer questões do tema</button>
            <button class="btn-ghost btn-sm" id="hero-srs"><i class="ph ph-alarm"></i> Revisões vencidas</button>
            ${weak ? `<button class="btn-ghost btn-sm" id="hero-weak"><i class="ph ph-warning"></i> Reforçar ${escapeHtml(weak.label)} (${Math.round(weak.accuracy * 100)}%)</button>` : ""}
          </div>
        </div>
      </div>`;
  }

  container.innerHTML = `
    <div class="planner-dashboard">
      ${heroHTML}

      <div class="planner-layout">
        <!-- SIDEBAR: WEEKS LIST -->
        <div class="planner-sidebar panel glass-panel">
          <h3>Semanas de Estudo</h3>
          <div class="weeks-grid">
            ${window.PLANNER_WEEKS.map((w, i) => {
              const wkProg = state.plannerProgress[w.week] || { studied: false, rev24h: false, rev7d: false, rev30d: false };
              let statusClass = '';
              if (wkProg.studied) {
                statusClass = 'completed';
                if (wkProg.rev24h && wkProg.rev7d && wkProg.rev30d) {
                  statusClass = 'fully-reviewed';
                }
              }
              const isActive = w.week === viewedWeek ? 'active' : '';
              const isCurrent = sched && sched.currentIndex === i ? 'is-current' : '';
              const isHighYield = w.highYield ? '<span class="hy-badge" title="Tema de Alto Rendimento (Muito cobrado na USP)">🔥</span>' : '';
              const meta = areaMeta(w.area);
              const dateLbl = sched ? `<span class="week-date">${fmtBR(sched.items[i].start)}</span>` : '';

              return `
                <button class="week-select-btn ${statusClass} ${isActive} ${isCurrent}" data-week="${w.week}">
                  <span class="week-area-dot ${meta.cls}"></span>
                  <span class="week-num">Tema ${w.week}${isCurrent ? ' · agora' : ''}</span>
                  <span class="week-topic-title">${escapeHtml(w.theme)}</span>
                  ${dateLbl}
                  ${isHighYield}
                </button>
              `;
            }).join('')}
          </div>
        </div>

        <!-- MAIN DETAILS PANEL -->
        <div class="planner-details-panel panel glass-panel">
          <div class="week-detail-header">
            <div class="week-title-area">
              <span class="area-badge ${areaMeta(currentWeekData.area).cls}">
                ${currentWeekData.area}
              </span>
              <h2 class="week-theme-title">Semana ${currentWeekData.week}: ${escapeHtml(currentWeekData.theme)}</h2>
            </div>
            ${currentWeekData.highYield ? `
              <div class="high-yield-banner">
                <i class="ph-fill ph-flame" style="color: #fb7185;"></i> Tema de Alto Rendimento (Prioridade USP)
              </div>
            ` : ''}
          </div>

          <div class="week-body-grid">
            <!-- CHECKLIST & SYLLABUS -->
            <div class="syllabus-card">
              <h3><i class="ph ph-check-square" style="color: var(--primary);"></i> Conteúdo Programático</h3>
              <p class="syllabus-intro">Domine os seguintes pontos-chave cobrados na prova:</p>
              <ul class="syllabus-list">
                ${currentWeekData.details.map((detail) => `
                  <li>
                    <i class="ph ph-check-circle" style="color: var(--primary); flex-shrink: 0; margin-top: 2px;"></i>
                    <span>${escapeHtml(detail)}</span>
                  </li>
                `).join('')}
              </ul>

              <div class="planner-actions" style="margin-top: 24px;">
                <button class="btn-primary" id="btn-practice-questions" style="display: flex; align-items: center; gap: 8px; justify-content: center; width: 100%;">
                  <i class="ph ph-magnifying-glass"></i> Praticar Questões do Tema
                </button>
              </div>
            </div>

            <!-- TRACKING & SPACED REPETITION -->
            <div class="tracking-card">
              <h3><i class="ph ph-arrows-clockwise" style="color: var(--success);"></i> Controle de Revisão</h3>
              
              <!-- Main studied checkbox -->
              <div class="track-item main-study" style="margin-bottom: 20px;">
                <label class="checkbox-container">
                  <input type="checkbox" id="chk-studied" ${progress.studied ? 'checked' : ''}>
                  <span class="checkmark"></span>
                  <span class="checkbox-label" style="font-weight: 600; font-size: 1rem;">Estudo Teórico Concluído</span>
                </label>
              </div>

              <!-- Spaced repetition section -->
              <div class="spaced-repetition-box ${progress.studied ? 'enabled' : 'disabled'}" style="opacity: ${progress.studied ? '1' : '0.5'}; pointer-events: ${progress.studied ? 'auto' : 'none'};">
                <h4 style="margin-bottom: 12px; font-size: 0.9rem; color: var(--text-secondary); text-transform: uppercase;">Ciclo de Revisão Espaçada</h4>
                
                <div class="track-item rev-item">
                  <label class="checkbox-container">
                    <input type="checkbox" id="chk-rev-24h" ${progress.rev24h ? 'checked' : ''} ${!progress.studied ? 'disabled' : ''}>
                    <span class="checkmark"></span>
                    <div class="rev-text">
                      <span class="checkbox-label">Revisão R1 (24 horas)</span>
                      <span class="rev-date" id="date-rev-24h" style="font-size: 0.8rem; color: var(--text-muted); display: block;"></span>
                    </div>
                  </label>
                </div>

                <div class="track-item rev-item">
                  <label class="checkbox-container">
                    <input type="checkbox" id="chk-rev-7d" ${progress.rev7d ? 'checked' : ''} ${!progress.studied ? 'disabled' : ''}>
                    <span class="checkmark"></span>
                    <div class="rev-text">
                      <span class="checkbox-label">Revisão R2 (7 dias)</span>
                      <span class="rev-date" id="date-rev-7d" style="font-size: 0.8rem; color: var(--text-muted); display: block;"></span>
                    </div>
                  </label>
                </div>

                <div class="track-item rev-item">
                  <label class="checkbox-container">
                    <input type="checkbox" id="chk-rev-30d" ${progress.rev30d ? 'checked' : ''} ${!progress.studied ? 'disabled' : ''}>
                    <span class="checkmark"></span>
                    <div class="rev-text">
                      <span class="checkbox-label">Revisão R3 (30 dias)</span>
                      <span class="rev-date" id="date-rev-30d" style="font-size: 0.8rem; color: var(--text-muted); display: block;"></span>
                    </div>
                  </label>
                </div>
              </div>

              ${progress.studied && progress.studied_at ? `
                <div class="study-date-info" style="margin-top: 16px; font-size: 0.8rem; color: var(--text-muted); display: flex; align-items: center; gap: 6px;">
                  <i class="ph ph-info" style="width: 14px; height: 14px;"></i>
                  <span>Estudado em: ${new Date(progress.studied_at).toLocaleDateString('pt-BR')} às ${new Date(progress.studied_at).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'})}</span>
                </div>
              ` : ''}
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  // Calcular datas da revisão espaçada baseadas na data de conclusão teórica
  if (progress.studied && progress.studied_at) {
    const baseDate = new Date(progress.studied_at);
    
    const d24h = new Date(baseDate);
    d24h.setDate(baseDate.getDate() + 1);
    const date24hEl = document.getElementById('date-rev-24h');
    if (date24hEl) date24hEl.textContent = `Agendado: ${d24h.toLocaleDateString('pt-BR')}`;

    const d7d = new Date(baseDate);
    d7d.setDate(baseDate.getDate() + 7);
    const date7dEl = document.getElementById('date-rev-7d');
    if (date7dEl) date7dEl.textContent = `Agendado: ${d7d.toLocaleDateString('pt-BR')}`;

    const d30d = new Date(baseDate);
    d30d.setDate(baseDate.getDate() + 30);
    const date30dEl = document.getElementById('date-rev-30d');
    if (date30dEl) date30dEl.textContent = `Agendado: ${d30d.toLocaleDateString('pt-BR')}`;
  }

  // Event Listeners para a barra lateral de seleção de semanas
  const selectBtns = container.querySelectorAll('.week-select-btn');
  selectBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const wk = parseInt(btn.getAttribute('data-week'), 10);
      state.viewedPlannerWeek = wk;
      localStorage.setItem("medquest_last_viewed_week", wk.toString());
      renderPlanner();
    });
  });

  // ── Config do plano (data da prova / ritmo) ──
  const cfgToggle = document.getElementById('cfg-toggle');
  if (cfgToggle) {
    cfgToggle.addEventListener('click', () => {
      document.getElementById('planner-setup')?.classList.toggle('collapsed');
    });
  }
  const cfgSave = document.getElementById('cfg-save');
  if (cfgSave) {
    cfgSave.addEventListener('click', async () => {
      const exam = document.getElementById('cfg-exam-date').value;
      if (!exam) { alert('Escolha a data da prova.'); return; }
      const payload = {
        exam_date: exam,
        start_date: document.getElementById('cfg-start-date').value || toISODate(startOfDay(new Date())),
        days_per_week: parseInt(document.getElementById('cfg-days-week').value, 10) || 6,
        questions_per_day: parseInt(document.getElementById('cfg-questions-day').value, 10) || 30,
      };
      try {
        await api('/api/planner/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        state.viewedPlannerWeek = undefined; // recalcula para o tema atual
        await loadPlanner();
      } catch (err) {
        console.error('Falha ao salvar config do plano:', err);
      }
    });
  }

  // ── Ações do card "Esta semana" ──
  const heroStudy = document.getElementById('hero-study');
  if (heroStudy && sched) {
    heroStudy.addEventListener('click', () => {
      state.viewedPlannerWeek = window.PLANNER_WEEKS[sched.currentIndex].week;
      renderPlanner();
      document.querySelector('.planner-details-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }
  const heroPractice = document.getElementById('hero-practice');
  if (heroPractice && sched) {
    heroPractice.addEventListener('click', () => practiceTopic(window.PLANNER_WEEKS[sched.currentIndex]));
  }
  const heroSrs = document.getElementById('hero-srs');
  if (heroSrs) {
    heroSrs.addEventListener('click', () => {
      resetFilters();
      const chip = document.querySelector('#f-status .chip[data-value="srs_due"]');
      if (chip) chip.click();
      goToStudyTab();
    });
  }
  const heroWeak = document.getElementById('hero-weak');
  if (heroWeak && weak) {
    heroWeak.addEventListener('click', () => jumpToStudyArea(weak.label));
  }

  // Event Listeners dos checkboxes de progresso
  const chkStudied = document.getElementById('chk-studied');
  const chkRev24h = document.getElementById('chk-rev-24h');
  const chkRev7d = document.getElementById('chk-rev-7d');
  const chkRev30d = document.getElementById('chk-rev-30d');

  if (chkStudied) {
    chkStudied.addEventListener('change', async (e) => {
      const studied = e.target.checked;
      try {
        const res = await api(`/api/planner/${viewedWeek}/study`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ studied })
        });
        state.plannerProgress[viewedWeek].studied = res.studied;
        state.plannerProgress[viewedWeek].studied_at = res.studied_at;
        if (!studied) {
          state.plannerProgress[viewedWeek].rev24h = false;
          state.plannerProgress[viewedWeek].rev7d = false;
          state.plannerProgress[viewedWeek].rev30d = false;
        }
        renderPlanner();
      } catch (err) {
        console.error("Failed to save study state:", err);
      }
    });
  }

  if (chkRev24h) {
    chkRev24h.addEventListener('change', async (e) => {
      const checked = e.target.checked;
      try {
        await api(`/api/planner/${viewedWeek}/revision`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ type: "rev24h", checked })
        });
        state.plannerProgress[viewedWeek].rev24h = checked;
        renderPlanner();
      } catch (err) {
        console.error("Failed to save revision state:", err);
      }
    });
  }

  if (chkRev7d) {
    chkRev7d.addEventListener('change', async (e) => {
      const checked = e.target.checked;
      try {
        await api(`/api/planner/${viewedWeek}/revision`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ type: "rev7d", checked })
        });
        state.plannerProgress[viewedWeek].rev7d = checked;
        renderPlanner();
      } catch (err) {
        console.error("Failed to save revision state:", err);
      }
    });
  }

  if (chkRev30d) {
    chkRev30d.addEventListener('change', async (e) => {
      const checked = e.target.checked;
      try {
        await api(`/api/planner/${viewedWeek}/revision`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ type: "rev30d", checked })
        });
        state.plannerProgress[viewedWeek].rev30d = checked;
        renderPlanner();
      } catch (err) {
        console.error("Failed to save revision state:", err);
      }
    });
  }

  // Event Listener do botão "Praticar Questões do Tema"
  const practiceBtn = document.getElementById('btn-practice-questions');
  if (practiceBtn) {
    practiceBtn.addEventListener('click', () => practiceTopic(currentWeekData));
  }
}

// Seleciona o chip de área correspondente ao valor do banco (dbArea).
function selectAreaChip(dbArea) {
  const chip = Array.from(document.querySelectorAll("#f-area .chip")).find(
    (c) => c.dataset.value.toLowerCase().trim() === dbArea.toLowerCase().trim()
  );
  if (chip && !chip.classList.contains("active")) chip.click();
  return !!chip;
}

// Vai para o modo Estudar filtrando pela área do tema + seus subtemas canônicos.
function practiceTopic(weekData) {
  resetFilters();
  selectAreaChip(areaMeta(weekData.area).db);
  // Preferência: subtemas canônicos exatos (precisos após a reclassificação).
  if (Array.isArray(weekData.dbSubtemas) && weekData.dbSubtemas.length) {
    weekData.dbSubtemas.forEach((s) => addSubtemaChip(s));
  } else {
    // Fallback: busca pelo primeiro termo do tema.
    const searchTerm = weekData.theme.split(" ")[0].replace(/[^a-zA-ZáéíóúÁÉÍÓÚâêôãõçÇ]/g, "");
    if (searchTerm && searchTerm.length > 2) addSubtemaChip(searchTerm);
  }
  goToStudyTab();
}

// Vai para o modo Estudar filtrando por uma área (rótulo do banco).
function jumpToStudyArea(dbArea) {
  resetFilters();
  selectAreaChip(dbArea);
  goToStudyTab();
}

// ── ★ Mapa de Cobertura USP ──────────────────────────────────

const COV_STATUS = {
  not_started: { cls: "cov-red",    label: "Não iniciado", icon: "🔴" },
  in_progress: { cls: "cov-yellow", label: "Em progresso",  icon: "🟡" },
  mastered:    { cls: "cov-green",  label: "Dominado",      icon: "🟢" },
};

// Reverse lookup: valor de área do banco -> metadados (badge/rótulo).
function areaMetaByDb(dbArea) {
  for (const label in AREA_META) {
    if (AREA_META[label].db === dbArea) return AREA_META[label];
  }
  return { db: dbArea, cls: "spec-clinicamedica", short: dbArea };
}

async function loadCoverage() {
  const container = $("#view-coverage");
  if (!container) return;
  container.innerHTML = `<div class="cov-loading"><i class="ph ph-spinner"></i> Calculando cobertura...</div>`;
  try {
    const [cov, planner] = await Promise.all([
      api("/api/coverage"),
      api("/api/planner").catch(() => ({})),
    ]);
    // temas do currículo estudados por área do banco
    const studiedByDbArea = {};
    const totalByDbArea = {};
    (window.PLANNER_WEEKS || []).forEach((w) => {
      const db = areaMeta(w.area).db;
      totalByDbArea[db] = (totalByDbArea[db] || 0) + 1;
      if (planner && planner[w.week] && planner[w.week].studied) {
        studiedByDbArea[db] = (studiedByDbArea[db] || 0) + 1;
      }
    });
    state.coverage = { areas: cov.areas, studiedByDbArea, totalByDbArea };
    renderCoverage();
  } catch (err) {
    console.error("Failed to load coverage:", err);
    container.innerHTML = `<div class="cov-loading">Erro ao carregar a cobertura.</div>`;
  }
}

function renderCoverage() {
  const container = $("#view-coverage");
  const { areas, studiedByDbArea, totalByDbArea } = state.coverage;
  const gapsOnly = state.coverageGapsOnly || false;

  // totais gerais
  let T = 0, M = 0, P = 0, N = 0;
  areas.forEach((a) => { T += a.n_subtemas; M += a.mastered; P += a.in_progress; N += a.not_started; });
  const pctMastered = T ? Math.round((M / T) * 100) : 0;

  const areaCards = areas.map((a) => {
    const meta = areaMetaByDb(a.area);
    const studied = studiedByDbArea[a.area] || 0;
    const totalThemes = totalByDbArea[a.area] || 0;
    const acc = a.accuracy != null ? Math.round(a.accuracy * 100) + "%" : "—";
    const wM = a.n_subtemas ? (a.mastered / a.n_subtemas) * 100 : 0;
    const wP = a.n_subtemas ? (a.in_progress / a.n_subtemas) * 100 : 0;
    const wN = a.n_subtemas ? (a.not_started / a.n_subtemas) * 100 : 0;

    // ordena: lacunas primeiro (não iniciado, em progresso), depois dominados; dentro, mais questões primeiro
    const order = { not_started: 0, in_progress: 1, mastered: 2 };
    let subs = a.subtemas.slice().sort((x, y) =>
      (order[x.status] - order[y.status]) || (y.n_questions - x.n_questions));
    if (gapsOnly) subs = subs.filter((s) => s.status !== "mastered");

    // Limita a exibição aos subtemas mais cobrados (prioridade USP) para não poluir.
    const CAP = 40;
    const shown = subs.slice(0, CAP);
    const extra = subs.length - shown.length;

    const chips = shown.map((s) => {
      const st = COV_STATUS[s.status];
      const accTxt = s.attempts ? ` · ${Math.round(s.accuracy * 100)}%` : "";
      return `<button class="cov-chip ${st.cls}" data-area="${escapeHtml(a.area)}" data-subtema="${escapeHtml(s.subtema)}"
                title="${st.label} — ${s.n_questions} questões, ${s.answered} respondidas${accTxt}">
                <span class="cov-chip-name">${escapeHtml(s.subtema)}</span>
                <span class="cov-chip-count">${s.n_questions}${accTxt}</span>
              </button>`;
    }).join("") + (extra > 0
      ? `<span class="cov-more muted small">+${extra} subtemas menores (1–2 questões)</span>`
      : "");

    return `
      <div class="cov-area-card panel glass-panel">
        <div class="cov-area-head">
          <span class="area-badge ${meta.cls}">${escapeHtml(meta.short)}</span>
          <div class="cov-area-stats">
            <span><b>${a.n_questions}</b> questões</span>
            <span><b>${a.n_subtemas}</b> subtemas</span>
            <span>acurácia <b>${acc}</b></span>
            <span>currículo <b>${studied}/${totalThemes}</b></span>
          </div>
        </div>
        <div class="cov-stackbar" title="${a.mastered} dominados · ${a.in_progress} em progresso · ${a.not_started} não iniciados">
          <span class="cov-green"  style="width:${wM}%"></span>
          <span class="cov-yellow" style="width:${wP}%"></span>
          <span class="cov-red"    style="width:${wN}%"></span>
        </div>
        <div class="cov-chips">${chips || '<span class="muted small">Nenhum subtema neste filtro.</span>'}</div>
      </div>`;
  }).join("");

  container.innerHTML = `
    <div class="cov-dashboard">
      <div class="cov-header panel glass-panel">
        <div>
          <h2><i class="ph-fill ph-target"></i> Cobertura do Conteúdo USP</h2>
          <p class="muted">Cada subtema pintado pelo seu domínio. Vermelho = buraco a preencher. Clique para praticar.</p>
        </div>
        <div class="cov-overall">
          <div class="cov-ring" style="--pct:${pctMastered}">
            <span>${pctMastered}%</span>
          </div>
          <div class="cov-legend">
            <span><i class="cov-dot cov-green"></i> ${M} dominados</span>
            <span><i class="cov-dot cov-yellow"></i> ${P} em progresso</span>
            <span><i class="cov-dot cov-red"></i> ${N} não iniciados</span>
            <span class="muted small">${T} subtemas no total</span>
          </div>
        </div>
        <label class="cov-toggle">
          <input type="checkbox" id="cov-gaps-only" ${gapsOnly ? "checked" : ""}>
          Mostrar só as lacunas
        </label>
      </div>
      ${areaCards}
    </div>`;

  const toggle = document.getElementById("cov-gaps-only");
  if (toggle) toggle.addEventListener("change", (e) => {
    state.coverageGapsOnly = e.target.checked;
    renderCoverage();
  });

  container.querySelectorAll(".cov-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      resetFilters();
      selectAreaChip(btn.dataset.area);
      addSubtemaChip(btn.dataset.subtema);
      goToStudyTab();
    });
  });
}

// ── Boot ─────────────────────────────────────────────────────
initFilters();
