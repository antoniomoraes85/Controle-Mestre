"""Importância subjetiva do estudo, separada de incidências históricas documentadas."""
from __future__ import annotations
from core import norm
def prepare(c):
    c.execute("""CREATE TABLE IF NOT EXISTS topic_importance(
      subject_key TEXT NOT NULL,topic_key TEXT NOT NULL,
      level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 5),
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
    except (TypeError,ValueError):raise ValueError('Nível deve ser inteiro de 1 a 5.')
    if value<1 or value>5:raise ValueError('Nível deve estar entre 1 e 5.')
    c.execute('''INSERT INTO topic_importance(subject_key,topic_key,level)
      VALUES(?,?,?) ON CONFLICT(subject_key,topic_key)
      DO UPDATE SET level=excluded.level,updated_at=CURRENT_TIMESTAMP''',(sk,tk,value))
    c.commit()
    return {'ok':True,'importance_level':value}
def read(c):
    prepare(c)
    return {(x[0],x[1]):x[2] for x in
            c.execute('SELECT subject_key,topic_key,level FROM topic_importance')}
def level_for_incidence(pct):
    # Heurística de ORGANIZAÇÃO, nunca classificação publicada pela banca.
    if pct is None:return None
    return 5 if pct>=20 else 4 if pct>=12 else 3 if pct>=8 else 2 if pct>=4 else 1
