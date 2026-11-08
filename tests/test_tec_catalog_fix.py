"""Regression checks for TEC Avançado, legacy Qconcursos and lesson UI."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent))
from _isolation import isolate
import core
import sources
import lesson_catalog

class TecCatalogTests(unittest.TestCase):
    def setUp(self):
        isolate(self)
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.c=core.connect(self.root/'test.db')
        self.p=patch.object(sources,'TEC_ROOT',self.root/'tec')
        self.p.start()
    def tearDown(self):
        self.p.stop();self.c.close();self.tmp.cleanup()
    def test_tec_bookmarks_separate_legacy(self):
        sources.register_bookmark(self.c,'Antigo','https://www.qconcursos.com/questoes/123')
        sources.register_tec_bookmark(self.c,'Caderno FCC','https://www.tecconcursos.com.br/questoes/999')
        self.assertEqual(len(sources.list_bookmarks(self.c)),1)
        self.assertEqual(len(sources.list_bookmarks(self.c,'TEC Concursos')),1)
        self.assertEqual(sources.list_bookmarks(self.c,'TEC Concursos')[0]['title'],'Caderno FCC')
        for url in ('https://www.qconcursos.com/questoes/123','https://tecconcursos.com.br.evil.test/x',
                    'http://tecconcursos.com.br/x','https://user:pass@tecconcursos.com.br/x'):
            with self.subTest(url=url),self.assertRaises(ValueError):
                sources.register_tec_bookmark(self.c,'Block',url)
    def test_tec_import_separate_idempotent_and_no_login(self):
        d=self.root/'tec';d.mkdir()
        (d/'resultado.csv').write_text('data;disciplina;assunto;total;acertos;banca;link;id\n'
              '07/11/2026;Direito Tributário;Tributo;20;15;FCC;https://www.tecconcursos.com.br/questoes/25;tec-25\n',encoding='utf-8')
        self.assertEqual(sources.preview_csv(self.c,'resultado.csv','TEC Concursos')['questions'],20)
        self.assertEqual(sources.import_csv(self.c,'resultado.csv','TEC Concursos')['inserted'],1)
        self.assertEqual(sources.import_csv(self.c,'resultado.csv','TEC Concursos')['inserted'],0)
        row=self.c.execute('SELECT platform,source,total,correct FROM questions').fetchone()
        self.assertEqual(tuple(row),('TEC Concursos','tec-user-csv',20,15))
        self.assertEqual(sources.status(self.c)['tec_csv_files'],['resultado.csv'])
    def test_tec_csv_rejects_qc_url(self):
        (self.root/'tec').mkdir()
        (self.root/'tec'/'fail.csv').write_text('data;disciplina;total;acertos;link\n07/11/2026;Direito;10;7;https://www.qconcursos.com/x\n',encoding='utf8')
        with self.assertRaises(ValueError):sources.preview_csv(self.c,'fail.csv','TEC Concursos')
    def test_catalog_available_even_without_pdfs(self):
        st=sources.status(self.c)
        self.assertEqual(st['catalog']['total_lessons'],125)
        self.assertEqual(st['materials'],[])
        self.assertEqual(st['tec_bookmarks'],[])
        self.assertIn('MATERIAL TEÓRICO',st['expected_external_path'])

if __name__=='__main__':unittest.main()