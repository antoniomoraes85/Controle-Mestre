"""Testes sem conteúdo licenciado e sem utilizar dados privados do usuário."""
import os
import sys
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core
import sources
import backup_manager

class SourcesTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.db=self.root/'fixture.sqlite3'
        self.original=core.DB_PATH
        core.DB_PATH=self.db
        self.conn=core.connect()
        self.pdf_root=self.root/'materiais'
        self.qc_root=self.root/'qconcursos'
        self.patch_pdf=patch.object(sources,'PDF_ROOT',self.pdf_root)
        self.patch_qc=patch.object(sources,'QC_ROOT',self.qc_root)
        self.patch_pdf.start();self.patch_qc.start()
    def tearDown(self):
        self.conn.close()
        core.DB_PATH=self.original
        self.patch_pdf.stop();self.patch_qc.stop()
        self.temp.cleanup()

    def test_pdf_catalog_keeps_only_metadata_and_mappings(self):
        p=self.pdf_root/'Direito Tributário'/'curso-122-aula-05-completo.pdf'
        p.parent.mkdir(parents=True)
        p.write_bytes(b'%PDF-1.7\nsynthetic test pdf\n%%EOF')
        a=sources.scan_pdfs(self.conn);self.assertEqual(a['scanned'],1)
        items=sources.list_materials(self.conn)
        self.assertEqual(len(items),1)
        self.assertEqual(items[0]['lesson'],'Aula 05')
        self.assertNotIn('synthetic test pdf',repr(items))
        sources.assign_material(self.conn,items[0]['id'],'Direito Tributário','Obrigação tributária','Curso Fiscal','Aula 05')
        self.assertEqual(sources.list_materials(self.conn)[0]['topic'],'Obrigação tributária')
        self.assertEqual(sources.scan_pdfs(self.conn)['scanned'],1)
        self.assertEqual(len(sources.list_materials(self.conn)),1)
        p.unlink();sources.scan_pdfs(self.conn)
        self.assertEqual(sources.list_materials(self.conn)[0]['status'],'Ausente')

    def test_pdf_symlink_and_nonpdf_ignored(self):
        self.pdf_root.mkdir(parents=True)
        (self.pdf_root/'not_pdf.pdf').write_text('not a pdf')
        outside=self.root/'outside.pdf';outside.write_bytes(b'%PDF-1.4\n')
        (self.pdf_root/'alias.pdf').symlink_to(outside)
        r=sources.scan_pdfs(self.conn)
        self.assertEqual(r['scanned'],0)
        self.assertEqual(len(r['errors']),2)

    def test_bookmark_allows_only_official_host(self):
        sources.register_bookmark(self.conn,'Minha FCC','https://www.qconcursos.com/questoes-de-concursos/questoes?x=1')
        self.assertEqual(len(sources.list_bookmarks(self.conn)),1)
        for value in ('http://www.qconcursos.com/questoes','https://qconcursos.com.evil.invalid/',
                      'file:///etc/passwd','https://user:pw@qconcursos.com/'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                sources.register_bookmark(self.conn,'Teste',value)

    def test_csv_import_is_transactional_idempotent_and_no_text(self):
        self.qc_root.mkdir(parents=True)
        f=self.qc_root/'resultado.csv'
        f.write_text('data;disciplina;assunto;total;acertos;banca;link;id\n'
                     '07/11/2026;Direito Tributário;Obrigação tributária;20;15;FCC;https://www.qconcursos.com/cadernos/123;batch-A\n'
                     '06/11/2026;Direito Constitucional;CF;10;9;FCC;;batch-B\n',encoding='utf-8')
        pre=sources.preview_csv(self.conn,'resultado.csv')
        self.assertEqual(pre['questions'],30)
        r=sources.import_csv(self.conn,'resultado.csv')
        self.assertEqual(r['inserted'],2)
        self.assertEqual(sources.import_csv(self.conn,'resultado.csv')['inserted'],0)
        stats=self.conn.execute("SELECT SUM(total),SUM(correct) FROM questions WHERE source='qconcursos-user-csv'").fetchone()
        self.assertEqual(tuple(stats),(30,24))
        self.assertFalse(self.conn.execute('SELECT COUNT(*) FROM sessions').fetchone()[0])
        f.write_text(f.read_text(encoding='utf-8').replace('20;15','20;14'),encoding='utf-8')
        # Same external ID, edited export -> unchanged to avoid dupes.
        r=sources.import_csv(self.conn,'resultado.csv')
        self.assertEqual(r['inserted'],0)
        self.assertEqual(r['skipped'],2)

    def test_csv_rejects_invalid_rows_before_writing(self):
        self.qc_root.mkdir(parents=True)
        f=self.qc_root/'invalid.csv'
        f.write_text('data;disciplina;total;acertos\n2026-11-07;Contabilidade Geral;10;6\n2026-11-07;Direito;10;15\n',encoding='utf-8')
        with self.assertRaises(ValueError): sources.import_csv(self.conn,f.name)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM questions WHERE source='qconcursos-user-csv'").fetchone()[0],0)
        for name in ('../invalid.csv','evil/invalid.csv','other.txt','..\\evil.csv'):
            with self.subTest(name=name),self.assertRaises(ValueError):sources.preview_csv(self.conn,name)

    def test_backup_restores_consistent_data(self):
        self.conn.execute("INSERT INTO sessions(day,subject,topic,method,minutes,day_type,source) VALUES ('2026-11-07','Direito Tributário','Teste','Teoria',35,'Livre leve','synthetic')")
        self.conn.commit()
        dest=backup_manager.make_backup(self.db,self.root/'backups',force=True)
        self.assertTrue(backup_manager.verify_backup(dest))
        with sqlite3.connect(str(dest)) as check:
            self.assertEqual(check.execute('SELECT SUM(minutes) FROM sessions').fetchone()[0],35)
        dest2=backup_manager.make_backup(self.db,self.root/'backups')
        self.assertEqual(dest,dest2)

if __name__=='__main__':unittest.main()