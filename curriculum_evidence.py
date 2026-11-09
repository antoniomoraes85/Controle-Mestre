"""Evidências locais de incidência, separadas do guia e de previsões futuras.

A extração dos PDFs é realizada no Windows pelo agente local. Este módulo só
aceita dados estruturados auditáveis com página e fonte, sem adivinhar percentuais.
"""
from __future__ import annotations
from core import norm
from datetime import datetime

def prepare(c):
    c.execute("""CREATE TABLE IF NOT EXISTS curriculum_evidence(
      id INTEGER PRIMARY KEY,
      subject TEXT NOT NULL, topic TEXT NOT NULL,
      incidence_pct REAL CHECK(incidence_pct BETWEEN 0 AND 100),
      qualitative TEXT NOT NULL DEFAULT '',
      material_type TEXT NOT NULL,
      document_reference TEXT NOT NULL,
      page INTEGER NOT NULL CHECK(page > 0),
      bank TEXT NOT NULL DEFAULT '',
      sample_period TEXT NOT NULL DEFAULT '',
      sample_count INTEGER CHECK(sample_count IS NULL OR sample_count > 0),
      excerpt TEXT NOT NULL DEFAULT '',
      verified INTEGER NOT NULL DEFAULT 0 CHECK(verified IN (0,1)),
      created_at TEXT NOT NULL,
      UNIQUE(subject,topic,material_type,document_reference,page)
    )""")
    c.commit()

def register(c,entries,verified=False):
    """Importa evidências verificáveis. Sem verificação, ficam em revisão."""
    prepare(c)
    if not isinstance(entries,list) or len(entries)>2000:
        raise ValueError('Forneça uma lista de até 2000 evidências.')
    records=[]
    for x in entries:
        if not isinstance(x,dict):raise ValueError('Evidência inválida.')
        subject=str(x.get('subject') or '').strip()
        topic=str(x.get('topic') or '').strip()
        typ=str(x.get('material_type') or '').strip()
        ref=str(x.get('document_reference') or '').strip()
        if not all((subject,topic,typ,ref)) or any(len(a)>350 for a in (subject,topic,typ,ref)):
            raise ValueError('Assunto, disciplina, tipo e documento são obrigatórios.')
        # Valores inventados ou não informados NÃO viram zero.
        value=x.get('incidence_pct')
        if value is not None:
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not 0<=value<=100:
                raise ValueError('Incidência deve ser percentual entre 0 e 100 ou nula.')
        page=x.get('page')
        if isinstance(page,bool) or not isinstance(page,int) or page<1:
            raise ValueError('Cada estatística exige página do PDF.')
        qualitative=str(x.get('qualitative') or '')[:200]
        bank=str(x.get('bank') or '')[:150]
        period=str(x.get('sample_period') or '')[:120]
        size=x.get('sample_count')
        if size is not None and (isinstance(size,bool) or not isinstance(size,int) or size<1):
            raise ValueError('Amostra inválida.')
        excerpt=str(x.get('excerpt') or '').strip()
        if len(excerpt)>180:raise ValueError('Trecho de evidência limitado a 180 caracteres.')
        if value is None and not qualitative:
            raise ValueError('Informe percentual documentado ou evidência qualitativa.')
        records.append((subject,topic,value,qualitative,typ,ref,page,bank,period,size,
                        excerpt,int(bool(verified)),datetime.now().astimezone().isoformat(timespec='seconds')))
    # Transação única, sem commit parcial; não altera vínculos ou progresso.
    try:
        for row in records:
            c.execute("""INSERT INTO curriculum_evidence
              (subject,topic,incidence_pct,qualitative,material_type,document_reference,
               page,bank,sample_period,sample_count,excerpt,verified,created_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
              ON CONFLICT(subject,topic,material_type,document_reference,page)
              DO UPDATE SET incidence_pct=excluded.incidence_pct,
                qualitative=excluded.qualitative,bank=excluded.bank,
                sample_period=excluded.sample_period,sample_count=excluded.sample_count,
                excerpt=excluded.excerpt,
                verified=excluded.verified,created_at=excluded.created_at""",row)
        c.commit()
    except Exception:
        c.rollback()
        raise
    return {'received':len(records),'verified':verified}

def read_verified(c):
    prepare(c)
    out={}
    for row in c.execute("""SELECT subject,topic,incidence_pct,qualitative,material_type,
       document_reference,page,bank,sample_period,sample_count
       FROM curriculum_evidence WHERE verified=1 ORDER BY id"""):
        d=dict(row)
        key=(norm(d['subject']),norm(d['topic']))
        out.setdefault(key,[]).append(d)
    return out
