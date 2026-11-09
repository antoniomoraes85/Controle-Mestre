"""Priorização transparente (1–10), sem IA opaca e sem falsificar incidência.

Não substitui prioridade manual. Usa apenas indicadores disponíveis:
incidência histórica documentada, rendimento (amostra >= 10),
progresso explicitamente registrado e peso da disciplina.
"""
from __future__ import annotations

FACTORS={'incidence':0.4,'performance':0.35,'progress':0.15,'subject_weight':0.10}
def clamp(x):return min(1.0,max(0.0,float(x)))

def score(*,incidence_pct=None,total_questions=0,correct_questions=0,
          progress_pct=None,subject_weight=None):
    available={}
    detail=[]
    evidence_count=0
    if incidence_pct is not None:
        if not 0<=incidence_pct<=100:raise ValueError('Incidência inválida.')
        available['incidence']=clamp(incidence_pct/30)
        detail.append(f'Incidência histórica: {incidence_pct:g}% (fonte documentada)')
        evidence_count+=1
    total_questions=int(total_questions or 0)
    correct_questions=int(correct_questions or 0)
    if not 0<=correct_questions<=total_questions:
        raise ValueError('Resultados de questões inválidos.')
    if total_questions>=10:
        rate=correct_questions/total_questions
        available['performance']=1-rate
        detail.append(f'Rendimento: {correct_questions}/{total_questions} ({rate:.0%})')
        evidence_count+=1
    elif total_questions:
        detail.append(f'Amostra pequena: {total_questions} questões (mínimo 10 para pontuar)')
    if progress_pct is not None:
        if not 0<=progress_pct<=100:raise ValueError('Progresso inválido.')
        available['progress']=1-progress_pct/100
        detail.append(f'Progresso registrado: {progress_pct:g}%')
        evidence_count+=1
    if subject_weight is not None:
        if not 0<=subject_weight<=10:raise ValueError('Peso inválido.')
        available['subject_weight']=clamp(subject_weight/10)
        detail.append(f'Peso configurado da disciplina: {subject_weight:g}/10')
    # Peso da matéria isolado NÃO é suficiente para atribuir prioridade individual.
    if not evidence_count:
        return {'priority':None,'evidence_level':'insuficiente',
                'reason':'; '.join(detail) or 'Sem estatísticas ou progresso registrado',
                'factors':available,'suggested_method':None,'sample_small':0<total_questions<10}
    denominator=sum(FACTORS[k] for k in available)
    value=sum(FACTORS[k]*v for k,v in available.items())/denominator
    priority=max(1,min(10,1+round(value*9)))
    confidence='alta' if incidence_pct is not None and total_questions>=30 else (
        'moderada' if evidence_count>=2 else 'preliminar')
    if total_questions>=10 and correct_questions/total_questions<0.65:
        method='Caderno de erros'
    elif progress_pct is None or progress_pct<50:
        method='Teoria'
    elif incidence_pct is not None and incidence_pct>=12:
        method='Questões'
    else:
        method='Revisão'
    detail.append('Modelo heurístico, não estatística oficial nem previsão da prova')
    return {'priority':priority,'evidence_level':confidence,'reason':'; '.join(detail),
            'factors':available,'suggested_method':method,
            'sample_small':0<total_questions<10}
