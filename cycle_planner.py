"""Ciclos e microciclos persistentes em blocos de 30 minutos.

Marcadores de planejamento NÃO criam sessões ou horas líquidas. Rodadas concluídas
permanecem registradas e reiniciam os marcadores na rodada seguinte.
"""
from __future__ import annotations
from datetime import datetime
from core import all_rows,DEFAULT_SUBJECTS

KINDS=('Ciclo','Microciclo','Semana fixa')
METHODS=('Teoria','Questões','Lei seca','Revisão','Flashcards','Caderno de erros','Simulado')
SUBJECTS={x[0] for x in DEFAULT_SUBJECTS}
def now():return datetime.now().astimezone().isoformat(timespec='seconds')
def prepare(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS study_cycle_definitions(
       id INTEGER PRIMARY KEY, title TEXT NOT NULL, kind TEXT NOT NULL,
       parent_id INTEGER REFERENCES study_cycle_definitions(id),
       round_number INTEGER NOT NULL DEFAULT 1, archived INTEGER NOT NULL DEFAULT 0,
       created_at TEXT NOT NULL,
       CHECK(kind IN ('Ciclo','Microciclo','Semana fixa')),
       CHECK(round_number>0)
    );
    CREATE TABLE IF NOT EXISTS study_cycle_segments(
       id INTEGER PRIMARY KEY,
       cycle_id INTEGER NOT NULL REFERENCES study_cycle_definitions(id),
       position INTEGER NOT NULL,
       subject TEXT NOT NULL,
       topic TEXT NOT NULL DEFAULT '',
       method TEXT NOT NULL,
       blocks INTEGER NOT NULL CHECK(blocks BETWEEN 1 AND 12)
    );
    CREATE TABLE IF NOT EXISTS study_cycle_marks(
       id INTEGER PRIMARY KEY,
       segment_id INTEGER NOT NULL REFERENCES study_cycle_segments(id),
       round_number INTEGER NOT NULL,
       block_number INTEGER NOT NULL,
       marked_at TEXT NOT NULL,
       UNIQUE(segment_id,round_number,block_number)
    );
    CREATE TABLE IF NOT EXISTS study_cycle_rounds(
       id INTEGER PRIMARY KEY,
       cycle_id INTEGER NOT NULL REFERENCES study_cycle_definitions(id),
       round_number INTEGER NOT NULL,
       finished_at TEXT NOT NULL,
       UNIQUE(cycle_id,round_number)
    );
    """)
    c.commit()
def _cycle(c,ident):
    row=c.execute('SELECT * FROM study_cycle_definitions WHERE id=?',(ident,)).fetchone()
    if row is None or row['archived']:raise ValueError('Ciclo não encontrado ou arquivado.')
    return row
def create(c,title,kind='Ciclo',parent_id=None):
    prepare(c)
    title=str(title or '').strip()
    if not 2<=len(title)<=120 or kind not in KINDS:raise ValueError('Informe um nome e tipo de ciclo válidos.')
    if kind=='Microciclo':
        if not isinstance(parent_id,int) or isinstance(parent_id,bool):raise ValueError('Escolha o ciclo principal.')
        parent=_cycle(c,parent_id)
        if parent['kind']=='Microciclo':raise ValueError('Microciclos não podem conter outros microciclos.')
    elif parent_id is not None:raise ValueError('Somente microciclos possuem ciclo principal.')
    cur=c.execute("""INSERT INTO study_cycle_definitions(title,kind,parent_id,created_at)
        VALUES (?,?,?,?)""",(title,kind,parent_id,now()))
    c.commit()
    return {'ok':True,'id':cur.lastrowid}
def add_segment(c,cycle_id,subject,topic,method,blocks):
    prepare(c)
    _cycle(c,cycle_id)
    subject=str(subject or '').strip()
    topic=str(topic or '').strip()
    if subject not in SUBJECTS:raise ValueError('Disciplina não cadastrada.')
    if len(topic)>250 or method not in METHODS:raise ValueError('Assunto ou modalidade inválida.')
    if isinstance(blocks,bool):raise ValueError('Blocos inválidos.')
    try:
        n=int(blocks)
        if str(blocks).strip()!=str(n):raise ValueError()
    except (TypeError,ValueError):raise ValueError('Blocos devem ser números inteiros.')
    if not 1<=n<=12:raise ValueError('Use 1 a 12 blocos de 30 minutos.')
    pos=c.execute('SELECT COALESCE(MAX(position),0)+1 FROM study_cycle_segments WHERE cycle_id=?',(cycle_id,)).fetchone()[0]
    cur=c.execute("""INSERT INTO study_cycle_segments(cycle_id,position,subject,topic,method,blocks)
        VALUES(?,?,?,?,?,?)""",(cycle_id,pos,subject,topic,method,n))
    c.commit()
    return {'ok':True,'id':cur.lastrowid}
def mark(c,segment_id,block_number,done=True):
    prepare(c)
    if not isinstance(segment_id,int) or isinstance(segment_id,bool):raise ValueError('ID inválido.')
    segment=c.execute('SELECT * FROM study_cycle_segments WHERE id=?',(segment_id,)).fetchone()
    if not segment:raise ValueError('Etapa não encontrada.')
    cycle=_cycle(c,segment['cycle_id'])
    if isinstance(block_number,bool):raise ValueError('Marcador inválido.')
    try:n=int(block_number)
    except (TypeError,ValueError):raise ValueError('Marcador inválido.')
    if not 1<=n<=segment['blocks']:raise ValueError('Marcador inexistente.')
    if not isinstance(done,bool):raise ValueError('Estado do marcador inválido.')
    round_no=cycle['round_number']
    try:
        if done:
            c.execute('INSERT OR IGNORE INTO study_cycle_marks(segment_id,round_number,block_number,marked_at) VALUES(?,?,?,?)',
                      (segment_id,round_no,n,now()))
        else:
            c.execute('DELETE FROM study_cycle_marks WHERE segment_id=? AND round_number=? AND block_number=?',
                      (segment_id,round_no,n))
        segments=c.execute('SELECT id,blocks FROM study_cycle_segments WHERE cycle_id=?',(cycle['id'],)).fetchall()
        target=sum(x['blocks'] for x in segments)
        finished=c.execute("""SELECT COUNT(*) FROM study_cycle_marks WHERE round_number=?
            AND segment_id IN(SELECT id FROM study_cycle_segments WHERE cycle_id=?)""",
            (round_no,cycle['id'])).fetchone()[0]
        completed=bool(target and finished==target)
        if completed:
            c.execute('INSERT OR IGNORE INTO study_cycle_rounds(cycle_id,round_number,finished_at) VALUES(?,?,?)',
                      (cycle['id'],round_no,now()))
            c.execute('UPDATE study_cycle_definitions SET round_number=round_number+1 WHERE id=?',(cycle['id'],))
        c.commit()
    except Exception:
        c.rollback();raise
    return {'ok':True,'round_completed':completed,'current_round':round_no+(1 if completed else 0)}
def read(c):
    prepare(c)
    cycles=all_rows(c,'SELECT * FROM study_cycle_definitions WHERE archived=0 ORDER BY id DESC')
    for cycle in cycles:
        cycle['segments']=all_rows(c,'''SELECT * FROM study_cycle_segments WHERE cycle_id=? ORDER BY position,id''',(cycle['id'],))
        count=0;total=0
        for row in cycle['segments']:
            done={x[0] for x in c.execute('SELECT block_number FROM study_cycle_marks WHERE segment_id=? AND round_number=?',
                     (row['id'],cycle['round_number'])).fetchall()}
            row['done']=sorted(done);count+=len(done);total+=row['blocks']
        cycle['marked_blocks']=count;cycle['planned_blocks']=total
        cycle['completed_rounds']=c.execute('SELECT COUNT(*) FROM study_cycle_rounds WHERE cycle_id=?',(cycle['id'],)).fetchone()[0]
    return {'cycles':cycles,'kinds':KINDS,'methods':METHODS,'block_minutes':30,
            'note':'Marcadores de ciclos são planejamento e não somam horas de estudo automaticamente.'}
