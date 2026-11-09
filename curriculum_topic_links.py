"""Relação muitos-para-muitos: um PDF contém diversos assuntos e vice-versa.

Somente assuntos confirmados/validados por página aparecem no quadro curricular.
Não edita títulos originais, links manuais ou arquivos PDF.
"""
from __future__ import annotations
from datetime import datetime
from core import norm

def prepare(c):
    c.execute("""CREATE TABLE IF NOT EXISTS curriculum_topic_links(
      id INTEGER PRIMARY KEY,
      material_id INTEGER NOT NULL REFERENCES study_materials(id),
      subject TEXT NOT NULL,topic TEXT NOT NULL,
      subtopic TEXT NOT NULL DEFAULT '',lesson TEXT NOT NULL DEFAULT '',
      page_from INTEGER NOT NULL CHECK(page_from > 0),
      page_to INTEGER NOT NULL CHECK(page_to >= page_from),
      excerpt TEXT NOT NULL DEFAULT '',
      verified INTEGER NOT NULL DEFAULT 0 CHECK(verified IN (0,1)),
      updated_at TEXT NOT NULL,
      UNIQUE(material_id,subject,topic,subtopic,page_from)
    )""")
    c.execute('CREATE INDEX IF NOT EXISTS idx_curriculum_topic_links_material ON curriculum_topic_links(material_id)')
    c.commit()

def register(c,links,verified=False):
    prepare(c)
    if not isinstance(links,list) or len(links)>5000:raise ValueError('Até 5000 vínculos por lote.')
    validated=[]
    for x in links:
        if not isinstance(x,dict):raise ValueError('Vínculo inválido.')
        mid=x.get('material_id')
        if isinstance(mid,bool) or not isinstance(mid,int) or mid<1:raise ValueError('ID de PDF inválido.')
        material=c.execute("""SELECT id,subject,lesson,pages FROM study_materials
                              WHERE id=? AND status='Disponível'""",(mid,)).fetchone()
        if not material:raise ValueError(f'PDF {mid} não foi catalogado.')
        subject=str(x.get('subject') or '').strip()
        topic=str(x.get('topic') or '').strip()
        subtopic=str(x.get('subtopic') or '').strip()
        lesson=str(x.get('lesson') or material['lesson'] or '').strip()
        if not subject or not topic or any(len(v)>280 for v in (subject,topic,subtopic,lesson)):
            raise ValueError('Disciplina e assunto obrigatórios, sem títulos muito extensos.')
        if material['subject'] and norm(material['subject'])!=norm(subject):
            raise ValueError('Disciplina conflitante com PDF catalogado; revisar antes.')
        start=x.get('page_from');end=x.get('page_to',start)
        if (isinstance(start,bool) or not isinstance(start,int) or start<1 or
            isinstance(end,bool) or not isinstance(end,int) or end<start):
            raise ValueError('Intervalo de páginas inválido.')
        if material['pages'] and end>material['pages']:
            raise ValueError('Intervalo excede as páginas catalogadas do PDF.')
        excerpt=str(x.get('excerpt') or '').strip()
        if len(excerpt)>180:raise ValueError('Trecho limitado a 180 caracteres.')
        validated.append((mid,subject,topic,subtopic,lesson,start,end,excerpt,
          int(bool(verified)),datetime.now().astimezone().isoformat(timespec='seconds')))
    try:
        for row in validated:
            c.execute("""INSERT INTO curriculum_topic_links
               (material_id,subject,topic,subtopic,lesson,page_from,page_to,
                excerpt,verified,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(material_id,subject,topic,subtopic,page_from)
               DO UPDATE SET lesson=excluded.lesson,page_to=excluded.page_to,
                excerpt=excluded.excerpt,verified=excluded.verified,
                updated_at=excluded.updated_at
               WHERE curriculum_topic_links.verified=0 OR excluded.verified=1""",row)
        c.commit()
    except Exception:
        c.rollback();raise
    return {'received':len(validated),'verified':verified}

def read_verified(c):
    prepare(c)
    return [dict(x) for x in c.execute("""SELECT l.*,m.file_name,m.material_type,m.status
       FROM curriculum_topic_links l JOIN study_materials m ON m.id=l.material_id
       WHERE l.verified=1 AND m.status='Disponível' ORDER BY l.subject,l.lesson,l.page_from""")]
