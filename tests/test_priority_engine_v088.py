"""Prioridade de 1–10, precedência manual e evidências locais verificáveis."""
import sys,tempfile,unittest,sqlite3
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core,topic_importance,priority_engine,curriculum_evidence,curriculum_insights,study_guide

class PriorityEngineTests(unittest.TestCase):
    def test_absence_of_data_is_not_fabricated(self):
        z=priority_engine.score(subject_weight=10)
        self.assertIsNone(z['priority'])
        self.assertEqual(z['evidence_level'],'insuficiente')
    def test_high_incidence_and_low_performance(self):
        z=priority_engine.score(incidence_pct=28,total_questions=30,correct_questions=6,
                                 progress_pct=15,subject_weight=10)
        self.assertGreaterEqual(z['priority'],8)
        self.assertEqual(z['evidence_level'],'alta')
        self.assertEqual(z['suggested_method'],'Caderno de erros')
    def test_only_small_question_sample_is_insufficient(self):
        z=priority_engine.score(total_questions=2,correct_questions=0,subject_weight=10)
        self.assertIsNone(z['priority'])
        self.assertTrue(z['sample_small'])
    def test_missing_incidence_not_zero(self):
        z=priority_engine.score(total_questions=20,correct_questions=15,subject_weight=8)
        self.assertTrue(1<=z['priority']<=10)
        self.assertNotIn('incidence',z['factors'])
    def test_reject_bad_metrics(self):
        with self.assertRaises(ValueError):priority_engine.score(total_questions=5,correct_questions=9)
        with self.assertRaises(ValueError):priority_engine.score(incidence_pct=-4)

class PriorityPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.c=core.connect(Path(self.tmp.name)/'test.sqlite3')
    def tearDown(self):self.c.close();self.tmp.cleanup()
    def test_v1_five_level_remains_unchanged_when_migrating(self):
        self.c.execute('''CREATE TABLE topic_importance(
          subject_key TEXT NOT NULL,topic_key TEXT NOT NULL,
          level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 5),
          updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY(subject_key,topic_key))''')
        self.c.execute('INSERT INTO topic_importance(subject_key,topic_key,level) VALUES(?,?,?)',
                       ('direito tributario','obrigacao tributaria',5))
        self.c.commit()
        old=topic_importance.read_details(self.c)
        self.assertEqual(old[('direito tributario','obrigacao tributaria')]['scale'],'1-5')
        topic_importance.save(self.c,'Direito Tributário','Obrigação Tributária',9)
        new=topic_importance.read_details(self.c)
        self.assertEqual(new[('direito tributario','obrigacao tributaria')]['level'],9)
        self.assertEqual(new[('direito tributario','obrigacao tributaria')]['scale'],'1-10')
        legacy=self.c.execute('SELECT level FROM topic_importance').fetchone()[0]
        self.assertEqual(legacy,5)
    def test_priority_persists_and_validation(self):
        topic_importance.save(self.c,'Contabilidade Geral','Ativo',10)
        self.assertEqual(topic_importance.read(self.c)[('contabilidade geral','ativo')],10)
        with self.assertRaises(ValueError):
            topic_importance.save(self.c,'Contabilidade Geral','Ativo',11)
        with self.assertRaises(ValueError):
            topic_importance.save(self.c,'Contabilidade Geral','Ativo',True)
        self.assertEqual(topic_importance.read(self.c)[('contabilidade geral','ativo')],10)
    def test_evidence_conflicting_sources_are_not_combined(self):
        z=[
          dict(subject='Direito Tributário',topic='Obrigação tributária',
               incidence_pct=8.41,material_type='Bizu Estratégico',
               document_reference='BIZU_Aula18.pdf',page=3,excerpt='8,41% das questões'),
          dict(subject='Direito Tributário',topic='Obrigação tributária',
               incidence_pct=9.7,material_type='Passo Estratégico',
               document_reference='PASSO_Aula11.pdf',page=11,excerpt='9,7%')
        ]
        curriculum_evidence.register(self.c,z,verified=True)
        with patch.object(curriculum_insights,'catalog_lessons',return_value=[]):
            state=curriculum_insights.report(self.c)
        item=next(x for x in state['subjects'] if x['subject']=='Direito Tributário')['topics'][0]
        self.assertTrue(item['incidence_conflict'])
        self.assertIsNone(item['incidence_pct'])
        self.assertIn('divergentes',item['incidence_source'])
    def test_unverified_evidence_is_not_a_published_statistic(self):
        z=[dict(subject='Direito Tributário',topic='Novo tema',incidence_pct=23,
                material_type='Bizu Estratégico',document_reference='local.pdf',page=2)]
        curriculum_evidence.register(self.c,z,verified=False)
        self.assertFalse(curriculum_evidence.read_verified(self.c))
    def test_evidence_requires_page_and_source(self):
        with self.assertRaises(ValueError):
            curriculum_evidence.register(self.c,[{'subject':'Direito Tributário','topic':'Tema',
              'incidence_pct':88,'material_type':'Bizu Estratégico','document_reference':'x.pdf'}],verified=True)

if __name__=='__main__':unittest.main()
