"""Persistência e rotas reais de questões, usando SQLite temporário e HTTP local."""
from __future__ import annotations
import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from _isolation import isolate
import core
from web_server import AppHandler


class QuestionHistoryHTTPTests(unittest.TestCase):
    def setUp(self):
        isolate(self)
        self.tmp=tempfile.TemporaryDirectory()
        self.old_db=core.DB_PATH
        core.DB_PATH=Path(self.tmp.name)/'study.sqlite'
        c=core.connect()
        c.close()
        self.server=ThreadingHTTPServer(('127.0.0.1',0),AppHandler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.root=f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        core.DB_PATH=self.old_db
        self.tmp.cleanup()

    def call(self,route,data=None):
        request=Request(self.root+route)
        if data is not None:
            request=Request(self.root+route,data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type':'application/json','Origin':self.root})
        try:
            with urlopen(request,timeout=5) as res:return res.status,json.loads(res.read())
        except HTTPError as e:
            return e.code,json.loads(e.read())

    def header(self,**kwargs):
        obj=dict(subject='Direito Tributário',topic='Obrigação tributária',day='2026-11-08',
                 total=2,correct=1,mode='individual',request_id='demo-stable-001')
        obj.update(kwargs)
        return obj

    def test_health_reports_actual_version(self):
        status,health=self.call('/api/health')
        self.assertEqual(status,200)
        self.assertEqual(health['version'],'0.8.4')

    def test_history_survives_new_connections_and_retries(self):
        status,new=self.call('/api/questions/batch',self.header(mode='batch'))
        self.assertEqual(status,201)
        self.assertEqual(new['status'],'finalized')
        self.assertEqual(self.call('/api/questions/history')[1]['items'][0]['id'],new['batch_id'])
        status,repeat=self.call('/api/questions/batch',self.header(mode='batch'))
        self.assertEqual(status,201)
        self.assertEqual(repeat['batch_id'],new['batch_id'])
        self.assertEqual(len(self.call('/api/questions/history')[1]['items']),1)
        c=core.connect()
        try:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM questions WHERE source='error_tracking'").fetchone()[0],1)
        finally:c.close()

    def test_history_merges_legacy_and_detailed_without_duplicates(self):
        # Registro antigo: não tem metadados de bateria, mas não pode desaparecer.
        c=core.connect()
        try:
            core.add_questions(c,day='2026-11-07',subject='Contabilidade Geral',
                               topic='Estoques',total=12,correct=10,bank='FCC',
                               platform='Qconcursos',source='manual')
        finally:c.close()
        status,new=self.call('/api/questions/batch',self.header(mode='batch'))
        self.assertEqual(status,201)
        status,history=self.call('/api/questions/history')
        self.assertEqual(status,200)
        items=history['items']
        self.assertEqual(len(items),2)
        self.assertEqual(len({item['id'] for item in items}),2)
        legacy=next(item for item in items if item['subject']=='Contabilidade Geral')
        detailed=next(item for item in items if item['subject']=='Direito Tributário')
        self.assertIsNone(legacy['mode'])
        self.assertEqual(legacy['banca'],'FCC')
        self.assertEqual(detailed['mode'],'batch')
        self.assertEqual(detailed['batch_id'],new['batch_id'])

    def test_individual_draft_survives_requests_and_finalizes_once(self):
        status,result=self.call('/api/questions/batch',self.header())
        self.assertEqual(status,201)
        self.assertEqual(result['status'],'draft')
        bid=result['batch_id']
        drafts=self.call('/api/questions/drafts')[1]['items']
        self.assertEqual(drafts[0]['items_added'],0)
        self.assertEqual(drafts[0]['id'],bid)
        self.assertEqual(self.call('/api/overview')[1]['metrics']['week_questions']['total'],0)
        for result_name in ('Correta','Incorreta'):
            status,_=self.call('/api/questions/item',dict(
                batch_id=bid,subject='Direito Tributário',topic='Obrigação tributária',
                result=result_name,primary_cause='Esquecimento'))
            self.assertEqual(status,201)
        status,finish=self.call('/api/questions/batch/finalize',{'batch_id':bid})
        self.assertEqual(status,200)
        self.assertEqual(finish['status'],'finalized')
        self.assertEqual(self.call('/api/questions/batch/finalize',{'batch_id':bid})[0],200)
        self.assertEqual(len(self.call('/api/questions/history')[1]['items']),1)
        self.assertEqual(self.call('/api/questions/drafts')[1]['items'],[])
        self.assertEqual(len(self.call('/api/questions/caderno')[1]),1)
        c=core.connect()
        try:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM questions').fetchone()[0],1)
        finally:c.close()

    def test_cannot_close_partial_or_duplicate_items(self):
        bid=self.call('/api/questions/batch',self.header())[1]['batch_id']
        status,_=self.call('/api/questions/item',dict(batch_id=bid,subject='Direito Tributário',
             topic='Obrigação tributária',result='Correta'))
        self.assertEqual(status,201)
        self.assertEqual(self.call('/api/questions/batch/finalize',{'batch_id':bid})[0],400)
        self.assertEqual(self.call('/api/questions/item',dict(batch_id=bid,subject='Direito Tributário',
             topic='Obrigação tributária',result='Incorreta',question_ref='q2'))[0],201)
        self.assertEqual(self.call('/api/questions/item',dict(batch_id=bid,subject='Direito Tributário',
             topic='Obrigação tributária',result='Incorreta',question_ref='q2'))[0],400)


if __name__=='__main__':
    unittest.main()
