"""Metadados de disciplinas, tópicos, PDF e incidência não especulativa."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core, sources, study_guide, curriculum_insights, lesson_catalog

class CurriculumTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.c=core.connect(Path(self.tmp.name)/'test.db')
        sources.prepare(self.c)
        self.guide=study_guide.create(self.c,'Meu edital',25)['id']
    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def pdf(self,subject='Direito Tributário',topic='',lesson='Aula 03'):
        self.c.execute("""INSERT INTO study_materials
          (relative_path,file_name,digest,size_bytes,subject,topic,lesson,updated_at,material_type)
          VALUES(?,?,?,?,?,?,?,?,?)""",
          ('dummy/aula03.pdf','aula03.pdf','123',100,subject,topic,lesson,'2026-11-08','Teoria'))
        self.c.commit()

    def test_catalog_links_pdf_to_exact_lesson(self):
        self.pdf()
        sample=[{'disciplina':'Direito Tributário','aula':'Aula 03','assunto':'Obrigação tributária'}]
        with patch.object(curriculum_insights,'catalog_lessons',return_value=sample):
            data=curriculum_insights.report(self.c)
        self.assertEqual(data['stats']['pdfs'],1)
        self.assertEqual(data['total_topics'],1)
        self.assertEqual(data['subjects'][0]['topics'][0]['pdfs'][0]['name'],'aula03.pdf')
        self.assertIsNone(data['subjects'][0]['topics'][0]['incidence_pct'])

    def test_completion_and_incidence_preserve_source(self):
        study_guide.save_entry(self.c,self.guide,{
          'subject':'Direito Tributário','topic':'Obrigação tributária',
          'incidence_pct':8.41,'source_type':'Bizu Estratégico',
          'source_reference':'Aula 18'})
        e=study_guide.read(self.c)['entries'][0]
        study_guide.progress(self.c,self.guide,e['id'],'Concluído',100)
        with patch.object(curriculum_insights,'catalog_lessons',return_value=[]):
            data=curriculum_insights.report(self.c)
        x=data['subjects'][0]['topics'][0]
        self.assertEqual(x['progress'],100)
        self.assertEqual(x['incidence_pct'],8.41)
        self.assertIn('Bizu',x['incidence_source'])
        self.assertEqual(data['total_progress_pct'],100)

    def test_uncatalogued_pdf_never_creates_fabricated_topic(self):
        self.pdf(topic='')
        with patch.object(curriculum_insights,'catalog_lessons',return_value=[]):
            data=curriculum_insights.report(self.c)
        self.assertEqual(data['total_topics'],0)
        self.assertEqual(len(data['unlinked_pdfs']),1)

    def test_status_also_recovers_lessons_from_pdf_metadata(self):
        self.pdf(topic='Fato gerador do ICMS',lesson='Aula 05')
        with patch.object(lesson_catalog,'lessons',return_value=[]):
            data=lesson_catalog.status(self.c)
        dt=next(x for x in data['subjects'] if x['subject']=='Direito Tributário')
        self.assertEqual(dt['lesson_count'],1)
        self.assertEqual(dt['lessons'][0]['topic'],'Fato gerador do ICMS')
        self.assertIsNone(dt['lessons'][0]['incidence_pct'])

if __name__=='__main__':unittest.main()
