/* Provas completas de Português, evolução cronológica e comparação entre bancas. */
import {api} from './http.js';
import {escapeHTML as h} from './format.js';
const p=x=>x==null?'—':(x*100).toLocaleString('pt-BR',{maximumFractionDigits:1})+'%';
const pt=(x,minutes)=>({rate:x,total:minutes});
function progressBar(value){return `<div class="cm-ratio-track"><span style="width:${Math.max(0,Math.min(100,100*value))}%"></span></div>`;}
function trend(title,entries,rate){
  let points=entries.slice().sort((a,b)=>a.day.localeCompare(b.day)||a.id-b.id);
  if(!points.length)return `<section class="panel"><div class="panel-head"><h2>${h(title)}</h2></div><div class="panel-content"><p class="subtitle">Aguardando os primeiros registros.</p></div></section>`;
  const max=points.length;
  const circles=points.map((e,i)=>{
    const n=rate(e), x=max===1?50:5+i*90/(max-1),y=95-Math.max(0,Math.min(1,n))*90;
    return `<circle cx="${x}" cy="${y}" r="1.4"><title>${h(e.day)} — ${p(n)}</title></circle>`;
  }).join('');
  const path=points.map((e,i)=>{
    const x=max===1?50:5+i*90/(max-1),y=95-Math.max(0,Math.min(1,rate(e)))*90;
    return `${i?'L':'M'}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(' ');
  return `<section class="panel"><div class="panel-head"><h2>${h(title)}</h2></div>
    <div class="panel-content"><svg viewBox="0 0 100 100" role="img"
     aria-label="Evolução dos rendimentos, cada ponto representa uma prova">
    <path d="${path}" fill="none" stroke="#e4b52a" stroke-width="1.8" vector-effect="non-scaling-stroke"/>
    <g fill="#ffd35a" stroke="#30313c" stroke-width=".2">${circles}</g></svg>
    <p class="subtitle">${points.length} registro(s) · ordem cronológica · eixo vertical 0% a 100%</p></div></section>`;
}
function bankChart(title,rows,key='rate',count='exams'){
  return `<section class="panel"><div class="panel-head"><h2>${h(title)}</h2></div><div class="panel-content">
  ${rows.length?rows.map(x=>`<div class="cm-bank-row"><div class="cm-bank-top"><span>${h(x.bank)}</span><b>${p(x[key])}</b>
    <small>${x[count]} registro(s)</small></div>${progressBar(x[key]||0)}</div>`).join(''):
    '<p class="subtitle">Nenhuma banca com registros nesta categoria.</p>'}
  </div></section>`;
}
export async function renderAssessmentInsights(root){
  root.textContent='Carregando histórico de avaliações...';
  try{
    const data=await api('assessment/insights');
    const ptex=data.portuguese;
    root.innerHTML=`<section class="panel"><div class="panel-head"><div>
      <h2>Provas completas de Português — histórico independente</h2>
      <p>Provas anteriores por banca, com acertos, erros, brancos e evolução individual.</p></div>
      <button class="btn primary" data-action="portuguese-form">+ Registrar prova de Português</button></div>
      <div class="panel-content">
      <div class="cm-time-stats">
        <div class="panel"><div class="panel-content"><small>Provas completas</small><h2>${ptex.length}</h2></div></div>
        <div class="panel"><div class="panel-content"><small>Rendimento ponderado</small><h2>${p(data.portuguese_rate)}</h2></div></div>
      </div>
      ${ptex.length?`<div class="table-wrap"><table class="act-table"><thead><tr>
        <th>Data</th><th>Prova anterior</th><th>Banca</th><th>Ano</th><th>Acertos</th><th>Rendimento</th><th>Ação</th>
      </tr></thead><tbody>${ptex.map(e=>`<tr><td>${h(e.day)}</td><td>${h(e.title)}</td>
        <td>${h(e.bank)}</td><td>${h(e.year||'—')}</td><td>${e.correct}/${e.total}</td>
        <td>${p(e.correct/e.total)}</td><td><button class="btn small" data-action="portuguese-delete" data-id="${e.id}">Excluir</button></td>
      </tr>`).join('')}</tbody></table></div>`:
      '<p class="subtitle">Ainda não há provas completas de Português cadastradas.</p>'}
      <p class="subtitle">Provas de Português não entram automaticamente nos simulados gerais nem nas questões avulsas.</p>
      </div></section>
      <div class="cm-dashboard-grid">
        ${trend('Português · evolução por prova',ptex,e=>e.correct/e.total)}
        ${trend('Simulados · evolução por prova',data.mocks||[],e=>e.correct/e.total)}
        ${trend('Redações · evolução por avaliação',data.essays||[],e=>e.grade/e.maximum_grade)}
        ${bankChart('Português · rendimento por banca',data.portuguese_banks)}
        ${bankChart('Simulados · rendimento por banca',data.mock_banks)}
        ${bankChart('Redações · rendimento por banca',data.essays_banks,'mean_rate','count')}
      </div>`;
  }catch(ex){root.textContent='Falha ao carregar históricos: '+ex.message;}
}
export function portugueseForm(modal,api){
  const d=new Date(),day=[d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');
  modal('Registrar prova completa de Português',`<form>
    <div class="fields"><div class="field"><label>Concurso / prova</label>
      <input required maxlength="160" name="title" placeholder="Ex.: SEFAZ-RS 2018 — Português"></div>
      <div class="field"><label>Banca organizadora</label><input required maxlength="80" name="bank" placeholder="Ex.: FCC, Cebraspe, FGV"></div></div>
    <div class="fields"><div class="field"><label>Data de resolução</label><input required type="date" name="day" value="${day}"></div>
      <div class="field"><label>Ano da prova</label><input type="number" min="1990" max="2100" name="year"></div>
      <div class="field"><label>Origem / referência</label><input maxlength="160" name="origin" placeholder="Ex.: concurso e cargo"></div></div>
    <div class="fields"><div class="field"><label>Total de questões</label><input type="number" name="total" min="1" max="300" required value="20"></div>
      <div class="field"><label>Acertos</label><input type="number" name="correct" min="0" required value="0"></div>
      <div class="field"><label>Erros</label><input type="number" name="wrong" min="0" required value="20"></div>
      <div class="field"><label>Brancos</label><input type="number" name="blank" min="0" required value="0"></div>
      <div class="field"><label>Tempo (minutos, opcional)</label><input type="number" name="minutes" min="1" max="600"></div></div>
    <div class="field"><label>Observações / assuntos com dificuldade</label><textarea name="notes" maxlength="1200"></textarea></div>
    <p class="assess-note">Total = acertos + erros + brancos. O registro fica separado de simulados e questões avulsas.</p>
    <div class="form-actions"><button class="btn ghost" type="button" data-action="close-modal">Cancelar</button>
      <button class="btn primary" type="submit">Salvar prova</button></div>
    </form>`,async f=>{await api('assessment/portuguese',Object.fromEntries(f))});
}
