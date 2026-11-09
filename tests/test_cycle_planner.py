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
    def test_mode_selection_persists_and_keeps_week_plan(self):
        self.assertEqual(cycle_planner.get_mode(self.c),'Semana fixa')
        cid=cycle_planner.create(self.c,'Rodízio fiscal','Ciclo')['id']
        seg=cycle_planner.add_segment(self.c,cid,'Contabilidade Geral','Ativo','Teoria',2)['id']
        cycle_planner.set_mode(self.c,'Ciclo')
        self.assertEqual(cycle_planner.read(self.c)['mode'],'Ciclo')
        self.c.close()
        self.c=core.connect(Path(self.tmp.name)/'test.db')
        self.assertEqual(cycle_planner.get_mode(self.c),'Ciclo')
        self.assertEqual(cycle_planner.read(self.c)['cycles'][0]['segments'][0]['id'],seg)
        cycle_planner.set_mode(self.c,'Semana fixa')
        self.assertEqual(len(cycle_planner.read(self.c)['cycles']),1)
        with self.assertRaises(ValueError):
            cycle_planner.set_mode(self.c,'Modo inexistente')

    def test_reorder_and_edit_before_study(self):
        cid=cycle_planner.create(self.c,'Sequência principal')['id']
        first=cycle_planner.add_segment(self.c,cid,'Contabilidade Geral','','Teoria',2)['id']
        second=cycle_planner.add_segment(self.c,cid,'Direito Tributário','Crédito Tributário','Questões',1)['id']
        self.assertEqual(cycle_planner.read(self.c)['cycles'][0]['segments'][0]['id'],first)
        self.assertTrue(cycle_planner.move_segment(self.c,second,-1)['changed'])
        self.assertEqual(cycle_planner.read(self.c)['cycles'][0]['segments'][0]['id'],second)
        cycle_planner.modify_segment(self.c,first,'Contabilidade Geral','Balanço Patrimonial','Revisão',3)
        data=cycle_planner.read(self.c)['cycles'][0]
        self.assertEqual(data['segments'][1]['topic'],'Balanço Patrimonial')
        self.assertEqual(data['segments'][1]['blocks'],3)
        self.assertEqual(data['planned_blocks'],4)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM sessions').fetchone()[0],0)

    def test_archive_preserves_marked_history_and_locks_edit(self):
        cid=cycle_planner.create(self.c,'Ciclo com histórico')['id']
        seg=cycle_planner.add_segment(self.c,cid,'Contabilidade Geral','Ativo','Teoria',2)['id']
        cycle_planner.mark(self.c,seg,1,True)
        with self.assertRaises(ValueError):
            cycle_planner.modify_segment(self.c,seg,'Direito Tributário','Crédito','Questões',2)
        cycle_planner.archive_segment(self.c,seg)
        self.assertEqual(cycle_planner.read(self.c)['cycles'][0]['segments'],[])
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM study_cycle_marks').fetchone()[0],1)
        with self.assertRaises(ValueError):
            cycle_planner.mark(self.c,seg,2,True)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM sessions').fetchone()[0],0)

    def test_reorder_rejects_invalid_direction(self):
        cid=cycle_planner.create(self.c,'Plano de testes')['id']
        seg=cycle_planner.add_segment(self.c,cid,'Contabilidade Geral','','Teoria',1)['id']
        with self.assertRaises(ValueError):
            cycle_planner.move_segment(self.c,seg,2)
        self.assertFalse(cycle_planner.move_segment(self.c,seg,-1)['changed'])

    def test_anki_method_supported(self):
        cid=cycle_planner.create(self.c,'Ciclo com Anki','Ciclo')['id']
        seg=cycle_planner.add_segment(self.c,cid,'Direito Tributário','CTN','Anki',2)['id']
        cycle=cycle_planner.read(self.c)['cycles'][0]
        self.assertEqual(cycle['segments'][0]['method'],'Anki')
        self.assertIn('Anki',cycle_planner.METHODS)

if __name__=='__main__':unittest.main()
