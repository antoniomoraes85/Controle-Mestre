"""Reforços e orientações baseados somente em evidências registradas.

NUNCA converte um escore de prioridade em probabilidade de prova/aprovação.
Consulta somente leitura no SQLite legado; não altera o agendador Anki FSRS.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

ERROR_GUIDANCE = {
    'desconhecimento': ('Desconhecimento', 'Retome a explicação teórica do assunto e resolva uma bateria diagnóstica curta, sem consulta prévia ao gabarito.'),
    'esquecimento': ('Esquecimento', 'Recupere a regra de memória, faça questões de recuperação ativa e programe revisão no sistema que você já utiliza.'),
    'confusao conceitual': ('Confusão conceitual', 'Construa um quadro comparativo dos conceitos confundidos e resolva questões que exijam distingui-los.'),
    'erro de interpretacao': ('Interpretação', 'Releia os comandos das questões erradas, destaque as condições e explique por que cada alternativa é correta ou incorreta.'),
    'falta de atencao': ('Atenção', 'Refaça as questões devagar, identificando palavras restritivas, exceções e a alternativa efetivamente solicitada.'),
    'falta de tempo': ('Gestão do tempo', 'Resolva uma bateria curta com cronômetro e revise em quais etapas consumiu mais tempo.'),
}


def _normalize(value):
    import unicodedata
    value = unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode().lower()
    return ' '.join(value.replace('-', ' ').replace('_', ' ').split())


def _guidance(reason, due):
    key = _normalize(reason)
    aliases = {'confusao':'confusao conceitual', 'interpretacao':'erro de interpretacao',
               'desatencao':'falta de atencao', 'tempo':'falta de tempo'}
    key = aliases.get(key, key)
    main = ERROR_GUIDANCE.get(key)
    if main:
        guidance = main[1]
        label = main[0]
    else:
        label = 'Causa não individualizada'
        guidance = 'Refaça as questões erradas sem consultar os comentários e registre a causa específica antes de escolher um reforço.'
    if due:
        guidance += ' Há revisão vencida ou prevista para hoje; confira sua fila antes de adicionar outra.'
    return label, guidance


def recommend(c, today=None, window_days=90, min_questions=15, limit=12):
    """Retorna recomendações determinísticas; não cria tarefas nem soma horas.

    questions.error_type é uma causa por bateria, NÃO por questão. Um registro
    explicita uma hipótese do aluno e não constitui diagnóstico clínico/pedagógico.
    """
    if min_questions < 1 or window_days < 1 or limit < 1:
        raise ValueError('Janela, amostra mínima e limite devem ser positivos.')
    ref = today or date.today()
    if isinstance(ref, str):
        ref = date.fromisoformat(ref)
    if not isinstance(ref, date):
        raise ValueError('Data de referência inválida.')
    beginning = (ref - timedelta(days=window_days - 1)).isoformat()
    end = ref.isoformat()

    def rows(sql, params=()):
        return [dict(row) for row in c.execute(sql, params).fetchall()]

    question_rows = rows("""SELECT subject, topic, SUM(total) AS total,
                SUM(correct) AS correct, COUNT(*) AS batches
                FROM questions WHERE day BETWEEN ? AND ?
                GROUP BY subject, topic""", (beginning, end))
    causes = rows("""SELECT subject, topic, error_type, COUNT(*) AS batches,
                SUM(total-correct) AS wrong_in_batches
                FROM questions WHERE day BETWEEN ? AND ? AND total>correct
                    AND TRIM(error_type)!=''
                GROUP BY subject, topic, error_type""", (beginning, end))
    individual_causes = rows("""SELECT qb.subject AS subject, qb.topic AS topic,
                qi.primary_cause AS cause, COUNT(*) AS count
                FROM question_items qi
                JOIN question_batches qb ON qi.batch_id=qb.id
                WHERE qb.status='finalized' AND qb.day BETWEEN ? AND ?
                AND qi.result='Incorreta'
                AND qi.primary_cause NOT IN ('','Não especificado')
                GROUP BY qb.subject,qb.topic,qi.primary_cause""",(beginning,end))
    flagged = rows("""SELECT qb.subject AS subject, qb.topic AS topic, COUNT(*) AS total
                FROM question_items qi
                JOIN question_batches qb ON qi.batch_id=qb.id
                WHERE qb.status='finalized' AND qb.day BETWEEN ? AND ?
                AND qi.result='Incorreta' AND qi.needs_reinforcement=1
                GROUP BY qb.subject,qb.topic""",(beginning,end))
    reviews = rows("""SELECT subject, topic, COUNT(*) AS due FROM reviews
                WHERE status='Pendente' AND due_on <= ? GROUP BY subject, topic""", (end,))
    open_errors = rows("""SELECT subject, topic, COUNT(*) AS total FROM errors
                WHERE status='Aberto' GROUP BY subject, topic""")
    notes = defaultdict(list)
    for row in causes:
        notes[(row['subject'],row['topic'])].append(row)
    by_item = defaultdict(list)
    for row in individual_causes:
        by_item[(row['subject'],row['topic'])].append(row)
    by_flagged = {(r['subject'],r['topic']):int(r['total']) for r in flagged}
    by_q = {(r['subject'],r['topic']): r for r in question_rows}
    by_r = {(r['subject'],r['topic']):int(r['due']) for r in reviews}
    by_e = {(r['subject'],r['topic']):int(r['total']) for r in open_errors}
    keys = set(by_q) | set(by_r) | set(by_e) | set(by_flagged)
    findings = []
    for subject, topic in keys:
        q = by_q.get((subject,topic),{})
        n,correct = int(q.get('total') or 0),int(q.get('correct') or 0)
        if n and not (0 <= correct <= n):
            raise ValueError('Resultados de questões inconsistentes.')
        missed = n-correct
        rate = correct/n if n else None
        due = by_r.get((subject,topic),0)
        opened = by_e.get((subject,topic),0)
        marked = by_flagged.get((subject,topic),0)
        eligible = n >= min_questions
        if eligible and missed >= 6 and missed/n >= .45:
            level, action = 'Intenso', 'Refazer erros + revisão dirigida'
        elif eligible and missed >= 4 and missed/n >= .25:
            level, action = 'Moderado', 'Bateria de reforço por assunto'
        elif due or opened or marked:
            level, action = 'Pendente', 'Revisar pendências e diagnosticar' if not eligible else 'Revisão direcionada'
        elif n and not eligible:
            level, action = 'Diagnóstico', 'Ampliar amostra antes de classificar dificuldade'
        else:
            continue
        cause_rows = sorted(notes[(subject,topic)],key=lambda r:(-int(r['wrong_in_batches']),r['error_type']))
        item_rows = sorted(by_item[(subject,topic)],key=lambda r:(-int(r['count']),r['cause']))
        has_item_causes = bool(item_rows)
        raw = item_rows[0]['cause'] if has_item_causes else (cause_rows[0]['error_type'] if cause_rows else '')
        cause_label, advice = _guidance(raw, due)
        if level=='Diagnóstico':
            advice = 'A amostra é insuficiente para concluir que exista dificuldade. Resolva mais questões e registre as causas dos erros.'
        evidence = 'Suficiente para triagem' if n >= min_questions else 'Insuficiente para inferir dificuldade'
        score = round(100 * (missed/n if eligible else 0) + min(due,4)*9 + min(opened,4)*5 + min(marked,4)*5, 1)
        findings.append({
            'subject':subject,'topic':topic,'level':level,'action':action,
            'question_total':n,'correct':correct,'missed':missed,
            'accuracy':round(rate,4) if rate is not None else None,
            'due_reviews':due,'open_errors':opened,'marked_items':marked,'evidence':evidence,
            'dominant_item_cause':cause_label if has_item_causes else None,
            'dominant_batch_cause':cause_label if cause_rows and not has_item_causes else None,
            'cause_scope':('Causa principal observada nas questões individuais.' if has_item_causes else
                           'Causa declarada por bateria; não permite inferir cada item.' if cause_rows else
                           'Não existe causa de erro individual identificada.'),
            'guidance':advice,'priority_score':score,
            'explanation':f'{correct}/{n} acertos' if n else 'Sem questões registradas no período',
        })
    order = {'Intenso':0,'Moderado':1,'Pendente':2,'Diagnóstico':3}
    findings.sort(key=lambda x:(order[x['level']],-x['priority_score'],x['subject'],x['topic']))
    return {
        'generated_on':end,'window_days':window_days,'min_questions':min_questions,
        'total_questions_in_window':sum(int(r['total']) for r in question_rows),
        'items':findings[:limit],
        'notes':['Triagem heurística, não previsão de aprovação ou probabilidade de cobrança.',
                 'Causas de erro existentes são registradas por bateria e não por questão.',
                 'A orientação exige verificação humana; reforços não são adicionados ao plano automaticamente.']
    }
