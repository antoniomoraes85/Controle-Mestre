"""Links de cadernos por assunto: domínios HTTPS seguros e persistência."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core,lesson_question_links

class LessonLinksTests(unittest.TestCase):
  def setUp(self):
    self.tmp=tempfile.TemporaryDirectory()
    self.c=core.connect(Path(self.tmp.name)/'t.db')
  def tearDown(self):
    self.c.close();self.tmp.cleanup()
  def test_tec_qc_and_bizu_links_are_saved_locally(self):
    for i,url in enumerate(['https://www.tecconcursos.com.br/questoes',
                             'https://www.qconcursos.com/questoes',
                             'https://questo.es/qgg7rt']):
      lesson_question_links.save(self.c,{'subject':'Direito Tributário',
        'topic':'Obrigação Tributária','label':'Caderno '+str(i),'url':url})
    self.assertEqual(len(lesson_question_links.list_links(self.c)),3)
    self.assertEqual(self.c.execute('SELECT COUNT(*) FROM questions').fetchone()[0],0)
  def test_phishing_and_insecure_links_rejected(self):
    for url in ['http://questo.es/qgg7rt','https://tecconcursos.com.br.evil.net/a',
                'javascript:alert(1)','https://user:pass@www.qconcursos.com/']:
      with self.assertRaises(ValueError):
        lesson_question_links.save(self.c,{'subject':'A','topic':'B','url':url})
    self.assertFalse(lesson_question_links.list_links(self.c))
  def test_upsert_url_does_not_duplicate(self):
    payload={'subject':'Português','topic':'Interpretação de textos',
             'url':'https://www.qconcursos.com/questoes','label':'Questões'}
    lesson_question_links.save(self.c,payload)
    lesson_question_links.save(self.c,{**payload,'label':'Novo nome'})
    self.assertEqual(len(lesson_question_links.list_links(self.c)),1)
    self.assertEqual(lesson_question_links.list_links(self.c)[0]['label'],'Novo nome')

if __name__=='__main__':unittest.main()
