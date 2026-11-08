"""Guia de estudos persistente, privado e rastreável.

A classificação por incidência é informativa, não um edital oficial.
Nenhum conteúdo de PDF é armazenado nem sincronizado externamente.
"""
from __future__ import annotations
from datetime import datetime, timezone
import math
import sqlite3
from core import all_rows

STATES=("Não iniciado","Em estudo","Revisão","Concluído")
SOURCE_TYPES=("Manual","Bizu Estratégico","Passo Estratégico","Edital oficial","Outro")

def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def prepare(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS study_guides(
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        weekly_hours REAL NOT NULL DEFAULT 25,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS study_guide_entries(
        id INTEGER PRIMARY KEY,
        guide_id INTEGER NOT NULL REFERENCES study_guides(id),
        subject TEXT NOT NULL,
        topic TEXT NOT NULL,
        incidence_pct REAL,
        source_type TEXT NOT NULL,
        source_reference TEXT NOT NULL DEFAULT '',
        source_page INTEGER,
        status TEXT NOT NULL DEFAULT 'Não iniciado',
        progress INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(guide_id,subject,topic,source_type,source_reference)
    );
    CREATE INDEX IF NOT EXISTS study_guide_entries_by_subject
        ON study_guide_entries(guide_id,subject);
    """)
    c.commit()

def _guide(c,guide_id):
    if not c.execute('SELECT 1 FROM study_guides WHERE id=?',(guide_id,)).fetchone():
        raise ValueError('Guia de estudos não encontrado.')

def read(c):
    prepare(c)
    return {
        'guides':all_rows(c,'SELECT * FROM study_guides ORDER BY id DESC'),
        'entries':all_rows(c,'SELECT * FROM study_guide_entries ORDER BY guide_id,subject,incidence_pct DESC,topic'),
        'states':STATES,
        'note':'Incidências extraídas de fontes históricas; não são percentuais oficiais do edital SEFAZ-RS.'
    }

def create(c,title='Preparação SEFAZ-RS',weekly_hours=25):
    prepare(c)
    title=str(title or '').strip()
    try:weekly_hours=float(weekly_hours)
    except (TypeError,ValueError):raise ValueError('Carga horária semanal inválida.')
    if not 1<=len(title)<=120 or not math.isfinite(weekly_hours) or not 1<=weekly_hours<=80:
        raise ValueError('Informe título (1 a 120 caracteres) e carga semanal entre 1 e 80 horas.')
    cur=c.execute('INSERT INTO study_guides(title,weekly_hours,created_at) VALUES(?,?,?)',
                  (title,weekly_hours,_now()))
    c.commit()
    return {'id':cur.lastrowid}

def _validate(row):
    if not isinstance(row,dict):raise ValueError('Registro de assunto inválido.')
    subject=str(row.get('subject') or '').strip()
    topic=str(row.get('topic') or '').strip()
    source_type=str(row.get('source_type') or 'Manual').strip()
    source_reference=str(row.get('source_reference') or '').strip()
    if not 1<=len(subject)<=120 or not 1<=len(topic)<=250:
        raise ValueError('Disciplina ou assunto inválido.')
    if source_type not in SOURCE_TYPES or len(source_reference)>180:
        raise ValueError('Fonte inválida.')
    percentage=row.get('incidence_pct')
    if percentage in (None,''):percentage=None
    else:
        try:percentage=float(str(percentage).replace(',','.'))
        except (ValueError,TypeError):raise ValueError('Incidência precisa ser numérica.')
        if not math.isfinite(percentage) or not 0<=percentage<=100:
            raise ValueError('Incidência deve estar entre 0 e 100%.')
        percentage=round(percentage,3)
    page=row.get('source_page')
    if page in (None,''):page=None
    else:
        if isinstance(page,bool):raise ValueError('Página inválida.')
        try:page=int(page)
        except (ValueError,TypeError):raise ValueError('Página inválida.')
        if not 1<=page<=5000:raise ValueError('Página inválida.')
    return (subject,topic,percentage,source_type,source_reference,page)

def import_rows(c,guide_id,rows,confirm=False):
    prepare(c);_guide(c,guide_id)
    if confirm is not True:raise ValueError('Confirmação necessária.')
    if not isinstance(rows,list) or not 1<=len(rows)<=200:
        raise ValueError('Envie de 1 até 200 assuntos por importação.')
    values=[_validate(r) for r in rows]
    now=_now();n=0
    try:
        c.execute('BEGIN IMMEDIATE')
        for r in values:
            cur=c.execute("""INSERT OR IGNORE INTO study_guide_entries
                (guide_id,subject,topic,incidence_pct,source_type,source_reference,
                source_page,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?)""",(guide_id,*r,now,now))
            n+=cur.rowcount
        c.commit()
    except Exception:
        c.rollback()
        raise
    return {'inserted':n,'skipped':len(values)-n}

def progress(c,guide_id,entry_id,status,percentage):
    prepare(c);_guide(c,guide_id)
    if status not in STATES:raise ValueError('Status desconhecido.')
    if isinstance(percentage,bool):raise ValueError('Progresso inválido.')
    try:p=int(percentage)
    except (ValueError,TypeError):raise ValueError('Progresso inválido.')
    if not 0<=p<=100:raise ValueError('Progresso deve estar entre 0 e 100.')
    if status=='Concluído' and p!=100:raise ValueError('Concluído exige 100%.')
    cur=c.execute("""UPDATE study_guide_entries SET status=?,progress=?,updated_at=?
        WHERE guide_id=? AND id=?""",(status,p,_now(),guide_id,entry_id))
    if not cur.rowcount:raise ValueError('Assunto não encontrado no guia.')
    c.commit()
    return {'ok':True,'id':entry_id}

def save_entry(c,guide_id,row):
    x=import_rows(c,guide_id,[row],confirm=True)
    if not x['inserted']:raise ValueError('Assunto já cadastrado com essa fonte.')
    return x
