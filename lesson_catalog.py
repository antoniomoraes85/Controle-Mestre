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
    from sources import prepare
    prepare(c)
    rows=lessons()
    # Uma aula pode ter arquivos de teoria, questões, simplificado e Passo.
    mats=all_rows(c,"""SELECT id,subject,lesson,material_type,status,file_name
        FROM study_materials WHERE status='Disponível'""")
    linked=defaultdict(list)
    for m in mats:
        if not m['subject'] or not m['lesson']:continue
        linked[(m['subject'],norm(m['lesson']))].append({
            'id':m['id'], 'type':m['material_type'], 'file':m['file_name']})
    summary=Counter(x['disciplina'] for x in rows)
    output=[]
    for subj in EXPECTED_SUBJECTS:
        group=[]
        for r in rows:
            if r['disciplina']!=subj:continue
            files=linked[(subj,norm(r['aula']))]
            group.append({'lesson':r['aula'],'topic':r['assunto'],
                          'materials':files,'available':bool(files)})
        output.append({'subject':subj,'lesson_count':len(group),
                       'matched_lessons':sum(bool(x['materials']) for x in group),
                       'status':'Aguardando lista de aulas' if not group else 'Catálogo fornecido pelo aluno',
                       'lessons':group})
    return {'total_lessons':len(rows),'subjects':output,
            'source':('Listas fornecidas pelo titular em 07/11/2026; não são a íntegra dos próximos editais.'
                      if rows else 'Catálogo local não instalado: copie dados/catalogo/aulas_primeiro_ciclo.csv da distribuição pessoal.'),
            'pending_subjects':[s for s in EXPECTED_SUBJECTS if not summary[s]]}