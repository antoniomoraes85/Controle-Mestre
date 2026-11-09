"""Identificação conservadora de PDF por pasta e texto da primeira página.

Códigos de curso NÃO identificam uma disciplina: alguns cursos integram
Bizus de diversas matérias, inclusive com aulas de igual número.
Nunca sobrescreve vínculos manuais nem persiste texto extraído dos PDFs.
"""
from __future__ import annotations
import re
from collections import defaultdict
from pathlib import PurePosixPath
from core import norm,all_rows,DEFAULT_SUBJECTS

ALIASES={
  'auditoria contabil':'Auditoria',
  'auditoria':'Auditoria',
  'analise das demonstracoes contabeis':'Análise das Demonstrações Contábeis',
  'contabilidade de custos':'Contabilidade de Custos',
  'contabilidade geral':'Contabilidade Geral',
  'direito tributario':'Direito Tributário',
  'direito empresarial':'Direito Empresarial',
  'direito constitucional':'Direito Constitucional',
  'direito administrativo':'Direito Administrativo',
  'direito penal':'Direito Penal',
  'direito civil':'Direito Civil',
  'portugues':'Português',
  'tecnologia da informacao':'Tecnologia da Informação',
  'estatistica':'Estatística',
  'matematica financeira':'Matemática Financeira',
}
def folder_subject(relative_path):
    # Só pasta inequívoca: nunca inferir pelo código numérico de curso.
    subjects=[s[0] for s in DEFAULT_SUBJECTS]
    for folder in reversed(PurePosixPath(str(relative_path)).parts[:-1]):
        raw=norm(folder)
        found=[s for s in subjects if norm(s)==raw or
               re.search(r'(?<![a-z])'+re.escape(norm(s))+r'(?![a-z])',raw)]
        if len(found)==1:return found[0]
    return ''

def subject_from_text(text):
    n=norm(text)
    # Reforma requer evidência específica; caso contrário, não classificar
    # como Direito Tributário genérico quando o foco é Reforma Tributária.
    if 'reforma tributaria' in n:
        if '214 2025' in n or 'lei complementar 214' in n:
            return 'Reforma Tributária — EC 132 e LC 214'
        if '227 2026' in n or 'lei complementar 227' in n:
            return 'Reforma Tributária — LC 227'
        return ''
    matches=[]
    for alias,subject in ALIASES.items():
        key=re.escape(alias)
        if re.search(r'(?:bizu estrategico|passo estrategico)\s+(?:de|da|do)\s+'+key+r'\b',n) or \
           re.search(r'\bdisciplina\s+(?:de|da|do)\s+'+key+r'\b',n):
            matches.append((len(alias),subject))
    if not matches:return ''
    distinct={sub for _,sub in matches}
    return next(iter(distinct)) if len(distinct)==1 else ''

def read_first_pages(path):
    """Até duas páginas locais, somente para identificação. Não guarda conteúdo."""
    try:
        import fitz
        with fitz.open(path) as pdf:
            if pdf.needs_pass:return ''
            return ' '.join(pdf[i].get_text(sort=True)[:5000]
                            for i in range(min(2,len(pdf))))
    except (ImportError,OSError,ValueError,RuntimeError):
        return ''

def infer(c,apply=True):
    from sources import prepare,detect_type,path_for_key
    from lesson_catalog import lessons
    prepare(c)
    rows=all_rows(c,"""SELECT id,relative_path,file_name,subject,topic,lesson,material_type
        FROM study_materials WHERE status='Disponível' ORDER BY id""")
    catalog=defaultdict(list)
    for entry in lessons():
        catalog[(norm(entry['disciplina']),norm(entry['aula']))].append(entry['assunto'])
    result={'updated':0,'subjects_assigned':0,'topics_assigned':0,
            'types_assigned':0,'remaining_unlinked':0,'review':[],'inspected':0,
            'note':'PDFs não são enviados à nuvem. Cursos multi-disciplinares nunca são classificados por código isolado.'}
    for item in rows:
        folder=folder_subject(item['relative_path'])
        # Classificar somente os arquivos que ainda precisam de alguma informação.
        preview=''
        needs_preview=not item['subject'] or (item['material_type']=='Teoria' and 'curso-' in item['file_name'].lower())
        if needs_preview:
            try:
                preview=read_first_pages(path_for_key(c,item['relative_path']))
            except ValueError:
                pass
            result['inspected']+=bool(preview)
        text_subject=subject_from_text(preview) if preview else ''
        if folder and text_subject and folder!=text_subject:
            # Pasta e conteúdo contraditórios; nunca corrigir por palpite.
            inferred_subject=''
        else:
            inferred_subject=text_subject or folder
        subject=item['subject'] or inferred_subject
        topic=item['topic']
        identified=detect_type(str(PurePosixPath(item['relative_path']).parent)+' '+item['file_name'])
        n=norm(preview[:5000])
        if re.search(r'\bbizu estrategico\b',n):identified='Bizu Estratégico'
        elif re.search(r'\bpasso estrategico\b',n):identified='Passo Estratégico'
        typ=item['material_type']
        if typ=='Teoria' and identified!='Teoria' and not item['topic']:typ=identified
        # 'Aula 03' de um Bizu NÃO é aula 03 do curso teórico.
        if subject and item['lesson'] and not topic and typ in ('Teoria','Simplificado','Questões'):
            candidates=catalog.get((norm(subject),norm(item['lesson'])),[])
            if len(candidates)==1:topic=candidates[0]
        if not subject or not topic:
            result['remaining_unlinked']+=1
            if len(result['review'])<25:result['review'].append({
                'id':item['id'],'file':item['file_name'],
                'reason':'Disciplina não identificada' if not subject else
                  'PDF sem correspondência temática direta (pode ser Bizu, Passo ou revisão).'})
        if (subject,topic,typ)!=(item['subject'],item['topic'],item['material_type']):
            result['updated']+=1
            result['subjects_assigned']+=bool(subject and not item['subject'])
            result['topics_assigned']+=bool(topic and not item['topic'])
            result['types_assigned']+=typ!=item['material_type']
            if apply:
                c.execute('''UPDATE study_materials
                     SET subject=?,topic=?,material_type=? WHERE id=?''',
                     (subject,topic,typ,item['id']))
    if apply:c.commit()
    return result
