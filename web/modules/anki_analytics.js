/* Análise do histórico de revisões Anki sem alterações nos baralhos. */
import {api} from './http.js';
import {escapeHTML} from './format.js';
const h=escapeHTML;
const pct=n=>(100*n).toLocaleString('pt-BR',{maximumFractionDigits:1})+'%';
export async function renderAnkiAnalytics(root){
  if(!root)return;
  async function draw(){
    root.innerHTML='<p class="subtitle">Carregando histórico de revisões…</p>';
    try{
      const data=await api('anki/analytics');
      const rows=data.subjects;
      const reliable=rows.filter(x=>x.review_sample_sufficient);
      const attention=reliable.filter(x=>x.review_success_rate<.80);
      const max=Math.max(1,...data.daily.map(x=>x.all_answers));
      root.innerHTML=`<section class="panel"><div class="panel-head"><div>
          <h2>Anki · Desempenho por disciplina (últimos 30 dias)</h2>
          <p>Leitura do histórico de respostas do Anki. Não modifica cartões, baralhos nem FSRS.</p>
        </div><span class="hint">FONTE: ANKICONNECT / REVLOG</span></div>
        <div class="panel-content">
          <div class="fiscal-actions">
            <button class="btn primary" type="button" id="anki-stats-refresh">Analisar respostas (30 dias)</button>
            <span class="subtitle">Última análise: ${data.last_sync?h(data.last_sync.replace('T',' ')):'ainda não realizada'}</span>
          </div>
          <div class="info-box" style="margin-top:12px">
            <strong>Critério:</strong> índice de respostas não-Again somente em revisões
            programadas (tipo 1). Mínimo de ${data.sample_min} respostas por disciplina para exibir
            percentuais comparáveis. Este índice <b>não mede domínio futuro nem nota de prova</b>.
            O tempo do Anki não é somado às horas do cronômetro.
          </div>
          <div class="cm-time-stats">
            <div class="panel"><div class="panel-content"><small>Respostas registradas</small><h2>${data.total_answers}</h2></div></div>
            <div class="panel"><div class="panel-content"><small>Respostas Again</small><h2>${data.total_again}</h2></div></div>
            <div class="panel"><div class="panel-content"><small>Revisões programadas</small><h2>${data.total_review_answers}</h2></div></div>
            <div class="panel"><div class="panel-content"><small>Disciplinas com amostra</small><h2>${reliable.length}</h2></div></div>
          </div>
          ${attention.length?`<div class="info-box"><strong>Pontos de atenção observados:</strong>
            ${attention.map(x=>`${h(x.subject)} (${pct(x.review_success_rate)}, n=${x.review_answers})`).join(' · ')}.
            Priorize diagnóstico dos erros antes de aumentar o volume de cartões.</div>`:
            '<p class="subtitle">Nenhuma disciplina possui evidência suficiente de baixo desempenho no período.</p>'}
          ${rows.length?`<div class="table-wrap"><table class="act-table"><thead>
            <tr><th>Disciplina</th><th>Respostas</th><th>Again</th><th>Revisões tipo 1</th><th>Índice não-Again</th><th>Interpretação</th></tr>
            </thead><tbody>${rows.map(x=>`<tr><td>${h(x.subject)}</td>
              <td>${x.all_answers}</td><td>${x.again_answers}</td><td>${x.review_answers}</td>
              <td>${x.review_sample_sufficient?pct(x.review_success_rate):'Amostra insuficiente'}</td>
              <td>${!x.review_sample_sufficient?'Acompanhar':x.review_success_rate<.8?'Reforçar':'Monitorar'}</td>
            </tr>`).join('')}</tbody></table></div>`:
            '<p class="subtitle">Nenhum histórico de respostas analisado. Mantenha o Anki aberto e clique em Analisar respostas (30 dias).</p>'}
          <h3 style="margin:20px 0 10px">Atividade diária de revisões</h3>
          <div class="cm-time-list">${data.daily.map(x=>`
            <div class="cm-time-row" title="${h(x.day)} · ${x.all_answers} respostas / ${x.again_answers} Again">
              <span class="cm-time-label">${h(x.day.slice(8)+'/'+x.day.slice(5,7))}</span>
              <div class="cm-time-track"><span style="width:${x.all_answers/max*100}%"></span></div>
              <b>${x.all_answers}</b>
            </div>`).join('')||'<p class="subtitle">Sem revisões no período.</p>'}</div>
        </div></section>`;
    }catch(ex){root.textContent='Não foi possível analisar o Anki: '+ex.message;}
  }
  if(root.dataset.boundAnkiAnalytics!=='1'){
    root.dataset.boundAnkiAnalytics='1';
    root.addEventListener('click',async e=>{
      if(e.target.closest('#anki-stats-refresh')){
        if(!confirm('Ler e analisar as respostas dos últimos 30 dias? O Anki deve estar aberto. Os cartões não serão modificados.'))return;
        const button=e.target.closest('button');button.disabled=true;button.textContent='Lendo revisões…';
        try{
          const result=await api('anki/analytics/sync',{profile:'Principal',confirm:true});
          await draw();
          alert('Análise registrada: '+result.events+' respostas no período. '+result.recognized_decks+' baralhos reconhecidos.');
        }catch(ex){alert('Falha na análise: '+ex.message);}
        finally{button.disabled=false;}
      }
    });
  }
  await draw();
}
