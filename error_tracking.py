"""CONTROLE MESTRE | Módulo de Registro Detalhado de Erros — FASE 1.

Dois modos de registro:
  MODO A — POR BATERIA: o estudante informa totais e causas agregadas.
  MODO B — POR QUESTÃO: registro individual com causa principal e secundárias.

Regras arquiteturais:
- Nunca atribui automaticamente todos os erros da bateria à mesma causa sem
  explicitar a simplificação.
- Mantém origem identificável em todos os registros.
- Sem decisões opacas; todas as regras auditáveis neste arquivo.
- Sem dependências externas; apenas Python stdlib + SQLite.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from core import all_rows, parse_day

# ---------------------------------------------------------------------------
# Causas canônicas de erro
# ---------------------------------------------------------------------------
ERROR_CAUSES = [
    'Desconhecimento',
    'Esquecimento',
    'Confusão conceitual',
    'Erro de interpretação',
    'Falta de atenção',
    'Falta de tempo',
    'Outro motivo',
    'Não especificado',
]

ITEM_RESULTS = ('Correta', 'Incorreta', 'Não resolvida')

ITEM_DIFFICULTIES = ('Fácil', 'Médio', 'Difícil', 'Muito difícil')

CORRECTION_STATUSES = ('Aberto', 'Corrigida', 'Revisada')

GABARITO_TIMINGS = ('Antes da resolução', 'Após a resolução', 'Não consultado')

# ---------------------------------------------------------------------------
# Migração de schema — chamada a partir de core.connect()
# ---------------------------------------------------------------------------

SCHEMA_SQL = '''
CREATE TABLE IF NOT EXISTS question_batches (
    id              INTEGER PRIMARY KEY,
    day             TEXT    NOT NULL,
    subject         TEXT    NOT NULL,
    topic           TEXT    NOT NULL DEFAULT '',
    platform        TEXT    NOT NULL DEFAULT '',
    banca           TEXT    NOT NULL DEFAULT '',
    total           INTEGER NOT NULL CHECK(total >= 1),
    correct         INTEGER NOT NULL CHECK(correct >= 0 AND correct <= total),
    unanswered      INTEGER NOT NULL DEFAULT 0 CHECK(unanswered >= 0),
    time_used_min   REAL    NOT NULL DEFAULT 0 CHECK(time_used_min >= 0),
    had_prior_review INTEGER NOT NULL DEFAULT 0,
    gabarito_timing TEXT    NOT NULL DEFAULT 'Não consultado',
    mode            TEXT    NOT NULL DEFAULT 'batch' CHECK(mode IN ('batch','individual')),
    cause_counts    TEXT    NOT NULL DEFAULT '{}',
    notes           TEXT    NOT NULL DEFAULT '',
    source          TEXT    NOT NULL DEFAULT 'web',
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS question_items (
    id                  INTEGER PRIMARY KEY,
    batch_id            INTEGER NOT NULL REFERENCES question_batches(id),
    question_ref        TEXT    NOT NULL DEFAULT '',
    subject             TEXT    NOT NULL,
    topic               TEXT    NOT NULL DEFAULT '',
    subtopic            TEXT    NOT NULL DEFAULT '',
    result              TEXT    NOT NULL CHECK(result IN ('Correta','Incorreta','Não resolvida')),
    primary_cause       TEXT    NOT NULL DEFAULT 'Não especificado',
    secondary_causes    TEXT    NOT NULL DEFAULT '[]',
    observation         TEXT    NOT NULL DEFAULT '',
    difficulty          TEXT    NOT NULL DEFAULT '',
    resolution_time_s   INTEGER NOT NULL DEFAULT 0,
    consulted_gabarito  INTEGER NOT NULL DEFAULT 0,
    needs_reinforcement INTEGER NOT NULL DEFAULT 0,
    correction_status   TEXT    NOT NULL DEFAULT 'Aberto',
    created_at          TEXT    NOT NULL
);
'''

# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now().isoformat(timespec='seconds')


def _validate_cause(cause: str, field: str = 'causa') -> str:
    if cause not in ERROR_CAUSES:
        raise ValueError(f'{field} inválida: {cause!r}. Escolha entre: {", ".join(ERROR_CAUSES)}')
    return cause


def _validate_cause_counts(counts: dict[str, int]) -> dict[str, int]:
    """Valida e normaliza o mapa causa→quantidade para registros por bateria."""
    out: dict[str, int] = {}
    for cause, qty in counts.items():
        _validate_cause(cause, f'causa "{cause}"')
        qty_int = int(qty)
        if qty_int < 0:
            raise ValueError(f'Quantidade para "{cause}" não pode ser negativa.')
        if qty_int > 0:
            out[cause] = qty_int
    return out


def _ensure_schema(c: Any) -> None:
    """Aplica migração de schema idempotente; seguro para chamar múltiplas vezes."""
    c.executescript(SCHEMA_SQL)
    c.commit()


# ---------------------------------------------------------------------------
# API pública — MODO A (por bateria)
# ---------------------------------------------------------------------------

def register_batch(
    c: Any,
    *,
    day: str | date,
    subject: str,
    topic: str = '',
    platform: str = '',
    banca: str = '',
    total: int,
    correct: int,
    unanswered: int = 0,
    time_used_min: float = 0.0,
    had_prior_review: bool = False,
    gabarito_timing: str = 'Não consultado',
    mode: str = 'batch',
    cause_counts: dict[str, int] | None = None,
    notes: str = '',
    source: str = 'web',
    request_id: str | None = None,
) -> int:
    """Registra uma bateria de questões e retorna o id inserido.

    Parameters
    ----------
    cause_counts : dict[str, int] | None
        Mapa {causa: quantidade} para o modo POR BATERIA. Opcional: se omitido
        ou vazio, assume classificação de causa como 'Não especificado'.
        NOTA: a plataforma distingue uma classificação GERAL da bateria de
        classificações individuais verificadas (via question_items). Não atribui
        automaticamente todos os erros à mesma causa sem comunicar a simplificação.
    """
    _ensure_schema(c)
    request_id = str(request_id or '').strip() or None
    if request_id:
        previous = c.execute('SELECT id FROM question_batches WHERE request_id=?', (request_id,)).fetchone()
        if previous:
            return int(previous[0])
    day_str = parse_day(day)
    if not day_str:
        raise ValueError('Data inválida.')
    subject = subject.strip()
    if not subject:
        raise ValueError('Disciplina é obrigatória.')
    total = int(total)
    correct = int(correct)
    unanswered = int(unanswered)
    if total < 1:
        raise ValueError('Total de questões deve ser pelo menos 1.')
    if not 0 <= correct <= total:
        raise ValueError('Acertos inválidos: deve ser entre 0 e total.')
    if not 0 <= unanswered <= total:
        raise ValueError('Questões não resolvidas inválidas.')
    if correct + unanswered > total:
        raise ValueError('Acertos + não resolvidas excedem o total.')
    if gabarito_timing not in GABARITO_TIMINGS:
        raise ValueError(f'gabarito_timing inválido. Use: {", ".join(GABARITO_TIMINGS)}')
    if mode not in ('batch', 'individual'):
        raise ValueError('mode deve ser "batch" ou "individual".')

    import math
    if not math.isfinite(float(time_used_min)) or float(time_used_min) < 0:
        raise ValueError('Tempo deve ser finito e não negativo.')
    counts_clean = _validate_cause_counts(cause_counts or {})
    # Verifica consistência: a soma das causas não pode superar os erros registráveis.
    errors_count = total - correct - unanswered
    if counts_clean and sum(counts_clean.values()) > errors_count:
        raise ValueError(
            f'A soma das causas ({sum(counts_clean.values())}) '
            f'supera o número de erros ({errors_count}).'
        )

    cur = c.execute(
        '''INSERT INTO question_batches
           (day, subject, topic, platform, banca, total, correct, unanswered,
            time_used_min, had_prior_review, gabarito_timing, mode,
            cause_counts, notes, source, created_at, status, request_id)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT DO NOTHING''',
        (
            day_str, subject, topic.strip(), platform.strip(), banca.strip(),
            total, correct, unanswered,
            float(time_used_min), int(had_prior_review),
            gabarito_timing, mode,
            json.dumps(counts_clean, ensure_ascii=False),
            notes.strip(), source, _now_iso(), 'draft', request_id,
        ),
    )
    c.commit()
    if cur.rowcount == 0 and request_id:
        existing = c.execute('SELECT id FROM question_batches WHERE request_id=?',(request_id,)).fetchone()
        if existing:
            return int(existing[0])
    if cur.rowcount != 1:
        raise ValueError('Não foi possível registrar a bateria.')
    return cur.lastrowid  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# API pública — MODO B (por questão individual)
# ---------------------------------------------------------------------------

def register_question_item(
    c: Any,
    *,
    batch_id: int,
    question_ref: str = '',
    subject: str,
    topic: str = '',
    subtopic: str = '',
    result: str,
    primary_cause: str = 'Não especificado',
    secondary_causes: list[str] | None = None,
    observation: str = '',
    difficulty: str = '',
    resolution_time_s: int = 0,
    consulted_gabarito: bool = False,
    needs_reinforcement: bool = False,
    correction_status: str = 'Aberto',
) -> int:
    """Registra um item individual associado a uma bateria existente.

    Parameters
    ----------
    result : str
        'Correta', 'Incorreta' ou 'Não resolvida'.
    primary_cause : str
        Causa principal do erro. Obrigatório somente se result == 'Incorreta'.
    secondary_causes : list[str] | None
        Causas secundárias opcionais. As análises indicam quando usam causa
        principal ou múltiplas causas para evitar confusão estatística.
    """
    _ensure_schema(c)
    if result not in ITEM_RESULTS:
        raise ValueError(f'result inválido. Use: {", ".join(ITEM_RESULTS)}')
    if result == 'Incorreta':
        _validate_cause(primary_cause, 'primary_cause')
    if difficulty and difficulty not in ITEM_DIFFICULTIES:
        raise ValueError(f'difficulty inválida. Use: {", ".join(ITEM_DIFFICULTIES)}')
    if correction_status not in CORRECTION_STATUSES:
        raise ValueError(f'correction_status inválido. Use: {", ".join(CORRECTION_STATUSES)}')

    sec = secondary_causes or []
    for sc in sec:
        _validate_cause(sc, f'secondary_cause "{sc}"')

    # O item precisa pertencer à bateria ainda aberta e respeitar o seu limite.
    batch = c.execute('SELECT subject,topic,total,mode,status FROM question_batches WHERE id=?',
                      (batch_id,)).fetchone()
    if not batch:
        raise ValueError(f'Bateria {batch_id} não encontrada.')
    if batch['mode'] != 'individual' or batch['status'] != 'draft':
        raise ValueError('Somente baterias individuais em rascunho aceitam itens.')
    if subject.strip() != batch['subject']:
        raise ValueError('Disciplina da questão não corresponde à bateria.')
    if batch['topic'] and topic.strip() != batch['topic']:
        raise ValueError('Assunto da questão não corresponde à bateria.')
    count = c.execute('SELECT COUNT(*) FROM question_items WHERE batch_id=?', (batch_id,)).fetchone()[0]
    if count >= batch['total']:
        raise ValueError('Quantidade de questões excede o total da bateria.')
    if int(resolution_time_s) < 0:
        raise ValueError('Tempo da questão não pode ser negativo.')
    if question_ref.strip() and c.execute(
        'SELECT 1 FROM question_items WHERE batch_id=? AND question_ref=?',
        (batch_id, question_ref.strip())
    ).fetchone():
        raise ValueError('Identificador de questão repetido na bateria.')

    cur = c.execute(
        '''INSERT INTO question_items
           (batch_id, question_ref, subject, topic, subtopic, result,
            primary_cause, secondary_causes, observation, difficulty,
            resolution_time_s, consulted_gabarito, needs_reinforcement,
            correction_status, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (
            batch_id, question_ref.strip(), subject.strip(), topic.strip(),
            subtopic.strip(), result,
            primary_cause if result == 'Incorreta' else '',
            json.dumps(sec, ensure_ascii=False),
            observation.strip(), difficulty,
            int(resolution_time_s), int(consulted_gabarito),
            int(needs_reinforcement), correction_status,
            _now_iso(),
        ),
    )
    c.commit()
    return cur.lastrowid  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# API pública — Consultas e Análise
# ---------------------------------------------------------------------------

def get_batch(c: Any, batch_id: int) -> dict:
    """Retorna a bateria com seus itens individuais."""
    _ensure_schema(c)
    row = c.execute('SELECT * FROM question_batches WHERE id=?', (batch_id,)).fetchone()
    if not row:
        raise ValueError(f'Bateria {batch_id} não encontrada.')
    batch = dict(row)
    batch['cause_counts'] = json.loads(batch['cause_counts'])
    items_raw = all_rows(c, 'SELECT * FROM question_items WHERE batch_id=? ORDER BY id', (batch_id,))
    for it in items_raw:
        it['secondary_causes'] = json.loads(it.get('secondary_causes', '[]'))
    batch['items'] = items_raw
    return batch


def get_error_summary(
    c: Any,
    subject: str | None = None,
    topic: str | None = None,
    since: str | date | None = None,
) -> dict:
    """Retorna estatísticas agregadas de erros por causa.

    NOTA METODOLÓGICA: distingue (a) causas declaradas pelo estudante em baterias
    e (b) causas verificadas individualmente. As duas origens são separadas na saída
    para evitar confusão estatística.
    """
    _ensure_schema(c)
    args_b: list = []
    where_b = "WHERE status!='draft'"
    args_i: list = []
    where_i = "WHERE result='Incorreta' AND batch_id IN (SELECT id FROM question_batches WHERE status!='draft')"

    if subject:
        where_b += ' AND subject=?'
        args_b.append(subject.strip())
        where_i += ' AND subject=?'
        args_i.append(subject.strip())
    if topic:
        where_b += ' AND topic=?'
        args_b.append(topic.strip())
        where_i += ' AND topic=?'
        args_i.append(topic.strip())
    if since:
        since_str = parse_day(since)
        where_b += ' AND day >= ?'
        args_b.append(since_str)
        # question_items não tem 'day'; juntar com batch
        where_i += (' AND batch_id IN '
                    '(SELECT id FROM question_batches WHERE day >= ?)')
        args_i.append(since_str)

    # Totais globais de baterias
    batches = all_rows(
        c,
        f'SELECT SUM(total) t, SUM(correct) c, SUM(unanswered) u '
        f'FROM question_batches {where_b}',
        args_b,
    )
    b = batches[0] if batches else {}
    total_q = int(b.get('t') or 0)
    total_ok = int(b.get('c') or 0)
    total_na = int(b.get('u') or 0)
    total_err = total_q - total_ok - total_na

    # Causas declaradas em baterias (agregadas dos JSONs)
    batch_rows = all_rows(
        c,
        f'SELECT cause_counts FROM question_batches {where_b}',
        args_b,
    )
    batch_causes: dict[str, int] = {}
    for row in batch_rows:
        for cause, qty in json.loads(row['cause_counts']).items():
            batch_causes[cause] = batch_causes.get(cause, 0) + qty

    # Causas verificadas por item individual
    item_rows = all_rows(
        c,
        f'SELECT primary_cause, secondary_causes '
        f'FROM question_items {where_i}',
        args_i,
    )
    item_primary: dict[str, int] = {}
    item_secondary: dict[str, int] = {}
    for row in item_rows:
        pc = row['primary_cause']
        if pc:
            item_primary[pc] = item_primary.get(pc, 0) + 1
        for sc in json.loads(row.get('secondary_causes') or '[]'):
            item_secondary[sc] = item_secondary.get(sc, 0) + 1

    return {
        'totals': {
            'questions': total_q,
            'correct': total_ok,
            'incorrect': total_err,
            'unanswered': total_na,
            'rate': round(total_ok / total_q, 4) if total_q else None,
        },
        'batch_declared_causes': batch_causes,
        'item_primary_causes': item_primary,
        'item_secondary_causes': item_secondary,
        'note': (
            'batch_declared_causes: causas informadas pelo estudante no modo POR BATERIA '
            '(classificação geral, pode ser uma simplificação). '
            'item_primary_causes: causas verificadas por questão individual (maior precisão).'
        ),
    }


def get_caderno_erros(
    c: Any,
    subject: str | None = None,
    topic: str | None = None,
    primary_cause: str | None = None,
    correction_status: str | None = None,
    needs_reinforcement: bool | None = None,
    limit: int = 100,
) -> list[dict]:
    """Retorna o caderno de erros: itens individuais com contexto da bateria.

    Cada item inclui dados da bateria (disciplina, assunto, data, banca, plataforma)
    para evitar consultas adicionais.
    """
    _ensure_schema(c)
    where = 'WHERE qi.result = \'Incorreta\''
    args: list = []

    if subject:
        where += ' AND qi.subject=?'
        args.append(subject.strip())
    if topic:
        where += ' AND qi.topic=?'
        args.append(topic.strip())
    if primary_cause:
        where += ' AND qi.primary_cause=?'
        args.append(primary_cause)
    if correction_status:
        where += ' AND qi.correction_status=?'
        args.append(correction_status)
    if needs_reinforcement is not None:
        where += ' AND qi.needs_reinforcement=?'
        args.append(int(needs_reinforcement))

    args.append(max(1, min(500, int(limit))))

    rows = all_rows(
        c,
        f'''SELECT qi.id, qi.batch_id, qi.question_ref, qi.subject, qi.topic,
                   qi.subtopic, qi.result, qi.primary_cause, qi.secondary_causes,
                   qi.observation, qi.difficulty, qi.resolution_time_s,
                   qi.consulted_gabarito, qi.needs_reinforcement,
                   qi.correction_status, qi.created_at,
                   qb.day, qb.banca, qb.platform, qb.gabarito_timing
            FROM question_items qi
            JOIN question_batches qb ON qb.id = qi.batch_id
            {where}
            ORDER BY qb.day DESC, qi.id DESC
            LIMIT ?''',
        args,
    )
    for row in rows:
        row['secondary_causes'] = json.loads(row.get('secondary_causes') or '[]')
    return rows


def update_item_correction(
    c: Any,
    item_id: int,
    correction_status: str,
    observation: str | None = None,
) -> None:
    """Atualiza o status de correção de um item individual."""
    _ensure_schema(c)
    if correction_status not in CORRECTION_STATUSES:
        raise ValueError(f'correction_status inválido. Use: {", ".join(CORRECTION_STATUSES)}')
    if not c.execute('SELECT 1 FROM question_items WHERE id=?', (item_id,)).fetchone():
        raise ValueError(f'Item {item_id} não encontrado.')
    if observation is not None:
        c.execute(
            'UPDATE question_items SET correction_status=?, observation=? WHERE id=?',
            (correction_status, observation.strip(), item_id),
        )
    else:
        c.execute(
            'UPDATE question_items SET correction_status=? WHERE id=?',
            (correction_status, item_id),
        )
    c.commit()


def feed_performance(c: Any, batch_id: int) -> dict:
    """Retorna dados formatados para alimentar desempenho, histórico, caderno de
    erros, diagnóstico e motor de reforços — sem duplicidade.

    Esta função é o ponto de integração: após registrar uma bateria, o chamador
    usa este resultado para atualizar a tabela `questions` legada (compatibilidade)
    e enfileirar avaliação de reforço.
    """
    _ensure_schema(c)
    batch = get_batch(c, batch_id)
    errors = total = correct = 0
    for it in batch['items']:
        total += 1
        if it['result'] == 'Correta':
            correct += 1
        elif it['result'] == 'Incorreta':
            errors += 1
    # Se não há itens individuais, usa os totais da bateria.
    if total == 0:
        total = batch['total']
        correct = batch['correct']
        errors = total - correct - batch['unanswered']

    return {
        'batch_id': batch_id,
        'day': batch['day'],
        'subject': batch['subject'],
        'topic': batch['topic'],
        'platform': batch['platform'],
        'banca': batch['banca'],
        'total': total,
        'correct': correct,
        'incorrect': errors,
        'unanswered': batch['unanswered'],
        'rate': round(correct / total, 4) if total > 0 else None,
        'mode': batch['mode'],
        'has_individual_items': len(batch['items']) > 0,
        'needs_reinforcement_count': sum(
            1 for it in batch['items'] if it.get('needs_reinforcement')
        ),
    }


def finalize_batch(c: Any, batch_id: int) -> dict:
    """Finaliza uma bateria e alimenta a tabela legada exatamente uma vez.

    O INSERT legado e o estado final são transacionados juntos. Em caso de
    retry, o registro existente é devolvido; rascunhos jamais entram no
    desempenho. Registros anteriores à migração ('legacy') não são recontados.
    """
    _ensure_schema(c)
    batch = c.execute('SELECT * FROM question_batches WHERE id=?', (batch_id,)).fetchone()
    if not batch:
        raise ValueError('Bateria não encontrada.')
    if batch['status'] == 'legacy':
        raise ValueError('Bateria histórica: não pode ser finalizada novamente.')
    if batch['status'] == 'finalized':
        return feed_performance(c, batch_id)
    if batch['status'] != 'draft':
        raise ValueError('Estado de bateria desconhecido.')
    if batch['mode'] == 'individual':
        counts = {
            r['result']: r['n'] for r in c.execute(
                'SELECT result, COUNT(*) AS n FROM question_items WHERE batch_id=? GROUP BY result',
                (batch_id,)
            )
        }
        if sum(counts.values()) != batch['total']:
            raise ValueError('Registre todas as questões antes de finalizar a bateria.')
        if counts.get('Correta',0) != batch['correct'] or counts.get('Não resolvida',0) != batch['unanswered']:
            raise ValueError('Acertos e não resolvidas devem coincidir com o cabeçalho.')
        expected_err = batch['total'] - batch['correct'] - batch['unanswered']
        if counts.get('Incorreta',0) != expected_err:
            raise ValueError('Quantidade de erros não coincide com o cabeçalho.')
    fingerprint = f'cm_error_tracking_batch:{batch_id}'
    try:
        c.execute('BEGIN IMMEDIATE')
        c.execute(
            '''INSERT OR IGNORE INTO questions
               (day,subject,topic,bank,platform,total,correct,error_type,notes,source,fingerprint)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
            (batch['day'], batch['subject'], batch['topic'], batch['banca'],
             batch['platform'], batch['total'], batch['correct'], '',
             'Bateria consolidada via registro detalhado', 'error_tracking',
             fingerprint)
        )
        legacy = c.execute('SELECT id FROM questions WHERE fingerprint=?', (fingerprint,)).fetchone()
        if not legacy:
            raise RuntimeError('Falha ao consolidar o registro de questões.')
        c.execute(
            "UPDATE question_batches SET status='finalized', legacy_question_id=? WHERE id=? AND status='draft'",
            (legacy[0],batch_id)
        )
        c.commit()
    except Exception:
        c.rollback()
        raise
    return feed_performance(c, batch_id)
