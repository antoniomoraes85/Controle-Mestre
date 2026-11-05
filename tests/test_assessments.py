"""Regras de avaliação, compatibilidade com SQLite antigo e não duplicidade."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import connect,add_questions,metric_data
from assessments import ensure_schema,insert_mock,insert_essay,delete_assessment,assessment_summary


class AssessmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.c=connect(Path(self.tmp.name)/'cm.db')
    def tearDown(self):
        self.c.close();self.tmp.cleanup()
    def test_migration_idempotent(self):
        ensure_schema(self.c);ensure_schema(self.c)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM mock_exams').fetchone()[0],0)
    def test_results_not_mixed_with_questions(self):
        add_questions(self.c,'2026-11-05','Direito Tributário','Obrigação',10,9)
        insert_mock(self.c,{'day':'2026-11-05','title':'Simulado 1','total':20,'correct':15,'wrong':3,'blank':2,'guesses':4})
        rates=metric_data(self.c)
        self.assertEqual(self.c.execute('SELECT SUM(total) FROM questions').fetchone()[0],10)
        v=assessment_summary(self.c)
        self.assertEqual(v['mock_rate'],.75)
        self.assertEqual(v['mock_questions'],20)
    def test_mock_validation(self):
        base={'day':'2026-11-05','title':'Teste','total':20,'correct':15,'wrong':5,'blank':0,'guesses':3}
        bad=[dict(base,blank=5),dict(base,guesses=23),dict(base,total=0),dict(base,title=' '),dict(base,grade=21,maximum_grade=20),dict(base,guesses=-1)]
        for row in bad:
            with self.subTest(row=row),self.assertRaises(ValueError):insert_mock(self.c,row)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM mock_exams').fetchone()[0],0)
    def test_essay_normalization(self):
        insert_essay(self.c,{'day':'2026-11-05','topic':'Tema 1','grade':9,'maximum_grade':10})
        insert_essay(self.c,{'day':'2026-11-05','topic':'Tema 2','grade':35,'maximum_grade':50})
        self.assertAlmostEqual(assessment_summary(self.c)['essay_mean_pct'],80,places=2)
        with self.assertRaises(ValueError):insert_essay(self.c,{'day':'2026-11-05','topic':'Tema 3','grade':55,'maximum_grade':50})
    def test_delete_with_restricted_table(self):
        id_=insert_essay(self.c,{'day':'2026-11-05','topic':'Tema','grade':8,'maximum_grade':10})
        with self.assertRaises(ValueError):delete_assessment(self.c,'subjects',id_)
        self.assertTrue(delete_assessment(self.c,'essays',id_))
        self.assertEqual(assessment_summary(self.c)['essay_count'],0)

if __name__=='__main__':unittest.main()