"""Testes determinísticos: ciclos persistentes, microciclos e rodadas de 30 min."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core,cycle_planner

class CyclePlannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.c=core.connect(Path(self.tmp.name)/'test.db')
    def tearDown(self):
        self.c.close();self.tmp.cleanup()
    def test_cycle_two_blocks_auto_new_round_without_study_sessions(self):
        cid=cycle_planner.create(self.c,'Ciclo SEFAZ','Ciclo')['id']
        a=cycle_planner.add_segment(self.c,cid,'Contabilidade Geral','Balanço patrimonial','Teoria',1)['id']
        z=cycle_planner.add_segment(self.c,cid,'Direito Tributário','Obrigações','Questões',1)['id']
        self.assertFalse(cycle_planner.mark(self.c,a,1,True)['round_completed'])
        # Reenvio idempotente não duplica marcador.
        self.assertFalse(cycle_planner.mark(self.c,a,1,True)['round_completed'])
        self.assertTrue(cycle_planner.mark(self.c,z,1,True)['round_completed'])
        row=cycle_planner.read(self.c)['cycles'][0]
        self.assertEqual(row['round_number'],2)
        self.assertEqual(row['completed_rounds'],1)
        self.assertEqual(row['marked_blocks'],0)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM sessions').fetchone()[0],0)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM study_cycle_marks').fetchone()[0],2)
    def test_microcycle_under_parent(self):
        cid=cycle_planner.create(self.c,'Fiscal')['id']
        micro=cycle_planner.create(self.c,'Obrigação tributária','Microciclo',cid)['id']
        cycle_planner.add_segment(self.c,micro,'Direito Tributário','Obrigação tributária','Lei seca',3)
        r=cycle_planner.read(self.c)
        m=next(x for x in r['cycles'] if x['id']==micro)
        self.assertEqual(m['parent_id'],cid)
        self.assertEqual(m['planned_blocks'],3)
        self.assertEqual(r['block_minutes'],30)
        with self.assertRaises(ValueError):cycle_planner.create(self.c,'Aninhado','Microciclo',micro)
    def test_invalid_subject_time_and_mark(self):
        cid=cycle_planner.create(self.c,'Plano semanal','Semana fixa')['id']
        with self.assertRaises(ValueError):cycle_planner.add_segment(self.c,cid,'Matéria fictícia','','Teoria',1)
        with self.assertRaises(ValueError):cycle_planner.add_segment(self.c,cid,'Português','','Teoria',0)
        with self.assertRaises(ValueError):cycle_planner.add_segment(self.c,cid,'Português','','Teoria',13)
        seg=cycle_planner.add_segment(self.c,cid,'Português','Sintaxe','Revisão',2)['id']
        with self.assertRaises(ValueError):cycle_planner.mark(self.c,seg,3,True)
        cycle_planner.mark(self.c,seg,1,True)
        cycle_planner.mark(self.c,seg,1,False)
        self.assertEqual(cycle_planner.read(self.c)['cycles'][0]['marked_blocks'],0)
if __name__=='__main__':unittest.main()
