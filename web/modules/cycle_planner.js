/* Ciclos e microciclos de 30 minutos, sem lançar sessões fictícias. */
import {api} from './http.js';
import {escapeHTML as h} from './format.js';
let subjects=[],topics={};
const esc=h;
const kinds=['Ciclo','Microciclo','Semana fixa'];
const methods=['Teoria','Questões','Lei seca','Revisão','Flashcards','Caderno de erros','Simulado'];
function opts(values){return values.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('');}
async function draw(root){
  const [data,curriculum]=await Promise.all([api('study-cycles'),api('curriculum')]);
  topics=Object.fromEntries(curriculum.subjects.map(x=>[x.subject,x.topics.map(a=>a.topic)]));
  subjects=Array.from(new Set(curriculum.subjects.map(x=>x.subject))).sort((a,b)=>a.localeCompare(b,'pt-BR'));
  if(!subjects.length)subjects=['Contabilidade Geral','Direito Tributário'];
  root.innerHTML=`<section class="panel"><div class="panel-head"><div>
   <h2>Meu ciclo de estudos</h2><p>Cadastre sequência de matérias e microciclos por assunto e modalidade de estudo.</p>
   </div><span class="hint">CADA BLOCO = 30 MIN</span></div><div class="panel-content">
   <div class="info-box">Cada marcador representa 30 minutos <b>planejados</b>.
   Vermelho = pendente; verde = concluído. Ao concluir todos os blocos de um ciclo,
   a rodada é arquivada e a seguinte inicia. Use o cronômetro para contabilizar horas líquidas reais;
   os marcadores não criam sessões automaticamente.</div>
   <details id="cycle-create-details"><summary class="btn primary">+ Criar ciclo ou microciclo</summary>
    <form id="cm-cycle-create" style="margin-top:14px"><div class="fields">
       <div class="field"><label>Nome</label><input name="title" maxlength="120" required placeholder="Ex.: Ciclo SEFAZ-RS 1"></div>
       <div class="field"><label>Tipo de planejamento</label><select name="kind">${opts(kinds)}</select></div>
       <div class="field"><label>Ciclo principal (somente para microciclo)</label>
          <select name="parent_id"><option value="">Nenhum</option>
          ${data.cycles.filter(x=>x.kind!=='Microciclo').map(x=>`<option value="${x.id}">${esc(x.title)}</option>`).join('')}
          </select></div></div>
       <button class="btn primary" type="submit">Criar e salvar</button>
    </form></details>
   ${!data.cycles.length?'<p class="subtitle" style="margin-top:14px">Nenhum ciclo criado ainda. Clique acima para começar.</p>':''}
   <div class="cm-cycle-grid">
   ${data.cycles.map(c=>`<article class="cm-cycle-card"><h3>${esc(c.title)}</h3>
     <div class="cm-bank-top"><small>${esc(c.kind)} · rodada ${c.round_number} ·
       ${c.completed_rounds} rodada(s) concluída(s)</small><b>${c.marked_blocks}/${c.planned_blocks} blocos</b></div>
     <div class="cm-curr-progress"><span style="width:${c.planned_blocks?100*c.marked_blocks/c.planned_blocks:0}%"></span></div>
     ${c.segments.map(x=>`<div class="cm-cycle-item"><div><strong>${esc(x.subject)}</strong>
         <small>${esc(x.topic||'Conteúdo livre')} · ${esc(x.method)} · ${x.blocks*30} min planejados</small></div>
         <div class="cm-cycle-blocks">${Array.from({length:x.blocks},(_,i)=>`<button type="button"
           class="cm-cycle-check" data-cycle-segment="${x.id}" data-block="${i+1}" data-done="${x.done.includes(i+1)}"
           title="Marcar bloco ${i+1} de 30 minutos como ${x.done.includes(i+1)?'pendente':'concluído'}"
           aria-label="Bloco ${i+1} ${x.done.includes(i+1)?'concluído':'pendente'}">${x.done.includes(i+1)?'✓':'○'}</button>`).join('')}</div>
       </div>`).join('')}
     <details><summary class="btn small">+ Adicionar etapa ao ciclo</summary>
       <form class="cm-cycle-add" data-cid="${c.id}" style="margin-top:12px">
         <div class="field"><label>Disciplina</label><select name="subject" required>${opts(subjects)}</select></div>
         <div class="field"><label>Assunto</label><input name="topic" list="cm-cycle-topics-${c.id}" maxlength="250"
             placeholder="Escolha um assunto ou digite"></div>
         <datalist id="cm-cycle-topics-${c.id}"></datalist>
         <div class="fields">
           <div class="field"><label>Modalidade</label><select name="method">${opts(methods)}</select></div>
           <div class="field"><label>Blocos de 30 minutos</label><input name="blocks" type="number" min="1" max="12" value="1" required></div>
         </div><button type="submit" class="btn primary">Adicionar matéria/assunto</button>
       </form></details>
     <p class="cm-cycle-warning">Blocos planejados não entram automaticamente nas horas líquidas.</p></article>`).join('')}
   </div></div></section>`;
   for(const f of root.querySelectorAll('form.cm-cycle-add')){
     const sub=f.elements.subject, list=f.querySelector('datalist');
     const refresh=()=>{list.innerHTML=(topics[sub.value]||[]).map(x=>`<option value="${esc(x)}"></option>`).join('');};
     sub.addEventListener('change',refresh);refresh();
   }
}
export async function renderCyclePlanner(root){
 if(!root)return;
 if(root.dataset.cmCycleBound!=='1'){
  root.dataset.cmCycleBound='1';
  root.addEventListener('submit',async event=>{
   const form=event.target;
   if(form.id!=='cm-cycle-create'&&!form.classList.contains('cm-cycle-add'))return;
   event.preventDefault();
   const values=Object.fromEntries(new FormData(form).entries());
   try{
    if(form.id==='cm-cycle-create'){
      await api('study-cycles/create',{title:values.title,kind:values.kind,
        parent_id:values.kind==='Microciclo'?Number(values.parent_id)||null:null});
    }else{
      await api('study-cycles/item',{cycle_id:Number(form.dataset.cid),
        subject:values.subject,topic:values.topic,method:values.method,blocks:Number(values.blocks)});
    }
    await draw(root);
   }catch(err){alert('Não foi possível salvar: '+err.message);}
  });
  root.addEventListener('click',async event=>{
    const btn=event.target.closest('.cm-cycle-check');
    if(!btn)return;
    btn.disabled=true;
    try{
      const done=btn.dataset.done!=='true';
      const result=await api('study-cycles/mark',{
        segment_id:Number(btn.dataset.cycleSegment),block_number:Number(btn.dataset.block),done});
      await draw(root);
      if(result.round_completed)alert('Rodada concluída! Os marcadores foram reiniciados. O histórico permanece salvo.');
    }catch(err){alert('Falha ao marcar bloco: '+err.message);btn.disabled=false;}
  });
 }
 try{await draw(root);}catch(err){root.textContent='Falha ao carregar ciclos: '+err.message;}
}
