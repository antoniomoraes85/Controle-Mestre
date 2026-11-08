"""Testes de provas de Português e comparações por banca sem contaminar outras séries."""
import sys,tempfile,unittest
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core,assessment_insights,assessments

class AssessmentInsightsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.c=core.connect(Path(self.tmp.name)/'exam.sqlite3')
        self.today=date.today().isoformat()
    def tearDown(self):
        self.c.close();self.tmp.cleanup()
    def pt(self,bank='FCC',correct=12,wrong=8):
        return {'day':self.today,'title':'Prova de Português anterior','bank':bank,'year':2022,
            'total':correct+wrong,'correct':correct,'wrong':wrong,'blank':0}
    def test_portuguese_independent_of_mock_essay_and_questions(self):
        assessment_insights.record(self.c,self.pt())
        assessments.insert_mock(self.c,{'day':self.today,'title':'Geral','bank':'FCC',
                'total':10,'correct':6,'wrong':4,'blank':0,'guesses':0})
        assessments.insert_essay(self.c,{'day':self.today,'topic':'Redação','bank':'FGV',
                'grade':70,'maximum_grade':100})
        report=assessment_insights.report(self.c)
        self.assertEqual(len(report['portuguese']),1)
        self.assertEqual(len(report['mocks']),1)
        self.assertEqual(len(report['essays']),1)
        self.assertAlmostEqual(report['portuguese_rate'],.6)
        self.assertAlmostEqual(report['mock_banks'][0]['rate'],.6)
        self.assertAlmostEqual(report['essays_banks'][0]['mean_rate'],.7)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM questions').fetchone()[0],0)

    def test_bank_weighted_rate_and_preserve_other_banks(self):
        assessment_insights.record(self.c,self.pt(bank='FCC',correct=1,wrong=9))
        assessment_insights.record(self.c,self.pt(bank='FCC',correct=80,wrong=20))
        assessment_insights.record(self.c,self.pt(bank='FGV',correct=18,wrong=2))
        rs=assessment_insights.report(self.c)
        self.assertEqual(len(rs['portuguese_banks']),2)
        fcc=next(x for x in rs['portuguese_banks'] if x['bank']=='FCC')
        self.assertEqual(fcc['total'],110)
        self.assertEqual(fcc['correct'],81)
        self.assertAlmostEqual(fcc['rate'],81/110)

    def test_validation_rejects_inconsistent_or_ambiguous_exam(self):
        bad=self.pt();bad['wrong']=9
        with self.assertRaises(ValueError):assessment_insights.record(self.c,bad)
        bad=self.pt();bad['bank']=''
        with self.assertRaises(ValueError):assessment_insights.record(self.c,bad)
        self.assertFalse(assessment_insights.report(self.c)['portuguese'])

    def test_delete_only_matching_portuguese_exam(self):
        ident=assessment_insights.record(self.c,self.pt())['id']
        assessment_insights.remove(self.c,ident)
        self.assertFalse(assessment_insights.report(self.c)['portuguese'])
        with self.assertRaises(ValueError):assessment_insights.remove(self.c,ident)
if __name__=='__main__':unittest.main()
