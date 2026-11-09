/* Quadro curricular, rastreado por assunto; dados reais do SQLite. */
import {api} from './http.js';
import {escapeHTML as h} from './format.js';
const pc=n=>Number(n).toLocaleString('pt-BR',{maximumFractionDigits:1})+'%';
const states=['Não iniciado','Em estudo','Revisão','Concluído'];
const pill=(n)=>n==null?'<span class="cm-inc-unknown">Não estimada</span>':
  `<span class="cm-inc-val">${pc(n)}</span>`;
let selectedSubject='';
function progress(v){return `<div class="cm-curr-progress"><span style="width:${Math.min(100,Math.max(0,v))}%"></span></div>`;}
async function draw(root){
  const data=await api('curriculum');
  const includeEmpty=root.dataset.includeEmpty==='true';
  const subjectNames=data.subjects.filter(s=>includeEmpty||s.topic_count).map(s=>s.subject);
  if(selectedSubject&&!subjectNames.includes(selectedSubject))selectedSubject='';
  root.innerHTML=`<section class="panel cm-curriculum-panel"><div class="panel-head"><div>
    <h2>Plano de estudo · matérias e assuntos</h2>
    <p>Progresso, incidência histórica, questões resolvidas e aulas com PDF — tudo por assunto.</p>
    </div><span class="hint">HISTÓRICO PERSISTENTE</span></div>
    <div class="panel-content">
      <div class="cm-curr-summary">
        <div><span>Assuntos identificados</span><strong>${data.total_topics}</strong></div>
        <div><span>Progresso nos tópicos cadastrados</span><strong>${data.total_progress_pct==null?'—':pc(data.total_progress_pct)}</strong></div>
        <div><span>PDFs catalogados</span><strong>${data.stats.pdfs}</strong></div>
        <div><span>PDFs sem vínculo exato</span><strong>${data.unlinked_pdfs.length}</strong></div>
      </div>
      <div class="info-box"><strong>Transparência:</strong> ${h(data.notice)} As taxas de questões usam exclusivamente acertos e totais informados no histórico.</div>
      <label class="cm-curr-filter">Disciplina
        <select id="cm-curr-filter"><option value="">Todas as disciplinas</option>
        ${subjectNames.map(name=>`<option value="${h(name)}" ${selectedSubject===name?'selected':''}>${h(name)}</option>`).join('')}
        </select></label>
      ${data.subjects.filter(s=>(includeEmpty||s.topic_count)&&(!selectedSubject||s.subject===selectedSubject))
          .map(g=>`<details class="cm-curr-subject" ${selectedSubject?'open':''}>
             <summary><div class="cm-curr-title"><strong>${h(g.subject)}</strong>
               <span>${g.topic_count} assuntos · ${g.questions} questões ·
                Rendimento: ${g.question_rate==null?'Sem amostra':pc(g.question_rate*100)}</span>
               </div><div class="cm-curr-subj-progress">${progress(g.progress_pct)}
                <b>${pc(g.progress_pct)}</b></div></summary>
              ${g.topic_count? `<div class="table-wrap"><table class="act-table cm-curr-table">
                <thead><tr><th>Aula</th><th>Assunto</th><th>Prioridade (1–10)</th><th>Incidência e fonte</th>
                  <th>Progresso</th><th>Questões / rendimento</th><th>Material</th><th>Ação</th></tr></thead>
                <tbody>${g.topics.map(t=>`<tr>
                  <td class="cm-curr-lesson">${h(t.lesson||'—')}</td>
                  <td><strong>${h(t.topic)}</strong>
                      <small class="cm-curr-origin">${h(t.origins.join(' · '))}</small></td>
                  <td><button class="cm-inc-level" type="button"
                    data-level="${t.importance_level||''}" data-importance-subject="${h(t.subject)}"
                    data-importance-topic="${h(t.topic)}" data-priority-reason="${h(t.priority_reason)}"
                    title="${h(t.priority_reason)}">
                    ${t.importance_level?'Prioridade '+t.importance_level+'/10':'Não calculada'}</button>
                    <small class="cm-curr-origin">${h(t.importance_basis)}</small>
                    ${t.importance_manual && t.priority_suggestion!=null?
                        `<small class="cm-curr-origin">Sugestão automática: ${t.priority_suggestion}/10</small>`:''}
                    </td>
                  <td>${pill(t.incidence_pct)}
                     <small class="cm-curr-origin" title="${h(t.incidence_source)}">${h(t.incidence_source||'Sem percentual documentado')}</small></td>
                  <td>${progress(t.progress)}
                     <span>${pc(t.progress)} · ${h(t.status)}</span></td>
                  <td>${t.total_questions? `${t.correct_questions}/${t.total_questions}
                     <strong>${pc(t.question_rate*100)}</strong>`:'Ainda não registrado'}</td>
                  <td>${t.pdfs.length?t.pdfs.map(p=>`<button type="button" class="btn small" data-action="open-material" data-id="${p.id}" title="${h(p.name)}">${h(p.type)} ↗</button>`).join('<br>'):
                      '<span class="cm-inc-unknown">Sem vínculo</span>'}</td>
                  <td>${t.entry_id?
                     `<button class="btn small" data-edit-progress="${t.entry_id}"
                         data-guide-id="${t.guide_id}" data-progress="${t.progress}"
                         data-status="${h(t.status)}">Atualizar</button>`:
                     `<button class="btn small" data-add-guide="1"
                         data-subject="${h(t.subject)}" data-topic="${h(t.topic)}"
                         data-incidence="${t.incidence_pct??''}">Adicionar ao guia</button>`}</td>
                </tr>`).join('')}</tbody>
              </table></div>`:
                   '<p class="subtitle" style="padding:15px">Sem assunto catalogado nesta disciplina. Importe a lista de aulas ou vincule seus PDFs.</p>'}</details>`).join('')}
      ${!data.total_topics?'<p class="subtitle">Ainda não existe catálogo de assuntos. Abra Materiais e TEC, configure sua pasta de PDFs e clique em Atualizar biblioteca; ou importe as incidências do Bizu abaixo.</p>':''}
    </div></section>`;
}
export async function renderCurriculum(root,options={}){
  if(root)root.dataset.includeEmpty=options.includeEmpty?'true':'false';
  if(!root)return;
  if(root.dataset.boundCurriculum!=='1'){
    root.dataset.boundCurriculum='1';
    root.addEventListener('change',async e=>{
      if(e.target.id==='cm-curr-filter'){selectedSubject=e.target.value;await draw(root);}
    });
    root.addEventListener('click',async e=>{
      const btn=e.target.closest('button');
      if(!btn)return;
      try{
        if(btn.dataset.importanceTopic){
          const initial=btn.dataset.level||'';
          const txt=prompt('Prioridade pessoal do assunto (1–10). A sugestão automática não altera sua escolha:',initial);
          if(txt===null)return;
          const value=Number(txt);
          if(!Number.isInteger(value)||value<1||value>10){alert('Informe uma prioridade inteira de 1 a 10.');return;}
          await api('curriculum/importance',{subject:btn.dataset.importanceSubject,
            topic:btn.dataset.importanceTopic,level:value});
          await draw(root);return;
        }
        if(btn.dataset.editProgress){
          const prev=Number(btn.dataset.progress);
          const input=prompt('Progresso (0 a 100%) neste assunto:',String(prev));
          if(input===null)return;
          const p=Number(input.replace(',','.'));
          if(!Number.isInteger(p)||p<0||p>100){alert('Digite um número inteiro entre 0 e 100.');return;}
          const status=p===100?'Concluído':p>0?'Em estudo':'Não iniciado';
          await api('study-guide/progress',{guide_id:Number(btn.dataset.guideId),
            entry_id:Number(btn.dataset.editProgress),status,progress:p});
          await draw(root);
        }
        if(btn.dataset.addGuide){
          if(!confirm('Adicionar este assunto ao guia de estudos persistente?'))return;
          const state=await api('study-guide');
          let gid=state.guides[0]?.id;
          if(!gid){const made=await api('study-guide/create',{title:'SEFAZ-RS · Meu guia',weekly_hours:25});gid=made.id;}
          await api('study-guide/entry',{guide_id:gid,subject:btn.dataset.subject,
            topic:btn.dataset.topic,source_type:'Manual',
            source_reference:'Assunto identificado na biblioteca ou catálogo local',
            incidence_pct:btn.dataset.incidence||null});
          await draw(root);
        }
      }catch(err){alert('Não foi possível atualizar: '+err.message);}
    });
  }
  try{await draw(root);}catch(e){root.textContent='Não foi possível carregar o plano por assunto: '+e.message;}
}
