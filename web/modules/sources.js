/* Bibliotecas locais: metadados de PDF e importação autorizada de resultados. */
import {escapeHTML,selectOptions} from './format.js';
const h=escapeHTML;
const btn=(action,label)=>`<button class="btn primary" data-action="${action}">${h(label)}</button>`;
export function sourcesView(d,{heading}){
 const src=d.sources||{materials:[],bookmarks:[],csv_files:[]};
 const mats=src.materials||[], bookmarks=src.bookmarks||[],csv=src.csv_files||[];
 return `${heading('Meus materiais e Qconcursos','PDFs locais do Estratégia, cadernos de questões e resultados próprios.')}
 <div class="info-box">Os PDFs ficam somente em <b>dados/materiais/estrategia/</b>. O catálogo armazena referências e metadados, não o texto completo do curso. Nenhuma senha ou conteúdo protegido é enviado a serviços externos.</div>
 <section class="panel"><div class="panel-head"><h2>Biblioteca Estratégia</h2><span class="hint">${mats.length} PDFs catalogados</span>${btn('scan-materials','Atualizar biblioteca')}</div>
 ${mats.length?`<div class="table-wrap"><table class="act-table"><thead><tr><th>Aula / arquivo</th><th>Disciplina e assunto</th><th>Páginas</th><th>Ação</th></tr></thead><tbody>
 ${mats.map(x=>`<tr><td><strong>${h(x.lesson||'Aula a identificar')}</strong><br><small title="${h(x.relative_path)}">${h(x.file_name)}</small></td><td>${h(x.subject||'Não vinculada')}<br><small>${h(x.topic||x.course||'—')}</small></td><td>${x.pages==null?'—':x.pages}</td><td><button class="btn small" data-action="edit-material" data-id="${x.id}">Vincular</button></td></tr>`).join('')}</tbody></table></div>`:
 '<div class="panel-content"><p class="subtitle">Coloque seus PDFs na pasta privada indicada acima e clique em Atualizar biblioteca. Arquivos ainda não disponibilizados não aparecem aqui.</p></div>'}</section>
 <section class="panel" style="margin-top:18px"><div class="panel-head"><h2>Meus cadernos Qconcursos</h2>${btn('new-qc-bookmark','+ Salvar link')}</div>
 <div class="panel-content">${bookmarks.length?bookmarks.map(b=>`<div class="priority-item"><div class="grow"><b>${h(b.title)}</b><small>${h(b.subject||'Sem disciplina')} · ${h(b.topic||'Assunto livre')}</small></div><a href="${h(b.url)}" class="btn small" target="_blank" rel="noopener noreferrer">Abrir no Qconcursos ↗</a></div>`).join(''):'<p class="subtitle">Salve links oficiais de cadernos ou filtros do seu plano Qconcursos. O login continua no próprio site.</p>'}</div></section>
 <section class="panel" style="margin-top:18px"><div class="panel-head"><h2>Importar resultados de questões</h2></div><div class="panel-content"><p class="subtitle">CSV elaborado por você com <b>data;disciplina;assunto;total;acertos;banca;link;id</b>. Guarde-o em <b>dados/importacoes/qconcursos/</b>. Não importa enunciados nem acessa sua conta automaticamente.</p>
 ${csv.length?`<div class="field" style="margin-top:12px"><label for="qc-file">Arquivos CSV encontrados</label><select id="qc-file">${selectOptions(csv)}</select></div><div style="margin-top:12px">${btn('qc-preview','Pré-visualizar resultados')}</div>`:'<div class="info-box warning" style="margin-top:12px">Ainda não existe CSV na pasta de importação. Caso sua conta não ofereça exportação de desempenho, preencha a planilha de resultados manualmente.</div>'}
 </div></section>`;
}