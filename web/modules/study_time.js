/* Gráficos e somatórios reais de minutos (fonte única: tabela sessions). */
import {api} from './http.js';
import {escapeHTML} from './format.js';
const h=escapeHTML;
const hours=m=>(m/60).toLocaleString('pt-BR',{minimumFractionDigits:1,maximumFractionDigits:1})+' h';
const bar=(label,minutes,max)=>`<div class="cm-time-row" title="${h(label)} · ${hours(minutes)}">
  <span class="cm-time-label">${h(label)}</span>
  <div class="cm-time-track"><span style="width:${max?Math.max(0.75,(minutes/max)*100):0}%"></span></div>
  <b>${hours(minutes)}</b>
</div>`;
function series(title,items,formatLabel){
  const max=Math.max(1,...items.map(x=>Number(x.minutes)||0));
  return `<section class="panel"><div class="panel-head"><h2>${h(title)}</h2></div>
    <div class="panel-content cm-time-list">${items.some(x=>x.minutes>0)?
      items.map(x=>bar(formatLabel(x.label),Number(x.minutes),max)).join(''):
      '<p class="subtitle">Nenhuma hora registrada neste período.</p>'}</div></section>`;
}
export async function renderStudyTime(root){
  if(!root)return;
  root.textContent='Carregando horas de estudo...';
  try{
    const r=await api('study-time');
    const totals=`<div class="cm-time-stats">
      <div class="panel"><div class="panel-content"><small>Hoje</small><h2>${hours(r.day_minutes)}</h2></div></div>
      <div class="panel"><div class="panel-content"><small>Semana</small><h2>${hours(r.week_minutes)}</h2></div></div>
      <div class="panel"><div class="panel-content"><small>Mês</small><h2>${hours(r.month_minutes)}</h2></div></div>
      <div class="panel"><div class="panel-content"><small>Total geral</small><h2>${hours(r.total_minutes)}</h2></div></div>
    </div>`;
    const subjects=r.subjects.length?`<section class="panel"><div class="panel-head">
        <h2>Horas acumuladas por disciplina</h2><span class="hint">SEM DUPLICIDADE</span></div>
        <div class="table-wrap"><table class="act-table"><thead><tr><th>Disciplina</th>
        <th>Semana</th><th>Mês</th><th>Total geral</th></tr></thead><tbody>
        ${r.subjects.map(x=>`<tr><td>${h(x.subject)}</td>
        <td>${hours(x.week_minutes)}</td><td>${hours(x.month_minutes)}</td>
        <td><strong>${hours(x.total_minutes)}</strong></td></tr>`).join('')}
        </tbody></table></div></section>`:'<p class="subtitle">Registre a primeira sessão usando o cronômetro para acompanhar a evolução.</p>';
    root.innerHTML=`<div class="info-box">As horas vêm exclusivamente das sessões salvas no banco SQLite.
      Ao finalizar o cronômetro, o registro é somado à disciplina escolhida.
      Pausas e períodos com o aplicativo fechado não entram na contagem.</div>
      ${totals}<div class="cm-time-grid">
      ${series('Últimos 31 dias',r.daily,x=>x.slice(8)+'/'+x.slice(5,7))}
      ${series('Últimas 12 semanas',r.weekly,x=>x.slice(8)+'/'+x.slice(5,7))}
      ${series('Últimos 12 meses',r.monthly,x=>x.slice(5,7)+'/'+x.slice(0,4))}
      </div>${subjects}`;
  }catch(error){root.textContent='Não foi possível carregar os gráficos: '+error.message;}
}
