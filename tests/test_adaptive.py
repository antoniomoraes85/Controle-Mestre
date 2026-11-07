"""Testes para motor adaptativo com banco temporário, sem dados pessoais."""
import tempfile
import unittest
from pathlib import Path
from datetime import date, timedelta
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import connect,save_topic,save_day,add_questions,add_session,all_rows
from adaptive import diagnose, preview_plan, apply_plan

class AdaptiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.c=connect(Path(self.tmp.name)/'db.sqlite')
        self.monday=date(2026,11,2)
        self.ref=date(2026,11,7)
    def tearDown(self):self.c.close();self.tmp.cleanup()

    def test_no_data_is_not_zero_accuracy(self):
        diag=diagnose(self.c,self.ref)
        self.assertEqual(diag['total_questions_in_window'],0)
        self.assertEqual(diag['coverage'],'Diagnóstico inicial')
        self.assertTrue(diag['recommendations'])
        self.assertTrue(all(x['rate'] is None and x['confidence']=='Insuficiente' for x in diag['recommendations']))
        self.assertFalse(self.c.execute('select 1 from plans').fetchone())

    def test_weakness_and_error_reason_and_revision(self):
        save_topic(self.c,'Direito Tributário','Obrigação tributária',progress=40,incidence=2)
        add_questions(self.c,'2026-11-04','Direito Tributário','Obrigação tributária',40,14,error_type='Confusão conceitual')
        self.c.execute("INSERT INTO reviews(created_on,due_on,subject,topic,status,source) VALUES(?,?,?,?,?,?)",('2026-10-10','2026-11-01','Direito Tributário','Obrigação tributária','Pendente','manual'))
        self.c.commit()
        rec=next(x for x in diagnose(self.c,self.ref,limit=100)['recommendations'] if x['subject']=='Direito Tributário' and x['topic']=='Obrigação tributária')
        self.assertAlmostEqual(rec['rate'],.35)
        self.assertEqual(rec['due_reviews'],1)
        self.assertEqual(rec['main_error'],'Confusão conceitual')
        self.assertEqual(rec['method'],'Revisão')
        self.assertEqual(rec['questions'],40)
        self.assertIn('40',rec['rationale'])

    def test_small_sample_doesnt_imply_weakness(self):
        save_topic(self.c,'Contabilidade Geral','Inventários')
        add_questions(self.c,'2026-11-04','Contabilidade Geral','Inventários',2,0)
        rec=next(x for x in diagnose(self.c,self.ref,limit=100)['recommendations'] if x['topic']=='Inventários')
        self.assertEqual(rec['confidence'],'Insuficiente')
        self.assertEqual(rec['action'],'Consolidar teoria')  # progress=0 informado

    def test_older_questions_excluded(self):
        save_topic(self.c,'Direito Tributário','Lançamento')
        add_questions(self.c,'2026-06-01','Direito Tributário','Lançamento',40,2)
        rec=next(x for x in diagnose(self.c,self.ref,limit=100)['recommendations'] if x['topic']=='Lançamento')
        self.assertEqual(rec['questions'],0)
        self.assertIsNone(rec['rate'])

    def test_preview_readonly_and_availability_shortfall(self):
        for i in range(7):save_day(self.c,self.monday+timedelta(days=i),'Reset')
        save_day(self.c,self.monday,'Plantão',120)
        save_day(self.c,self.monday+timedelta(days=1),'Livre forte',180)
        p=preview_plan(self.c,self.monday,self.ref)
        self.assertEqual(p['target_minutes'],1500)
        self.assertEqual(p['capacity_minutes'],300)
        self.assertEqual(p['total_planned_minutes'],300)
        self.assertEqual(p['shortfall_minutes'],1200)
        self.assertEqual(sum(t['target_minutes'] for t in p['tasks']),300)
        self.assertTrue(all(x['day'] in ('2026-11-02','2026-11-03') for x in p['tasks']))
        self.assertEqual(self.c.execute('select count(*) from plans').fetchone()[0],0)

    def test_plan_preserves_completed_and_requires_confirmation(self):
        for i in range(7):save_day(self.c,self.monday+timedelta(days=i),'Reset')
        save_day(self.c,self.monday,'Livre forte',120)
        save_day(self.c,self.monday+timedelta(days=1),'Livre leve',120)
        self.c.execute("INSERT INTO plans(day,subject,topic,method,target_minutes,priority,rationale,status,batch) VALUES(?,?,?,?,?,?,?,?,?)",('2026-11-02','Direito Tributário','Já concluído','Teoria',50,10,'teste','Concluída','original'))
        self.c.execute("INSERT INTO plans(day,subject,topic,method,target_minutes,priority,rationale,status,batch) VALUES(?,?,?,?,?,?,?,?,?)",('2026-11-02','Direito Civil','Pendente anterior','Teoria',50,10,'teste','Pendente','original'))
        self.c.commit()
        before=self.c.execute('select count(*) from plans').fetchone()[0]
        with self.assertRaises(ValueError):apply_plan(self.c,self.monday)
        self.assertEqual(self.c.execute('select count(*) from plans').fetchone()[0],before)
        r=apply_plan(self.c,self.monday,confirm=True)
        self.assertEqual(r['total_planned_minutes'],240)
        self.assertEqual(r['preserved_completed_minutes'],50)
        self.assertEqual(self.c.execute("select count(*) from plans where status='Concluída'").fetchone()[0],1)
        self.assertEqual(self.c.execute("select count(*) from plans where topic='Pendente anterior'").fetchone()[0],0)
        self.assertEqual(self.c.execute("select sum(target_minutes) from plans").fetchone()[0],240)
        again=apply_plan(self.c,self.monday,confirm=True)
        self.assertEqual(self.c.execute("select sum(target_minutes) from plans").fetchone()[0],240)

    def test_no_topic_questions_appear_in_diagnosis(self):
        save_topic(self.c,'Direito Tributário','Lançamento')
        add_questions(self.c,'2026-11-04','Direito Tributário','',30,10)
        rows=diagnose(self.c,self.ref,limit=100)['recommendations']
        general=next(x for x in rows if x['subject']=='Direito Tributário' and not x['topic'])
        self.assertEqual(general['questions'],30)
        self.assertAlmostEqual(general['rate'],1/3,places=4)

    def test_misleading_progress_not_inferred(self):
        add_questions(self.c,'2026-11-04','Legislação Tributária RS I','ICMS',30,27)
        diag=diagnose(self.c,self.ref,limit=100)
        row=next(x for x in diag['recommendations'] if x['topic']=='ICMS')
        self.assertIsNone(row['progress'])
        self.assertAlmostEqual(row['rate'],.9)

if __name__=='__main__':unittest.main()