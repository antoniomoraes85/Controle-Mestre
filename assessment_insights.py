"""Provas completas de Português e estatísticas descritivas de avaliações.

Separa provas de Português, simulados gerais, redações e questões avulsas.
Nada soma uma população de avaliação a outra automaticamente.
"""
from __future__ import annotations
from core import all_rows,parse_day
from assessments import ensure_schema
import math
from datetime import date

def prepare(c):
    ensure_schema(c)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS portuguese_exams(
        id INTEGER PRIMARY KEY,
        day TEXT NOT NULL,
        title TEXT NOT NULL,
        year INTEGER,
        bank TEXT NOT NULL,
        origin TEXT NOT NULL DEFAULT '',
        total INTEGER NOT NULL CHECK(total BETWEEN 1 AND 300),
        correct INTEGER NOT NULL CHECK(correct>=0),
        wrong INTEGER NOT NULL CHECK(wrong>=0),
        blank INTEGER NOT NULL CHECK(blank>=0),
        minutes INTEGER,
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK(correct+wrong+blank=total),
        CHECK(minutes IS NULL OR (minutes>0 AND minutes<=600))
    );
    CREATE INDEX IF NOT EXISTS idx_portuguese_day ON portuguese_exams(day);
    CREATE INDEX IF NOT EXISTS idx_portuguese_bank ON portuguese_exams(bank,day);
    """)
    c.commit()

def record(c,p):
    prepare(c)
    if not isinstance(p,dict):raise ValueError('Dados de prova inválidos.')
    day=parse_day(p.get('day'))
    if not day or day>date.today().isoformat():raise ValueError('Data inválida ou futura.')
    title=str(p.get('title') or '').strip()
    bank=str(p.get('bank') or '').strip()
    origin=str(p.get('origin') or '').strip()
    notes=str(p.get('notes') or '').strip()
    if not 1<=len(title)<=160 or not 1<=len(bank)<=80:raise ValueError('Título e banca são obrigatórios.')
    if len(origin)>160 or len(notes)>1200:raise ValueError('Texto acima do limite.')
    def n(name,default=None):
        raw=p.get(name,default)
        if raw is None or raw=='':return None
        if isinstance(raw,bool):raise ValueError(name+' inválido.')
        try:
            val=int(raw)
            if float(raw)!=val:raise ValueError()
            return val
        except (TypeError,ValueError,OverflowError):raise ValueError(name+' deve ser inteiro.')
    total=n('total');correct=n('correct');wrong=n('wrong');blank=n('blank',0)
    minutes=n('minutes')
    year=n('year')
    if any(v is None for v in (total,correct,wrong,blank)) or not 1<=total<=300 or min(correct,wrong,blank)<0 or sum([correct,wrong,blank])!=total:
        raise ValueError('Total deve ser igual a acertos + erros + brancos.')
    if minutes is not None and not 1<=minutes<=600:raise ValueError('Minutos inválidos.')
    if year is not None and not 1990<=year<=2100:raise ValueError('Ano da prova inválido.')
    cur=c.execute("""INSERT INTO portuguese_exams
        (day,title,year,bank,origin,total,correct,wrong,blank,minutes,notes)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (day,title,year,bank,origin,total,correct,wrong,blank,minutes,notes))
    c.commit()
    return {'id':cur.lastrowid,'ok':True}

def _by_bank(rows,total_key='total',correct_key='correct'):
    groups={}
    for row in rows:
        bank=(row.get('bank') or 'Não informada').strip() or 'Não informada'
        g=groups.setdefault(bank,{'bank':bank,'exams':0,'total':0,'correct':0})
        g['exams']+=1
        g['total']+=int(row[total_key]);g['correct']+=int(row[correct_key])
    out=list(groups.values())
    for g in out:g['rate']=g['correct']/g['total'] if g['total'] else None
    return sorted(out,key=lambda g:(-g['exams'],g['bank']))

def report(c):
    prepare(c)
    pt=all_rows(c,'SELECT * FROM portuguese_exams ORDER BY day DESC,id DESC LIMIT 300')
    mock=all_rows(c,'SELECT * FROM mock_exams ORDER BY day DESC,id DESC LIMIT 300')
    essays=all_rows(c,'SELECT * FROM essays ORDER BY day DESC,id DESC LIMIT 300')
    # Uma mesma redação não deve contribuir como 100 questões; normalizar pela nota máxima.
    essay_banks={}
    for e in essays:
        bank=(e['bank'] or 'Não informada').strip() or 'Não informada'
        g=essay_banks.setdefault(bank,{'bank':bank,'count':0,'sum_pct':0})
        g['count']+=1;g['sum_pct']+=e['grade']/e['maximum_grade']
    essay_groups=[{'bank':v['bank'],'count':v['count'],'mean_rate':v['sum_pct']/v['count']}
                  for v in essay_banks.values()]
    essay_groups.sort(key=lambda g:(-g['count'],g['bank']))
    return {'portuguese':pt,'portuguese_banks':_by_bank(pt),
            'mock_banks':_by_bank(mock),'essays_banks':essay_groups,
            'portuguese_rate':sum(x['correct'] for x in pt)/sum(x['total'] for x in pt) if pt else None,
            'definitions':{
                'portuguese':'Acertos / total incluindo brancos (provas completas de Português, apenas).',
                'mock':'Acertos / total incluindo brancos (simulados completos, apenas).',
                'essay':'Média não ponderada de nota / nota máxima, por redação.'
            }}
def remove(c,ident):
    prepare(c)
    if not isinstance(ident,int) or isinstance(ident,bool) or ident<=0:raise ValueError('ID inválido.')
    cur=c.execute('DELETE FROM portuguese_exams WHERE id=?',(ident,))
    if not cur.rowcount:raise ValueError('Prova não encontrada.')
    c.commit()
    return {'ok':True}
