"""Conector Anki: testes sem tocar na coleção particular do usuário."""
import sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent))
from _isolation import isolate
import core,anki_bridge,fiscal_path,sources

class AnkiBridgeTests(unittest.TestCase):
    def setUp(self):
        isolate(self)
        self.tmp=tempfile.TemporaryDirectory()
        self.c=core.connect(Path(self.tmp.name)/'data.db')
    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()
    def test_version_and_deck_mapping_nine(self):
        def mock(action,params=None):
            if action=='version':return 5
            if action=='deckNamesAndIds':return {
                'Contabilidade Geral::Questões':11,
                'Reforma Tributária (LC nº 227/2026)::Lei Seca':12,
                'Reforma Tributária (EC nº 132/2023 e LC nº 214/2025)::Mapa':13,
                'Outros::Música':14}
            raise AssertionError('Não deveria consultar cartões na detecção')
        with patch.object(anki_bridge,'invoke',side_effect=mock):d=anki_bridge.detect()
        self.assertEqual(d['selected_decks'],3)
        self.assertEqual([x['subject'] for x in d['decks'] if '227' in x['deck']],['Reforma Tributária — LC 227'])
    def test_allowlist_rejects_mutation(self):
        with self.assertRaises(ValueError):anki_bridge.invoke('addNote',{'note':{}})
        with self.assertRaises(ValueError):anki_bridge.invoke('setEaseFactors',{})
    def test_collection_snapshot_counts_no_double_count(self):
        calls=[]
        def mock(action,params=None):
            calls.append(action)
            if action=='version':return 5
            if action=='deckNamesAndIds':return {'Contabilidade Geral':1,'Contabilidade Geral::Lei Seca':2}
            query=params['query']
            if 'Lei Seca' in query:
                if 'rated:1' in query:return [1]
                if 'is:new' in query:return []
                return [1,2]
            if 'is:due' in query:return [1,2]
            if 'is:new' in query:return [3]
            if 'rated:1' in query:return [1]
            return [1,2,3]
        with patch.object(anki_bridge,'invoke',side_effect=mock):snap=anki_bridge.collect_snapshot('Principal')
        self.assertEqual(snap['subjects'][0]['card_count'],3)
        self.assertEqual(snap['subjects'][0]['due_count'],2)
        self.assertEqual(snap['subjects'][0]['new_count'],1)
        self.assertTrue(all(c in anki_bridge.ALLOWED for c in calls))
        with self.assertRaises(ValueError):anki_bridge.save_snapshot(self.c,snap,False)
        anki_bridge.save_snapshot(self.c,snap,True)
        anki_bridge.save_snapshot(self.c,snap,True)
        self.assertEqual(self.c.execute('SELECT count(*) FROM anki_live_snapshots').fetchone()[0],1)
        self.assertEqual(self.c.execute('SELECT count(*) FROM sessions').fetchone()[0],0)
        self.assertEqual(self.c.execute('SELECT count(*) FROM anki').fetchone()[0],0)
    def test_fail_closed_on_unavailable(self):
        with patch.object(anki_bridge,'invoke',side_effect=ValueError('offline')):
            with self.assertRaisesRegex(ValueError,'offline'):anki_bridge.detect()
        self.assertEqual(self.c.execute('SELECT count(*) FROM sessions').fetchone()[0],0)
    def test_existing_track_enriched_no_old_tasks_removed(self):
        fiscal_path.activate(self.c)
        topic=self.c.execute('SELECT id FROM fiscal_topics WHERE subject=? LIMIT 1',('Contabilidade Geral',)).fetchone()[0]
        self.c.execute('INSERT INTO fiscal_tasks(track_id,topic_id,week_start,day,step,method,minutes) VALUES (?,?,?,?,?,?,?)',
          (fiscal_path.TRACK_ID,topic,'2026-11-02','2026-11-03',0,'Teoria',70))
        self.c.execute('DELETE FROM fiscal_topics WHERE subject=?',('Direito Civil',))
        self.c.commit()
        result=fiscal_path.activate(self.c)
        self.assertGreater(result['created'],0)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM fiscal_tasks').fetchone()[0],1)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM fiscal_topics WHERE subject=?',('Direito Civil',)).fetchone()[0],6)
    def test_pdf_auto_classification_from_private_folder(self):
        root=Path(self.tmp.name)/'files'
        p1=root/'Teoria'/'Contabilidade de Custos'/'aula-03.pdf'
        p2=root/'Passo_Estrategico'/'Reforma Tributária (LC nº 227-2026)'/'aula_01.pdf'
        for path in (p1,p2):
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(b'%PDF-1.4\n%%EOF\n')
        with patch.object(sources,'PDF_ROOT',root):
            sources.scan_pdfs(self.c)
            rows=sources.list_materials(self.c)
        self.assertEqual({x['subject'] for x in rows},{'Contabilidade de Custos','Reforma Tributária — LC 227'})
        self.assertEqual({x['material_type'] for x in rows},{'Teoria','Passo Estratégico'})

if __name__=='__main__': unittest.main()