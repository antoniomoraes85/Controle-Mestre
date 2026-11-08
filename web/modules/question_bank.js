/* Questões avulsas, por disciplina e banca; proporções ponderadas, sem séries sintéticas. */
import {api} from './http.js';
import {escapeHTML as h} from './format.js';
const pct=v=>(100*v).toLocaleString('pt-BR',{maximumFractionDigits:1})+'%';
export async function renderQuestionBankPerformance(root){
  if(!root)return;
  root.textContent='Carregando desempenho por banca...';
  try{
    const data=await api('questions/bank-performance');
    const subjects=Array.from(new Set(data.rows.map(x=>x.subject))).sort((a,b)=>a.localeCompare(b,'pt-BR'));
    root.innerHTML=`<section class="panel"><div class="panel-head"><div>
      <h2>Meu rendimento em questões por disciplina e banca</h2>
      <p>Comparação ponderada pelo número de questões resolvidas. Sem misturar redações, provas de Português ou simulados.</p></div>
      <span class="hint">BANCAS E MATÉRIAS</span></div>
      <div class="panel-content">
        <label class="cm-filter-label" for="cm-bank-subject">Filtrar matéria
          <select id="cm-bank-subject"><option value="">Todas as matérias</option>
          ${subjects.map(x=>`<option value="${h(x)}">${h(x)}</option>`).join('')}</select></label>
        <p class="subtitle">Gráfico de acertos / total. Abaixo de ${data.minimum} questões por banca, a amostra é identificada como pequena. Não presume probabilidade de acerto futura.</p>
        <div class="cm-bank-performance">${data.rows.map(x=>`<div class="cm-question-bank" data-subject="${h(x.subject)}">
          <div class="cm-bank-top"><span><strong>${h(x.subject)}</strong> · ${h(x.bank)}</span>
            <b>${pct(x.rate)}</b><small>${x.correct}/${x.total} questões</small></div>
          <div class="cm-ratio-track"><span style="width:${(x.rate*100).toFixed(1)}%"></span></div>
          ${x.sample_sufficient?'':'<small class="cm-sample-warning">Amostra pequena — não usar como conclusão definitiva.</small>'}
        </div>`).join('')||'<p class="subtitle">Cadastre questões e informe a banca para ver a comparação.</p>'}</div>
      </div></section>`;
    root.querySelector('#cm-bank-subject').addEventListener('change',e=>{
      root.querySelectorAll('.cm-question-bank').forEach(row=>row.hidden=Boolean(e.target.value&&row.dataset.subject!==e.target.value));
    });
  }catch(ex){root.textContent='Não foi possível analisar as bancas: '+ex.message;}
}
