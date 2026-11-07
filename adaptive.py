"""CONTROLE MESTRE v0.5 — recomendações auditáveis por assunto.

Os escores são heurísticos, NÃO probabilidades de aprovação. Dados ausentes
não são confundidos com 0% de acerto. Relatórios não modificam o banco.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import date, timedelta, datetime
import math

from core import all_rows, get_days, parse_day

WINDOW_DAYS = 90
MIN_SAMPLE = 15


def _today(value=None):
    day = parse_day(value or date.today())
    if not day:
        raise ValueError('Data de referência inválida.')
    return date.fromisoformat(day)


def diagnose(c, today=None, limit=12):
    """Pontos fracos sem inferir taxas de acerto de disciplinas não avaliadas."""
    ref = _today(today)
    since = (ref - timedelta(days=WINDOW_DAYS - 1)).isoformat()
    through = ref.isoformat()
    subs = {r['name']:r for r in all_rows(c,'SELECT name,weight,area FROM subjects')}
    topics = all_rows(c, '''SELECT subject,topic,MAX(incidence) incidence,
         MAX(progress) progress FROM topics WHERE TRIM(topic)!=''
         GROUP BY subject,topic''')
    question_rows = all_rows(c,'''SELECT subject,topic,SUM(total) total,SUM(correct) correct,
         MAX(day) last_question FROM questions WHERE day BETWEEN ? AND ?
         GROUP BY subject,topic''',(since,through))
    reasons = all_rows(c,'''SELECT subject,topic,error_type,SUM(total-correct) misses
         FROM questions WHERE day BETWEEN ? AND ? AND total>correct
           AND TRIM(error_type)!=''
         GROUP BY subject,topic,error_type''',(since,through))
    reviews = all_rows(c,'''SELECT subject,topic,COUNT(*) pending FROM reviews
         WHERE status='Pendente' AND due_on<=? GROUP BY subject,topic''',(through,))
    sessions = all_rows(c,'''SELECT subject,topic,MAX(day) last_day
         FROM sessions WHERE day<=? GROUP BY subject,topic''',(through,))
    errorrows = all_rows(c,'''SELECT subject,topic,COUNT(*) open_errors FROM errors
         WHERE status='Aberto' GROUP BY subject,topic''')

    by_topic = {}
    for r in topics:
        by_topic[(r['subject'],r['topic'])] = {
            'subject':r['subject'], 'topic':r['topic'],
            'incidence':float(r['incidence'] or 1), 'progress':float(r['progress'] or 0),
            'has_progress':True}
    for items in [question_rows,reviews,sessions,errorrows]:
        for r in items:
            if r['subject'] not in subs: continue
            key=(r['subject'],r['topic'])
            by_topic.setdefault(key,{'subject':r['subject'],'topic':r['topic'],
                'incidence':1.0,'progress':None,'has_progress':False})
    represented = {key[0] for key in by_topic}
    for name in subs:
        if name not in represented:
            by_topic[(name,'')]={'subject':name,'topic':'','incidence':1.0,
                                  'progress':None,'has_progress':False}
    qs={(r['subject'],r['topic']):r for r in question_rows}
    rs={(r['subject'],r['topic']):r for r in reviews}
    ss={(r['subject'],r['topic']):r for r in sessions}
    ee={(r['subject'],r['topic']):r for r in errorrows}
    reason_map=defaultdict(Counter)
    for r in reasons:
        reason_map[(r['subject'],r['topic'])][r['error_type']]+=int(r['misses'])

    ranked = []
    for key, info in by_topic.items():
        subject=info['subject']; subj=subs[subject]
        q=qs.get(key,{})
        n=int(q.get('total') or 0); correct=int(q.get('correct') or 0)
        rate=correct/n if n else None
        due=int(rs.get(key,{}).get('pending') or 0)
        pending_err=int(ee.get(key,{}).get('open_errors') or 0)
        last=ss.get(key,{}).get('last_day')
        gap=(ref-date.fromisoformat(last)).days if last else None
        incidence=max(.5,min(2.,float(info['incidence'])))
        # N<15: dados insuficientes. Falta de registros demanda diagnóstico, não 'fraqueza'.
        base=float(subj['weight'])*incidence
        weakness=(1-rate) if n>=MIN_SAMPLE else .25
        unknown=.32 if n<MIN_SAMPLE else 0
        review_burden=.18*min(due,4)
        stale=min(1,max(0,gap-7)/21)*.16 if gap is not None else 0
        progress_gap=.24*(1-info['progress']/100) if info['has_progress'] else .06
        score=base*(1+.95*weakness+unknown+review_burden+stale+progress_gap+.06*min(pending_err,3))
        if due:
            action='Revisão'; label='Regularizar revisão pendente'
        elif n>=MIN_SAMPLE and rate<.70:
            action='Caderno de erros' if pending_err or reason_map[key] else 'Questões'
            label='Reforço direcionado dos erros'
        elif n<MIN_SAMPLE:
            action='Questões' if info['progress'] is None or info['progress']>=60 else 'Teoria'
            label='Diagnosticar domínio' if action=='Questões' else 'Consolidar teoria'
        elif info['progress'] is not None and info['progress']<70:
            action='Teoria';label='Aprofundar conteúdo incompleto'
        else:
            action='Revisão';label='Manter retenção'
        main_reason=reason_map[key].most_common(1)
        reason=main_reason[0][0] if main_reason else None
        rationale=[f'Peso {subj["weight"]:g}/10']
        if n>=MIN_SAMPLE:rationale.append(f'{correct}/{n} acertos ({rate:.0%}) em {WINDOW_DAYS} dias')
        elif n:rationale.append(f'Amostra insuficiente: {n} questões')
        else:rationale.append('Sem questões registradas no período')
        if due:rationale.append(f'{due} revisão(ões) vencida(s) ou para hoje')
        if reason:rationale.append(f'Erro predominante na bateria: {reason}')
        if info['has_progress']:rationale.append(f'Conteúdo marcado como {info["progress"]:.0f}% concluído')
        ranked.append({'subject':subject,'topic':info['topic'],
            'weight':float(subj['weight']),'incidence':round(incidence,2),
            'score':round(score,2),'questions':n,'correct':correct,
            'rate':round(rate,4) if rate is not None else None,
            'confidence':'Aferido' if n>=50 else ('Parcial' if n>=MIN_SAMPLE else 'Insuficiente'),
            'due_reviews':due,'open_errors':pending_err,'main_error':reason,
            'progress':info['progress'] if info['has_progress'] else None,
            'last_study_days':gap,'method':action,'action':label,
            'rationale':' · '.join(rationale)})

    ranked.sort(key=lambda x:(-x['score'],-x['questions'],x['subject'],x['topic']))
    # Máximo de 3 assuntos/discip., preservando diversidade no diagnóstico.
    result=[];used=Counter()
    for x in ranked:
        if used[x['subject']]>=3:continue
        result.append(x);used[x['subject']]+=1
        if len(result)>=limit:break
    question_count=sum(int(r['total']) for r in question_rows)
    return {'generated_on':through,'window_days':WINDOW_DAYS,'min_sample':MIN_SAMPLE,
        'total_questions_in_window':question_count,
        'coverage':'Parcial' if question_count>=MIN_SAMPLE else 'Diagnóstico inicial',
        'recommendations':result,
        'notes':['Escores são prioridades heurísticas, não previsões de aprovação.',
                 'Sem amostra suficiente, a proposta é diagnosticar antes de reforçar.',
                 'O percentual de acertos considera somente questões avulsas registradas.']}


def _rank_pool(c, ref):
    # Pool maior que a visualização para não concentrar todos os blocos em um assunto.
    r=diagnose(c,ref,limit=80)['recommendations']
    return r


def preview_plan(c,week_start=None, today=None):
    ref=_today(today or date.today())
    ws=_today(week_start or ref);ws-=timedelta(days=ws.weekday())
    end=ws+timedelta(days=6)
    start_iso,end_iso=ws.isoformat(),end.isoformat()
    days=get_days(c,ws)
    target=int(c.execute("SELECT value FROM settings WHERE key='weekly_target_min'").fetchone()[0])
    done=all_rows(c,"""SELECT day,SUM(target_minutes) minutes FROM plans
        WHERE day BETWEEN ? AND ? AND status='Concluída' GROUP BY day""",(start_iso,end_iso))
    finished={r['day']:int(r['minutes']) for r in done}
    preserved=sum(finished.values())
    available=[dict(d,available=max(0,d['cap_minutes']-finished.get(d['day'],0))) for d in days]
    capacity=sum(d['cap_minutes'] for d in days)
    remaining_cap=sum(d['available'] for d in available)
    budget=min(max(target-preserved,0),remaining_cap)
    # Distribuição inteira sem exceder capacidade, preservando minutos de orçamento.
    distribution=[]
    for d in available:
        share=budget*d['available']/remaining_cap if remaining_cap else 0
        distribution.append({**d,'allocated':min(d['available'],int(share)),'fraction':share-int(share)})
    leftover=budget-sum(d['allocated'] for d in distribution)
    for d in sorted(distribution,key=lambda x:-x['fraction']):
        if leftover==0:break
        if d['allocated']<d['available']:d['allocated']+=1;leftover-=1
    ranked=_rank_pool(c,ref)
    by_topic=Counter();by_sub=Counter()
    tasks=[]
    for d in distribution:
        left=d['allocated']
        while left>0 and ranked:
            # Um assunto repetido é gradualmente penalizado, não excluído.
            best=max(ranked,key=lambda x:x['score']/(1+.65*by_topic[(x['subject'],x['topic'])]+.14*by_sub[x['subject']]))
            task_minutes=min(left,30 if d['kind']=='Plantão' else (40 if d['kind']=='Pós-plantão' else 50))
            if left-task_minutes<20:task_minutes=left
            # Evita tarefa menor que 20 min separada; agrega ao bloco imediatamente anterior.
            if tasks and tasks[-1]['day']==d['day'] and left<20:
                tasks[-1]['target_minutes']+=left
                left=0
                break
            method=best['method']
            if d['kind']=='Plantão' and method in ('Teoria','Caderno de erros'):
                method='Revisão' if best['due_reviews'] else 'Questões'
            if d['kind']=='Pós-plantão' and method=='Teoria':method='Revisão'
            tasks.append({'day':d['day'],'subject':best['subject'],
                'topic':best['topic'] or 'Diagnóstico da disciplina','method':method,
                'target_minutes':task_minutes,
                'target_questions':round(task_minutes/2.5) if method=='Questões' else 0,
                'priority':best['score'],
                'rationale':best['rationale'],'status':'Pendente'})
            by_topic[(best['subject'],best['topic'])]+=1
            by_sub[best['subject']]+=1
            left-=task_minutes
    planned=sum(t['target_minutes'] for t in tasks)
    assert planned==budget, (planned,budget)
    return {'week_start':start_iso,'week_end':end_iso,'target_minutes':target,
            'capacity_minutes':capacity,'preserved_completed_minutes':preserved,
            'new_planned_minutes':planned,'total_planned_minutes':preserved+planned,
            'shortfall_minutes':max(0,target-preserved-planned),
            'task_count':len(tasks),'tasks':tasks,
            'warning':'A disponibilidade cadastrada é menor que a meta semanal.' if target>capacity else None,
            'mode':'Prévia: nenhuma atividade foi alterada.'}


def apply_plan(c,week_start=None,confirm=False):
    if confirm is not True:
        raise ValueError('Confirmação explícita necessária para substituir as tarefas pendentes.')
    result=preview_plan(c,week_start)
    start,end=result['week_start'],result['week_end']
    batch='adaptive:'+start+':'+datetime.now().isoformat(timespec='microseconds')
    # transação única: nem remoção parcial, nem duplicação em caso de falha.
    try:
        c.execute('BEGIN IMMEDIATE')
        c.execute("DELETE FROM plans WHERE day BETWEEN ? AND ? AND status='Pendente'",(start,end))
        for t in result['tasks']:
            c.execute('''INSERT INTO plans(day,subject,topic,method,target_minutes,target_questions,
                    priority,rationale,status,batch) VALUES(?,?,?,?,?,?,?,?,?,?)''',
                (t['day'],t['subject'],t['topic'],t['method'],t['target_minutes'],
                 t['target_questions'],t['priority'],t['rationale'],'Pendente',batch))
        c.commit()
    except Exception:
        c.rollback();raise
    return {k:v for k,v in result.items() if k!='tasks'} | {'mode':'Aplicado','activities':len(result['tasks'])}