"""Testes para o módulo error_tracking — FASE 1.

Isolamento hermético: usa apenas SQLite em memória/temp; nenhum arquivo
privado do titular é lido. Todos os dados são sintéticos.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import connect
from error_tracking import (
    ERROR_CAUSES,
    ITEM_RESULTS,
    CORRECTION_STATUSES,
    GABARITO_TIMINGS,
    feed_performance,
    get_batch,
    get_caderno_erros,
    get_error_summary,
    register_batch,
    register_question_item,
    update_item_correction,
    _ensure_schema,
)


def _db():
    """Conexão em memória com schema completo aplicado."""
    tmp = tempfile.TemporaryDirectory()
    c = connect(Path(tmp.name) / 'test.sqlite')
    _ensure_schema(c)
    return c, tmp


class TestErrorCauses(unittest.TestCase):
    """Verifica que as causas canônicas estão corretas e completas."""

    def test_eight_causes(self):
        self.assertEqual(len(ERROR_CAUSES), 8)

    def test_nao_especificado_presente(self):
        self.assertIn('Não especificado', ERROR_CAUSES)

    def test_desconhecimento_presente(self):
        self.assertIn('Desconhecimento', ERROR_CAUSES)


class TestRegisterBatch(unittest.TestCase):
    def setUp(self):
        self.c, self.tmp = _db()

    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def test_batch_simples_retorna_id_positivo(self):
        bid = register_batch(self.c, day='2026-11-08', subject='Direito Tributário',
                             total=20, correct=15)
        self.assertGreater(bid, 0)

    def test_batch_com_cause_counts(self):
        bid = register_batch(
            self.c, day='2026-11-08', subject='Direito Tributário',
            total=10, correct=6,
            cause_counts={'Desconhecimento': 2, 'Esquecimento': 1},
        )
        batch = get_batch(self.c, bid)
        self.assertEqual(batch['cause_counts']['Desconhecimento'], 2)
        self.assertEqual(batch['cause_counts']['Esquecimento'], 1)

    def test_batch_total_invalido_levanta_erro(self):
        with self.assertRaises(ValueError):
            register_batch(self.c, day='2026-11-08', subject='Direito Tributário',
                           total=0, correct=0)

    def test_batch_acertos_maiores_que_total_invalido(self):
        with self.assertRaises(ValueError):
            register_batch(self.c, day='2026-11-08', subject='Direito Tributário',
                           total=5, correct=6)

    def test_batch_data_invalida(self):
        with self.assertRaises(ValueError):
            register_batch(self.c, day='not-a-date', subject='Direito Tributário',
                           total=5, correct=3)

    def test_batch_disciplina_vazia_invalida(self):
        with self.assertRaises(ValueError):
            register_batch(self.c, day='2026-11-08', subject='   ',
                           total=5, correct=3)

    def test_batch_causa_invalida_levanta_erro(self):
        with self.assertRaises(ValueError):
            register_batch(self.c, day='2026-11-08', subject='Direito Tributário',
                           total=10, correct=5,
                           cause_counts={'CausaInventada': 3})

    def test_soma_causas_nao_excede_erros(self):
        # 10 total, 7 acertos, 0 sem resp → 3 erros; causas somam 4 → erro
        with self.assertRaises(ValueError):
            register_batch(self.c, day='2026-11-08', subject='Direito Tributário',
                           total=10, correct=7,
                           cause_counts={'Desconhecimento': 4})

    def test_gabarito_timing_invalido(self):
        with self.assertRaises(ValueError):
            register_batch(self.c, day='2026-11-08', subject='Direito Tributário',
                           total=5, correct=3, gabarito_timing='Não existe')

    def test_mode_invalido(self):
        with self.assertRaises(ValueError):
            register_batch(self.c, day='2026-11-08', subject='Direito Tributário',
                           total=5, correct=3, mode='invalido')

    def test_nao_resolvidas_mais_acertos_excedem_total(self):
        with self.assertRaises(ValueError):
            register_batch(self.c, day='2026-11-08', subject='Direito Tributário',
                           total=5, correct=3, unanswered=3)

    def test_campos_opcionais_sao_opcionais(self):
        """Deve funcionar sem fornecer nenhum campo opcional."""
        bid = register_batch(self.c, day='2026-11-08', subject='Direito Tributário',
                             total=10, correct=8)
        self.assertIsNotNone(bid)

    def test_todos_gabarito_timings_aceitos(self):
        for i, timing in enumerate(GABARITO_TIMINGS):
            bid = register_batch(self.c, day='2026-11-0' + str(i + 1),
                                 subject='Direito Tributário',
                                 total=5, correct=3, gabarito_timing=timing)
            self.assertGreater(bid, 0)


class TestRegisterItem(unittest.TestCase):
    def setUp(self):
        self.c, self.tmp = _db()
        self.bid = register_batch(self.c, day='2026-11-08',
                                  subject='Direito Tributário',
                                  total=5, correct=3, mode='individual')

    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def test_item_correta_sem_causa(self):
        iid = register_question_item(self.c, batch_id=self.bid,
                                     subject='Direito Tributário',
                                     result='Correta')
        self.assertGreater(iid, 0)

    def test_item_incorreta_com_causa(self):
        iid = register_question_item(self.c, batch_id=self.bid,
                                     subject='Direito Tributário',
                                     result='Incorreta',
                                     primary_cause='Desconhecimento')
        self.assertGreater(iid, 0)

    def test_item_nao_resolvida(self):
        iid = register_question_item(self.c, batch_id=self.bid,
                                     subject='Direito Tributário',
                                     result='Não resolvida')
        self.assertGreater(iid, 0)

    def test_result_invalido_levanta_erro(self):
        with self.assertRaises(ValueError):
            register_question_item(self.c, batch_id=self.bid,
                                   subject='Direito Tributário',
                                   result='Inventado')

    def test_causa_invalida_levanta_erro(self):
        with self.assertRaises(ValueError):
            register_question_item(self.c, batch_id=self.bid,
                                   subject='Direito Tributário',
                                   result='Incorreta',
                                   primary_cause='CausaFalsa')

    def test_batch_inexistente_levanta_erro(self):
        with self.assertRaises(ValueError):
            register_question_item(self.c, batch_id=99999,
                                   subject='Direito Tributário',
                                   result='Correta')

    def test_secondary_causes_salvas_corretamente(self):
        iid = register_question_item(
            self.c, batch_id=self.bid, subject='Direito Tributário',
            result='Incorreta', primary_cause='Esquecimento',
            secondary_causes=['Falta de atenção'],
        )
        batch = get_batch(self.c, self.bid)
        item = next(it for it in batch['items'] if it['id'] == iid)
        self.assertIn('Falta de atenção', item['secondary_causes'])

    def test_difficulty_invalida_levanta_erro(self):
        with self.assertRaises(ValueError):
            register_question_item(self.c, batch_id=self.bid,
                                   subject='Direito Tributário',
                                   result='Incorreta',
                                   primary_cause='Desconhecimento',
                                   difficulty='Impossível')

    def test_correction_status_invalido(self):
        with self.assertRaises(ValueError):
            register_question_item(self.c, batch_id=self.bid,
                                   subject='Direito Tributário',
                                   result='Incorreta',
                                   primary_cause='Desconhecimento',
                                   correction_status='Cancelada')

    def test_todos_resultados_aceitos(self):
        for result in ITEM_RESULTS:
            iid = register_question_item(
                self.c, batch_id=self.bid, subject='Direito Tributário',
                result=result,
                primary_cause='Desconhecimento' if result == 'Incorreta' else 'Não especificado',
            )
            self.assertGreater(iid, 0)

    def test_campos_opcionais_permanecem_opcionais(self):
        """Deve funcionar com apenas batch_id, subject e result."""
        iid = register_question_item(
            self.c, batch_id=self.bid, subject='Direito Tributário',
            result='Correta',
        )
        self.assertIsNotNone(iid)


class TestGetBatch(unittest.TestCase):
    def setUp(self):
        self.c, self.tmp = _db()
        self.bid = register_batch(self.c, day='2026-11-08',
                                  subject='Direito Tributário',
                                  total=3, correct=2, mode='individual')
        register_question_item(self.c, batch_id=self.bid,
                               subject='Direito Tributário', result='Correta')
        register_question_item(self.c, batch_id=self.bid,
                               subject='Direito Tributário', result='Correta')
        register_question_item(self.c, batch_id=self.bid,
                               subject='Direito Tributário', result='Incorreta',
                               primary_cause='Desconhecimento')

    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def test_batch_contem_tres_itens(self):
        b = get_batch(self.c, self.bid)
        self.assertEqual(len(b['items']), 3)

    def test_batch_id_correto(self):
        b = get_batch(self.c, self.bid)
        self.assertEqual(b['id'], self.bid)

    def test_batch_inexistente_levanta_erro(self):
        with self.assertRaises(ValueError):
            get_batch(self.c, 99999)

    def test_cause_counts_deserializado(self):
        b = get_batch(self.c, self.bid)
        self.assertIsInstance(b['cause_counts'], dict)


class TestGetErrorSummary(unittest.TestCase):
    def setUp(self):
        self.c, self.tmp = _db()
        b1 = register_batch(self.c, day='2026-11-08', subject='Direito Tributário',
                             total=10, correct=7,
                             cause_counts={'Desconhecimento': 2, 'Esquecimento': 1})
        b2 = register_batch(self.c, day='2026-11-07', subject='Direito Tributário',
                             total=5, correct=4, cause_counts={'Desconhecimento': 1})
        register_question_item(self.c, batch_id=b1, subject='Direito Tributário',
                                result='Incorreta', primary_cause='Esquecimento')
        register_question_item(self.c, batch_id=b2, subject='Direito Tributário',
                                result='Incorreta', primary_cause='Desconhecimento')

    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def test_totais_corretos(self):
        s = get_error_summary(self.c)
        self.assertEqual(s['totals']['questions'], 15)
        self.assertEqual(s['totals']['correct'], 11)
        self.assertEqual(s['totals']['incorrect'], 4)

    def test_taxa_calculada(self):
        s = get_error_summary(self.c)
        self.assertAlmostEqual(s['totals']['rate'], 11 / 15, places=4)

    def test_causas_bateria_agregadas(self):
        s = get_error_summary(self.c)
        self.assertEqual(s['batch_declared_causes']['Desconhecimento'], 3)
        self.assertEqual(s['batch_declared_causes']['Esquecimento'], 1)

    def test_causas_itens_individuais(self):
        s = get_error_summary(self.c)
        self.assertEqual(s['item_primary_causes']['Esquecimento'], 1)
        self.assertEqual(s['item_primary_causes']['Desconhecimento'], 1)

    def test_nota_metodologica_presente(self):
        s = get_error_summary(self.c)
        self.assertIn('batch_declared_causes', s['note'])
        self.assertIn('item_primary_causes', s['note'])

    def test_filtro_por_disciplina(self):
        register_batch(self.c, day='2026-11-08', subject='Contabilidade Geral',
                       total=5, correct=5)
        s = get_error_summary(self.c, subject='Direito Tributário')
        self.assertEqual(s['totals']['questions'], 15)

    def test_filtro_por_since(self):
        s = get_error_summary(self.c, since='2026-11-08')
        # Apenas b1 é de 2026-11-08
        self.assertEqual(s['totals']['questions'], 10)

    def test_sem_dados_taxa_none(self):
        c2, tmp2 = _db()
        try:
            s = get_error_summary(c2)
            self.assertIsNone(s['totals']['rate'])
        finally:
            c2.close(); tmp2.cleanup()


class TestGetCadernoErros(unittest.TestCase):
    def setUp(self):
        self.c, self.tmp = _db()
        self.bid = register_batch(self.c, day='2026-11-08',
                                  subject='Direito Tributário', topic='Obrigação',
                                  total=5, correct=3, mode='individual')
        self.iid1 = register_question_item(
            self.c, batch_id=self.bid, subject='Direito Tributário',
            topic='Obrigação', result='Incorreta',
            primary_cause='Desconhecimento', needs_reinforcement=True,
        )
        self.iid2 = register_question_item(
            self.c, batch_id=self.bid, subject='Direito Tributário',
            topic='Obrigação', result='Incorreta',
            primary_cause='Esquecimento', needs_reinforcement=False,
        )
        register_question_item(
            self.c, batch_id=self.bid, subject='Direito Tributário',
            topic='Obrigação', result='Correta',
        )

    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def test_caderno_retorna_apenas_incorretas(self):
        caderno = get_caderno_erros(self.c)
        for it in caderno:
            self.assertEqual(it['result'], 'Incorreta')

    def test_caderno_contem_dois_erros(self):
        caderno = get_caderno_erros(self.c)
        self.assertEqual(len(caderno), 2)

    def test_filtro_needs_reinforcement(self):
        caderno = get_caderno_erros(self.c, needs_reinforcement=True)
        self.assertEqual(len(caderno), 1)
        self.assertEqual(caderno[0]['id'], self.iid1)

    def test_filtro_primary_cause(self):
        caderno = get_caderno_erros(self.c, primary_cause='Esquecimento')
        self.assertEqual(len(caderno), 1)
        self.assertEqual(caderno[0]['id'], self.iid2)

    def test_caderno_contem_dados_da_bateria(self):
        caderno = get_caderno_erros(self.c)
        self.assertIn('day', caderno[0])
        self.assertIn('banca', caderno[0])

    def test_secondary_causes_deserializado(self):
        caderno = get_caderno_erros(self.c)
        for it in caderno:
            self.assertIsInstance(it['secondary_causes'], list)

    def test_limite_respeitado(self):
        caderno = get_caderno_erros(self.c, limit=1)
        self.assertEqual(len(caderno), 1)


class TestUpdateItemCorrection(unittest.TestCase):
    def setUp(self):
        self.c, self.tmp = _db()
        self.bid = register_batch(self.c, day='2026-11-08',
                                  subject='Direito Tributário',
                                  total=1, correct=0, mode='individual')
        self.iid = register_question_item(
            self.c, batch_id=self.bid, subject='Direito Tributário',
            result='Incorreta', primary_cause='Desconhecimento',
        )

    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def test_atualizar_para_corrigida(self):
        update_item_correction(self.c, self.iid, 'Corrigida')
        row = self.c.execute('SELECT correction_status FROM question_items WHERE id=?',
                             (self.iid,)).fetchone()
        self.assertEqual(row[0], 'Corrigida')

    def test_atualizar_com_observacao(self):
        update_item_correction(self.c, self.iid, 'Revisada', 'Revisei com material.')
        row = self.c.execute('SELECT correction_status, observation FROM question_items WHERE id=?',
                             (self.iid,)).fetchone()
        self.assertEqual(row[0], 'Revisada')
        self.assertEqual(row[1], 'Revisei com material.')

    def test_status_invalido_levanta_erro(self):
        with self.assertRaises(ValueError):
            update_item_correction(self.c, self.iid, 'Inexistente')

    def test_item_inexistente_levanta_erro(self):
        with self.assertRaises(ValueError):
            update_item_correction(self.c, 99999, 'Corrigida')

    def test_todos_statuses_aceitos(self):
        for status in CORRECTION_STATUSES:
            update_item_correction(self.c, self.iid, status)


class TestFeedPerformance(unittest.TestCase):
    def setUp(self):
        self.c, self.tmp = _db()

    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def test_sem_itens_usa_totais_da_bateria(self):
        bid = register_batch(self.c, day='2026-11-08',
                             subject='Direito Tributário',
                             total=10, correct=7)
        perf = feed_performance(self.c, bid)
        self.assertEqual(perf['total'], 10)
        self.assertEqual(perf['correct'], 7)
        self.assertEqual(perf['incorrect'], 3)
        self.assertFalse(perf['has_individual_items'])

    def test_com_itens_usa_contagem_de_itens(self):
        bid = register_batch(self.c, day='2026-11-08',
                             subject='Direito Tributário',
                             total=3, correct=2, mode='individual')
        register_question_item(self.c, batch_id=bid,
                               subject='Direito Tributário', result='Correta')
        register_question_item(self.c, batch_id=bid,
                               subject='Direito Tributário', result='Incorreta',
                               primary_cause='Desconhecimento')
        register_question_item(self.c, batch_id=bid,
                               subject='Direito Tributário', result='Correta')
        perf = feed_performance(self.c, bid)
        self.assertEqual(perf['total'], 3)
        self.assertEqual(perf['correct'], 2)
        self.assertEqual(perf['incorrect'], 1)
        self.assertTrue(perf['has_individual_items'])

    def test_taxa_calculada(self):
        bid = register_batch(self.c, day='2026-11-08',
                             subject='Direito Tributário',
                             total=4, correct=1)
        perf = feed_performance(self.c, bid)
        self.assertAlmostEqual(perf['rate'], 0.25, places=4)

    def test_needs_reinforcement_count(self):
        bid = register_batch(self.c, day='2026-11-08',
                             subject='Direito Tributário',
                             total=2, correct=0, mode='individual')
        register_question_item(self.c, batch_id=bid,
                               subject='Direito Tributário', result='Incorreta',
                               primary_cause='Desconhecimento',
                               needs_reinforcement=True)
        register_question_item(self.c, batch_id=bid,
                               subject='Direito Tributário', result='Incorreta',
                               primary_cause='Esquecimento',
                               needs_reinforcement=False)
        perf = feed_performance(self.c, bid)
        self.assertEqual(perf['needs_reinforcement_count'], 1)


class TestSchemaMigrationIdempotent(unittest.TestCase):
    """Garantir que chamar _ensure_schema múltiplas vezes é seguro."""

    def test_idempotente(self):
        c, tmp = _db()
        try:
            _ensure_schema(c)
            _ensure_schema(c)
            # Deve ser possível criar uma bateria após re-aplicar o schema.
            bid = register_batch(c, day='2026-11-08',
                                 subject='Direito Tributário', total=1, correct=1)
            self.assertGreater(bid, 0)
        finally:
            c.close(); tmp.cleanup()


if __name__ == '__main__':
    unittest.main()
