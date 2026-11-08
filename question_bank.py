"""Desempenho de questões por disciplina e banca: média ponderada por questão."""
from __future__ import annotations
from core import all_rows

def report(c,min_total=10):
    if isinstance(min_total,bool):raise ValueError('Amostra inválida.')
    min_total=int(min_total)
    if not 1<=min_total<=1000:raise ValueError('Amostra mínima inválida.')
    rows=all_rows(c,"""SELECT subject, COALESCE(NULLIF(TRIM(bank),''),'Não informada') AS bank,
        SUM(total) AS total, SUM(correct) AS correct, COUNT(*) AS batches
        FROM questions GROUP BY subject,COALESCE(NULLIF(TRIM(bank),''),'Não informada')
        HAVING SUM(total)>0
        ORDER BY subject, total DESC, bank""")
    for x in rows:
        x['rate']=x['correct']/x['total']
        x['sample_sufficient']=x['total']>=min_total
    by_subject={}
    for x in rows:
        g=by_subject.setdefault(x['subject'],{'subject':x['subject'],'total':0,'correct':0,'banks':0})
        g['total']+=x['total'];g['correct']+=x['correct'];g['banks']+=1
    subjects=list(by_subject.values())
    for x in subjects:x['rate']=x['correct']/x['total']
    subjects.sort(key=lambda x:(x['rate'], -x['total'],x['subject']))
    return {'rows':rows,'subjects':subjects,'minimum':min_total,'note':
      'Acertos / total de questões, incluindo brancos quando registrados; ponderado pelo número de questões. '
      'Não inclui simulados completos, redações nem provas de Português; ausência de banca é identificada.'}
