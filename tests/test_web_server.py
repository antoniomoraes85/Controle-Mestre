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
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent))
from _isolation import isolate
import core
import sources
from unittest.mock import patch
from web_server import AppHandler, current_week

class WebServerTests(unittest.TestCase):
    def setUp(self):
        isolate(self)
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

    def test_branding_assets_and_favicon_served(self):
        with urlopen(self.base+'/assets/branding/logo_sidebar.svg',timeout=5) as r:
            self.assertEqual(r.status,200)
            self.assertIn('image/svg+xml',r.headers.get('Content-Type',''))
            self.assertIn(b'CONTROLE',r.read())
        with urlopen(self.base+'/assets/branding/banner_hero_premium.webp',timeout=5) as r:
            self.assertEqual(r.status,200)
            self.assertIn('image/webp',r.headers.get('Content-Type',''))
        with urlopen(self.base+'/favicon.ico',timeout=5) as r:
            self.assertEqual(r.status,200)
            self.assertIn('image/x-icon',r.headers.get('Content-Type',''))
        # Traversal é rejeitado
        try:
            with urlopen(self.base+'/assets/branding/../app.js',timeout=5):
                self.fail('Deveria falhar')
        except HTTPError as e:
            self.assertIn(e.code, (400, 404))


    def test_sources_api_and_qc_bookmarks(self):
        code,d=self.call('/api/overview')
        self.assertEqual(code,200)
        self.assertIn('sources',d)
        self.assertEqual(len(d['sources']['materials']),0)
        code,_=self.call('/api/qconcursos/bookmark',{'title':'Bloco FCC','url':'https://www.qconcursos.com/questoes-de-concursos/questoes'})
        self.assertEqual(code,201)
        code,_=self.call('/api/qconcursos/bookmark',{'title':'site invalido','url':'https://qconcursos.com.evil.invalid'})
        self.assertEqual(code,400)
        self.assertEqual(len(self.call('/api/sources')[1]['bookmarks']),1)
        code,_=self.call('/api/qconcursos/import',{'file_name':'missing.csv','confirm':True})
        self.assertEqual(code,400)
        with urlopen(self.base+'/modules/sources.js',timeout=5) as r:
            self.assertIn(b'sourcesView',r.read())

    def test_sources_scan_and_csv_preview_endpoints(self):
        base=Path(self.tmp.name)
        pdfdir=base/'pdfs';pdfdir.mkdir()
        (pdfdir/'curso-111-aula-03.pdf').write_bytes(b'%PDF-1.4\nfixture\n%%EOF')
        csvdir=base/'qc';csvdir.mkdir()
        (csvdir/'my_results.csv').write_text('data;disciplina;assunto;total;acertos;banca\n07/11/2026;Direito Tributário;Obrigação;10;8;FCC\n',encoding='utf-8')
        with patch.object(sources,'PDF_ROOT',pdfdir),patch.object(sources,'QC_ROOT',csvdir):
            self.assertEqual(self.call('/api/sources/scan',{})[1]['scanned'],1)
            _,data=self.call('/api/sources')
            self.assertEqual(len(data['materials']),1)
            self.assertEqual(data['csv_files'],['my_results.csv'])
            self.assertEqual(self.call('/api/qconcursos/preview',{'file_name':'my_results.csv'})[1]['rows'],1)
            self.assertEqual(self.call('/api/qconcursos/import',{'file_name':'my_results.csv'})[0],400)
            self.assertEqual(self.call('/api/qconcursos/import',{'file_name':'my_results.csv','confirm':True})[1]['inserted'],1)
            self.assertEqual(self.call('/api/qconcursos/import',{'file_name':'my_results.csv','confirm':True})[1]['inserted'],0)

    def test_tec_advanced_routes_and_catalog(self):
        base=Path(self.tmp.name)
        tec=base/'tec';tec.mkdir()
        (tec/'resultados.csv').write_text(
            'data;disciplina;assunto;total;acertos;banca;link;id\n'
            '07/11/2026;Contabilidade Geral;Conceitos;12;10;FCC;https://www.tecconcursos.com.br/questoes/123;tec01\n',
            encoding='utf8')
        with patch.object(sources,'TEC_ROOT',tec):
            code,st=self.call('/api/sources')
            self.assertEqual(code,200)
            self.assertEqual(st['catalog']['total_lessons'],125)
            self.assertEqual(st['tec_csv_files'],['resultados.csv'])
            self.assertEqual(self.call('/api/tec/bookmark',{'title':'Caderno Fiscal','url':'https://www.tecconcursos.com.br/cadernos/25'})[0],201)
            self.assertEqual(self.call('/api/tec/bookmark',{'title':'Inseguro','url':'https://evil.example.test/'})[0],400)
            self.assertEqual(self.call('/api/sources')[1]['tec_bookmarks'][0]['title'],'Caderno Fiscal')
            self.assertEqual(self.call('/api/tec/preview',{'file_name':'resultados.csv'})[1]['rows'],1)
            self.assertEqual(self.call('/api/tec/import',{'file_name':'resultados.csv'})[0],400)
            self.assertEqual(self.call('/api/tec/import',{'file_name':'resultados.csv','confirm':True})[1]['inserted'],1)
            self.assertEqual(self.call('/api/tec/import',{'file_name':'resultados.csv','confirm':True})[1]['inserted'],0)
            self.assertIn(self.call('/api/health')[1]['version'], ('0.6.2', '0.7.0', '0.8.1', '0.8.2', '0.8.3'))

    def test_no_path_traversal(self):
        self.assertEqual(self.call('/some/../secrets')[0],404)

if __name__=='__main__':unittest.main()