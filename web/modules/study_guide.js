/* Guia de estudos editável com dados locais persistentes e fontes transparentes. */
import {api} from './http.js';
import {escapeHTML} from './format.js';
const h=escapeHTML;
const states=['Não iniciado','Em estudo','Revisão','Concluído'];
let guideId=0, filterSubject='';
const v=x=>String(x??'');
const opt=(items,selected)=>items.map(x=>`<option value="${h(x)}" ${x===selected?'selected':''}>${h(x)}</option>`).join('');
async function draw(root){
  let state,preset;
  try{[state,preset]=await Promise.all([api('study-guide'),api('study-guide/preset')]);}
  catch(ex){root.textContent='Erro ao carregar o guia: '+ex.message;return;}
  const guides=state.guides;
  if(!guides.length){
    root.innerHTML=`<section class="panel"><div class="panel-head"><h2>Meu guia de estudos</h2></div>
      <div class="panel-content"><p>Crie seu guia. Disciplinas, assuntos, incidências, progresso e fontes ficam salvos no banco SQLite do CONTROLE MESTRE.</p>
      <form id="sg-create"><div class="fields">
        <div class="field"><label>Nome do guia</label><input name="title" required maxlength="120" value="SEFAZ-RS · Auditor Fiscal"></div>
        <div class="field"><label>Horas líquidas por semana</label><input name="weekly_hours" type="number" min="1" max="80" step=".5" value="25"></div>
      </div><button class="btn primary" type="submit">Criar e salvar meu guia</button></form></div></section>`;
    return;
  }
  const preferred=Number(localStorage.getItem('cm_guide_id')||0);
  guideId=guides.some(g=>g.id===preferred)?preferred:guides[0].id;
  const active=guides.find(g=>g.id===guideId);
  const rows=state.entries.filter(e=>e.guide_id===guideId);
  const subjects=[...new Set(rows.map(x=>x.subject))].sort((a,b)=>a.localeCompare(b,'pt-BR'));
  if(filterSubject&&!subjects.includes(filterSubject))filterSubject='';
  const shown=filterSubject?rows.filter(x=>x.subject===filterSubject):rows;
  const complete=rows.filter(x=>x.status==='Concluído').length;
  root.innerHTML=`<section class="panel"><div class="panel-head"><div><h2>Meu guia de estudos</h2>
    <p>${h(active.title)} · ${active.weekly_hours} h líquidas/semana · ${rows.length} assuntos · ${complete} concluídos</p>
    </div><span class="hint">SALVO LOCALMENTE</span></div>
    <div class="panel-content">
      <div class="fiscal-actions">
        <label>Selecionar guia <select id="sg-guide-pick">${guides.map(x=>`<option value="${x.id}" ${x.id===guideId?'selected':''}>${h(x.title)}</option>`).join('')}</select></label>
        <button class="btn" id="sg-new">Novo guia</button>
        <button class="btn primary" id="sg-seed" ${rows.length?'':'title="Importar assuntos do Bizu"'}>Importar incidências dos Bizus (${preset.rows.length})</button>
      </div>
      <div class="info-box" style="margin:14px 0">
        <strong>Fonte e limites.</strong> Percentuais = levantamentos históricos dos PDFs Bizu Estratégico enviados.
        Não são incidências oficiais da SEFAZ-RS nem o edital verticalizado integral.
        Campos sem amostra aparecem como <b>não estimado</b>. O Passo Estratégico não foi fornecido.
        A importação é idempotente: não apaga progresso e não duplica o mesmo assunto/fonte.
      </div>
      <details><summary>Adicionar disciplina/assunto manualmente</summary>
        <form id="sg-add" style="margin-top:12px"><div class="fields">
          <div class="field"><label>Disciplina</label><input name="subject" required maxlength="120" placeholder="Ex.: Legislação Tributária RS I"></div>
          <div class="field"><label>Assunto do edital</label><input name="topic" required maxlength="250" placeholder="Ex.: Fato gerador do ICMS"></div>
          <div class="field"><label>Incidência % (opcional)</label><input name="incidence_pct" type="number" min="0" max="100" step="0.01"></div>
          <div class="field"><label>Fonte</label><select name="source_type">${opt(['Manual','Bizu Estratégico','Passo Estratégico','Edital oficial','Outro'],'Manual')}</select></div>
          <div class="field"><label>Referência</label><input name="source_reference" maxlength="180" placeholder="Nome do edital ou estudo estatístico"></div>
          <div class="field"><label>Página</label><input name="source_page" type="number" min="1" max="5000"></div>
        </div><button class="btn primary" type="submit">Salvar assunto</button></form></details>
      <div class="fiscal-actions" style="margin:16px 0">
        <label>Filtrar disciplina <select id="sg-subject"><option value="">Todas</option>${subjects.map(x=>`<option value="${h(x)}" ${x===filterSubject?'selected':''}>${h(x)}</option>`).join('')}</select></label>
        <span class="subtitle">${shown.length} de ${rows.length} assuntos</span>
      </div>
      ${shown.length?`<div class="table-wrap"><table class="act-table">
        <thead><tr><th>Disciplina</th><th>Assunto</th><th>Incidência histórica</th><th>Fonte</th><th>Progresso</th><th>Status</th><th></th></tr></thead>
        <tbody>${shown.map(row=>`<tr data-sg-id="${row.id}">
          <td>${h(row.subject)}</td><td>${h(row.topic)}</td>
          <td><strong>${row.incidence_pct===null?'Não estimado':Number(row.incidence_pct).toLocaleString('pt-BR')+'%'}</strong></td>
          <td><small>${h(row.source_type)}${row.source_page?' · p. '+row.source_page:''}</small><br>
              <small title="${h(row.source_reference)}">${h(row.source_reference||'Sem referência')}</small></td>
          <td><input class="sg-progress" aria-label="Progresso em percentagem" type="number" min="0" max="100" step="5" value="${row.progress}" style="width:76px"></td>
          <td><select class="sg-state">${opt(states,row.status)}</select></td>
          <td><button type="button" class="btn" data-sg-save="${row.id}">Salvar</button></td>
          </tr>`).join('')}</tbody></table></div>`:
          '<p class="subtitle">Nenhum assunto cadastrado. Importe as incidências ou adicione disciplinas e tópicos manualmente.</p>'}
    </div></section>`;
}
export async function renderStudyGuide(root){
  if(root.dataset.studyGuideBound!=='1'){
    root.dataset.studyGuideBound='1';
    root.addEventListener('submit',async e=>{
      const id=e.target.id;
      if(!['sg-create','sg-add'].includes(id))return;
      e.preventDefault();const data=Object.fromEntries(new FormData(e.target).entries());
      try{
        if(id==='sg-create'){
          const res=await api('study-guide/create',data);
          localStorage.setItem('cm_guide_id',String(res.id));
          filterSubject='';
        }else{data.guide_id=guideId;await api('study-guide/entry',data);}
        await draw(root);
      }catch(ex){alert('Não foi possível salvar: '+ex.message)}
    });
    root.addEventListener('click',async e=>{
      const button=e.target.closest('button');
      if(!button)return;
      try{
        if(button.id==='sg-new'){
          const title=prompt('Nome do novo guia de estudos:', 'SEFAZ-RS · Meu guia');
          if(title===null)return;
          const res=await api('study-guide/create',{title,weekly_hours:25});
          localStorage.setItem('cm_guide_id',String(res.id));filterSubject='';
          await draw(root);
        }
        if(button.id==='sg-seed'){
          if(!confirm('Adicionar os assuntos do Bizu Estratégico ao guia atual?\nO histórico e os registros existentes serão preservados.'))return;
          const result=await api('study-guide/preset',{guide_id:guideId,confirm:true});
          await draw(root);
          alert(result.inserted+' assuntos adicionados; '+result.skipped+' já existiam.');
        }
        if(button.dataset.sgSave){
          const tr=button.closest('tr');
          const status=tr.querySelector('.sg-state').value;
          const progress=Number(tr.querySelector('.sg-progress').value);
          await api('study-guide/progress',{guide_id:guideId,entry_id:Number(button.dataset.sgSave),status,progress});
          await draw(root);
        }
      }catch(ex){alert('Falha: '+ex.message);}
    });
    root.addEventListener('change',async e=>{
      if(e.target.id==='sg-subject'){filterSubject=e.target.value;await draw(root);}
      if(e.target.id==='sg-guide-pick'){localStorage.setItem('cm_guide_id',e.target.value);filterSubject='';await draw(root);}
    });
  }
  await draw(root);
}
