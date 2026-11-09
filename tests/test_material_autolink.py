"""Associação PDF: inferência conservadora sem sobrescrever relações manuais."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core,sources,material_autolink,topic_importance

class MaterialAutolinkTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.c=core.connect(Path(self.tmp.name)/'db.sqlite')
  sources.prepare(self.c)
 def tearDown(self):
  self.c.close();self.tmp.cleanup()
 def insert(self,path,subject='',topic='',lesson='Aula 03',type_='Teoria'):
  name=path.split('/')[-1]
  self.c.execute("""INSERT INTO study_materials
   (relative_path,file_name,digest,size_bytes,subject,topic,lesson,material_type,updated_at)
   VALUES(?,?,?,42,?,?,?,?,?)""",(path,name,name,subject,topic,lesson,type_,'2026-11-09'))
  self.c.commit()
 def test_folder_subject_and_catalog_exact_lesson(self):
  self.insert('@externo/1 - Contabilidade Geral/aula/curso-12345-aula-03-completo.pdf')
  mock=[{'disciplina':'Contabilidade Geral','aula':'Aula 03','assunto':'Balanço patrimonial'}]
  with patch.object(material_autolink,'lessons',return_value=mock):
   result=material_autolink.infer(self.c)
  self.assertEqual(result['subjects_assigned'],1)
  self.assertEqual(result['topics_assigned'],1)
  row=self.c.execute('SELECT subject,topic FROM study_materials').fetchone()
  self.assertEqual(row['subject'],'Contabilidade Geral')
  self.assertEqual(row['topic'],'Balanço patrimonial')
 def test_course_consensus_recovers_flat_pdf(self):
  self.insert('@externo/Cursos/curso-355031-aula-01-completo.pdf',
              subject='Contabilidade Geral',topic='Tema 1',lesson='Aula 01')
  self.insert('@externo/Cursos/curso-355031-aula-02-completo.pdf',
              subject='Contabilidade Geral',topic='Tema 2',lesson='Aula 02')
  self.insert('@externo/Cursos/curso-355031-aula-03-simplificado.pdf')
  with patch.object(material_autolink,'lessons',return_value=[]):
   out=material_autolink.infer(self.c)
  self.assertEqual(out['subjects_assigned'],1)
  self.assertEqual(out['types_assigned'],1)
  row=self.c.execute("SELECT subject,topic,material_type FROM study_materials WHERE lesson='Aula 03'").fetchone()
  self.assertEqual(row['subject'],'Contabilidade Geral')
  self.assertEqual(row['topic'],'')
  self.assertEqual(row['material_type'],'Simplificado')
 def test_ambiguous_course_never_assigns_wrong_subject(self):
  self.insert('@externo/Cursos/curso-22222-aula-01.pdf','Contabilidade Geral',lesson='Aula 01')
  self.insert('@externo/Cursos/curso-22222-aula-02.pdf','Direito Tributário',lesson='Aula 02')
  self.insert('@externo/Cursos/curso-22222-aula-03.pdf')
  with patch.object(material_autolink,'lessons',return_value=[]):
   res=material_autolink.infer(self.c)
  self.assertEqual(res['subjects_assigned'],0)
  row=self.c.execute("SELECT subject FROM study_materials WHERE lesson='Aula 03'").fetchone()[0]
  self.assertEqual(row,'')
 def test_manual_data_survives(self):
  self.insert('@externo/Contabilidade Geral/curso-33333-aula-03.pdf',
              subject='Direito Tributário',topic='Tópico informado por mim')
  with patch.object(material_autolink,'lessons',return_value=[]):
   material_autolink.infer(self.c)
  self.assertEqual(self.c.execute('SELECT topic FROM study_materials').fetchone()[0],
      'Tópico informado por mim')
 def test_manual_importance_is_persistent_and_separate_from_incidence(self):
  topic_importance.save(self.c,'Direito Tributário','Obrigação tributária',5)
  self.assertEqual(topic_importance.read(self.c)[('direito tributario','obrigacao tributaria')],5)
  self.assertEqual(topic_importance.level_for_incidence(None),None)
  self.assertEqual(topic_importance.level_for_incidence(22),5)
if __name__=='__main__':unittest.main()
