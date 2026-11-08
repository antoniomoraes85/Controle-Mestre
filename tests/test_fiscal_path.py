"""Testes da trilha com dados sintéticos, sem acesso a arquivos pessoais."""
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import date,timedelta
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core, sources, fiscal_path

class FiscalPathTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.c=core.connect(Path(self.temp.name)/'test.db')
        self.pdfpatch=patch.object(sources,'PDF_ROOT',Path(self.temp.name)/'docs')
        self.pdfpatch.start()
        self.week=date.today()-timedelta(days=date.today().weekday())
    def tearDown(self):
        self.c.close()
        self.pdfpatch.stop()
        self.temp.cleanup()
    def monday_next(self):
        return self.week+timedelta(days=7)
    def test_activate_explicit_and_idempotent(self):
        self.assertFalse(fiscal_path.status(self.c)['active'])
        self.assertEqual(fiscal_path.activate(self.c)['created'],175)  # 50 históricos + 125 aulas fornecidas
        self.assertEqual(fiscal_path.activate(self.c)['created'],0)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM fiscal_topics').fetchone()[0],175)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM plans').fetchone()[0],0)
    def test_preview_no_side_effect_and_only_valid_dates(self):
        fiscal_path.activate(self.c)
        pre=fiscal_path.preview_week(self.c,self.monday_next(),today=date.today())
        self.assertGreater(pre['task_count'],0)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM fiscal_tasks').fetchone()[0],0)
        self.assertTrue(all(p['day']>=self.monday_next().isoformat() for p in pre['tasks']))
        self.assertLessEqual(pre['planned_minutes'],pre['available_for_trail_minutes'])
        self.assertLessEqual(pre['available_for_trail_minutes'],pre['target_minutes'])
        # Tarefas por tópico respeitam progressão de etapas.
        by_topic={}
        for r in pre['tasks']:
            by_topic.setdefault(r['topic_id'],[]).append(r)
        for vals in by_topic.values():
            vals=sorted(vals,key=lambda t:t['step'])
            self.assertEqual([x['step'] for x in vals],list(range(len(vals))))
            self.assertEqual([x['day'] for x in vals],sorted(x['day'] for x in vals))
    def test_no_application_without_confirmation(self):
        fiscal_path.activate(self.c)
        with self.assertRaises(ValueError):fiscal_path.apply_week(self.c,self.monday_next())
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM fiscal_tasks').fetchone()[0],0)
    def test_apply_does_not_erase_plan_and_refuses_regeneration(self):
        fiscal_path.activate(self.c)
        w=self.monday_next()
        self.c.execute('''INSERT INTO plans(day,subject,topic,method,target_minutes,target_questions,priority,rationale,batch)
            VALUES(?,?,?,?,?,?,?,?,?)''',(w.isoformat(),'Português','Interpretação','Teoria',45,0,5,'fixture','manual'))
        self.c.commit()
        pre=fiscal_path.preview_week(self.c,w)
        self.assertLessEqual(pre['available_for_trail_minutes'],1500)
        n=fiscal_path.apply_week(self.c,w,True)['inserted']
        self.assertGreater(n,0)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM plans').fetchone()[0],1)
        with self.assertRaises(ValueError):fiscal_path.apply_week(self.c,w,True)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM fiscal_tasks').fetchone()[0],n)
    def test_week_zero_capacity_and_plantao(self):
        fiscal_path.activate(self.c)
        w=self.monday_next()
        for i in range(7):
            core.save_day(self.c,w+timedelta(days=i),'Reset',0)
        pre=fiscal_path.preview_week(self.c,w)
        self.assertEqual(pre['task_count'],0)
        self.assertEqual(pre['planned_minutes'],0)
        core.save_day(self.c,w,'Plantão',120)
        pre=fiscal_path.preview_week(self.c,w)
        self.assertLessEqual(pre['planned_minutes'],120)
        self.assertEqual(pre['available_for_trail_minutes'],120)
    def test_recognize_passo_pdfs_and_map_only_existing_materials(self):
        fiscal_path.activate(self.c)
        root=Path(self.temp.name)/'docs'
        for kind in ['Teoria','Passo_Estrategico']:
            dst=root/kind/'Contabilidade Geral'/'aula_00.pdf'
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_bytes(b'%PDF-1.5\n%%EOF\n')
        r=sources.scan_pdfs(self.c)
        self.assertEqual(r['scanned'],2)
        mats=sources.list_materials(self.c)
        self.assertEqual({x['material_type'] for x in mats},{'Teoria','Passo Estratégico'})
        m=mats[0]
        sources.assign_material(self.c,m['id'],'Contabilidade Geral','Patrimônio, ativo, passivo e patrimônio líquido',material_type='Teoria')
        self.assertEqual(sources.path_for_material(self.c,m['id']).name,'aula_00.pdf')
        self.assertTrue(any(x['id']==m['id'] for x in fiscal_path._subject_materials(self.c,'Contabilidade Geral','Patrimônio, ativo, passivo e patrimônio líquido','Teoria')))
    def test_never_credits_future_completed_task(self):
        fiscal_path.activate(self.c)
        w=self.monday_next()
        fiscal_path.apply_week(self.c,w,True)
        task=self.c.execute('SELECT id FROM fiscal_tasks ORDER BY day LIMIT 1').fetchone()[0]
        with self.assertRaises(ValueError):fiscal_path.complete_task(self.c,task,35)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM sessions').fetchone()[0],0)
    def test_complete_real_minutes_questions_and_idempotence(self):
        fiscal_path.activate(self.c)
        # semana em curso (ou semana anterior) garante cronologia para teste
        w=self.week
        # crie tarefas sintéticas em hoje sem gerar calendario comercial
        topic=self.c.execute('SELECT id FROM fiscal_topics LIMIT 1').fetchone()[0]
        today=date.today().isoformat()
        self.c.execute('''INSERT INTO fiscal_tasks(track_id,topic_id,week_start,day,step,method,minutes,target_questions)
           VALUES(?,?,?,?,?,?,?,?)''',(fiscal_path.TRACK_ID,topic,w.isoformat(),today,1,'Questões de fixação',45,12))
        ident=self.c.execute('SELECT id FROM fiscal_tasks').fetchone()[0]
        self.c.commit()
        fiscal_path.complete_task(self.c,ident,minutes=42,total=12,correct=8,error_type='Confusão conceitual')
        self.assertEqual(self.c.execute('SELECT SUM(minutes) FROM sessions').fetchone()[0],42)
        self.assertEqual(self.c.execute('SELECT SUM(total) FROM questions').fetchone()[0],12)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM errors').fetchone()[0],1)
        with self.assertRaises(ValueError):fiscal_path.complete_task(self.c,ident,minutes=42,total=12,correct=8)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM questions').fetchone()[0],1)
    def test_require_all_question_fields_and_keep_transaction_clean(self):
        fiscal_path.activate(self.c)
        topic=self.c.execute('SELECT id FROM fiscal_topics LIMIT 1').fetchone()[0]
        today=date.today().isoformat()
        self.c.execute('''INSERT INTO fiscal_tasks(track_id,topic_id,week_start,day,step,method,minutes)
          VALUES(?,?,?,?,?,?,?)''',(fiscal_path.TRACK_ID,topic,self.week.isoformat(),today,0,'Teoria',70))
        ident=self.c.execute('SELECT id FROM fiscal_tasks').fetchone()[0]
        self.c.commit()
        with self.assertRaises(ValueError):fiscal_path.complete_task(self.c,ident,35,total=10,correct=7)
        with self.assertRaises(ValueError):fiscal_path.complete_task(self.c,ident,35,total=10)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM sessions').fetchone()[0],0)

if __name__=='__main__':unittest.main()