"""Prioridade manual de 1 a 10 com preservação integral dos registros legados 1–5.

Os dados antigos permanecem na tabela topic_importance (CHECK 1..5).
Registros novos usam topic_importance_v2, com precedência de leitura.
Não há conversão silenciosa dos valores escolhidos na escala anterior.
"""
from __future__ import annotations
from core import norm

def prepare(c):
    c.execute("""CREATE TABLE IF NOT EXISTS topic_importance_v2(
      subject_key TEXT NOT NULL,
      topic_key TEXT NOT NULL,
      level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 10),
      updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY(subject_key,topic_key)
    )""")
    c.commit()

def save(c,subject,topic,level):
    prepare(c)
    sk,tk=norm(subject),norm(topic)
    if not sk or not tk or len(sk)>150 or len(tk)>280:
        raise ValueError('Assunto e disciplina obrigatórios.')
    if isinstance(level,bool):raise ValueError('Nível inválido.')
    try:
        value=int(level)
        if str(level).strip()!=str(value):raise ValueError()
    except (TypeError,ValueError):
        raise ValueError('Nível deve ser inteiro de 1 a 10.')
    if value<1 or value>10:raise ValueError('Nível deve estar entre 1 e 10.')
    c.execute('''INSERT INTO topic_importance_v2(subject_key,topic_key,level)
      VALUES(?,?,?) ON CONFLICT(subject_key,topic_key)
      DO UPDATE SET level=excluded.level,updated_at=CURRENT_TIMESTAMP''',(sk,tk,value))
    c.commit()
    return {'ok':True,'importance_level':value,'scale':'1-10','manual':True}

def read_details(c):
    prepare(c)
    output={}
    old=c.execute("""SELECT name FROM sqlite_master WHERE type='table'
                      AND name='topic_importance'""").fetchone()
    if old:
        for k,t,v in c.execute('SELECT subject_key,topic_key,level FROM topic_importance'):
            output[(k,t)]={'level':v,'scale':'1-5','legacy':True}
    for k,t,v in c.execute('SELECT subject_key,topic_key,level FROM topic_importance_v2'):
        output[(k,t)]={'level':v,'scale':'1-10','legacy':False}
    return output

def read(c):
    return {key:value['level'] for key,value in read_details(c).items()}

def level_for_incidence(pct):
    """Compatibilidade com a antiga escala, apenas para integrações legadas."""
    if pct is None:return None
    return 5 if pct>=20 else 4 if pct>=12 else 3 if pct>=8 else 2 if pct>=4 else 1
