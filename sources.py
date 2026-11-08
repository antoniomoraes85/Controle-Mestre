"""Catálogo local do Estratégia e importação própria de resultados do TEC/legado.

Não faz scraping, não guarda PDFs no SQLite e não extrai enunciados protegidos.
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from core import ROOT, DB_PATH, all_rows, parse_day, norm, map_subject

PDF_ROOT = DB_PATH.parent / 'materiais' / 'estrategia'
QC_ROOT = DB_PATH.parent / 'importacoes' / 'qconcursos'
TEC_ROOT = DB_PATH.parent / 'importacoes' / 'tec'
MAX_PDF_SIZE = 150 * 1024 * 1024
MAX_CSV_SIZE = 2 * 1024 * 1024
MAX_FILES = 500
EXTERNAL_PREFIX = '@externo/'
EXTERNAL_SETTING = 'materials_external_root'


def external_root(c):
    """Pasta explícita ou irmã da aplicação; nunca exige copiar os PDFs."""
    c.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
    row = c.execute('SELECT value FROM settings WHERE key=?',(EXTERNAL_SETTING,)).fetchone()
    candidates=([Path(row[0])] if row and row[0] else []) + [
        ROOT.parent / 'MATERIAL TEÓRICO', ROOT.parent / 'MATERIAL TEORICO',
        ROOT / 'MATERIAL TEÓRICO']
    # Windows: títulos podem usar grafias/maiúsculas diferentes; verificar apenas
    # irmãos da aplicação, sem buscas amplas no computador ou acesso à nuvem.
    try:
        candidates.extend(x for x in ROOT.parent.iterdir() if x.is_dir() and norm(x.name)=='material teorico')
    except OSError:
        pass
    for p in candidates:
        if p.is_dir() and not p.is_symlink() and norm(p.name)=='material teorico':
            return p.resolve()
    return None


def set_external_root(c, path, confirm=False):
    if confirm is not True:raise ValueError('Confirmação explícita obrigatória.')
    if not isinstance(path,str) or not 3 <= len(path) <= 1000:
        raise ValueError('Informe o caminho da pasta MATERIAL TEÓRICO.')
    p=Path(path.strip().strip('"'))
    if not p.is_absolute() or not p.is_dir() or p.is_symlink() or norm(p.name)!='material teorico':
        raise ValueError('Selecione uma pasta local existente chamada MATERIAL TEÓRICO.')
    c.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
              (EXTERNAL_SETTING,str(p.resolve())))
    c.commit()
    return {'ok':True,'external_root':str(p.resolve()),'note':'Nenhum arquivo foi movido ou copiado.'}


def roots(c):
    internal=PDF_ROOT.resolve()
    external=external_root(c)
    return [('internal',internal)] + ([('external',external)] if external and external != internal else [])


def path_for_key(c, key):
    if key.startswith(EXTERNAL_PREFIX):
        root=external_root(c)
        if not root:raise ValueError('Pasta externa não está disponível; confira a unidade ou configure o caminho.')
        part=key[len(EXTERNAL_PREFIX):]
    else:
        root=PDF_ROOT.resolve()
        part=key
    dest=root / part
    if dest.is_symlink() or not dest.resolve().is_relative_to(root):
        raise ValueError('PDF fora da pasta autorizada')
    return dest


def detect_subject(folder):
    x=norm(folder)
    if 'reforma tributaria' in x and '227' in x:return 'Reforma Tributária — LC 227'
    if 'reforma tributaria' in x and ('132' in x or '214' in x):return 'Reforma Tributária — EC 132 e LC 214'
    candidate=map_subject(folder)
    return candidate if candidate in (
        'Contabilidade Geral', 'Contabilidade de Custos', 'Análise das Demonstrações Contábeis',
        'Direito Tributário','Reforma Tributária — EC 132 e LC 214','Reforma Tributária — LC 227',
        'Direito Administrativo','Direito Civil','Direito Constitucional') else ''


def detect_type(folder):
    x=norm(folder)
    if 'passo' in x:return 'Passo Estratégico'
    if 'questoes' in x:return 'Questões'
    if 'simplificad' in x:return 'Simplificado'
    return 'Teoria'


def detect_lesson(filename):
    m=re.search(r'(?<![A-Za-z])aula[\s._-]*(demo|\d{1,3})(?![0-9])',filename,re.I)
    if not m:return ''
    aula='Aula demo' if m[1].lower()=='demo' else 'Aula '+m[1].zfill(2)
    if re.search(r'(?<![A-Za-z])parte[\s._-]*(?:ii|2)(?![A-Za-z0-9])',filename,re.I):aula+=' - Parte II'
    return aula


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
      CREATE TABLE IF NOT EXISTS tec_imports (
        id INTEGER PRIMARY KEY, filename TEXT NOT NULL, digest TEXT NOT NULL UNIQUE,
        rows INTEGER NOT NULL, inserted INTEGER NOT NULL, imported_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS qc_imports (
        id INTEGER PRIMARY KEY, filename TEXT NOT NULL, digest TEXT NOT NULL UNIQUE,
        rows INTEGER NOT NULL, inserted INTEGER NOT NULL,
        imported_at TEXT NOT NULL
      );
    ''')
    bookmark_cols={r[1] for r in c.execute('PRAGMA table_info(question_bookmarks)')}
    if 'provider' not in bookmark_cols:
        c.execute("ALTER TABLE question_bookmarks ADD COLUMN provider TEXT NOT NULL DEFAULT 'Qconcursos'")
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
    """Catalogar PDFs internos e pasta externa irmã. Apenas metadados locais."""
    prepare(c)
    PDF_ROOT.mkdir(parents=True,exist_ok=True)
    targets=[]
    for category,root in roots(c):
        targets.extend((category,root,p) for p in root.rglob('*')
                       if p.is_file() and p.suffix.lower()=='.pdf')
    if len(targets)>MAX_FILES:
        raise ValueError(f'Limite de {MAX_FILES} PDFs por varredura excedido.')
    found,errors,seen=0,[],set()
    for category,root,p in sorted(targets,key=lambda x:str(x[2]).casefold()):
        if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):
            errors.append('Link ou arquivo fora da pasta: '+p.name);continue
        size=p.stat().st_size
        if not 4<=size<=MAX_PDF_SIZE:
            errors.append('PDF fora do limite: '+p.name);continue
        with p.open('rb') as f:
            if f.read(5)!=b'%PDF-':
                errors.append('Arquivo sem assinatura PDF: '+p.name);continue
        rel=p.relative_to(root).as_posix()
        key=(EXTERNAL_PREFIX if category=='external' else '')+rel
        seen.add(key)
        parts=p.relative_to(root).parts
        # Externo: "1 - Disciplina / Teoria Principal / Aula 00.pdf"
        # Interno: "Teoria / Disciplina / Aula 00.pdf" (v0.6)
        subject_folder=parts[0] if category=='external' else (parts[1] if len(parts)>=3 else '')
        auto_subject=detect_subject(subject_folder)
        material_type=detect_type(str(p.parent.relative_to(root)))
        existing=c.execute('SELECT digest,material_type,subject,lesson FROM study_materials WHERE relative_path=?',(key,)).fetchone()
        digest=hash_file(p)
        lesson=detect_lesson(p.name)
        if existing and existing['digest']==digest and existing['material_type']==material_type:
            # Migração não destrutiva: preencher campos vazios, nunca sobrescrever vínculo manual.
            if auto_subject and not existing['subject']:
                c.execute('UPDATE study_materials SET subject=? WHERE relative_path=?',(auto_subject,key))
            if lesson and not existing['lesson']:
                c.execute('UPDATE study_materials SET lesson=? WHERE relative_path=?',(lesson,key))
            c.execute("UPDATE study_materials SET status='Disponível' WHERE relative_path=?",(key,))
            found+=1;continue
        pages,title=pdf_metadata(p)
        c.execute('''INSERT INTO study_materials
          (relative_path,file_name,digest,size_bytes,pages,lesson,pdf_title,updated_at,status,material_type,subject)
          VALUES (?,?,?,?,?,?,?,?, 'Disponível',?,?)
          ON CONFLICT(relative_path) DO UPDATE SET digest=excluded.digest,
            size_bytes=excluded.size_bytes,pages=excluded.pages,
            lesson=COALESCE(NULLIF(study_materials.lesson,''),excluded.lesson),
            pdf_title=excluded.pdf_title,updated_at=excluded.updated_at,status='Disponível',
            material_type=excluded.material_type,
            subject=COALESCE(NULLIF(study_materials.subject,''),excluded.subject) ''',
          (key,p.name,digest,size,pages,lesson,title,datetime.now().isoformat(timespec='seconds'),material_type,auto_subject))
        found+=1
    for row in c.execute('SELECT id,relative_path FROM study_materials').fetchall():
        if row['relative_path'] not in seen:
            # Não apagar históricos ou vínculos já registrados.
            c.execute("UPDATE study_materials SET status='Ausente' WHERE id=?",(row['id'],))
    c.commit()
    return {'scanned':found,'errors':errors[:30],
            'roots':[{'kind':kind,'path':str(root)} for kind,root in roots(c)]}


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
        if material_type not in ('Teoria','Passo Estratégico','Questões','Simplificado'):raise ValueError('Tipo de material inválido')
        c.execute('''UPDATE study_materials SET subject=?,topic=?,course=?,lesson=?,material_type=? WHERE id=?''', (*fields,material_type, ident))
    c.commit()
    return {'ok': True}


def register_bookmark(c, title, url, subject='', topic='', provider='Qconcursos'):
    prepare(c)
    title = str(title).strip()[:180]
    u = urlsplit(str(url).strip())
    host = (u.hostname or '').lower()
    allowed={'Qconcursos':('qconcursos.com','www.qconcursos.com'),
             'TEC Concursos':('tecconcursos.com.br','www.tecconcursos.com.br')}
    if provider not in allowed or u.scheme != 'https' or host not in allowed[provider]:
        raise ValueError('Use apenas links HTTPS oficiais do '+ ('TEC' if provider=='TEC Concursos' else 'Qconcursos'))
    if not title:
        raise ValueError('Informe um título')
    if u.username or u.password:
        raise ValueError('Não inclua credenciais no link')
    c.execute('''INSERT INTO question_bookmarks(title,url,subject,topic,created_at,provider)
      VALUES (?,?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET title=excluded.title,
      subject=excluded.subject,topic=excluded.topic''',
      (title, url.strip()[:2000], str(subject).strip()[:120], str(topic).strip()[:180],
       datetime.now().isoformat(timespec='seconds'),provider))
    c.commit()
    return {'ok': True}


def list_bookmarks(c, provider='Qconcursos'):
    prepare(c)
    return all_rows(c, '''SELECT id,title,url,subject,topic FROM question_bookmarks
        WHERE provider=? ORDER BY id DESC LIMIT 300''',(provider,))


def register_tec_bookmark(c,title,url,subject='',topic=''):
    return register_bookmark(c,title,url,subject,topic,provider='TEC Concursos')


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

def parse_results_csv(blob: bytes, provider='Qconcursos'):
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
            accepted=('tecconcursos.com.br','www.tecconcursos.com.br') if provider=='TEC Concursos' else ('qconcursos.com','www.qconcursos.com')
            if urlsplit(url).scheme != 'https' or h not in accepted:
                raise ValueError(f'Linha {i}: URL deve ser do {provider}')
        rows.append(dict(day=day, subject=subject, topic=get('topic')[:180],
                         total=total, correct=correct, bank=get('bank')[:80],
                         reference_url=url[:2000], external_id=get('external_id')[:140], line=i))
    if not rows:
        raise ValueError('CSV sem resultados válidos')
    return rows


def _csv_path(file_name: str, provider='Qconcursos'):
    folder=TEC_ROOT if provider=='TEC Concursos' else QC_ROOT
    folder.mkdir(parents=True,exist_ok=True)
    if not re.fullmatch(r'[\w .()\-]{1,140}\.csv', file_name, re.UNICODE) or file_name.startswith('.'):
        raise ValueError('Nome do arquivo CSV inválido')
    path = folder / file_name
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(folder.resolve()):
        raise ValueError('Arquivo CSV não localizado na pasta permitida')
    return path


def list_csv_files(provider='Qconcursos'):
    folder=TEC_ROOT if provider=='TEC Concursos' else QC_ROOT
    folder.mkdir(parents=True, exist_ok=True)
    return [p.name for p in sorted(folder.glob('*.csv')) if p.is_file() and not p.is_symlink()][:100]


def preview_csv(c, file_name, provider='Qconcursos'):
    prepare(c)
    p = _csv_path(str(file_name),provider)
    blob = p.read_bytes()
    rows = parse_results_csv(blob,provider)
    digest = hashlib.sha256(blob).hexdigest()
    table = 'tec_imports' if provider=='TEC Concursos' else 'qc_imports'
    old = c.execute('SELECT 1 FROM '+table+' WHERE digest=?',(digest,)).fetchone()
    return {'file_name':p.name,'rows':len(rows),'questions':sum(x['total'] for x in rows),
            'correct':sum(x['correct'] for x in rows),'already_imported':bool(old),
            'sample':rows[:5]}


def import_csv(c, file_name, provider='Qconcursos'):
    prepare(c)
    p = _csv_path(str(file_name),provider)
    blob = p.read_bytes()
    rows = parse_results_csv(blob,provider)
    digest = hashlib.sha256(blob).hexdigest()
    stamp = datetime.now().isoformat(timespec='seconds')
    table='tec_imports' if provider=='TEC Concursos' else 'qc_imports'
    if c.execute('SELECT 1 FROM '+table+' WHERE digest=?',(digest,)).fetchone():
        return {'rows':len(rows),'inserted':0,'skipped':len(rows),'already_imported':True}
    added = 0
    try:
        # All-or-nothing transaction: never import half a file on failure.
        c.execute('BEGIN IMMEDIATE')
        for item in rows:
            key = item['external_id'] or f"{digest}:{item['line']}"
            fingerprint = ('tec:' if provider=='TEC Concursos' else 'qc:') + hashlib.sha256(key.encode()).hexdigest()
            existing = c.execute('SELECT 1 FROM questions WHERE fingerprint=?',(fingerprint,)).fetchone()
            if existing: continue
            c.execute('INSERT OR IGNORE INTO subjects(name,weight,area) VALUES(?,?,?)',(item['subject'],4,'Outros'))
            cur = c.execute('''INSERT INTO questions(day,subject,topic,bank,platform,total,correct,
                         error_type,notes,source,fingerprint) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                (item['day'],item['subject'],item['topic'],item['bank'],provider,
                 item['total'],item['correct'],'',item['reference_url'],
                 'tec-user-csv' if provider=='TEC Concursos' else 'qconcursos-user-csv',fingerprint))
            added += cur.rowcount
        c.execute('INSERT INTO '+table+'(filename,digest,rows,inserted,imported_at) VALUES(?,?,?,?,?)',
                  (p.name,digest,len(rows),added,stamp))
        c.commit()
    except Exception:
        c.rollback()
        raise
    return {'rows':len(rows),'inserted':added,'skipped':len(rows)-added,'already_imported':False}


def status(c):
    from lesson_question_links import list_links
    from lesson_catalog import status as lesson_status
    return {'materials':list_materials(c),
            'lesson_links':list_links(c),
            'bookmarks':list_bookmarks(c),  # legado Qconcursos preservado
            'tec_bookmarks':list_bookmarks(c,'TEC Concursos'),
            'csv_files':list_csv_files(),  # legado Qconcursos preservado
            'tec_csv_files':list_csv_files('TEC Concursos'),
            'expected_external_path':str(ROOT.parent / 'MATERIAL TEÓRICO'),
            'roots':[{'kind':kind,'path':str(root)} for kind,root in roots(c)],
            'catalog':lesson_status(c)}


def path_for_material(c,ident):
    """Abertura local somente por ID e path sob raiz privada; nunca por caminho HTTP arbitrario."""
    prepare(c)
    if isinstance(ident,bool) or not isinstance(ident,int):raise ValueError('ID de PDF inválido')
    row=c.execute("SELECT relative_path,status FROM study_materials WHERE id=?",(ident,)).fetchone()
    if not row or row['status']!='Disponível':raise ValueError('PDF não encontrado')
    target=path_for_key(c,row['relative_path'])
    if not target.is_file():
        raise ValueError('Caminho de PDF inválido')
    if target.stat().st_size>MAX_PDF_SIZE:
        raise ValueError('Arquivo inválido')
    with target.open('rb') as check:
        if check.read(5)!=b'%PDF-':raise ValueError('Arquivo inválido')
    return target