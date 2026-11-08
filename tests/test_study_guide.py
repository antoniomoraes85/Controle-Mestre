"""Guia: persistência local, fonte de incidência e progresso."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core,study_guide,bizu_seed

class StudyGuideTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.c=core.connect(Path(self.tmp.name)/'fixture.db')
        self.guide=study_guide.create(self.c,'SEFAZ-RS · meu guia',25)['id']
    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def test_create_and_save_progress(self):
        row={'subject':'Direito Tributário','topic':'Obrigação Tributária',
             'incidence_pct':'8,41','source_type':'Bizu Estratégico',
             'source_reference':'Aula 18','source_page':3}
        self.assertEqual(study_guide.save_entry(self.c,self.guide,row)['inserted'],1)
        item=study_guide.read(self.c)['entries'][0]
        self.assertEqual(item['incidence_pct'],8.41)
        study_guide.progress(self.c,self.guide,item['id'],'Em estudo',75)
        item=study_guide.read(self.c)['entries'][0]
        self.assertEqual(item['status'],'Em estudo')
        self.assertEqual(item['progress'],75)

    def test_import_is_idempotent_and_preserves_progress(self):
        rows=bizu_seed.rows()
        first=study_guide.import_rows(self.c,self.guide,rows,True)
        self.assertGreater(first['inserted'],40)
        first_id=study_guide.read(self.c)['entries'][0]['id']
        study_guide.progress(self.c,self.guide,first_id,'Concluído',100)
        second=study_guide.import_rows(self.c,self.guide,rows,True)
        self.assertEqual(second['inserted'],0)
        item=self.c.execute('SELECT progress FROM study_guide_entries WHERE id=?',(first_id,)).fetchone()
        self.assertEqual(item[0],100)

    def test_missing_historical_percentage_remains_null(self):
        rows=study_guide.import_rows(self.c,self.guide,bizu_seed.rows(),True)
        result=study_guide.read(self.c)['entries']
        reform=[x for x in result if x['subject'].startswith('Reforma Tributária')]
        self.assertTrue(reform)
        self.assertTrue(all(x['incidence_pct'] is None for x in reform))

    def test_invalid_and_unconfirmed_import_are_rejected(self):
        with self.assertRaises(ValueError):
            study_guide.import_rows(self.c,self.guide,[{'subject':'A','topic':'B'}],False)
        with self.assertRaises(ValueError):
            study_guide.save_entry(self.c,self.guide,{'subject':'A','topic':'B','incidence_pct':120})
        with self.assertRaises(ValueError):
            study_guide.progress(self.c,self.guide,99,'Concluído',20)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM study_guide_entries').fetchone()[0],0)


if __name__=='__main__':unittest.main()
