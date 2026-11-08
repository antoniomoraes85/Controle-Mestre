"""Fixtures sintéticas para estrutura do desktop e catálogo privado (sem PDFs reais)."""
import tempfile
import unittest
from datetime import date,timedelta
from pathlib import Path
from unittest.mock import patch

import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent))
from _isolation import isolate
import core, sources, lesson_catalog, fiscal_path


class FolderCatalogTests(unittest.TestCase):
    def setUp(self):
        isolate(self)
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name).resolve()  # evita caminho curto 8.3 do Windows
        self.conn=core.connect(self.root/'fixture.db')
        self.external=self.root/'Controle-Mestre-main'/'MATERIAL TEÓRICO'
        self.external.mkdir(parents=True)
        self.patcher=patch.object(sources,'PDF_ROOT',self.root/'internal')
        self.patcher.start()
        self.other=patch.object(sources,'external_root',lambda c:self.external)
        self.other.start()
    def tearDown(self):
        self.other.stop();self.patcher.stop();self.conn.close();self.temp.cleanup()

    def pdf(self, folder, name):
        p=self.external/folder/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(b'%PDF-1.7\nsynthetic fixture\n%%EOF')
        return p

    def test_125_user_lessons_and_pending_civil(self):
        st=lesson_catalog.status(self.conn)
        self.assertEqual(st['total_lessons'],125)
        self.assertEqual(st['pending_subjects'],['Direito Civil'])
        by={x['subject']:x['lesson_count'] for x in st['subjects']}
        self.assertEqual(by['Contabilidade Geral'],33)
        self.assertEqual(by['Direito Tributário'],23)
        self.assertEqual(by['Direito Constitucional'],18)
        self.assertEqual(by['Direito Civil'],0)
        self.assertTrue(any(x['lesson']=='Aula 01 - Parte II' for x in st['subjects'][0]['lessons']))

    def test_external_numbered_folders_and_all_types(self):
        folder='1 - Contabilidade Geral e Avançada SEFAZ RS'
        for typ,name in [('Teoria Principal','curso-aula-00.pdf'),
                         ('PASSO ESTRATÉGICO','passo_aula_00.pdf'),
                         ('QUESTÕES','questoes_aula_00.pdf'),
                         ('Simplificado','simplificado_aula_00.pdf')]:
            self.pdf(folder+'/'+typ,name)
        self.pdf('6 - Reforma Tributária LC 227 - 2026/Teoria Principal','curso-aula-01.pdf')
        self.pdf('4 - Direito Tributário/Teoria Principal','aula_01_parte_II.pdf')
        report=sources.scan_pdfs(self.conn)
        self.assertEqual(report['scanned'],6)
        rec=sources.list_materials(self.conn)
        self.assertEqual({x['material_type'] for x in rec},{'Teoria','Simplificado','Questões','Passo Estratégico'})
        self.assertTrue(all(x['relative_path'].startswith('@externo/') for x in rec))
        self.assertEqual(next(x for x in rec if '227' in x['relative_path'])['subject'],'Reforma Tributária — LC 227')
        part=next(x for x in rec if 'parte_II' in x['file_name'])
        self.assertEqual(part['lesson'],'Aula 01 - Parte II')
        self.assertTrue(sources.path_for_material(self.conn,part['id']).is_file())
        self.assertEqual({x['material_type'] for x in rec if 'Contabilidade Geral e Avançada' in x['relative_path']},
                         {'Teoria','Simplificado','Questões','Passo Estratégico'})
        self.assertEqual(sources.scan_pdfs(self.conn)['scanned'],6)
        self.assertEqual(len(sources.list_materials(self.conn)),6)
        catalog=lesson_catalog.status(self.conn)
        contab=next(x for x in catalog['subjects'] if x['subject']=='Contabilidade Geral')
        aula=next(x for x in contab['lessons'] if x['lesson']=='Aula 00')
        self.assertEqual(len(aula['materials']),4)

    def test_no_linking_to_wrong_aula(self):
        self.pdf('1 - Contabilidade Geral e Avançada SEFAZ RS/Teoria Principal','aula_29.pdf')
        sources.scan_pdfs(self.conn)
        self.assertEqual(fiscal_path._subject_materials(self.conn,'Contabilidade Geral',
                         'Aula 00 — Conceitos, objetivos e finalidades da contabilidade','Teoria'),[])
        linked=fiscal_path._subject_materials(self.conn,'Contabilidade Geral',
                          'Aula 29 — CPC 48 - Instrumentos Financeiros','Teoria')
        self.assertEqual(len(linked),1)

    def test_catalog_replaces_generic_topics_in_new_plan(self):
        fiscal_path.activate(self.conn)
        w=date.today()+timedelta(days=(7-date.today().weekday()))
        pre=fiscal_path.preview_week(self.conn,w, today=date.today())
        self.assertTrue(pre['tasks'])
        self.assertTrue(all(x['topic'].startswith('Aula ') for x in pre['tasks']))
        self.assertFalse(any(x['subject']=='Direito Civil' for x in pre['tasks']))
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM fiscal_tasks').fetchone()[0],0)

    def test_adding_missing_catalog_does_not_invent_schedule(self):
        fiscal_path.activate(self.conn)
        w=date.today()+timedelta(days=(7-date.today().weekday()))
        with patch.object(lesson_catalog,'CATALOG_FILE',self.root/'not-supplied.csv'):
            with self.assertRaisesRegex(ValueError,'Catálogo local'):
                fiscal_path.preview_week(self.conn,w)

    def test_external_path_validation_and_auto_detection(self):
        with self.assertRaises(ValueError):
            sources.set_external_root(self.conn,str(self.external),confirm=False)
        with self.assertRaises(ValueError):
            sources.set_external_root(self.conn,str(self.root),confirm=True)
        # Exercitar implementação real, sem patch de retorno.
        with patch.object(sources,'external_root',wraps=sources.external_root) as _unused:
            result=sources.set_external_root(self.conn,str(self.external),confirm=True)
            self.assertTrue(result['ok'])
        self.assertEqual(self.conn.execute('SELECT value FROM settings WHERE key=?',
                         (sources.EXTERNAL_SETTING,)).fetchone()[0],str(self.external.resolve()))

if __name__=='__main__':unittest.main()