/* Recomendações baseadas em registros do próprio usuário; nunca dados fictícios. */
import {escapeHTML,fmt,fmtHour,pct,dateFmt} from './format.js';

export function adaptiveView(d, {heading, actionBtn}) {
  const diag=d.adaptive||{}, plan=d.adaptive_preview||{};
  const items=diag.recommendations||[];
  const short=Number(plan.shortfall_minutes||0);
  const header=heading('Planejamento inteligente',
    'Diagnóstico por assunto, causas de erro e sugestão de tarefas auditáveis.',
    actionBtn('apply-adaptive','Aplicar plano inteligente','primary'));
  const summary=`<div class="metrics">
      <article class="metric blue"><label>QUESTÕES AVALIADAS • 90 DIAS</label><div class="num">${Number(diag.total_questions_in_window||0).toLocaleString('pt-BR')}</div><small>Dados pessoais registrados</small></article>
      <article class="metric green"><label>CARGA PROPOSTA</label><div class="num">${fmtHour(plan.total_planned_minutes||0)}</div><small>Meta: ${fmtHour(plan.target_minutes||0)}</small></article>
      <article class="metric orange"><label>ATIVIDADES NOVAS</label><div class="num">${Number(plan.task_count||0)}</div><small>Prévia — nenhuma alteração ainda</small></article>
      <article class="metric yellow"><label>HORAS NÃO ALOCADAS</label><div class="num">${fmtHour(short)}</div><small>${short?'Aumente a disponibilidade dos dias':'Disponibilidade compatível com a meta'}</small></article>
    </div>`;
  const warning=short?`<div class="info-box" role="status"><b>Disponibilidade insuficiente:</b> faltam ${fmtHour(short)} para atingir a meta semanal. Ajuste seus dias em Planejamento antes de aplicar. Nenhuma hora foi inventada.</div>`:
    `<div class="info-box">O plano considera a disponibilidade real da semana e preserva atividades já concluídas. Para substituir as pendentes, use o botão após revisar a prévia.</div>`;
  const intro=diag.coverage==='Diagnóstico inicial'?`<div class="info-box"><b>Diagnóstico inicial:</b> existem poucas questões recentes. As prioridades começam pelos pesos estratégicos e sugerem coleta de evidências, não classificam assuntos como dominados ou fracos sem dados.</div>`:'';
  const priority=items.length?items.map((x,i)=>`<article class="adaptive-item">
      <div class="adaptive-rank">${i+1}</div><div class="adaptive-info">
      <div class="adaptive-label"><b>${escapeHTML(x.subject)}</b><span class="tag ${x.confidence==='Aferido'?'high':'warn'}">${escapeHTML(x.confidence)}</span></div>
      <p class="adaptive-topic">${escapeHTML(x.topic||'Diagnóstico geral da disciplina')}</p>
      <p class="adaptive-rationale">${escapeHTML(x.rationale)}</p>
      <div class="adaptive-badges"><span>Próxima ação: <b>${escapeHTML(x.action)}</b></span>
      <span>${x.rate===null?'Acertos: não aferidos':`Acertos: ${pct(x.rate)}`}</span>
      ${x.due_reviews?`<span>${x.due_reviews} revisão(ões) pendente(s)</span>`:''}</div>
      </div><strong class="adaptive-score">${fmt(x.score)}</strong></article>`).join(''):'<p class="subtitle">Ainda não existem disciplinas ou assuntos suficientes para gerar prioridades.</p>';
  const tasks=(plan.tasks||[]).slice(0,25).map(x=>`<tr><td>${dateFmt(x.day)}</td><td>${escapeHTML(x.subject)}<br><small>${escapeHTML(x.topic)}</small></td><td>${escapeHTML(x.method)}</td><td>${fmtHour(x.target_minutes)}</td></tr>`).join('');
  const table=tasks?`<div class="table-wrap"><table class="act-table"><thead><tr><th>Dia</th><th>Disciplina / assunto</th><th>Método</th><th>Tempo</th></tr></thead><tbody>${tasks}</tbody></table></div>`:'<div class="panel-content"><p class="subtitle">Nenhuma tarefa foi sugerida para a disponibilidade configurada.</p></div>';
  const reinforce=(d.reinforcements?.items||[]).slice(0,6);
  const reinforceContent=reinforce.length?reinforce.map(x=>`<article class="adaptive-item">
    <div class="adaptive-info">
      <div class="adaptive-label"><b>${escapeHTML(x.subject)}</b>
        <span class="tag ${x.level==='Intenso'?'warn':'high'}">${escapeHTML('Reforço '+x.level)}</span></div>
      <p class="adaptive-topic">${escapeHTML(x.topic||'Disciplina — assunto não identificado')}</p>
      <p class="adaptive-rationale">${escapeHTML(x.explanation)} · ${x.accuracy===null?'Rendimento não aferido':pct(x.accuracy)} · ${x.due_reviews} revisão(ões) pendente(s)</p>
      <p class="adaptive-rationale"><b>Ação:</b> ${escapeHTML(x.action)}</p>
      <p class="adaptive-rationale"><b>Orientação:</b> ${escapeHTML(x.guidance)}</p>
      ${x.dominant_item_cause||x.dominant_batch_cause?`<p class="adaptive-rationale">Causa: ${escapeHTML(x.dominant_item_cause||x.dominant_batch_cause)} — ${escapeHTML(x.cause_scope)}</p>`:''}
      <small>${escapeHTML(x.evidence)}</small>
    </div></article>`).join(''):'<p class="subtitle">Ainda não há evidências suficientes para indicar reforços específicos.</p>';
  const reinforcementPanel=`<section class="panel" style="margin-bottom:18px">
    <div class="panel-head"><div><h2>Reforços inteligentes</h2><p>Triagem por assunto, dificuldades observadas e próximas ações</p></div><span class="hint">SEM ALTERAR O PLANO</span></div>
    <div class="panel-content">${reinforceContent}</div></section>`;
  return `${header}${summary}${warning}${intro}${reinforcementPanel}<div class="small-grid"><section class="panel">
    <div class="panel-head"><div><h2>Mapa de prioridades</h2><p>Recomendações com motivo e nível de evidência</p></div><span class="hint">TOP ${items.length}</span></div>
    <div class="panel-content">${priority}</div></section>
    <section class="panel"><div class="panel-head"><div><h2>Prévia da próxima semana</h2><p>Nenhuma atividade é alterada até sua confirmação</p></div><span class="hint">${plan.task_count||0} TAREFAS</span></div>${table}</section></div>
    <div class="info-box" style="margin-top:18px">O índice é uma <b>heurística explicável</b>, não uma previsão de aprovação. Os resultados não incluem simulados, rankings externos ou desempenho que não tenha sido registrado.</div>`;
}