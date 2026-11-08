"""Links de cadernos por assunto, metadados locais. Nunca lê provas protegidas."""
from __future__ import annotations
from datetime import datetime
from urllib.parse import urlsplit
from core import all_rows

ALLOWED_HOSTS={
    'questo.es','www.questo.es',
    'tecconcursos.com.br','www.tecconcursos.com.br',
    'qconcursos.com','www.qconcursos.com'
}
def prepare(c):
    c.execute("""CREATE TABLE IF NOT EXISTS lesson_question_links(
      id INTEGER PRIMARY KEY,
      subject TEXT NOT NULL,topic TEXT NOT NULL,url TEXT NOT NULL UNIQUE,
      label TEXT NOT NULL,
      created_at TEXT NOT NULL
    )""")
    c.commit()
def list_links(c):
    prepare(c)
    return all_rows(c,"SELECT id,subject,topic,url,label FROM lesson_question_links ORDER BY subject,topic,id")
def save(c,info):
    prepare(c)
    subject=str(info.get('subject') or '').strip()
    topic=str(info.get('topic') or '').strip()
    label=str(info.get('label') or 'Caderno de questões').strip()
    url=str(info.get('url') or '').strip()
    u=urlsplit(url)
    if not 1<=len(subject)<=120 or not 1<=len(topic)<=250 or not 1<=len(label)<=180:
        raise ValueError('Disciplina, assunto e nome do caderno são obrigatórios.')
    if not 1<=len(url)<=1800 or u.scheme!='https' or u.hostname not in ALLOWED_HOSTS or u.username or u.password:
        raise ValueError('Use links HTTPS do TEC, QConcursos ou questo.es.')
    c.execute("""INSERT INTO lesson_question_links(subject,topic,url,label,created_at)
        VALUES(?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET
        subject=excluded.subject,topic=excluded.topic,label=excluded.label""",
        (subject,topic,url,label,datetime.now().isoformat(timespec='seconds')))
    c.commit()
    return {'ok':True}
