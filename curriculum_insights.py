"""Visão curricular por assunto com proveniência explícita e dados locais.

Composição não destrutiva: guia editável, lista pessoal de aulas, tópicos do banco
e PDFs catalogados. NÃO é o novo edital oficial e não inventa incidências.
"""
from __future__ import annotations
from collections import defaultdict
from core import all_rows,norm,DEFAULT_SUBJECTS
from lesson_catalog import lessons as catalog_lessons
from study_guide import prepare as prepare_guide
from sources import prepare as prepare_sources
from bizu_seed import rows as bizu_rows
from topic_importance import read as importance_read,level_for_incidence

def report(c):
    prepare_guide(c);prepare_sources(c)
    result={}
    stats={'guide':0,'catalog':0,'topics':0,'pdfs':0}
    importance=importance_read(c)
    historical={}
    for raw in bizu_rows():
        if raw['incidence_pct'] is not None:
            historical[(norm(raw['subject']),norm(raw['topic']))]=raw
    def documented_incidence(subject,topic):
        key=(norm(subject),norm(topic))
        if key in historical:return historical[key]
        # Só aceita prefixo completo delimitado, p.ex. "Índices de liquidez:
        # objetivos..." vinculado à categoria histórica "Índices de liquidez".
        candidates=[]
        for (s,t),raw in historical.items():
            if s!=key[0] or not key[1].startswith(t+' '):continue
            candidates.append(raw)
        return candidates[0] if len(candidates)==1 else None

    def add(subject,topic,source,**fields):
        if not subject or not topic:return
        k=(norm(subject),norm(topic))
        if not k[0] or not k[1]:return
        entry=result.setdefault(k,{'subject':subject,'topic':topic,
            'lesson':'','status':'Não iniciado','progress':0,
            'incidence_pct':None,'incidence_source':'',
            'pdfs':[],'origins':[],'guide_id':None,'entry_id':None,'total_questions':0,'correct_questions':0})
        if source not in entry['origins']:entry['origins'].append(source)
        if entry['incidence_pct'] is None:
            historical_row=documented_incidence(subject,topic)
            if historical_row:
                entry['incidence_pct']=historical_row['incidence_pct']
                entry['incidence_source']=historical_row['source_type']+' · '+historical_row['source_reference']+' (categoria histórica, correspondência textual)'

        if fields.get('lesson') and not entry['lesson']:entry['lesson']=fields['lesson']
        if fields.get('incidence_pct') is not None and entry['incidence_pct'] is None:
            entry['incidence_pct']=fields['incidence_pct']
            entry['incidence_source']=fields.get('incidence_source','')
        if fields.get('entry_id'):
            entry['entry_id']=fields['entry_id'];entry['guide_id']=fields.get('guide_id')
        if fields.get('status') is not None:
            entry['status']=fields['status']
            entry['progress']=fields['progress']
        return entry
    # Registros já existentes: conservar progresso individual das diversas fontes.
    guide=all_rows(c,"""SELECT id,guide_id,subject,topic,status,progress,incidence_pct,
      source_type,source_reference FROM study_guide_entries ORDER BY id""")
    for row in guide:
        add(row['subject'],row['topic'],'Guia de estudos',
            entry_id=row['id'],guide_id=row['guide_id'],status=row['status'],progress=row['progress'],
            incidence_pct=row['incidence_pct'],incidence_source=row['source_type']+
            (' · '+row['source_reference'] if row['source_reference'] else ''))
    stats['guide']=len(guide)
    # O catálogo CSV é do titular. Não substitui o conteúdo de um edital oficial.
    catalog=catalog_lessons()
    by_lesson=defaultdict(list)
    for row in catalog:
        e=add(row['disciplina'],row['assunto'],'Catálogo de aulas',lesson=row['aula'])
        if e:by_lesson[(norm(row['disciplina']),norm(row['aula']))].append(e)
    stats['catalog']=len(catalog)
    # Prioridade histórica da tabela topics NÃO é percentual; não reinterpretar.
    from_topics=all_rows(c,'SELECT subject,topic,lesson,progress FROM topics')
    for row in from_topics:
        k=(norm(row['subject']),norm(row['topic']))
        e=add(row['subject'],row['topic'],'Tópicos antigos',lesson=row['lesson'])
        if e and not any(x.get('status') is not None for x in guide if norm(x['subject'])==k[0] and norm(x['topic'])==k[1]):
            raw=float(row['progress'] or 0)
            progress=round(raw*100 if 0<=raw<=1 else min(100,max(0,raw)))
            e['progress']=progress
            e['status']='Concluído' if progress==100 else 'Em estudo' if progress else 'Não iniciado'
    stats['topics']=len(from_topics)
    pdfs=all_rows(c,"""SELECT id,subject,topic,lesson,material_type,file_name
        FROM study_materials WHERE status='Disponível' ORDER BY subject,lesson,id""")
    unlinked=[]
    for pdf in pdfs:
        e=None
        if pdf['topic'] and pdf['subject']:
            e=add(pdf['subject'],pdf['topic'],'PDF catalogado',lesson=pdf['lesson'])
        if e is None and pdf['subject'] and pdf['lesson']:
            possible=by_lesson.get((norm(pdf['subject']),norm(pdf['lesson'])),[])
            if len(possible)==1:e=possible[0]
        doc={'id':pdf['id'],'name':pdf['file_name'],'type':pdf['material_type']}
        if e:e['pdfs'].append(doc)
        else:unlinked.append({'id':pdf['id'],'subject':pdf['subject'],
                              'lesson':pdf['lesson'],'file_name':pdf['file_name']})
    stats['pdfs']=len(pdfs)
    # Desempenho real apenas por assunto com nome exatamente normalizado.
    questions=all_rows(c,"""SELECT subject,topic,SUM(total) AS total,
         SUM(correct) AS correct FROM questions WHERE TRIM(topic)<>'' GROUP BY subject,topic""")
    for row in questions:
        e=result.get((norm(row['subject']),norm(row['topic'])))
        if e:
            e['total_questions']+=row['total']
            e['correct_questions']+=row['correct']
    grouped=defaultdict(list)
    for row in result.values():
        k=(norm(row['subject']),norm(row['topic']))
        manual=importance.get(k)
        row['importance_level']=manual if manual is not None else level_for_incidence(row['incidence_pct'])
        row['importance_basis']='Definido por você' if manual is not None else (
            'Faixa indicativa por incidência histórica (não oficial)' if row['incidence_pct'] is not None else 'Sem classificação')
        row['question_rate']=(row['correct_questions']/row['total_questions']
                              if row['total_questions'] else None)
        grouped[row['subject']].append(row)
    subjects=[]
    ordered=[x[0] for x in DEFAULT_SUBJECTS]
    ordered.extend(sorted(set(grouped)-set(ordered)))
    for subject in ordered:
        items=grouped.get(subject,[])
        items.sort(key=lambda x:(x['lesson'],x['topic']))
        completed=sum(x['progress'] for x in items)/len(items) if items else 0
        total_questions=sum(x['total_questions'] for x in items)
        correct_questions=sum(x['correct_questions'] for x in items)
        subjects.append({'subject':subject,'topics':items,'topic_count':len(items),
                         'progress_pct':round(completed,1),
                         'questions':total_questions,
                         'question_rate':(correct_questions/total_questions if total_questions else None)})
    return {'subjects':subjects,'stats':stats,'unlinked_pdfs':unlinked,
            'total_topics':len(result),
            'total_progress_pct':round(sum(e['progress'] for e in result.values())/len(result),1) if result else None,
            'notice':('Percentuais são incidências HISTÓRICAS das fontes informadas, não pesos oficiais. '
              'A conclusão é média dos tópicos cadastrados, não percentual de domínio do edital oficial. '
              'Sem lista ou fonte, o assunto e a incidência permanecem não estimados.')}
