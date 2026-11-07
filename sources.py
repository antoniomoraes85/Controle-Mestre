"""Catálogo local de materiais próprios e ponte autorizada para resultados Qconcursos.

Não faz scraping, não guarda PDFs no SQLite e não extrai enunciados protegidos.
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from core import ROOT, all_rows, parse_day, norm, map_subject

PDF_ROOT = ROOT / 'dados' / 'materiais' / 'estrategia'
QC_ROOT = ROOT / 'dados' / 'importacoes' / 'qconcursos'
MAX_PDF_SIZE = 150 * 1024 * 1024
MAX_CSV_SIZE = 2 * 1024 * 1024
MAX_FILES = 500


def prepare(c):
    c.executescript('''
      CREATE TABLE IF NOT EXISTS study_materials (
        id INTEGER PRIMARY KEY, provider TEXT NOT NULL DEFAULT 'Estratégia',
        relative_path TEXT NOT NULL UNIQUE, file_name TEXT NOT NULL,
        digest TEXT NOT NULL, size_bytes INTEGER NOT NULL,
        pages INTEGER, course TEXT NOT NULL DEFAULT '',
        subject TEXT NOT NULL DEFAULT '', topic TEXT NOT NULL DEFAULT '',
        lesson TEXT NOT NULL DEFAULT '', pdf_title TEXT NOT NULL DEFAULT '',
        updated_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Disponível'
      );
      CREATE TABLE IF NOT EXISTS question_bookmarks (
        id INTEGER PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL UNIQUE,
        subject TEXT NOT NULL DEFAULT '',topic TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS qc_imports (
        id INTEGER PRIMARY KEY, filename TEXT NOT NULL, digest TEXT NOT NULL UNIQUE,
        rows INTEGER NOT NULL, inserted INTEGER NOT NULL,
        imported_at TEXT NOT NULL
      );
    ''')
    cols={r[1] for r in c.execute('PRAGMA table_info(study_materials)')}
    if 'material_type' not in cols:
        c.execute("ALTER TABLE study_materials ADD COLUMN material_type TEXT NOT NULL DEFAULT 'Teoria'")


def pdf_metadata(path: Path):
    """Metadata only, never persistent full text. Optional external package."""
    try:
        import fitz
        with fitz.open(path) as pdf:
            if pdf.needs_pass:
                return None, ''
            return pdf.page_count, (pdf.metadata or {}).get('title', '')[:180]
    except Exception:  # optional dependency or malformed/encrypted PDF: keep catalog usable
        return None, ''


def hash_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for buf in iter(lambda: f.read(1024 * 1024), b''):
            h.update(buf)
    return h.hexdigest()


def scan_pdfs(c):
    """Index only PDF files under a fixed private directory; never copy bytes."""
    prepare(c)
    PDF_ROOT.mkdir(parents=True, exist_ok=True)
    files = sorted(PDF_ROOT.rglob('*.pdf'))
    if len(files) > MAX_FILES:
        raise ValueError(f'Limite de {MAX_FILES} PDFs por varredura excedido.')
    found, errors = 0, []
    for p in files:
        if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(PDF_ROOT.resolve()):
            errors.append(f'Arquivo inválido/atalho: {p.name}')
            continue
        size = p.stat().st_size
        if not (4 <= size <= MAX_PDF_SIZE):
            errors.append(f'Arquivo fora do limite: {p.name}')
            continue
        with p.open('rb') as file:
            if file.read(5) != b'%PDF-':
                errors.append(f'Não é PDF válido: {p.name}')
                continue
        key = p.relative_to(PDF_ROOT).as_posix()
        folder=norm(str(Path(key).parent))
        material_type='Passo Estratégico' if 'passo' in folder else 'Teoria'
        rel_parts=Path(key).parts
        subject_folder=rel_parts[1] if len(rel_parts)>=3 else ''
        folder_norm=norm(subject_folder)
        if 'reforma tributaria' in folder_norm and '227' in folder_norm:
            auto_subject='Reforma Tributária — LC 227'
        elif 'reforma tributaria' in folder_norm and ('132' in folder_norm or '214' in folder_norm):
            auto_subject='Reforma Tributária — EC 132 e LC 214'
        else:
            auto_subject=map_subject(subject_folder) if subject_folder else ''
        if auto_subject and not c.execute('SELECT 1 FROM subjects WHERE name=?',(auto_subject,)).fetchone():
            auto_subject=''
        existing = c.execute('SELECT digest,material_type,subject FROM study_materials WHERE relative_path=?', (key,)).fetchone()
        digest = hash_file(p)
        if existing and existing[0] == digest and existing[1]==material_type:
            if not existing[2] and auto_subject:
                c.execute('UPDATE study_materials SET subject=? WHERE relative_path=?',(auto_subject,key))
            found += 1
            continue
        pages, title = pdf_metadata(p)
        guess = re.search(r'(?:aula)[-_\s]*(\d{1,3})', p.name, re.IGNORECASE)
        lesson = ('Aula ' + guess.group(1).zfill(2)) if guess else ''
        c.execute('''INSERT INTO study_materials
          (relative_path,file_name,digest,size_bytes,pages,lesson,pdf_title,updated_at,status,material_type,subject)
          VALUES (?,?,?,?,?,?,?,?, 'Disponível',?,?)
          ON CONFLICT(relative_path) DO UPDATE SET digest=excluded.digest,
            size_bytes=excluded.size_bytes,pages=excluded.pages,
            pdf_title=excluded.pdf_title,updated_at=excluded.updated_at,status='Disponível',
            material_type=excluded.material_type,
            subject=COALESCE(NULLIF(study_materials.subject,''),excluded.subject) ''',
          (key, p.name, digest, size, pages, lesson, title, datetime.now().isoformat(timespec='seconds'),material_type,auto_subject))
        found += 1
    known = c.execute('SELECT id,relative_path FROM study_materials').fetchall()
    for row in known:
        path = PDF_ROOT / row['relative_path']
        if not path.is_file():
            c.execute("UPDATE study_materials SET status='Ausente' WHERE id=?", (row['id'],))
    c.commit()
    return {'scanned': found, 'errors': errors[:30]}


def list_materials(c):
    prepare(c)
    return all_rows(c, '''SELECT id,relative_path,file_name,size_bytes,pages,course,subject,
               topic,lesson,pdf_title,status,updated_at,material_type FROM study_materials
               ORDER BY status,subject,lesson,file_name LIMIT 600''')


def assign_material(c, ident, subject='', topic='', course='', lesson='', material_type=None):
    prepare(c)
    if not isinstance(ident, int) or isinstance(ident, bool):
        raise ValueError('Identificador de material inválido')
    fields = [str(x or '').strip()[:180] for x in (subject, topic, course, lesson)]
    row = c.execute('SELECT 1 FROM study_materials WHERE id=?', (ident,)).fetchone()
    if not row:
        raise ValueError('PDF não cadastrado')
    if material_type is None:
        c.execute('''UPDATE study_materials SET subject=?,topic=?,course=?,lesson=? WHERE id=?''', (*fields, ident))
    else:
        if material_type not in ('Teoria','Passo Estratégico'):raise ValueError('Tipo de material inválido')
        c.execute('''UPDATE study_materials SET subject=?,topic=?,course=?,lesson=?,material_type=? WHERE id=?''', (*fields,material_type, ident))
    c.commit()
    return {'ok': True}


def register_bookmark(c, title, url, subject='', topic=''):
    prepare(c)
    title = str(title).strip()[:180]
    u = urlsplit(str(url).strip())
    host = (u.hostname or '').lower()
    if u.scheme != 'https' or host not in ('qconcursos.com', 'www.qconcursos.com'):
        raise ValueError('Use apenas links HTTPS oficiais do qconcursos.com')
    if not title:
        raise ValueError('Informe um título')
    if u.username or u.password:
        raise ValueError('Não inclua credenciais no link')
    c.execute('''INSERT INTO question_bookmarks(title,url,subject,topic,created_at)
      VALUES (?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET title=excluded.title,
      subject=excluded.subject,topic=excluded.topic''',
      (title, url.strip()[:2000], str(subject).strip()[:120], str(topic).strip()[:180],datetime.now().isoformat(timespec='seconds')))
    c.commit()
    return {'ok': True}


def list_bookmarks(c):
    prepare(c)
    return all_rows(c, 'SELECT id,title,url,subject,topic FROM question_bookmarks ORDER BY id DESC LIMIT 300')


_ALIASES = {
    'day': ('data', 'dia', 'day'),
    'subject': ('disciplina', 'materia', 'matéria', 'subject'),
    'topic': ('assunto', 'tema', 'topic'),
    'total': ('total', 'questoes', 'questões', 'resolvidas'),
    'correct': ('acertos', 'corretas', 'correct'),
    'bank': ('banca', 'bank'),
    'reference_url': ('link', 'url', 'caderno'),
    'external_id': ('id', 'codigo', 'código', 'external_id'),
}

def parse_results_csv(blob: bytes):
    """Format is a user-created CSV of *results*, NOT a native QC export claim."""
    if not blob or len(blob) > MAX_CSV_SIZE:
        raise ValueError('CSV vazio ou superior a 2 MB')
    try:
        text = blob.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ValueError('Salve o CSV como UTF-8') from None
    sample = text[:2048]
    delimiter = ';' if sample.count(';') >= sample.count(',') else ','
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise ValueError('CSV sem cabeçalho')
    def clean(s):
        return re.sub(r'[^a-z0-9]', '', s.lower().translate(str.maketrans('áàâãéêíóôõúç', 'aaaaeeiooouc')))
    columns = {clean(x): x for x in reader.fieldnames if x}
    picks = {k: next((columns.get(clean(a)) for a in aliases if clean(a) in columns), None)
             for k, aliases in _ALIASES.items()}
    if any(not picks[x] for x in ('day','subject','total','correct')):
        raise ValueError('Colunas obrigatórias: data, disciplina, total, acertos')
    rows = []
    for i, obj in enumerate(reader, start=2):
        if i > 1002:
            raise ValueError('Máximo de 1000 resultados por CSV')
        get = lambda key: str(obj.get(picks[key], '') or '').strip() if picks[key] else ''
        if not any(obj.values()): continue
        day = parse_day(get('day'))
        subject = get('subject')[:120]
        try:
            total = int(get('total')); correct = int(get('correct'))
        except ValueError:
            raise ValueError(f'Linha {i}: total e acertos devem ser inteiros') from None
        if not day or not subject or total < 1 or correct < 0 or correct > total or total > 1000:
            raise ValueError(f'Linha {i}: data, disciplina ou contagem inválida')
        url = get('reference_url')
        if url:
            h=(urlsplit(url).hostname or '').lower()
            if urlsplit(url).scheme != 'https' or h not in ('qconcursos.com','www.qconcursos.com'):
                raise ValueError(f'Linha {i}: URL deve ser do Qconcursos')
        rows.append(dict(day=day, subject=subject, topic=get('topic')[:180],
                         total=total, correct=correct, bank=get('bank')[:80],
                         reference_url=url[:2000], external_id=get('external_id')[:140], line=i))
    if not rows:
        raise ValueError('CSV sem resultados válidos')
    return rows


def _csv_path(file_name: str):
    QC_ROOT.mkdir(parents=True,exist_ok=True)
    if not re.fullmatch(r'[\w .()\-]{1,140}\.csv', file_name, re.UNICODE) or file_name.startswith('.'):
        raise ValueError('Nome do arquivo CSV inválido')
    path = QC_ROOT / file_name
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(QC_ROOT.resolve()):
        raise ValueError('Arquivo CSV não localizado na pasta permitida')
    return path


def list_csv_files():
    QC_ROOT.mkdir(parents=True, exist_ok=True)
    return [p.name for p in sorted(QC_ROOT.glob('*.csv')) if p.is_file() and not p.is_symlink()][:100]


def preview_csv(c, file_name):
    prepare(c)
    p = _csv_path(str(file_name))
    blob = p.read_bytes()
    rows = parse_results_csv(blob)
    digest = hashlib.sha256(blob).hexdigest()
    old = c.execute('SELECT 1 FROM qc_imports WHERE digest=?',(digest,)).fetchone()
    return {'file_name':p.name,'rows':len(rows),'questions':sum(x['total'] for x in rows),
            'correct':sum(x['correct'] for x in rows),'already_imported':bool(old),
            'sample':rows[:5]}


def import_csv(c, file_name):
    prepare(c)
    p = _csv_path(str(file_name))
    blob = p.read_bytes()
    rows = parse_results_csv(blob)
    digest = hashlib.sha256(blob).hexdigest()
    stamp = datetime.now().isoformat(timespec='seconds')
    if c.execute('SELECT 1 FROM qc_imports WHERE digest=?',(digest,)).fetchone():
        return {'rows':len(rows),'inserted':0,'skipped':len(rows),'already_imported':True}
    added = 0
    try:
        # All-or-nothing transaction: never import half a file on failure.
        c.execute('BEGIN IMMEDIATE')
        for item in rows:
            key = item['external_id'] or f"{digest}:{item['line']}"
            fingerprint = 'qc:' + hashlib.sha256(key.encode()).hexdigest()
            existing = c.execute('SELECT 1 FROM questions WHERE fingerprint=?',(fingerprint,)).fetchone()
            if existing: continue
            c.execute('INSERT OR IGNORE INTO subjects(name,weight,area) VALUES(?,?,?)',(item['subject'],4,'Outros'))
            cur = c.execute('''INSERT INTO questions(day,subject,topic,bank,platform,total,correct,
                         error_type,notes,source,fingerprint) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                (item['day'],item['subject'],item['topic'],item['bank'],'Qconcursos',
                 item['total'],item['correct'],'',item['reference_url'],'qconcursos-user-csv',fingerprint))
            added += cur.rowcount
        c.execute('INSERT INTO qc_imports(filename,digest,rows,inserted,imported_at) VALUES(?,?,?,?,?)',
                  (p.name,digest,len(rows),added,stamp))
        c.commit()
    except Exception:
        c.rollback()
        raise
    return {'rows':len(rows),'inserted':added,'skipped':len(rows)-added,'already_imported':False}


def status(c):
    return {'materials':list_materials(c),'bookmarks':list_bookmarks(c),
            'csv_files':list_csv_files()}


def path_for_material(c,ident):
    """Abertura local somente por ID e path sob raiz privada; nunca por caminho HTTP arbitrario."""
    prepare(c)
    if isinstance(ident,bool) or not isinstance(ident,int):raise ValueError('ID de PDF inválido')
    row=c.execute("SELECT relative_path,status FROM study_materials WHERE id=?",(ident,)).fetchone()
    if not row or row['status']!='Disponível':raise ValueError('PDF não encontrado')
    target=PDF_ROOT / row['relative_path']
    if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(PDF_ROOT.resolve()):
        raise ValueError('Caminho de PDF inválido')
    if target.stat().st_size>MAX_PDF_SIZE:
        raise ValueError('Arquivo inválido')
    with target.open('rb') as check:
        if check.read(5)!=b'%PDF-':raise ValueError('Arquivo inválido')
    return target