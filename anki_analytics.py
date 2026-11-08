"""Análise local e somente leitura das respostas de revisão via AnkiConnect.

Não altera baralhos, cartões, agendamentos ou parâmetros FSRS.
Taxa = proporção de respostas NÃO Again em revisões tipo 1, não é memória real.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date, datetime, timedelta
from anki_bridge import detect, invoke
from core import all_rows

MAX_DECKS=90
MAX_EVENTS=80000
MIN_REVIEW_SAMPLE=20
WINDOW_DAYS=30

def prepare(c):
    c.execute("""CREATE TABLE IF NOT EXISTS anki_review_daily(
      profile TEXT NOT NULL,
      subject TEXT NOT NULL,
      day TEXT NOT NULL,
      all_answers INTEGER NOT NULL,
      again_answers INTEGER NOT NULL,
      review_answers INTEGER NOT NULL,
      review_again INTEGER NOT NULL,
      answer_time_ms INTEGER NOT NULL,
      sampled_at TEXT NOT NULL,
      PRIMARY KEY(profile,subject,day)
    )""")
    c.commit()

def _profile(value):
    value=str(value or '').strip()
    if not 1<=len(value)<=50 or any(ord(c)<32 for c in value):
        raise ValueError('Perfil Anki inválido.')
    return value

def collect(profile='Principal',today=None):
    profile=_profile(profile)
    now=datetime.now().astimezone()
    today=today or now.date()
    cutoff=today-timedelta(days=WINDOW_DAYS-1)
    since=int(datetime.combine(cutoff,datetime.min.time(),tzinfo=now.tzinfo).timestamp()*1000)-1
    discovered=detect()
    decks=sorted(discovered['decks'],
                 key=lambda x:(-x['deck'].count('::'),x['deck']))
    if len(decks)>MAX_DECKS:raise ValueError('Muitos baralhos encontrados. Limite de consulta excedido.')
    # A mesma revisão pode aparecer no pai e em um subbaralho: deduplicação por id do revlog.
    seen=set()
    daily=defaultdict(lambda:[0,0,0,0,0])
    for deck in decks:
        reviews=invoke('cardReviews',{'deck':deck['deck'],'startID':since})
        if not isinstance(reviews,list):raise ValueError('Histórico AnkiConnect inválido.')
        if len(reviews)>MAX_EVENTS:raise ValueError('Histórico Anki excedeu o limite de segurança.')
        for row in reviews:
            if not isinstance(row,(list,tuple)) or len(row)<9:continue
            try:
                identity=int(row[0]);ease=int(row[3]);ms=int(row[7]);kind=int(row[8])
                day=datetime.fromtimestamp(identity/1000,now.tzinfo).date()
            except (ValueError,TypeError,OverflowError,OSError):continue
            if identity in seen or day<cutoff or day>today:continue
            if ease not in (1,2,3,4) or kind not in (0,1,2,3):continue
            seen.add(identity)
            if len(seen)>MAX_EVENTS:raise ValueError('Histórico de revisões muito grande para a análise.')
            record=daily[(deck['subject'],day.isoformat())]
            record[0]+=1
            if ease==1:record[1]+=1
            if kind==1:
                record[2]+=1
                if ease==1:record[3]+=1
            record[4]+=max(0,min(ms,3600000))
    return {'profile':profile,'start':cutoff.isoformat(),'end':today.isoformat(),
            'rows':[{'subject':s,'day':day,
                'all_answers':a,'again_answers':g,'review_answers':v,'review_again':vg,'answer_time_ms':t}
                for (s,day),(a,g,v,vg,t) in sorted(daily.items())],
            'events':len(seen),'recognized_decks':len(decks),
            'total_decks':discovered['all_decks']}

def save(c,result):
    prepare(c)
    profile=_profile(result['profile'])
    rows=result['rows']
    if len(rows)>5000:raise ValueError('Muitos registros de resumo.')
    # Só substituímos registros derivados dentro da janela reimportada; histórico anterior intacto.
    try:
        c.execute('BEGIN IMMEDIATE')
        c.execute('DELETE FROM anki_review_daily WHERE profile=? AND day BETWEEN ? AND ?',
                  (profile,result['start'],result['end']))
        now=datetime.now().isoformat(timespec='seconds')
        c.executemany("""INSERT INTO anki_review_daily
          (profile,subject,day,all_answers,again_answers,review_answers,review_again,answer_time_ms,sampled_at)
          VALUES(?,?,?,?,?,?,?,?,?)""",[
          (profile,x['subject'],x['day'],x['all_answers'],x['again_answers'],
           x['review_answers'],x['review_again'],x['answer_time_ms'],now) for x in rows
        ])
        c.commit()
    except Exception:
        c.rollback()
        raise
    return {'ok':True,'profile':profile,'events':result['events'],
            'recognized_decks':result['recognized_decks'],'rows':len(rows)}

def report(c,profile='Principal',today=None):
    prepare(c);profile=_profile(profile)
    today=today or date.today()
    cutoff=(today-timedelta(days=WINDOW_DAYS-1)).isoformat()
    rows=all_rows(c,"""SELECT subject,day,all_answers,again_answers,review_answers,
                review_again,answer_time_ms,sampled_at
                FROM anki_review_daily WHERE profile=? AND day BETWEEN ? AND ?
                ORDER BY subject,day""",(profile,cutoff,today.isoformat()))
    summary={}
    daily={}
    last_sync=max((x['sampled_at'] for x in rows),default=None)
    for x in rows:
        rec=summary.setdefault(x['subject'],{'subject':x['subject'],
                          'all_answers':0,'again_answers':0,'review_answers':0,
                          'review_again':0,'answer_time_ms':0})
        for field in ('all_answers','again_answers','review_answers','review_again','answer_time_ms'):
            rec[field]+=int(x[field])
        d=daily.setdefault(x['day'],{'day':x['day'],'all_answers':0,'again_answers':0})
        d['all_answers']+=x['all_answers']
        d['again_answers']+=x['again_answers']
    subjects=[]
    for v in summary.values():
        v['review_success_rate']=round((v['review_answers']-v['review_again'])/v['review_answers'],4) if v['review_answers']>=MIN_REVIEW_SAMPLE else None
        v['review_sample_sufficient']=v['review_answers']>=MIN_REVIEW_SAMPLE
        subjects.append(v)
    subjects.sort(key=lambda x:(x['review_success_rate'] is None,
                                x['review_success_rate'] if x['review_success_rate'] is not None else 0,
                                -x['review_answers'],x['subject']))
    return {
        'profile':profile,'period_days':WINDOW_DAYS,'sample_min':MIN_REVIEW_SAMPLE,
        'last_sync':last_sync,
        'total_answers':sum(x['all_answers'] for x in subjects),
        'total_again':sum(x['again_answers'] for x in subjects),
        'total_review_answers':sum(x['review_answers'] for x in subjects),
        'subjects':subjects,'daily':[daily[k] for k in sorted(daily)],
        'notes':['Índice de respostas não-Again: apenas revisões programadas do tipo 1.',
                 'Amostras inferiores a 20 respostas de revisão não geram porcentagem.',
                 'Não representa retenção futura, domínio do assunto ou nota de concurso.',
                 'Minutos do Anki são informativos e NÃO são somados às horas líquidas do cronômetro.']
    }
