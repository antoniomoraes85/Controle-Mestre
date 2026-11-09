/* Biblioteca de aulas/PDF e integração manual autorizada ao TEC Concursos. */
import {escapeHTML,selectOptions} from './format.js';
const h=escapeHTML;
const btn=(action,label)=>`<button class="btn primary" data-action="${action}">${h(label)}</button>`;
export function sourcesView(d,{heading}){
 const src=d.sources||{materials:[],bookmarks:[],csv_files:[]};
 const mats=src.materials||[], bookmarks=src.tec_bookmarks||[],csv=src.tec_csv_files||[];
 const catalog=src.catalog||{subjects:[],total_lessons:0,pending_subjects:[]};
 const key=x=>String(x||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
 const linked=(subject,topic)=>[
  ...bookmarks.map(b=>({title:b.title,url:b.url,subject:b.subject,topic:b.topic})),
  ...(src.lesson_links||[]).map(b=>({title:b.label,url:b.url,subject:b.subject,topic:b.topic}))
 ].filter(b=>key(b.subject)===key(subject)&&key(b.topic)===key(topic));
 const lessonTopic=(subject,lesson)=>{const group=(catalog.subjects||[]).find(g=>g.subject===subject);
   const l=group?.lessons?.find(e=>key(e.lesson)===key(lesson));return l?.topic||'';};

 const extern=(src.roots||[]).find(x=>x.kind==='external');
 const libraryRoots=`<div class="info-box">Os PDFs podem permanecer em <b>MATERIAL TEÓRICO</b>, ao lado de <b>CONTROLE_MESTRE</b>, conforme sua organização atual. ${extern?`Pasta externa identificada: <b>${h(extern.path)}</b>.`:`Pasta externa ainda não localizada. Caminho esperado: <b>${h(src.expected_external_path||'MATERIAL TEÓRICO ao lado da aplicação')}</b>. Clique em Configurar pasta externa e cole o endereço do Explorador do Windows.`} Alternativa: <b>dados/materiais/estrategia/</b> (pasta interna). <button class="btn small" data-action="set-material-root">Configurar pasta externa</button><p style="margin-top:8px">O catálogo armazena apenas metadados: nenhum PDF é enviado ao GitHub, à nuvem ou copiado automaticamente.</p></div>`;
 const curriculum=`<section class="panel" style="margin:18px 0"><div class="panel-head"><h2>Catálogo de aulas e assuntos</h2><span class="hint">${catalog.total_lessons||0} aulas identificadas · ${(catalog.subjects||[]).length} disciplinas</span></div><div class="panel-content"><p class="subtitle">${h(catalog.source||'')} Incidência histórica somente quando documentada; sem percentual não significa 0%. PDFs e assuntos não vinculados permanecem identificados.</p>${(catalog.subjects||[]).map(group=>`<details style="margin-top:12px"><summary><strong>${h(group.subject)}</strong> — ${group.lesson_count} aula(s) · ${group.matched_lessons} com PDF vinculado</summary>${!group.lesson_count?'<p class="subtitle">Aguardando aula e assunto: vincule seus PDFs ou importe o CSV de catálogo.</p>':`<div class="table-wrap"><table class="act-table"><thead><tr><th>Aula</th><th>Assunto da aula</th><th>Incidência histórica</th><th>PDF</th><th>Caderno de questões</th></tr></thead><tbody>${group.lessons.map(l=>`<tr><td style="white-space:nowrap">${h(l.lesson)}</td><td><strong>${h(l.topic||'Assunto ainda não identificado')}</strong><small class="cm-curr-origin">${h(l.topic_origin||'')}</small></td>
<td>${l.incidence_pct==null?'<span class="cm-inc-unknown">Não estimada</span>':
    `<b class="cm-inc-val">${Number(l.incidence_pct).toLocaleString('pt-BR')}%</b><small class="cm-curr-origin" title="${h(l.incidence_source)}">${h(l.incidence_source)}</small>`}</td>
<td>${l.materials.length?l.materials.map(m=>`<a target="_blank" rel="noopener" class="fiscal-doc" href="/api/fiscal/pdf/${m.id}">${h(m.type)} ↗</a>`).join('<br>'):'<span class="fiscal-missing">Não vinculado</span>'}</td>
<td>${linked(group.subject,l.topic).length?
  linked(group.subject,l.topic).map(link=>`<a class="btn small" target="_blank" rel="noopener noreferrer" href="${h(link.url)}">${h(link.title)} ↗</a>`).join(' '):
  `<button class="btn small" data-action="link-lesson" data-subject="${h(group.subject)}" data-topic="${h(l.topic)}">+ Vincular caderno</button>`}</td></tr>`).join('')}</tbody></table></div>`}</details>`).join('')}</div></section>`;
 return `${heading('Materiais e TEC Concursos','Aulas do Estratégia, PDFs locais e cadernos do TEC Avançado.')}
 ${libraryRoots}
 ${curriculum}
 <section class="panel"><div class="panel-head"><h2>PDFs do Estratégia</h2><span class="hint">${mats.filter(x=>x.status==='Disponível').length} PDF(s) encontrados · ${(catalog.total_lessons||0)} aula(s) descritas</span>${btn('scan-materials','Atualizar biblioteca')}</div>
 ${mats.length?`<div class="table-wrap"><table class="act-table"><thead><tr><th>Aula / arquivo</th><th>Disciplina e assunto</th><th>Páginas</th><th>PDF / Ação</th></tr></thead><tbody>
 ${mats.map(x=>`<tr><td><strong>${h(x.lesson||'Aula a identificar')}</strong> <span class="tag">${h(x.material_type||'Teoria')}</span><br><small title="${h(x.relative_path)}">${h(x.file_name)}</small></td><td><strong>${h(x.subject||'Não vinculada')}</strong><br><small>${h(x.topic||lessonTopic(x.subject,x.lesson)||x.course||'Assunto não identificado — use Vincular')}</small></td><td>${x.pages==null?'—':x.pages}</td><td>${x.status==='Disponível'?
    `<a class="btn small" target="_blank" rel="noopener" href="/api/fiscal/pdf/${x.id}">Abrir PDF ↗</a> `:
    ''}<button class="btn small" data-action="edit-material" data-id="${x.id}">Vincular assunto</button></td></tr>`).join('')}</tbody></table></div>`:
 '<div class="panel-content"><p class="subtitle">O catálogo disponível aparece acima. Os PDFs são arquivos separados: configure a pasta MATERIAL TEÓRICO e clique em Atualizar biblioteca para vincular os documentos reais.</p></div>'}</section>
 <section class="panel" style="margin-top:18px"><div class="panel-head"><h2>Meus cadernos TEC Concursos</h2>${btn('new-tec-bookmark','+ Salvar link')}</div>
 <div class="panel-content">${bookmarks.length?bookmarks.map(b=>`<div class="priority-item"><div class="grow"><b>${h(b.title)}</b><small>${h(b.subject||'Sem disciplina')} · ${h(b.topic||'Assunto livre')}</small></div><a href="${h(b.url)}" class="btn small" target="_blank" rel="noopener noreferrer">Abrir no TEC ↗</a></div>`).join(''):'<p class="subtitle">Salve links oficiais de cadernos ou filtros do seu plano TEC Avançado. O login continua no próprio site.</p>'}</div></section>
 <section class="panel" style="margin-top:18px"><div class="panel-head"><h2>Importar resultados de questões</h2></div><div class="panel-content"><p class="subtitle">CSV elaborado por você com <b>data;disciplina;assunto;total;acertos;banca;link;id</b>. Guarde-o em <b>dados/importacoes/tec/</b>. Não importa enunciados nem acessa sua conta automaticamente.</p>
 ${csv.length?`<div class="field" style="margin-top:12px"><label for="tec-file">Arquivos CSV encontrados</label><select id="tec-file">${selectOptions(csv)}</select></div><div style="margin-top:12px">${btn('tec-preview','Pré-visualizar resultados')}</div>`:'<div class="info-box warning" style="margin-top:12px">Ainda não existe CSV preparado por você na pasta de importação. Caso o TEC não ofereça exportação compatível, preencha a planilha de resultados manualmente.</div>'}
 </div></section>`;
}