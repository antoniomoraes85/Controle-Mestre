"""CONTROLE MESTRE v0.7 (Entrega 1) — núcleo de cronogramas: Fixo e por Ciclos.

Camada ADITIVA sobre o banco existente:
  * não altera nem remove nenhuma tabela anterior (plans, fiscal_tasks, day_types...);
  * horas realizadas continuam em `sessions` (fonte única de horas líquidas),
    cada segmento com fingerprint próprio -> nenhuma hora é contada duas vezes;
  * replanejamento nunca apaga linhas: blocos mudam de dia, ficam sem dia ou
    'Cancelada'; concluídos permanecem intactos; ids/uids são estáveis;
  * prévia (somente leitura) + aplicação com confirmação, backup, transação e versão.

Escala 24x72: o plantão ocupa o dia calendário de início e o período entre inícios
é 96 h (4 dias). A disponibilidade de cada tipo de dia é CONFIGURADA pelo estudante;
nada presume que as 72 h de folga estejam livres.
Sem IA, sem scraping, sem alteração de PDFs.
"""
from __future__ import annotations
import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from core import all_rows, parse_day
from backup_manager import make_backup

SCHEMA_VERSION = 1
MODELS = ('cycle', 'fixed')
MODALITIES = ('Teoria', 'Questões de fixação', 'Passo Estratégico',
              'Revisão por questões', 'Caderno de erros')
SESSION_METHOD = {'Teoria': 'Teoria', 'Questões de fixação': 'Questões',
                  'Passo Estratégico': 'Revisão', 'Revisão por questões': 'Questões',
                  'Caderno de erros': 'Caderno de erros'}
# Ocorrências que bloqueiam o dia (disponibilidade 0) e as que definem minutos.
BLOCKING_KINDS = ('Férias', 'Viagem', 'Compromisso', 'Descanso', 'Indisponível')
OVERRIDE_KINDS = BLOCKING_KINDS + ('Plantão extra', 'Disponibilidade')
MIN_REMAINING = 10      # minutos mínimos ao retomar bloco já excedido
SEQUENCE_LIMIT = 400    # trava de segurança na geração do ciclo

# Valores iniciais EDITÁVEIS (não são regras pedagógicas).
DEFAULT_CONFIG = {
    'model': 'cycle',            # modelo inicial do titular
    'block_minutes': '30',       # duração padrão de bloco
    'shift_ref': '',             # data de início de um plantão de referência
    'shift_period_days': '4',    # 96 h entre inícios (24 h + 72 h)
    'shift_minutes': '0',        # estudo em dia de plantão (padrão: zero)
    'post_shift_minutes': '120', # dia seguinte ao plantão
    'off_minutes': '360',        # demais dias de folga
    'default_daily_minutes': '0',  # sem escala configurada
}
INT_KEYS = ('block_minutes', 'shift_period_days', 'shift_minutes',
            'post_shift_minutes', 'off_minutes', 'default_daily_minutes')


# ---------------------------------------------------------------- infraestrutura
class _Tx:
    """Transação atômica: tudo ou nada."""
    def __init__(self, c): self.c = c
    def __enter__(self):
        if self.c.in_transaction:
            self.c.commit()
        self.c.execute('BEGIN IMMEDIATE')
        return self.c
    def __exit__(self, et, ev, tb):
        if et:
            self.c.rollback()
        else:
            self.c.commit()
        return False


def _db_path(c):
    for r in c.execute('PRAGMA database_list').fetchall():
        if r[1] == 'main' and r[2]:
            return Path(r[2])
    return None


def _backup(c):
    """Backup verificado ANTES de alterar dados (ignora bancos em memória)."""
    if c.in_transaction:
        c.commit()
    path = _db_path(c)
    if not path or not path.is_file():
        return None
    return make_backup(path, path.parent / 'backups', max_copies=30, force=True)


def _day(v):
    d = parse_day(v)
    if not d:
        raise ValueError('Data inválida.')
    return d


def _monday(d):
    d = date.fromisoformat(d) if isinstance(d, str) else d
    return d - timedelta(days=d.weekday())


def migrate(c):
    """Migração aditiva e idempotente; faz backup antes de criar o esquema."""
    exists = c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='schedule_config'").fetchone()
    if exists:
        return {'created': False, 'backup': None, 'version': SCHEMA_VERSION}
    backup = _backup(c)
    with _Tx(c):
        for sql in (
            'CREATE TABLE IF NOT EXISTS schedule_config (key TEXT PRIMARY KEY, value TEXT NOT NULL)',
            '''CREATE TABLE IF NOT EXISTS schedule_cycle_items (id INTEGER PRIMARY KEY,
               position INTEGER NOT NULL, subject TEXT NOT NULL,
               modality TEXT NOT NULL DEFAULT 'Teoria', block_minutes INTEGER NOT NULL CHECK(block_minutes>0),
               blocks INTEGER NOT NULL DEFAULT 1 CHECK(blocks>0), weight REAL NOT NULL DEFAULT 1,
               active INTEGER NOT NULL DEFAULT 1, UNIQUE(subject,modality))''',
            '''CREATE TABLE IF NOT EXISTS schedule_fixed_slots (id INTEGER PRIMARY KEY,
               weekday INTEGER NOT NULL CHECK(weekday BETWEEN 0 AND 6), position INTEGER NOT NULL,
               subject TEXT NOT NULL, modality TEXT NOT NULL DEFAULT 'Teoria',
               minutes INTEGER NOT NULL CHECK(minutes>0), start_time TEXT NOT NULL DEFAULT '',
               active INTEGER NOT NULL DEFAULT 1)''',
            '''CREATE TABLE IF NOT EXISTS schedule_overrides (day TEXT PRIMARY KEY,
               kind TEXT NOT NULL, minutes INTEGER, note TEXT NOT NULL DEFAULT '')''',
            '''CREATE TABLE IF NOT EXISTS schedule_versions (id INTEGER PRIMARY KEY,
               created_at TEXT NOT NULL, model TEXT NOT NULL, range_start TEXT NOT NULL,
               range_end TEXT NOT NULL, summary TEXT NOT NULL, backup TEXT)''',
            '''CREATE TABLE IF NOT EXISTS schedule_blocks (id INTEGER PRIMARY KEY,
               uid TEXT NOT NULL UNIQUE, model TEXT NOT NULL, run INTEGER, item_id INTEGER,
               slot_id INTEGER, subject TEXT NOT NULL, modality TEXT NOT NULL,
               day TEXT, seq INTEGER NOT NULL DEFAULT 0, minutes INTEGER NOT NULL,
               actual_minutes INTEGER NOT NULL DEFAULT 0, segments INTEGER NOT NULL DEFAULT 0,
               status TEXT NOT NULL DEFAULT 'Pendente', started_at TEXT, completed_at TEXT,
               version_id INTEGER, notes TEXT NOT NULL DEFAULT '')''',
            'CREATE INDEX IF NOT EXISTS idx_schedule_blocks_day ON schedule_blocks(model,day,status)',
        ):
            c.execute(sql)
        for k, v in DEFAULT_CONFIG.items():
            c.execute('INSERT OR IGNORE INTO schedule_config(key,value) VALUES(?,?)', (k, v))
        c.execute("INSERT OR IGNORE INTO schedule_config(key,value) VALUES('schema_version',?)", (str(SCHEMA_VERSION),))
    return {'created': True, 'backup': str(backup) if backup else None, 'version': SCHEMA_VERSION}


# ---------------------------------------------------------------- configuração
def get_config(c):
    migrate(c)
    cfg = dict(DEFAULT_CONFIG)
    cfg.update({r['key']: r['value'] for r in all_rows(c, 'SELECT key,value FROM schedule_config')})
    out = dict(cfg)
    for k in INT_KEYS:
        out[k] = int(cfg[k])
    out['weekly_target_min'] = int(c.execute("SELECT value FROM settings WHERE key='weekly_target_min'").fetchone()[0])
    out['max_plantao_min'] = int(c.execute("SELECT value FROM settings WHERE key='max_plantao_min'").fetchone()[0])
    return out


def set_config(c, **values):
    """Altera configuração. Trocar de modelo NÃO apaga nem reescreve histórico."""
    migrate(c)
    clean = {}
    for k, v in values.items():
        if k == 'model':
            if v not in MODELS:
                raise ValueError('Modelo inválido: use "cycle" ou "fixed".')
            clean[k] = v
        elif k == 'shift_ref':
            clean[k] = _day(v) if v else ''
        elif k in INT_KEYS:
            n = int(v)
            limit = 1440 if k != 'shift_period_days' else 30
            low = 1 if k in ('block_minutes', 'shift_period_days') else 0
            if not low <= n <= limit:
                raise ValueError(f'Valor fora do intervalo em {k}.')
            if k == 'shift_period_days' and n < 2:
                raise ValueError('O intervalo entre plantões deve ter ao menos 2 dias.')
            clean[k] = str(n)
        else:
            raise ValueError(f'Configuração desconhecida: {k}')
    with _Tx(c):
        for k, v in clean.items():
            c.execute('INSERT INTO schedule_config(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (k, v))
    return get_config(c)


def configure_shift(c, ref_date, shift_minutes=0, post_shift_minutes=None, off_minutes=None, period_days=4):
    """Escala recorrente (24x72 por padrão). Datas futuras e passadas são projetadas."""
    values = {'shift_ref': ref_date, 'shift_period_days': period_days, 'shift_minutes': shift_minutes}
    if post_shift_minutes is not None:
        values['post_shift_minutes'] = post_shift_minutes
    if off_minutes is not None:
        values['off_minutes'] = off_minutes
    return set_config(c, **values)


# ---------------------------------------------------------------- disponibilidade
def set_override(c, day, kind, minutes=None, note=''):
    """Férias, viagem, compromisso, descanso, plantão extra ou disponibilidade pontual."""
    migrate(c)
    if kind not in OVERRIDE_KINDS:
        raise ValueError('Tipo de ocorrência inválido: ' + ', '.join(OVERRIDE_KINDS))
    if kind == 'Disponibilidade' and minutes is None:
        raise ValueError('Informe os minutos disponíveis.')
    if minutes is not None and not 0 <= int(minutes) <= 1440:
        raise ValueError('Minutos fora do intervalo.')
    with _Tx(c):
        c.execute('''INSERT INTO schedule_overrides(day,kind,minutes,note) VALUES(?,?,?,?)
           ON CONFLICT(day) DO UPDATE SET kind=excluded.kind,minutes=excluded.minutes,note=excluded.note''',
                  (_day(day), kind, None if minutes is None else int(minutes), str(note)[:200]))


def set_override_range(c, start, end, kind, minutes=None, note=''):
    a, b = date.fromisoformat(_day(start)), date.fromisoformat(_day(end))
    if b < a or (b - a).days > 366:
        raise ValueError('Intervalo inválido.')
    for i in range((b - a).days + 1):
        set_override(c, a + timedelta(days=i), kind, minutes, note)


def clear_override(c, day):
    migrate(c)
    with _Tx(c):
        c.execute('DELETE FROM schedule_overrides WHERE day=?', (_day(day),))


def shift_kind(cfg, day):
    """Tipo do dia na escala: Plantão, Pós-plantão ou Folga (None sem escala)."""
    if not cfg['shift_ref']:
        return None
    off = (date.fromisoformat(day) - date.fromisoformat(cfg['shift_ref'])).days % cfg['shift_period_days']
    return 'Plantão' if off == 0 else ('Pós-plantão' if off == 1 else 'Folga')


def availability_range(c, start, end, cfg=None):
    """Disponibilidade líquida por dia: ocorrência pontual > escala > padrão diário."""
    cfg = cfg or get_config(c)
    a, b = date.fromisoformat(_day(start)), date.fromisoformat(_day(end))
    over = {r['day']: r for r in all_rows(c, 'SELECT * FROM schedule_overrides WHERE day BETWEEN ? AND ?',
                                          (a.isoformat(), b.isoformat()))}
    out = []
    for i in range((b - a).days + 1):
        day = (a + timedelta(days=i)).isoformat()
        o = over.get(day)
        base = shift_kind(cfg, day)
        if o and o['kind'] in BLOCKING_KINDS:
            item = {'kind': o['kind'], 'minutes': 0, 'blocked': True, 'source': 'override', 'note': o['note']}
        elif o and o['kind'] == 'Plantão extra':
            item = {'kind': 'Plantão', 'minutes': min(cfg['shift_minutes'], cfg['max_plantao_min']),
                    'blocked': False, 'source': 'override', 'note': o['note']}
        elif o:
            item = {'kind': 'Disponibilidade', 'minutes': int(o['minutes']), 'blocked': False,
                    'source': 'override', 'note': o['note']}
        elif base:
            m = {'Plantão': min(cfg['shift_minutes'], cfg['max_plantao_min']),
                 'Pós-plantão': cfg['post_shift_minutes'], 'Folga': cfg['off_minutes']}[base]
            item = {'kind': base, 'minutes': m, 'blocked': False, 'source': 'scale', 'note': ''}
        else:
            item = {'kind': 'Livre', 'minutes': cfg['default_daily_minutes'], 'blocked': False,
                    'source': 'default', 'note': ''}
        out.append({'day': day, **item})
    return out


def availability(c, day, cfg=None):
    return availability_range(c, day, day, cfg)[0]


# ---------------------------------------------------------------- ciclo: itens
def _next_position(c, table):
    return int(c.execute(f'SELECT COALESCE(MAX(position),0)+1 FROM {table}').fetchone()[0])


def add_cycle_item(c, subject, modality='Teoria', block_minutes=None, blocks=1, weight=1, position=None):
    """Inclui disciplina/modalidade no ciclo; item já existente é reativado (sem duplicar)."""
    migrate(c)
    subject = str(subject).strip()
    if not subject:
        raise ValueError('Disciplina obrigatória.')
    if modality not in MODALITIES:
        raise ValueError('Modalidade inválida.')
    minutes = int(block_minutes or get_config(c)['block_minutes'])
    if minutes <= 0 or int(blocks) <= 0 or float(weight) <= 0:
        raise ValueError('Minutos, blocos e peso devem ser positivos.')
    with _Tx(c):
        row = c.execute('SELECT id,active FROM schedule_cycle_items WHERE subject=? AND modality=?', (subject, modality)).fetchone()
        if row:
            if row['active']:
                raise ValueError('Esta disciplina/modalidade já integra o ciclo.')
            c.execute('UPDATE schedule_cycle_items SET active=1,block_minutes=?,blocks=?,weight=?,position=? WHERE id=?',
                      (minutes, int(blocks), float(weight), position or _next_position(c, 'schedule_cycle_items'), row['id']))
            return row['id']
        cur = c.execute('''INSERT INTO schedule_cycle_items(position,subject,modality,block_minutes,blocks,weight)
                           VALUES(?,?,?,?,?,?)''', (position or _next_position(c, 'schedule_cycle_items'),
                                                    subject, modality, minutes, int(blocks), float(weight)))
        return cur.lastrowid


def update_cycle_item(c, item_id, **fields):
    """Edita bloco/peso/minutos/ativo. Nunca exclui: desativar preserva o histórico."""
    migrate(c)
    allowed = {'block_minutes', 'blocks', 'weight', 'active', 'modality'}
    if not fields or set(fields) - allowed:
        raise ValueError('Campos permitidos: ' + ', '.join(sorted(allowed)))
    if 'modality' in fields and fields['modality'] not in MODALITIES:
        raise ValueError('Modalidade inválida.')
    for k in ('block_minutes', 'blocks'):
        if k in fields and int(fields[k]) <= 0:
            raise ValueError(f'{k} deve ser positivo.')
    if 'weight' in fields and float(fields['weight']) <= 0:
        raise ValueError('Peso deve ser positivo.')
    if 'active' in fields:
        fields['active'] = 1 if fields['active'] else 0
    with _Tx(c):
        if not c.execute('SELECT 1 FROM schedule_cycle_items WHERE id=?', (item_id,)).fetchone():
            raise ValueError('Item de ciclo inexistente.')
        for k, v in fields.items():
            c.execute(f'UPDATE schedule_cycle_items SET {k}=? WHERE id=?', (v, item_id))


def reorder_cycle(c, item_ids):
    """Nova ordem do ciclo; itens omitidos seguem ao final. Progresso e histórico intactos."""
    migrate(c)
    ids = [int(i) for i in item_ids]
    if len(set(ids)) != len(ids):
        raise ValueError('Ids repetidos.')
    with _Tx(c):
        existing = [r['id'] for r in c.execute('SELECT id FROM schedule_cycle_items ORDER BY position,id').fetchall()]
        if set(ids) - set(existing):
            raise ValueError('Item de ciclo inexistente.')
        for pos, i in enumerate(ids + [x for x in existing if x not in ids], 1):
            c.execute('UPDATE schedule_cycle_items SET position=? WHERE id=?', (pos, i))


def list_cycle_items(c, only_active=False):
    migrate(c)
    return all_rows(c, 'SELECT * FROM schedule_cycle_items' + (' WHERE active=1' if only_active else '') + ' ORDER BY position,id')


# ---------------------------------------------------------------- fixo: slots
def add_fixed_slot(c, weekday, subject, minutes, modality='Teoria', start_time='', position=None):
    migrate(c)
    if int(weekday) not in range(7):
        raise ValueError('Dia da semana: 0 (segunda) a 6 (domingo).')
    if modality not in MODALITIES:
        raise ValueError('Modalidade inválida.')
    if int(minutes) <= 0 or not str(subject).strip():
        raise ValueError('Disciplina e minutos positivos são obrigatórios.')
    if start_time and not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', start_time):
        raise ValueError('Horário no formato HH:MM.')
    with _Tx(c):
        pos = position or int(c.execute('SELECT COALESCE(MAX(position),0)+1 FROM schedule_fixed_slots WHERE weekday=?', (int(weekday),)).fetchone()[0])
        return c.execute('''INSERT INTO schedule_fixed_slots(weekday,position,subject,modality,minutes,start_time)
                            VALUES(?,?,?,?,?,?)''', (int(weekday), pos, str(subject).strip(), modality, int(minutes), start_time)).lastrowid


def update_fixed_slot(c, slot_id, **fields):
    migrate(c)
    allowed = {'weekday', 'position', 'subject', 'modality', 'minutes', 'start_time', 'active'}
    if not fields or set(fields) - allowed:
        raise ValueError('Campos permitidos: ' + ', '.join(sorted(allowed)))
    if 'weekday' in fields and int(fields['weekday']) not in range(7):
        raise ValueError('Dia da semana inválido.')
    if 'minutes' in fields and int(fields['minutes']) <= 0:
        raise ValueError('Minutos devem ser positivos.')
    if 'modality' in fields and fields['modality'] not in MODALITIES:
        raise ValueError('Modalidade inválida.')
    if fields.get('start_time') and not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', fields['start_time']):
        raise ValueError('Horário no formato HH:MM.')
    if 'active' in fields:
        fields['active'] = 1 if fields['active'] else 0
    with _Tx(c):
        if not c.execute('SELECT 1 FROM schedule_fixed_slots WHERE id=?', (slot_id,)).fetchone():
            raise ValueError('Slot inexistente.')
        for k, v in fields.items():
            c.execute(f'UPDATE schedule_fixed_slots SET {k}=? WHERE id=?', (v, slot_id))


def list_fixed_slots(c, only_active=False):
    migrate(c)
    return all_rows(c, 'SELECT * FROM schedule_fixed_slots' + (' WHERE active=1' if only_active else '') +
                    ' ORDER BY weekday,position,id')


# ---------------------------------------------------------------- projeção
def _blocks(c, model=None):
    sql = 'SELECT * FROM schedule_blocks' + (' WHERE model=?' if model else '')
    return {r['uid']: r for r in all_rows(c, sql, (model,) if model else ())}


def _uid_cycle(run, item_id, k):
    return f'c:{run}:{item_id}:{k}'


def _cycle_sequence(c):
    """Sequência contínua e determinística de blocos ainda não concluídos.

    Ordem: 1) blocos interrompidos (retomada); 2) ciclo atual na ordem configurada;
    3) ciclos seguintes. O avanço depende SOMENTE de blocos 'Concluída' — nunca do
    calendário nem da segunda-feira."""
    items = list_cycle_items(c, only_active=True)
    rows = _blocks(c, 'cycle')
    by_item = {i['id']: i for i in list_cycle_items(c)}
    open_rows = sorted((r for r in rows.values() if r['status'] in ('Em andamento', 'Pausada')),
                       key=lambda r: (r['started_at'] or '', r['id']))
    for r in open_rows:
        yield {'uid': r['uid'], 'run': r['run'], 'item_id': r['item_id'], 'subject': r['subject'],
               'modality': r['modality'], 'minutes': max(r['minutes'] - r['actual_minutes'], MIN_REMAINING),
               'status': r['status'], 'resume': True, 'actual': r['actual_minutes']}
    if not items:
        return
    # O ciclo atual é definido SOMENTE por execução real; linhas apenas agendadas não avançam o ciclo.
    used = [r['run'] for r in rows.values() if r['status'] in ('Concluída', 'Em andamento', 'Pausada') and r['run']]
    run = max(used) if used else 1

    def finished(r):
        return all(rows.get(_uid_cycle(r, i['id'], k), {}).get('status') == 'Concluída'
                   for i in items for k in range(i['blocks']))
    while finished(run):
        run += 1
    count = 0
    while count < SEQUENCE_LIMIT:
        for i in items:
            for k in range(i['blocks']):
                uid = _uid_cycle(run, i['id'], k)
                row = rows.get(uid)
                if row and row['status'] in ('Concluída', 'Em andamento', 'Pausada'):
                    continue
                count += 1
                yield {'uid': uid, 'run': run, 'item_id': i['id'], 'subject': i['subject'],
                       'modality': i['modality'], 'minutes': i['block_minutes'],
                       'status': row['status'] if row else 'Novo', 'resume': False, 'actual': 0}
        run += 1


def next_block(c):
    """Próximo bloco do ciclo (retomada primeiro), sem gravar nada."""
    return next(_cycle_sequence(c), None)


def _sessions_by_day(c, start, end):
    return {r['day']: int(r['m']) for r in all_rows(
        c, 'SELECT day,SUM(minutes) m FROM sessions WHERE day BETWEEN ? AND ? GROUP BY day', (start, end))}


def _project_cycle(c, cfg, start, end):
    avail = availability_range(c, start, end, cfg)
    done = _sessions_by_day(c, _monday(start).isoformat(), end)
    week_done, week_plan = defaultdict(int), defaultdict(int)
    for d, m in done.items():
        week_done[_monday(d)] += m
    target = cfg['weekly_target_min']
    seq = _cycle_sequence(c)
    head, placed, warnings, n = next(seq, None), [], [], 0
    for a in avail:
        cap = max(0, a['minutes'] - done.get(a['day'], 0))
        wk = _monday(a['day'])
        while head is not None:
            need = head['minutes']
            if need > a['minutes'] and a['minutes'] > 0:
                msg = f'Bloco de {need} min excede a disponibilidade de {a["day"]} ({a["minutes"]} min).'
                if msg not in warnings:
                    warnings.append(msg)
                break
            if need > cap or need > target - week_done[wk] - week_plan[wk]:
                break
            n += 1
            placed.append({**head, 'day': a['day'], 'seq': n})
            cap -= need
            week_plan[wk] += need
            head = next(seq, None)
    return placed, avail, done, warnings


def _project_fixed(c, cfg, start, end):
    avail = availability_range(c, start, end, cfg)
    slots = list_fixed_slots(c, only_active=True)
    done = _sessions_by_day(c, start, end)
    placed, warnings = [], []
    for a in avail:
        day_slots = [s for s in slots if s['weekday'] == date.fromisoformat(a['day']).weekday()]
        if a['source'] == 'default':
            cap = sum(s['minutes'] for s in day_slots)
        else:
            cap = a['minutes']
        cap = max(0, cap - done.get(a['day'], 0)) if a['day'] >= date.today().isoformat() else cap
        used = 0
        ordered = day_slots  # já ordenados por posição; horários definem a ordem se todos informados
        if day_slots and all(s['start_time'] for s in day_slots):
            ordered = sorted(day_slots, key=lambda s: (s['start_time'], s['position'], s['id']))
        for s in ordered:
            if used + s['minutes'] > cap:
                warnings.append(f'{a["day"]}: "{s["subject"]}" ({s["minutes"]} min) não cabe na disponibilidade de {a["kind"]}.')
                continue
            used += s['minutes']
            placed.append({'uid': f'f:{a["day"]}:{s["id"]}', 'run': None, 'item_id': None, 'slot_id': s['id'],
                           'subject': s['subject'], 'modality': s['modality'], 'minutes': s['minutes'],
                           'start_time': s['start_time'], 'day': a['day'], 'seq': len(placed) + 1,
                           'status': 'Novo', 'resume': False, 'actual': 0})
    return placed, avail, done, warnings


def _week_report(c, cfg, avail, done, placed, start, end, today):
    weeks = {}
    planned = defaultdict(int)
    for p in placed:
        planned[_monday(p['day'])] += p['minutes']
    for a in avail:
        wk = _monday(a['day'])
        w = weeks.setdefault(wk, {'week_start': wk.isoformat(), 'capacity_minutes': 0, 'blocked_days': 0})
        if a['day'] >= today:
            w['capacity_minutes'] += max(0, a['minutes'] - done.get(a['day'], 0))
        w['blocked_days'] += 1 if a['blocked'] else 0
    wdone = defaultdict(int)
    for d, m in _sessions_by_day(c, min(weeks).isoformat(), end).items():
        wdone[_monday(d)] += m
    out = []
    for wk, w in sorted(weeks.items()):
        t = cfg['weekly_target_min']
        complete = wk >= date.fromisoformat(start) and wk + timedelta(days=6) <= date.fromisoformat(end)
        out.append({**w, 'target_minutes': t, 'done_minutes': wdone[wk], 'planned_minutes': planned[wk],
                    'covers_full_week': complete,
                    'availability_deficit_minutes': max(0, t - wdone[wk] - w['capacity_minutes']),
                    'unplanned_minutes': max(0, t - wdone[wk] - planned[wk])})
    return out


def preview(c, start=None, days=14, today=None, model=None):
    """Prévia SOMENTE LEITURA: mostra o que será criado, movido, mantido ou liberado."""
    cfg = get_config(c)
    model = model or cfg['model']
    if model not in MODELS:
        raise ValueError('Modelo inválido.')
    today_d = _day(today or date.today())
    first = _day(start or today_d)
    if first < today_d:
        raise ValueError('Não é possível planejar dias passados.')
    if not 1 <= int(days) <= 92:
        raise ValueError('O horizonte deve ter de 1 a 92 dias.')
    end = (date.fromisoformat(first) + timedelta(days=int(days) - 1)).isoformat()
    placed, avail, done, warnings = (_project_cycle if model == 'cycle' else _project_fixed)(c, cfg, first, end)
    existing = _blocks(c)
    created, moved, kept = [], [], []
    for p in placed:
        row = existing.get(p['uid'])
        if not row or row['status'] == 'Cancelada':
            created.append(p['uid'])
        elif row['day'] != p['day'] or (row['status'] == 'Pendente' and row['minutes'] != p['minutes']):
            moved.append(p['uid'])
        else:
            kept.append(p['uid'])
    keep_uids = {p['uid'] for p in placed}
    released = [u for u, r in existing.items() if r['status'] == 'Pendente' and r['day'] and r['day'] >= first
                and u not in keep_uids]
    if not cfg['shift_ref'] and cfg['default_daily_minutes'] == 0 and model == 'cycle':
        warnings.append('Sem escala e sem disponibilidade padrão: configure a escala ou os minutos diários.')
    if model == 'cycle' and not list_cycle_items(c, only_active=True):
        warnings.append('O ciclo não possui itens ativos.')
    for p in placed:
        p['change'] = ('novo' if p['uid'] in created else 'movido' if p['uid'] in moved else
                       'retomada' if p['resume'] else 'mantido')
    return {'mode': 'Prévia: nenhuma alteração foi gravada.', 'model': model, 'range_start': first,
            'range_end': end, 'blocks': placed, 'created': len(created), 'moved': len(moved),
            'kept': len(kept), 'released': released,
            'planned_minutes': sum(p['minutes'] for p in placed),
            'weeks': _week_report(c, cfg, avail, done, placed, first, end, today_d),
            'availability': avail, 'warnings': warnings}


def apply(c, start=None, days=14, today=None, model=None, confirm=False):
    """Aplica a prévia. Exige confirmação; backup + transação única + versão registrada.

    Nunca exclui: concluídos intactos; pendentes migram de dia, ficam sem dia ou
    'Cancelada' (fixo). Reexecutar não duplica blocos (uid determinístico)."""
    if confirm is not True:
        raise ValueError('Confirmação explícita necessária para aplicar o planejamento.')
    pv = preview(c, start, days, today, model)
    backup = _backup(c)
    model, first, end = pv['model'], pv['range_start'], pv['range_end']
    now = datetime.now().isoformat(timespec='seconds')
    with _Tx(c):
        vid = c.execute('INSERT INTO schedule_versions(created_at,model,range_start,range_end,summary,backup) VALUES(?,?,?,?,?,?)',
                        (now, model, first, end, json.dumps({k: pv[k] for k in ('created', 'moved', 'kept', 'planned_minutes')}),
                         str(backup) if backup else None)).lastrowid
        keep = set()
        for p in pv['blocks']:
            keep.add(p['uid'])
            row = c.execute('SELECT * FROM schedule_blocks WHERE uid=?', (p['uid'],)).fetchone()
            if not row:
                c.execute('''INSERT INTO schedule_blocks(uid,model,run,item_id,slot_id,subject,modality,day,seq,minutes,version_id)
                             VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                          (p['uid'], model, p['run'], p['item_id'], p.get('slot_id'), p['subject'], p['modality'],
                           p['day'], p['seq'], p['minutes'], vid))
            elif row['status'] in ('Pendente', 'Cancelada'):
                c.execute("UPDATE schedule_blocks SET day=?,seq=?,minutes=?,status='Pendente',version_id=? WHERE uid=?",
                          (p['day'], p['seq'], p['minutes'], vid, p['uid']))
            elif row['status'] in ('Em andamento', 'Pausada'):
                c.execute('UPDATE schedule_blocks SET day=?,seq=?,version_id=? WHERE uid=?', (p['day'], p['seq'], vid, p['uid']))
        # Pendentes fora da nova projeção: nunca excluídos.
        for r in c.execute("SELECT uid,model FROM schedule_blocks WHERE status='Pendente' AND day>=?", (first,)).fetchall():
            if r['uid'] in keep:
                continue
            if r['model'] == 'cycle':
                c.execute('UPDATE schedule_blocks SET day=NULL,version_id=? WHERE uid=?', (vid, r['uid']))
            elif r['model'] == 'fixed':
                c.execute("UPDATE schedule_blocks SET status='Cancelada',version_id=? WHERE uid=?", (vid, r['uid']))
    return {'mode': 'Aplicado', 'version_id': vid, 'backup': str(backup) if backup else None,
            'created': pv['created'], 'moved': pv['moved'], 'kept': pv['kept'],
            'released': len(pv['released']), 'planned_minutes': pv['planned_minutes'], 'warnings': pv['warnings']}


# ---------------------------------------------------------------- execução
def _valid_cycle_uid(c, uid):
    m = re.fullmatch(r'c:(\d+):(\d+):(\d+)', uid)
    if not m:
        return None
    run, item_id, k = map(int, m.groups())
    item = c.execute('SELECT * FROM schedule_cycle_items WHERE id=? AND active=1', (item_id,)).fetchone()
    return (run, item, k) if item and k < item['blocks'] and run >= 1 else None


def _ensure_block(c, uid):
    row = c.execute('SELECT * FROM schedule_blocks WHERE uid=?', (uid,)).fetchone()
    if row:
        return row
    v = _valid_cycle_uid(c, uid)
    if not v:
        raise ValueError('Bloco inexistente.')
    run, item, _ = v
    c.execute('''INSERT INTO schedule_blocks(uid,model,run,item_id,subject,modality,minutes)
                 VALUES(?,?,?,?,?,?,?)''', (uid, 'cycle', run, item['id'], item['subject'], item['modality'], item['block_minutes']))
    return c.execute('SELECT * FROM schedule_blocks WHERE uid=?', (uid,)).fetchone()


def _record_segment(c, row, minutes, day, note):
    """Registra horas reais em `sessions` com fingerprint único por segmento."""
    day = _day(day or date.today())
    if day > date.today().isoformat():
        raise ValueError('Data real futura não é permitida.')
    kind = availability(c, day)['kind']
    day_type = kind if kind in ('Plantão', 'Pós-plantão') else 'Livre leve'
    if day_type == 'Plantão':
        used = c.execute('SELECT COALESCE(SUM(minutes),0) FROM sessions WHERE day=?', (day,)).fetchone()[0]
        if used + minutes > int(c.execute("SELECT value FROM settings WHERE key='max_plantao_min'").fetchone()[0]):
            raise ValueError('Limite de minutos em dia de plantão excedido.')
    c.execute('''INSERT INTO sessions(day,subject,topic,method,minutes,day_type,notes,source,fingerprint,cycle)
                 VALUES(?,?,?,?,?,?,?,?,?,?)''',
              (day, row['subject'], '', SESSION_METHOD[row['modality']], minutes, day_type,
               ('Cronograma: ' + row['modality'] + (' — ' + note if note else ''))[:250], 'schedule',
               f'schedule-block:{row["uid"]}:{row["segments"] + 1}', None))


def _minutes(v):
    m = int(v)
    if not 0 <= m <= 600:
        raise ValueError('Minutos devem estar entre 0 e 600.')
    return m


def start_block(c, uid=None):
    """Inicia ou retoma um bloco. Sem uid, usa o próximo do ciclo (retomada primeiro).
    Aceita antecipar qualquer bloco válido do ciclo."""
    migrate(c)
    if uid is None:
        head = next_block(c)
        if not head:
            raise ValueError('Não há bloco disponível no ciclo.')
        uid = head['uid']
    with _Tx(c):
        row = _ensure_block(c, uid)
        if row['status'] not in ('Pendente', 'Pausada', 'Cancelada', 'Em andamento'):
            raise ValueError('Bloco já concluído.')
        if row['status'] == 'Cancelada' and not _valid_cycle_uid(c, uid):
            raise ValueError('Bloco cancelado não pode ser iniciado.')
        c.execute("UPDATE schedule_blocks SET status='Em andamento',started_at=COALESCE(started_at,?) WHERE uid=?",
                  (datetime.now().isoformat(timespec='seconds'), uid))
    return dict(c.execute('SELECT * FROM schedule_blocks WHERE uid=?', (uid,)).fetchone())


def pause_block(c, uid, minutes, day=None, note=''):
    """Interrompe: grava os minutos já estudados e mantém o bloco retomável."""
    minutes = _minutes(minutes)
    with _Tx(c):
        row = c.execute('SELECT * FROM schedule_blocks WHERE uid=?', (uid,)).fetchone()
        if not row or row['status'] != 'Em andamento':
            raise ValueError('Só é possível pausar um bloco em andamento.')
        if minutes:
            _record_segment(c, row, minutes, day, note)
        c.execute("UPDATE schedule_blocks SET status='Pausada',actual_minutes=actual_minutes+?,segments=segments+? WHERE uid=?",
                  (minutes, 1 if minutes else 0, uid))
    return dict(c.execute('SELECT * FROM schedule_blocks WHERE uid=?', (uid,)).fetchone())


def complete_block(c, uid, minutes=0, day=None, note=''):
    """Conclusão sempre explícita; exige horas reais > 0 no total. Uma única vez."""
    migrate(c)
    minutes = _minutes(minutes)
    with _Tx(c):
        row = _ensure_block(c, uid)
        if row['status'] in ('Concluída', 'Cancelada'):
            raise ValueError('Bloco já concluído ou cancelado.')
        if row['actual_minutes'] + minutes <= 0:
            raise ValueError('Informe o tempo realmente estudado; não há conclusão automática.')
        if minutes:
            _record_segment(c, row, minutes, day, note)
        c.execute("""UPDATE schedule_blocks SET status='Concluída',actual_minutes=actual_minutes+?,segments=segments+?,
                     completed_at=?,day=COALESCE(day,?) WHERE uid=?""",
                  (minutes, 1 if minutes else 0, datetime.now().isoformat(timespec='seconds'),
                   _day(day or date.today()), uid))
    return dict(c.execute('SELECT * FROM schedule_blocks WHERE uid=?', (uid,)).fetchone())


# ---------------------------------------------------------------- calendário
def calendar(c, start, end):
    """Dados para calendário semanal/mensal: escala, disponibilidade, blocos e horas feitas."""
    cfg = get_config(c)
    a, b = _day(start), _day(end)
    avail = availability_range(c, a, b, cfg)
    done = _sessions_by_day(c, a, b)
    blocks = defaultdict(list)
    for r in all_rows(c, '''SELECT uid,model,subject,modality,day,minutes,actual_minutes,status FROM schedule_blocks
                            WHERE day BETWEEN ? AND ? AND status!='Cancelada' AND model=? ORDER BY day,seq,id''', (a, b, cfg['model'])):
        blocks[r['day']].append(r)
    return [{**x, 'done_minutes': done.get(x['day'], 0), 'blocks': blocks.get(x['day'], []),
             'planned_minutes': sum(k['minutes'] for k in blocks.get(x['day'], []))} for x in avail]


def month_calendar(c, year, month):
    first = date(int(year), int(month), 1)
    last = (date(first.year + (first.month == 12), first.month % 12 + 1, 1) - timedelta(days=1))
    return calendar(c, first, last)
