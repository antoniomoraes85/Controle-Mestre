/**
 * CONTROLE MESTRE — Módulo de Registro Detalhado de Erros (FASE 1)
 * Dois modos: POR BATERIA (Modo A) | POR QUESTÃO (Modo B).
 *
 * API endpoints:
 *   GET  /api/questions/constants  — causas, resultados, dificuldades, etc.
 *   GET  /api/questions/caderno    — caderno de erros filtrado
 *   GET  /api/questions/summary    — estatísticas agregadas
 *   GET  /api/questions/batch/:id  — bateria com itens
 *   POST /api/questions/batch      — registrar bateria (Modo A)
 *   POST /api/questions/item       — registrar item individual (Modo B)
 *   POST /api/questions/item/correction — atualizar status de correção
 */
import { api } from './http.js';

// ---------------------------------------------------------------------------
// Estado do módulo
// ---------------------------------------------------------------------------
let _constants = null;
let _currentMode = 'batch'; // 'batch' | 'individual'
let _activeBatchId = null;   // Modo B: batch aberto para adição de itens

async function getConstants() {
  if (!_constants) _constants = await api('questions/constants');
  return _constants;
}

// ---------------------------------------------------------------------------
// Render principal — painel de registro
// ---------------------------------------------------------------------------
export async function renderQuestionsPanel(container, subjects) {
  const consts = await getConstants();
  container.innerHTML = `
    <section class="questions-panel" aria-label="Registro de Questões">
      <h2 class="panel-title">📝 Registro de Questões</h2>

      <!-- Toggle de modo -->
      <div class="mode-toggle" role="tablist" aria-label="Modo de registro">
        <button id="btn-mode-batch" role="tab" aria-selected="true"
                class="mode-btn mode-active" onclick="questionsModule.setMode('batch')">
          POR BATERIA
        </button>
        <button id="btn-mode-individual" role="tab" aria-selected="false"
                class="mode-btn" onclick="questionsModule.setMode('individual')">
          POR QUESTÃO
        </button>
      </div>

      <div id="questions-form-area"></div>
      <div id="questions-feedback" class="feedback-area" aria-live="polite"></div>
    </section>
  `;

  _renderModeForm(container, subjects, consts);
}

function _renderModeForm(container, subjects, consts) {
  const area = container.querySelector('#questions-form-area');
  if (_currentMode === 'batch') {
    area.innerHTML = _batchFormHTML(subjects, consts);
  } else {
    area.innerHTML = _individualFormHTML(subjects, consts);
  }
}

// ---------------------------------------------------------------------------
// Modo A — Formulário POR BATERIA
// ---------------------------------------------------------------------------
function _batchFormHTML(subjects, consts) {
  const subjectOptions = (subjects || [])
    .map(s => `<option value="${_esc(s.name)}">${_esc(s.name)}</option>`)
    .join('');

  const causeRows = consts.error_causes.map(cause => `
    <div class="cause-row">
      <label class="cause-label">${_esc(cause)}</label>
      <input type="number" min="0" max="999" value="0"
             class="cause-qty" data-cause="${_esc(cause)}"
             aria-label="Quantidade para ${_esc(cause)}">
    </div>
  `).join('');

  const timingOptions = consts.gabarito_timings
    .map(t => `<option value="${_esc(t)}">${_esc(t)}</option>`).join('');

  return `
    <form id="form-batch" class="register-form" onsubmit="questionsModule.submitBatch(event)">
      <div class="form-grid">
        <div class="form-group">
          <label for="b-subject">Disciplina *</label>
          <select id="b-subject" required>${subjectOptions}</select>
        </div>
        <div class="form-group">
          <label for="b-topic">Assunto</label>
          <input id="b-topic" type="text" maxlength="200" placeholder="Ex.: Obrigação Tributária">
        </div>
        <div class="form-group">
          <label for="b-day">Data *</label>
          <input id="b-day" type="date" required value="${_today()}">
        </div>
        <div class="form-group">
          <label for="b-platform">Plataforma</label>
          <input id="b-platform" type="text" maxlength="80" placeholder="TEC, Qconcursos...">
        </div>
        <div class="form-group">
          <label for="b-banca">Banca</label>
          <input id="b-banca" type="text" maxlength="80" placeholder="FCC, Cespe...">
        </div>
        <div class="form-group">
          <label for="b-total">Total de questões *</label>
          <input id="b-total" type="number" min="1" max="999" required>
        </div>
        <div class="form-group">
          <label for="b-correct">Acertos *</label>
          <input id="b-correct" type="number" min="0" max="999" required>
        </div>
        <div class="form-group">
          <label for="b-unanswered">Não resolvidas</label>
          <input id="b-unanswered" type="number" min="0" max="999" value="0">
        </div>
        <div class="form-group">
          <label for="b-time">Tempo utilizado (min)</label>
          <input id="b-time" type="number" min="0" max="999" step="0.5" value="0">
        </div>
        <div class="form-group">
          <label for="b-gabarito">Consulta ao gabarito</label>
          <select id="b-gabarito">${timingOptions}</select>
        </div>
        <div class="form-group form-check">
          <label>
            <input id="b-prior-review" type="checkbox">
            Havia feito revisão antes de resolver
          </label>
        </div>
      </div>

      <!-- Causas de erro por categoria -->
      <fieldset class="causes-fieldset">
        <legend>Causas predominantes dos erros
          <span class="note-inline">— opcional; use apenas se souber as quantidades</span>
        </legend>
        <p class="causes-note">
          ⚠️ Esta classificação é <strong>geral da bateria</strong>.
          Para maior precisão, use o modo <strong>POR QUESTÃO</strong>.
        </p>
        <div class="causes-grid">${causeRows}</div>
      </fieldset>

      <div class="form-group full-width">
        <label for="b-notes">Observações</label>
        <textarea id="b-notes" rows="2" maxlength="500"></textarea>
      </div>

      <div class="form-actions">
        <button type="submit" class="btn-primary">Registrar Bateria</button>
      </div>
    </form>
  `;
}

// ---------------------------------------------------------------------------
// Modo B — Formulário POR QUESTÃO
// ---------------------------------------------------------------------------
function _individualFormHTML(subjects, consts) {
  const subjectOptions = (subjects || [])
    .map(s => `<option value="${_esc(s.name)}">${_esc(s.name)}</option>`)
    .join('');

  const timingOptions = consts.gabarito_timings
    .map(t => `<option value="${_esc(t)}">${_esc(t)}</option>`).join('');

  const activeBatchNote = _activeBatchId
    ? `<div class="active-batch-note">
         📋 Bateria ativa: <strong>#${_activeBatchId}</strong>
         <button type="button" class="btn-link" onclick="questionsModule.clearActiveBatch()">
           Encerrar e iniciar nova
         </button>
       </div>`
    : '';

  return `
    ${activeBatchNote}
    <!-- Passo 1: Dados da bateria (se não houver ativa) -->
    ${_activeBatchId ? '' : `
    <details class="batch-header-collapsible" ${_activeBatchId ? '' : 'open'}>
      <summary>📋 Dados da bateria (preencha antes de lançar questões)</summary>
      <form id="form-batch-header" class="register-form"
            onsubmit="questionsModule.openBatchForItems(event)">
        <div class="form-grid">
          <div class="form-group">
            <label for="ih-subject">Disciplina *</label>
            <select id="ih-subject" required>${subjectOptions}</select>
          </div>
          <div class="form-group">
            <label for="ih-topic">Assunto</label>
            <input id="ih-topic" type="text" maxlength="200">
          </div>
          <div class="form-group">
            <label for="ih-day">Data *</label>
            <input id="ih-day" type="date" required value="${_today()}">
          </div>
          <div class="form-group">
            <label for="ih-platform">Plataforma</label>
            <input id="ih-platform" type="text" maxlength="80">
          </div>
          <div class="form-group">
            <label for="ih-banca">Banca</label>
            <input id="ih-banca" type="text" maxlength="80">
          </div>
          <div class="form-group">
            <label for="ih-total">Total de questões *</label>
            <input id="ih-total" type="number" min="1" max="999" required>
          </div>
          <div class="form-group">
            <label for="ih-correct">Acertos totais *</label>
            <input id="ih-correct" type="number" min="0" max="999" required>
          </div>
          <div class="form-group">
            <label for="ih-gabarito">Consulta ao gabarito</label>
            <select id="ih-gabarito">${timingOptions}</select>
          </div>
        </div>
        <div class="form-actions">
          <button type="submit" class="btn-secondary">Iniciar lançamento por questão</button>
        </div>
      </form>
    </details>
    `}

    <!-- Passo 2: Lançamento rápido por questão -->
    <div id="items-area" class="${_activeBatchId ? '' : 'hidden'}">
      <h3 class="section-title">Questões individuais</h3>
      <p class="section-hint">
        Marque cada questão rapidamente. Campos opcionais permanecem opcionais.
      </p>
      <form id="form-item" class="register-form"
            onsubmit="questionsModule.submitItem(event)">
        <div class="form-grid">
          <div class="form-group">
            <label for="qi-ref">ID/Ref. da questão</label>
            <input id="qi-ref" type="text" maxlength="100" placeholder="Opcional">
          </div>
          <div class="form-group">
            <label for="qi-subject">Disciplina</label>
            <select id="qi-subject">${subjectOptions}</select>
          </div>
          <div class="form-group">
            <label for="qi-topic">Assunto</label>
            <input id="qi-topic" type="text" maxlength="200">
          </div>
          <div class="form-group">
            <label for="qi-subtopic">Subassunto</label>
            <input id="qi-subtopic" type="text" maxlength="200">
          </div>
        </div>

        <!-- Resultado rápido -->
        <div class="result-quick-pick" role="group" aria-label="Resultado">
          <label class="result-label">Resultado *</label>
          <div class="result-buttons">
            ${consts.results.map(r => `
              <button type="button" class="result-btn result-${_resultClass(r)}"
                      data-result="${_esc(r)}"
                      onclick="questionsModule.pickResult(this)">
                ${_resultIcon(r)} ${_esc(r)}
              </button>
            `).join('')}
          </div>
          <input type="hidden" id="qi-result" required>
        </div>

        <!-- Causa (aparece quando resultado = Incorreta) -->
        <div id="cause-block" class="hidden">
          <div class="form-grid">
            <div class="form-group">
              <label for="qi-cause">Causa principal</label>
              <select id="qi-cause">
                ${consts.error_causes.map(c =>
                  `<option value="${_esc(c)}">${_esc(c)}</option>`).join('')}
              </select>
            </div>
            <div class="form-group">
              <label for="qi-difficulty">Dificuldade percebida</label>
              <select id="qi-difficulty">
                <option value="">— não informar —</option>
                ${consts.difficulties.map(d =>
                  `<option value="${_esc(d)}">${_esc(d)}</option>`).join('')}
              </select>
            </div>
            <div class="form-group">
              <label for="qi-time">Tempo de resolução (s)</label>
              <input id="qi-time" type="number" min="0" max="99999" value="0">
            </div>
          </div>
          <div class="form-group full-width">
            <label>Causas secundárias</label>
            <div class="secondary-causes-grid">
              ${consts.error_causes.map(c => `
                <label class="checkbox-label">
                  <input type="checkbox" class="sec-cause-cb" value="${_esc(c)}">
                  ${_esc(c)}
                </label>
              `).join('')}
            </div>
          </div>
        </div>

        <div class="form-grid">
          <div class="form-check">
            <label>
              <input id="qi-gabarito" type="checkbox">
              Consultou gabarito/comentário
            </label>
          </div>
          <div class="form-check">
            <label>
              <input id="qi-reinforcement" type="checkbox">
              Marcar para reforço
            </label>
          </div>
        </div>
        <div class="form-group full-width">
          <label for="qi-obs">Observação</label>
          <input id="qi-obs" type="text" maxlength="500" placeholder="Opcional">
        </div>

        <div class="form-actions">
          <button type="submit" class="btn-primary">➕ Adicionar questão</button>
        </div>
      </form>

      <div id="items-list" class="items-list"></div>

      <div class="form-actions form-actions-end">
        <button type="button" class="btn-secondary" onclick="questionsModule.clearActiveBatch()">
          ✅ Concluir bateria
        </button>
      </div>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Handlers de eventos — toggle de modo
// ---------------------------------------------------------------------------
export function setMode(mode) {
  _currentMode = mode;
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.classList.toggle('mode-active', btn.id === `btn-mode-${mode}`);
    btn.setAttribute('aria-selected', btn.id === `btn-mode-${mode}` ? 'true' : 'false');
  });
  const container = document.querySelector('.questions-panel');
  if (container) {
    getConstants().then(consts => {
      const subjects = window._cm_subjects || [];
      _renderModeForm(container.parentElement, subjects, consts);
    });
  }
}

// ---------------------------------------------------------------------------
// Handler — Envio de bateria (Modo A)
// ---------------------------------------------------------------------------
export async function submitBatch(event) {
  event.preventDefault();
  const fb = document.getElementById('questions-feedback');
  _setFeedback(fb, 'info', 'Registrando…');

  const causeCounts = {};
  document.querySelectorAll('.cause-qty').forEach(inp => {
    const qty = parseInt(inp.value, 10);
    if (qty > 0) causeCounts[inp.dataset.cause] = qty;
  });

  const payload = {
    subject: document.getElementById('b-subject').value,
    topic: document.getElementById('b-topic').value,
    day: document.getElementById('b-day').value,
    platform: document.getElementById('b-platform').value,
    banca: document.getElementById('b-banca').value,
    total: parseInt(document.getElementById('b-total').value, 10),
    correct: parseInt(document.getElementById('b-correct').value, 10),
    unanswered: parseInt(document.getElementById('b-unanswered').value || '0', 10),
    time_used_min: parseFloat(document.getElementById('b-time').value || '0'),
    had_prior_review: document.getElementById('b-prior-review').checked,
    gabarito_timing: document.getElementById('b-gabarito').value,
    mode: 'batch',
    cause_counts: causeCounts,
    notes: document.getElementById('b-notes').value,
  };

  try {
    const result = await api('questions/batch', payload);
    const rate = result.performance?.rate;
    const pct = rate !== null && rate !== undefined ? ` (${(rate * 100).toFixed(1)}%)` : '';
    _setFeedback(fb, 'success',
      `✅ Bateria #${result.batch_id} registrada — `
      + `${result.performance?.correct}/${result.performance?.total} acertos${pct}.`);
    document.getElementById('form-batch').reset();
    document.getElementById('b-day').value = _today();
  } catch (err) {
    _setFeedback(fb, 'error', `❌ ${err.message}`);
  }
}

// ---------------------------------------------------------------------------
// Handler — Abrir bateria para itens (Modo B)
// ---------------------------------------------------------------------------
export async function openBatchForItems(event) {
  event.preventDefault();
  const fb = document.getElementById('questions-feedback');
  _setFeedback(fb, 'info', 'Criando bateria…');

  const payload = {
    subject: document.getElementById('ih-subject').value,
    topic: document.getElementById('ih-topic').value,
    day: document.getElementById('ih-day').value,
    platform: document.getElementById('ih-platform').value,
    banca: document.getElementById('ih-banca').value,
    total: parseInt(document.getElementById('ih-total').value, 10),
    correct: parseInt(document.getElementById('ih-correct').value, 10),
    gabarito_timing: document.getElementById('ih-gabarito').value,
    mode: 'individual',
    cause_counts: {},
  };

  try {
    const result = await api('questions/batch', payload);
    _activeBatchId = result.batch_id;
    _setFeedback(fb, 'success', `✅ Bateria #${_activeBatchId} aberta. Adicione as questões abaixo.`);
    // Re-renderiza o formulário mostrando a área de itens
    const container = document.querySelector('.questions-panel');
    if (container) {
      const consts = await getConstants();
      _renderModeForm(container.parentElement, window._cm_subjects || [], consts);
    }
  } catch (err) {
    _setFeedback(fb, 'error', `❌ ${err.message}`);
  }
}

// ---------------------------------------------------------------------------
// Handler — Adicionar item individual (Modo B)
// ---------------------------------------------------------------------------
export async function submitItem(event) {
  event.preventDefault();
  if (!_activeBatchId) {
    alert('Nenhuma bateria ativa. Preencha os dados da bateria primeiro.');
    return;
  }
  const fb = document.getElementById('questions-feedback');
  const result = document.getElementById('qi-result').value;
  if (!result) { _setFeedback(fb, 'error', '❌ Selecione o resultado da questão.'); return; }

  const secondaryCauses = [...document.querySelectorAll('.sec-cause-cb:checked')]
    .map(cb => cb.value);

  const payload = {
    batch_id: _activeBatchId,
    question_ref: document.getElementById('qi-ref').value,
    subject: document.getElementById('qi-subject').value,
    topic: document.getElementById('qi-topic').value,
    subtopic: document.getElementById('qi-subtopic').value,
    result,
    primary_cause: result === 'Incorreta'
      ? (document.getElementById('qi-cause')?.value || 'Não especificado')
      : 'Não especificado',
    secondary_causes: secondaryCauses,
    observation: document.getElementById('qi-obs').value,
    difficulty: document.getElementById('qi-difficulty')?.value || '',
    resolution_time_s: parseInt(document.getElementById('qi-time')?.value || '0', 10),
    consulted_gabarito: document.getElementById('qi-gabarito').checked,
    needs_reinforcement: document.getElementById('qi-reinforcement').checked,
    correction_status: 'Aberto',
  };

  try {
    const res = await api('questions/item', payload);
    _setFeedback(fb, 'success', `✅ Questão #${res.item_id} adicionada.`);
    _appendItemToList(res.item_id, payload);
    document.getElementById('form-item').reset();
    document.getElementById('qi-result').value = '';
    document.querySelectorAll('.result-btn').forEach(b => b.classList.remove('result-selected'));
    document.getElementById('cause-block')?.classList.add('hidden');
  } catch (err) {
    _setFeedback(fb, 'error', `❌ ${err.message}`);
  }
}

function _appendItemToList(itemId, payload) {
  const list = document.getElementById('items-list');
  if (!list) return;
  const icon = _resultIcon(payload.result);
  const div = document.createElement('div');
  div.className = `item-entry item-${_resultClass(payload.result)}`;
  div.innerHTML = `<span class="item-num">#${itemId}</span>
    <span class="item-icon">${icon}</span>
    <span class="item-info">${_esc(payload.topic || payload.subject)}</span>
    ${payload.primary_cause && payload.result === 'Incorreta'
      ? `<span class="item-cause">${_esc(payload.primary_cause)}</span>` : ''}`;
  list.appendChild(div);
}

// ---------------------------------------------------------------------------
// Handler — Resultado rápido (Modo B)
// ---------------------------------------------------------------------------
export function pickResult(btn) {
  document.querySelectorAll('.result-btn').forEach(b => b.classList.remove('result-selected'));
  btn.classList.add('result-selected');
  document.getElementById('qi-result').value = btn.dataset.result;
  const causeBlock = document.getElementById('cause-block');
  if (causeBlock) {
    if (btn.dataset.result === 'Incorreta') causeBlock.classList.remove('hidden');
    else causeBlock.classList.add('hidden');
  }
}

// ---------------------------------------------------------------------------
// Handler — Encerrar bateria ativa
// ---------------------------------------------------------------------------
export async function clearActiveBatch() {
  _activeBatchId = null;
  const container = document.querySelector('.questions-panel');
  if (container) {
    const consts = await getConstants();
    _renderModeForm(container.parentElement, window._cm_subjects || [], consts);
  }
}

// ---------------------------------------------------------------------------
// Caderno de Erros — visualização
// ---------------------------------------------------------------------------
export async function renderCaderno(container, filters = {}) {
  container.innerHTML = '<p class="loading">Carregando caderno de erros…</p>';
  try {
    const params = new URLSearchParams();
    if (filters.subject) params.set('subject', filters.subject);
    if (filters.topic) params.set('topic', filters.topic);
    if (filters.primary_cause) params.set('primary_cause', filters.primary_cause);
    if (filters.correction_status) params.set('correction_status', filters.correction_status);
    if (filters.needs_reinforcement !== undefined)
      params.set('needs_reinforcement', filters.needs_reinforcement ? '1' : '0');

    const data = await api(`questions/caderno?${params}`);
    if (!data.length) {
      container.innerHTML = '<p class="empty-state">Nenhum erro registrado individualmente ainda.</p>';
      return;
    }
    container.innerHTML = `
      <table class="caderno-table" aria-label="Caderno de Erros">
        <thead>
          <tr>
            <th>Data</th><th>Disciplina</th><th>Assunto</th>
            <th>Causa principal</th><th>Dificuldade</th>
            <th>Correção</th><th>Reforço</th>
          </tr>
        </thead>
        <tbody>
          ${data.map(it => `
            <tr class="item-row item-${_resultClass(it.result)}">
              <td>${it.day}</td>
              <td>${_esc(it.subject)}</td>
              <td>${_esc(it.topic)}${it.subtopic ? ` › ${_esc(it.subtopic)}` : ''}</td>
              <td>${_esc(it.primary_cause)}</td>
              <td>${_esc(it.difficulty || '—')}</td>
              <td>
                <select class="correction-select" data-id="${it.id}"
                        onchange="questionsModule.updateCorrection(this)">
                  <option ${it.correction_status === 'Aberto' ? 'selected' : ''}>Aberto</option>
                  <option ${it.correction_status === 'Corrigida' ? 'selected' : ''}>Corrigida</option>
                  <option ${it.correction_status === 'Revisada' ? 'selected' : ''}>Revisada</option>
                </select>
              </td>
              <td>${it.needs_reinforcement ? '🔴' : '—'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = `<p class="error-state">❌ ${_esc(err.message)}</p>`;
  }
}

export async function updateCorrection(select) {
  const id = parseInt(select.dataset.id, 10);
  const status = select.value;
  try {
    await api('questions/item/correction', { id, correction_status: status });
  } catch (err) {
    alert(`Erro ao atualizar: ${err.message}`);
    // Reverter seleção visualmente (recarregar caderno).
  }
}

// ---------------------------------------------------------------------------
// Utilitários internos
// ---------------------------------------------------------------------------
function _esc(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#x27;');
}

function _today() {
  return new Date().toISOString().slice(0, 10);
}

function _resultClass(result) {
  if (result === 'Correta') return 'correct';
  if (result === 'Incorreta') return 'incorrect';
  return 'unanswered';
}

function _resultIcon(result) {
  if (result === 'Correta') return '✅';
  if (result === 'Incorreta') return '❌';
  return '⬜';
}

function _setFeedback(el, type, msg) {
  if (!el) return;
  el.className = `feedback-area feedback-${type}`;
  el.textContent = msg;
}
