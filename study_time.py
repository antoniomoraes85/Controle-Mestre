"""Agregações de tempo do estudo, com gravação idempotente no histórico único."""
from __future__ import annotations
from datetime import date, timedelta
from uuid import UUID

from core import all_rows, add_session, DAY_CAPS, METHODS


def _prev_month(y,m):
    return (y-1,12) if m==1 else (y,m-1)


def report(c,today=None):
    today=date.fromisoformat(str(today or date.today()))
    daily_start=today-timedelta(days=30)
    weekly_start=today-timedelta(days=today.weekday())-timedelta(weeks=11)
    month_keys=[]
    y,m=today.year,today.month
    for _ in range(12):
        month_keys.append(f'{y:04d}-{m:02d}')
        y,m=_prev_month(y,m)
    month_keys.reverse()
    rows=all_rows(c,"""SELECT day,subject,minutes FROM sessions
        WHERE day<=? ORDER BY day""",(today.isoformat(),))
    today_s=today.isoformat()
    daily={ (daily_start+timedelta(days=i)).isoformat():0 for i in range(31)}
    weekly={ (weekly_start+timedelta(weeks=i)).isoformat():0 for i in range(12)}
    months={key:0 for key in month_keys}
    by_subject={}
    week_start=(today-timedelta(days=today.weekday())).isoformat()
    month_start=today.replace(day=1).isoformat()
    total=0
    for row in rows:
        day,subject,minutes=row['day'],row['subject'],int(row['minutes'])
        total+=minutes
        rec=by_subject.setdefault(subject,{'subject':subject,'total_minutes':0,
                                         'week_minutes':0,'month_minutes':0})
        rec['total_minutes']+=minutes
        if day>=week_start:rec['week_minutes']+=minutes
        if day>=month_start:rec['month_minutes']+=minutes
        if day in daily:daily[day]+=minutes
        if day[:7] in months:months[day[:7]]+=minutes
        weekday=date.fromisoformat(day).weekday()
        monday=(date.fromisoformat(day)-timedelta(days=weekday)).isoformat()
        if monday in weekly:weekly[monday]+=minutes
    return {
        'today':today_s,'total_minutes':total,
        'day_minutes':daily.get(today_s,0),
        'week_minutes':sum(v for k,v in weekly.items() if k>=week_start),
        'month_minutes':months.get(today_s[:7],0),
        'daily':[{'label':k,'minutes':v} for k,v in daily.items()],
        'weekly':[{'label':k,'minutes':v} for k,v in weekly.items()],
        'monthly':[{'label':k,'minutes':v} for k,v in months.items()],
        'subjects':sorted(by_subject.values(),key=lambda x:(-x['total_minutes'],x['subject']))
    }


def save(c,data):
    subject=str(data.get('subject','')).strip()
    if not c.execute('SELECT 1 FROM subjects WHERE name=?',(subject,)).fetchone():
        raise ValueError('Selecione uma disciplina cadastrada.')
    identity=str(data.get('session_id','')).strip()
    try:UUID(identity)
    except (ValueError,TypeError,AttributeError):raise ValueError('Identificador de sessão inválido.')
    fingerprint='study_timer:'+identity
    # Idempotência: repetir uma solicitação devolve o registro anterior, sem somar duas vezes.
    existing=c.execute('SELECT id,day,subject,minutes FROM sessions WHERE fingerprint=?',(fingerprint,)).fetchone()
    if existing:
        if existing['subject']!=subject:
            raise ValueError('Identificador já utilizado por outra disciplina.')
        return {'ok':True,'id':existing['id'],'inserted':False,
                'minutes':existing['minutes'],'subject':subject}
    day=str(data.get('day') or date.today().isoformat())
    try:day=date.fromisoformat(day).isoformat()
    except ValueError:raise ValueError('Data inválida.')
    if day>date.today().isoformat():raise ValueError('A data não pode estar no futuro.')
    duration=data.get('minutes')
    if isinstance(duration,bool):raise ValueError('Minutos inválidos.')
    try:minutes=int(duration)
    except (ValueError,TypeError):raise ValueError('Minutos inválidos.')
    if not 1<=minutes<=600:raise ValueError('Sessão deve ter entre 1 e 600 minutos.')
    method=str(data.get('method','Teoria'))
    if method not in METHODS:raise ValueError('Modalidade de estudo inválida.')
    day_row=c.execute('SELECT kind FROM day_types WHERE day=?',(day,)).fetchone()
    kind=day_row['kind'] if day_row else 'Livre leve'
    if kind not in DAY_CAPS or kind=='Reset':
        kind='Livre leve'
    topic=str(data.get('topic') or '').strip()[:200]
    add_session(c,day,subject,topic,method,minutes,kind,
                notes='Cronômetro web, duração registrada ao finalizar',source='timer',
                fingerprint=fingerprint,auto_review=False)
    added=c.execute('SELECT id,minutes FROM sessions WHERE fingerprint=?',(fingerprint,)).fetchone()
    if not added:raise ValueError('Sessão não pôde ser registrada.')
    return {'ok':True,'id':added['id'],'inserted':True,'minutes':added['minutes'],'subject':subject}
