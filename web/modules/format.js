/** Formatos e codificação HTML compartilhados. Sem dependências. */
export const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const fmt=n=>Number(n||0).toLocaleString('pt-BR',{maximumFractionDigits:1});
export const fmtInt=n=>Number(n||0).toLocaleString('pt-BR');
export const pct=v=>v===null||v===undefined?'—':`${fmt(v*100)}%`;
export const fmtHour=m=>`${Math.floor((Number(m)||0)/60).toString().padStart(2,'0')}h${Math.floor((Number(m)||0)%60).toString().padStart(2,'0')}m`;
export const shortDay=s=>!s?'—':`${s.split('-')[2]}/${s.split('-')[1]}`;
export const dateFmt=s=>!s?'—':`${s.split('-')[2]}/${s.split('-')[1]}/${s.split('-')[0]}`;
export const selectOptions=(items,selected)=>items.map(v=>`<option value="${escapeHTML(v)}" ${v===selected?'selected':''}>${escapeHTML(v)}</option>`).join('');