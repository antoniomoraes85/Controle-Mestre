"""Catálogo fiel às listas de aulas fornecidas pelo proprietário.

Somente metadados curriculares, sem PDFs. Não confundir estas aulas com o
edital verticalizado oficial nem com tarefas executadas.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from core import ROOT, DB_PATH, all_rows, norm

# O banco e o catálogo pertencem ao mesmo diretório persistente; updates do
# código em AppData/ControleMestre/app não devem esconder listas pessoais.
CATALOG_FILE = DB_PATH.parent / 'catalogo' / 'aulas_primeiro_ciclo.csv'
LEGACY_CATALOG_FILE = ROOT / 'dados' / 'catalogo' / 'aulas_primeiro_ciclo.csv'

def catalog_path():
    return CATALOG_FILE if CATALOG_FILE.is_file() else LEGACY_CATALOG_FILE
EXPECTED_SUBJECTS = (
 'Contabilidade Geral', 'Contabilidade de Custos',
 'Análise das Demonstrações Contábeis', 'Direito Tributário',
 'Reforma Tributária — EC 132 e LC 214', 'Reforma Tributária — LC 227',
 'Direito Administrativo', 'Direito Civil', 'Direito Constitucional',
)


def lessons():
    path=catalog_path()
    if not path.is_file():
        return []  # instalação GitHub sem dados privados; nenhuma aula fictícia
    with path.open(encoding='utf-8-sig', newline='') as f:
        data = list(csv.DictReader(f, delimiter=';'))
    seen=set()
    for row in data:
        if not (row['disciplina'] in EXPECTED_SUBJECTS and row['aula'] and row['assunto']):
            raise ValueError('Catálogo contém aula inválida.')
        key=(row['disciplina'],norm(row['aula']))
        if key in seen:
            raise ValueError('Aulas duplicadas no catálogo: '+str(key))
        seen.add(key)
    return data


def status(c):
    """Combina lista pessoal e PDFs catalogados; nunca inventa nomes/percentuais."""
    from sources import prepare
    from bizu_seed import rows as bizu_rows
    from core import DEFAULT_SUBJECTS
    prepare(c)
    catalog=lessons()
    docs=all_rows(c,"""SELECT id,subject,lesson,topic,pdf_title,file_name,
                              material_type,status
                    FROM study_materials WHERE status='Disponível'""")
    guide=all_rows(c,'SELECT subject,topic,incidence_pct,source_type,source_reference FROM study_guide_entries') if _has_table(c,'study_guide_entries') else []
    percentages={}
    for item in bizu_rows():
        if item['incidence_pct'] is not None:
            percentages[(norm(item['subject']),norm(item['topic']))]=(item['incidence_pct'],item['source_reference'])
    # As fontes do guia têm precedência sobre o Bizu quando fornecidas explicitamente.
    for item in guide:
        if item['incidence_pct'] is not None:
            percentages[(norm(item['subject']),norm(item['topic']))]=(item['incidence_pct'],
                item['source_type']+' · '+item['source_reference'])
    grouped=defaultdict(dict)
    for item in catalog:
        key=norm(item['aula'])
        grouped[item['disciplina']][key]={
            'lesson':item['aula'],'topic':item['assunto'],
            'materials':[],'available':False,'topic_origin':'Catálogo pessoal'}
    extra=0
    unmapped=0
    for d in docs:
        # Bizus/Passos podem numerar aulas por outra matriz curricular.
        # Não vincular pelo número da aula sem título de assunto explícito.
        if d['material_type'] in ('Bizu Estratégico','Passo Estratégico') and not d['topic']:
            unmapped+=1
            continue
        subject=d['subject']
        lesson=d['lesson']
        if not subject or not lesson:
            unmapped+=1
            continue
        key=norm(lesson)
        row=grouped[subject].get(key)
        if row is None:
            row={'lesson':lesson,'topic':d['topic'] or '',
                 'materials':[],'available':False,
                 'topic_origin':'Vínculo manual de PDF' if d['topic'] else 'Assunto não identificado'}
            grouped[subject][key]=row
            extra+=1
        if not row['topic'] and d['topic']:
            row['topic']=d['topic']
            row['topic_origin']='Vínculo manual de PDF'
        row['materials'].append({'id':d['id'],'type':d['material_type'],
                                 'file':d['file_name']})
        row['available']=True
    subjects=[]
    known=set(grouped)
    # Todas as disciplinas aparecem na navegação, mesmo sem CSV.
    for subj in list(EXPECTED_SUBJECTS)+[x[0] for x in DEFAULT_SUBJECTS if x[0] not in EXPECTED_SUBJECTS]+sorted(known-{x[0] for x in DEFAULT_SUBJECTS}):
        rows=sorted(grouped.get(subj,{}).values(),key=lambda e:(norm(e['lesson']),e['topic']))
        for entry in rows:
            incidence=percentages.get((norm(subj),norm(entry['topic'])))
            entry['incidence_pct']=incidence[0] if incidence else None
            entry['incidence_source']=incidence[1] if incidence else ''
        subjects.append({'subject':subj,'lesson_count':len(rows),
          'matched_lessons':sum(x['available'] for x in rows),
          'status':'Aguardando catálogo/vínculo do PDF' if not rows else 'Catálogo local',
          'lessons':rows})
    return {'total_lessons':sum(x['lesson_count'] for x in subjects),
            'subjects':subjects,'unmapped_pdfs':unmapped,'supplemental_lessons':extra,
            'source':('Lista pessoal de aulas e PDFs catalogados. Não constitui edital oficial.'
                      if catalog else 'Não foi localizado CSV pessoal: exibindo apenas aulas identificadas nos PDFs catalogados.'),
            'pending_subjects':[x['subject'] for x in subjects
                if x['subject'] in EXPECTED_SUBJECTS and not x['lesson_count']]}


def _has_table(c,name):
    return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone() is not None
