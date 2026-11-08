"""Questões por disciplina e banca: ponderação e separação de avaliações."""
import sys,tempfile,unittest
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core,assessments,question_bank

class QuestionBankTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.c=core.connect(Path(self.tmp.name)/'test.db')
        self.today=date.today().isoformat()
    def tearDown(self):
        self.c.close();self.tmp.cleanup()
    def q(self,total,correct,bank):
        core.add_questions(self.c,self.today,'Direito Tributário','Obrigação tributária',
                total,correct,bank,'QConcursos')
    def test_performance_weighted_not_average_of_batteries(self):
        self.q(10,2,'FCC');self.q(90,81,'FCC')
        r=question_bank.report(self.c)
        self.assertEqual(len(r['rows']),1)
        self.assertEqual(r['rows'][0]['correct'],83)
        self.assertEqual(r['rows'][0]['total'],100)
        self.assertAlmostEqual(r['rows'][0]['rate'],.83)

    def test_other_assessments_are_not_added(self):
        self.q(20,15,'FGV')
        assessments.insert_mock(self.c,{'day':self.today,'title':'Simulado',
            'total':50,'correct':10,'wrong':40,'blank':0,'guesses':0,'bank':'FGV'})
        r=question_bank.report(self.c)
        self.assertEqual(r['rows'][0]['total'],20)
        self.assertEqual(r['rows'][0]['correct'],15)

    def test_small_sample_is_identified(self):
        self.q(5,2,'Cebraspe')
        r=question_bank.report(self.c)
        self.assertFalse(r['rows'][0]['sample_sufficient'])
        self.assertEqual(r['minimum'],10)
        with self.assertRaises(ValueError):question_bank.report(self.c,0)

if __name__=='__main__':unittest.main()
