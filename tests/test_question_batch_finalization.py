"""Regressões de ciclo de vida e idempotência das baterias — dados sintéticos."""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import connect
from error_tracking import register_batch, register_question_item, finalize_batch, get_error_summary


class BatchFinalizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.temp.name)/'db.sqlite')

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def create(self, total=3,correct=2,unanswered=0,mode='individual',request_id=None):
        return register_batch(self.db, day='2026-11-08', subject='Direito Tributário',
                              topic='Obrigação Tributária', total=total, correct=correct,
                              unanswered=unanswered, mode=mode, request_id=request_id)

    def item(self,bid,result,subject='Direito Tributário',topic='Obrigação Tributária'):
        return register_question_item(self.db,batch_id=bid,subject=subject,topic=topic,result=result)

    def test_rascunho_nao_entra_em_desempenho(self):
        self.create()
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM questions WHERE source='error_tracking'").fetchone()[0],0)
        self.assertEqual(get_error_summary(self.db)['totals']['questions'],0)

    def test_finalizar_modo_agregado_uma_unica_vez(self):
        bid=self.create(mode='batch')
        p1=finalize_batch(self.db,bid)
        p2=finalize_batch(self.db,bid)
        self.assertEqual(p1,p2)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM questions WHERE source='error_tracking'").fetchone()[0],1)
        self.assertEqual(get_error_summary(self.db)['totals']['questions'],3)

    def test_individual_incompleta_nao_finaliza(self):
        bid=self.create()
        self.item(bid,'Correta')
        with self.assertRaisesRegex(ValueError,'todas as questões'):
            finalize_batch(self.db,bid)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM questions').fetchone()[0],0)

    def test_individual_completa_preserva_taxa_e_uma_linha(self):
        bid=self.create()
        self.item(bid,'Correta')
        self.item(bid,'Incorreta')
        self.item(bid,'Correta')
        p=finalize_batch(self.db,bid)
        self.assertEqual(p['total'],3)
        self.assertEqual(p['correct'],2)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM questions WHERE source='error_tracking'").fetchone()[0],1)
        self.assertEqual(get_error_summary(self.db)['totals']['correct'],2)

    def test_reconciliacao_rejeita_cabecalho_inconsistente(self):
        bid=self.create()
        self.item(bid,'Correta')
        self.item(bid,'Correta')
        self.item(bid,'Correta')
        with self.assertRaisesRegex(ValueError,'Acertos'):
            finalize_batch(self.db,bid)
        self.assertEqual(get_error_summary(self.db)['totals']['questions'],0)

    def test_limite_de_itens(self):
        bid=self.create(total=1,correct=0)
        self.item(bid,'Incorreta')
        with self.assertRaisesRegex(ValueError,'excede'):
            self.item(bid,'Incorreta')

    def test_disciplina_e_assunto_consistentes(self):
        bid=self.create()
        with self.assertRaisesRegex(ValueError,'Disciplina'):
            self.item(bid,'Correta',subject='Contabilidade Geral')
        with self.assertRaisesRegex(ValueError,'Assunto'):
            self.item(bid,'Correta',topic='Lançamento')

    def test_idempotencia_de_cabecalho(self):
        bid1=self.create(mode='batch',request_id='sample-stable-001')
        bid2=self.create(mode='batch',request_id='sample-stable-001')
        self.assertEqual(bid1,bid2)
        finalize_batch(self.db,bid1)
        finalize_batch(self.db,bid2)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM questions WHERE source='error_tracking'").fetchone()[0],1)

    def test_nao_resolvidas_na_finalizacao(self):
        bid=self.create(total=2,correct=1,unanswered=1)
        self.item(bid,'Correta')
        self.item(bid,'Não resolvida')
        finalize_batch(self.db,bid)
        self.assertEqual(get_error_summary(self.db)['totals']['unanswered'],1)

    def test_migracao_reexecutada(self):
        self.db.close()
        self.db=connect(Path(self.temp.name)/'db.sqlite')
        self.db=connect(Path(self.temp.name)/'db.sqlite')
        self.assertTrue(self.db.execute("PRAGMA table_info(question_batches)").fetchall())


if __name__=='__main__':unittest.main()
