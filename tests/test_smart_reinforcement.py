"""Testes offline com SQLite sintético — nenhum dado pessoal."""
import sqlite3
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from smart_reinforcement import recommend


class ReinforcementTests(unittest.TestCase):
    def setUp(self):
        self.c = sqlite3.connect(':memory:')
        self.c.row_factory = sqlite3.Row
        self.c.executescript("""
            CREATE TABLE questions(day TEXT,subject TEXT,topic TEXT,total INTEGER,correct INTEGER,error_type TEXT);
            CREATE TABLE reviews(subject TEXT,topic TEXT,due_on TEXT,status TEXT);
            CREATE TABLE errors(subject TEXT,topic TEXT,status TEXT);
        """)

    def tearDown(self):
        self.c.close()

    def q(self, topic, total, correct, cause=''):
        self.c.execute('INSERT INTO questions VALUES(?,?,?,?,?,?)',
                       ('2026-11-07','Direito Tributário',topic,total,correct,cause))
        self.c.commit()

    def item(self, topic):
        return next(x for x in recommend(self.c, '2026-11-08')['items'] if x['topic']==topic)

    def test_without_data_does_not_invent_a_reinforcement(self):
        r = recommend(self.c,'2026-11-08')
        self.assertEqual(r['items'], [])
        self.assertEqual(r['total_questions_in_window'],0)

    def test_small_sample_is_not_intense(self):
        self.q('Lançamento',3,0,'Desconhecimento')
        row = self.item('Lançamento')
        self.assertEqual(row['level'],'Diagnóstico')
        self.assertEqual(row['evidence'],'Insuficiente para inferir dificuldade')
        self.assertEqual(row['accuracy'],0)

    def test_intense_and_conceptual_guidance(self):
        self.q('Obrigação tributária',30,10,'Confusão conceitual')
        row = self.item('Obrigação tributária')
        self.assertEqual(row['level'],'Intenso')
        self.assertEqual(row['missed'],20)
        self.assertIn('quadro comparativo',row['guidance'])
        self.assertIn('bateria',row['cause_scope'])

    def test_moderate_reinforcement(self):
        self.q('Crédito tributário',20,14,'Esquecimento')
        self.assertEqual(self.item('Crédito tributário')['level'],'Moderado')

    def test_overdue_without_questions_never_claims_weakness(self):
        self.c.execute("INSERT INTO reviews VALUES('Contabilidade Geral','Estoques','2026-11-05','Pendente')")
        row = recommend(self.c, '2026-11-08')['items'][0]
        self.assertEqual(row['level'],'Pendente')
        self.assertIsNone(row['accuracy'])
        self.assertEqual(row['evidence'],'Insuficiente para inferir dificuldade')

    def test_old_questions_excluded(self):
        self.c.execute("INSERT INTO questions VALUES('2026-01-01','Direito Civil','Contratos',40,0,'Esquecimento')")
        self.assertEqual(recommend(self.c, '2026-11-08')['items'],[])

    def test_repeat_does_not_change_database(self):
        self.q('Fato gerador',20,7,'Falta de atenção')
        before=self.c.total_changes
        one=recommend(self.c,'2026-11-08')
        two=recommend(self.c,'2026-11-08')
        self.assertEqual(one,two)
        self.assertEqual(before,self.c.total_changes)

    def test_invalid_limits_rejected(self):
        with self.assertRaises(ValueError):recommend(self.c,'2026-11-08',min_questions=0)
        with self.assertRaises(ValueError):recommend(self.c,'2026-11-08',window_days=0)

if __name__=='__main__':unittest.main()
