"""Testes HTTP do painel local, com SQLite isolado do banco pessoal."""
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request,urlopen

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core
from web_server import AppHandler, current_week

class WebServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.orig=core.DB_PATH
        core.DB_PATH=Path(self.tmp.name)/'fixture.db'
        self.c=core.connect();self.c.close()
        self.http=ThreadingHTTPServer(('127.0.0.1',0),AppHandler)
        self.t=threading.Thread(target=self.http.serve_forever,daemon=True)
        self.t.start()
        self.base=f'http://127.0.0.1:{self.http.server_port}'
    def tearDown(self):
        self.http.shutdown();self.http.server_close();self.t.join(timeout=2)
        core.DB_PATH=self.orig
        self.tmp.cleanup()
    def call(self,path,obj=None,origin=True):
        headers={}
        if obj is not None:
            headers={'Content-Type':'application/json'}
            if origin:headers['Origin']=self.base
        data=json.dumps(obj).encode() if obj is not None else None
        req=Request(self.base+path,data=data,headers=headers)
        try:
            with urlopen(req,timeout=5) as r:return r.status,json.loads(r.read())
        except HTTPError as e:return e.code,json.loads(e.read())
    def test_overview_empty_and_healthy(self):
        code,health=self.call('/api/health');self.assertEqual(code,200)
        code,state=self.call('/api/overview');self.assertEqual(code,200)
        self.assertEqual(state['metrics']['weekly_minutes'],0)
        self.assertIsNone(state['metrics']['last30_questions']['rate'])
        self.assertGreaterEqual(len(state['subjects']),20)
    def test_plan_then_complete_then_session(self):
        today=current_week().isoformat()
        self.assertEqual(self.call('/api/day',{'day':today,'kind':'Plantão','minutes':900})[0],200)
        state=self.call('/api/overview')[1]
        self.assertEqual(state['days'][0]['cap_minutes'],120)
        code,res=self.call('/api/plan/generate',{'week':today});self.assertEqual(code,200)
        state=self.call('/api/overview')[1]
        self.assertGreater(len(state['plans']),0)
        task=state['plans'][0]
        self.assertEqual(self.call('/api/task/complete',{'id':task['id'],'status':'Concluída'})[0],200)
        state=self.call('/api/overview')[1]
        self.assertEqual(state['done'],1)
        self.assertEqual(state['metrics']['weekly_minutes'],0)
        self.assertEqual(self.call('/api/session',{'subject':'Direito Tributário','method':'Teoria','minutes':35,'kind':'Livre leve'})[0],200)
        state=self.call('/api/overview')[1]
        self.assertEqual(state['metrics']['weekly_minutes'],35)
    def test_questions_validate_rates(self):
        args={'subject':'Contabilidade Geral','total':20,'correct':18}
        self.assertEqual(self.call('/api/questions',args)[0],200)
        self.assertEqual(self.call('/api/overview')[1]['metrics']['week_questions']['rate'],.9)
        args['correct']=22
        self.assertEqual(self.call('/api/questions',args)[0],400)
    def test_reject_other_origin(self):
        r=Request(self.base+'/api/setting',data=b'{"weekly_target_minutes":1800}',headers={'Content-Type':'application/json','Origin':'https://attacker.invalid'})
        with self.assertRaises(HTTPError) as cm:urlopen(r,timeout=5)
        self.assertEqual(cm.exception.code,403)
    def test_new_component_files(self):
        req=Request(self.base+'/modules/assessments.js')
        with urlopen(req,timeout=5) as r:
            self.assertEqual(r.status,200)
            self.assertIn(b'assessmentsView',r.read())
        self.assertEqual(self.call('/modules/..%2Fcore.py')[0],404)
    def test_assessment_api_and_rate_isolated(self):
        payload={'day':'2026-11-05','title':'Simulado local','total':30,
                 'correct':21,'wrong':7,'blank':2,'guesses':5}
        code,obj=self.call('/api/assessment/mock',payload)
        self.assertEqual(code,201)
        state=self.call('/api/overview')[1]
        self.assertEqual(state['assessments']['mock_rate'],.7)
        self.assertEqual(state['metrics']['week_questions']['total'],0)
        code,_=self.call('/api/assessment/mock',dict(payload,blank=5))
        self.assertEqual(code,400)
        code,_=self.call('/api/assessment/essay',{'day':'2026-11-05','topic':'Prova discursiva','grade':8,'maximum_grade':10})
        self.assertEqual(code,201)
        state=self.call('/api/overview')[1]
        self.assertEqual(state['assessments']['essay_count'],1)
        code,_=self.call('/api/assessment/delete',{'kind':'mock_exams','id':obj['id']})
        self.assertEqual(code,200)
        self.assertEqual(self.call('/api/overview')[1]['assessments']['mock_count'],0)
    def test_cross_site_fetch_blocked(self):
        req=Request(self.base+'/api/assessment/mock',data=b'{}',headers={
            'Content-Type':'application/json','Origin':self.base,'Sec-Fetch-Site':'cross-site'})
        with self.assertRaises(HTTPError) as cm:urlopen(req,timeout=5)
        self.assertEqual(cm.exception.code,403)
    def test_adaptive_preview_read_only_and_apply(self):
        code, data=self.call('/api/adaptive')
        self.assertEqual(code,200)
        self.assertIn('diagnosis',data)
        self.assertIn('preview',data)
        self.assertEqual(data['preview']['task_count']>0,True)
        state=self.call('/api/overview')[1]
        self.assertEqual(len(state['plans']),0)
        self.assertIn('adaptive',state)
        self.assertIn('adaptive_preview',state)
        self.assertEqual(self.call('/api/plan/adaptive',{'week':current_week().isoformat()})[0],400)
        code,result=self.call('/api/plan/adaptive',{'week':current_week().isoformat(),'confirm':True})
        self.assertEqual(code,200)
        self.assertEqual(result['mode'],'Aplicado')
        state=self.call('/api/overview')[1]
        self.assertEqual(result['activities'],len(state['plans']))
        self.assertEqual(self.call('/api/plan/adaptive',{'week':current_week().isoformat(),'confirm':'true'})[0],400)

    def test_adaptive_static_module_served(self):
        with urlopen(self.base+'/modules/adaptive.js',timeout=5) as r:
            self.assertEqual(r.status,200)
            self.assertIn(b'adaptiveView',r.read())

    def test_no_path_traversal(self):
        self.assertEqual(self.call('/some/../secrets')[0],404)

if __name__=='__main__':unittest.main()