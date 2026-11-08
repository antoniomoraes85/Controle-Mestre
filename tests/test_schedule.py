"""Testes do núcleo de cronogramas (Entrega 1) com banco sintético e temporário."""
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core
import schedule as sch

SUBJECTS = ['Contabilidade Geral', 'Direito Tributário', 'Direito Constitucional',
            'Contabilidade de Custos', 'Reforma Tributária — EC 132 e LC 214',
            'Direito Administrativo', 'Análise das Demonstrações Contábeis',
            'Direito Civil', 'Reforma Tributária — LC 227']
TODAY = date.today()


def iso(offset=0):
    return (TODAY + timedelta(days=offset)).isoformat()


def dump(c):
    return {t: [tuple(r) for r in c.execute(f'SELECT * FROM {t} ORDER BY 1').fetchall()]
            for t in ('schedule_blocks', 'schedule_versions', 'sessions', 'schedule_cycle_items',
                      'schedule_fixed_slots', 'schedule_overrides', 'schedule_config')}


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dbfile = Path(self.temp.name) / 'dados' / 't.db'
        self.c = core.connect(self.dbfile)

    def tearDown(self):
        self.c.close()
        self.temp.cleanup()

    def shift(self, ref=0, **kw):
        # dia 0 = plantão, 1 = pós-plantão, 2-3 = folga
        return sch.configure_shift(self.c, iso(ref), **kw)

    def cycle(self, n=9, minutes=30, blocks=1):
        return [sch.add_cycle_item(self.c, s, block_minutes=minutes, blocks=blocks) for s in SUBJECTS[:n]]

    def done_today(self, uid, minutes=30):
        return sch.complete_block(self.c, uid, minutes, day=iso(0))


class MigrationSafety(Base):
    def test_migration_idempotent_with_backup_and_legacy_untouched(self):
        core.add_session(self.c, iso(-3), 'Direito Civil', '', 'Teoria', 40, fingerprint='legacy')
        before = self.c.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]
        first = sch.migrate(self.c)
        self.assertTrue(first['created'])
        self.assertTrue(Path(first['backup']).is_file())
        self.assertTrue(Path(first['backup']).parent.name == 'backups')
        again = sch.migrate(self.c)
        self.assertFalse(again['created'])
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM sessions').fetchone()[0], before)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM schedule_config WHERE key="schema_version"').fetchone()[0], 1)

    def test_apply_requires_confirmation_and_preview_is_readonly(self):
        self.shift()
        self.cycle(3)
        snapshot = dump(self.c)
        pv = sch.preview(self.c, iso(0))
        self.assertGreater(len(pv['blocks']), 0)
        self.assertEqual(dump(self.c), snapshot)
        with self.assertRaises(ValueError):
            sch.apply(self.c, iso(0))
        self.assertEqual(dump(self.c), snapshot)  # cancelar = não aplicar

    def test_apply_atomic_on_failure(self):
        self.shift()
        self.cycle(3)
        sch.migrate(self.c)
        before = dump(self.c)
        with patch.object(sch.json, 'dumps', side_effect=RuntimeError('falha')):
            with self.assertRaises(RuntimeError):
                sch.apply(self.c, iso(0), confirm=True)
        self.assertEqual(dump(self.c), before)

    def test_apply_creates_backup_and_version(self):
        self.shift()
        self.cycle(3)
        r = sch.apply(self.c, iso(0), confirm=True)
        self.assertTrue(Path(r['backup']).is_file())
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM schedule_versions').fetchone()[0], 1)


class Scale24x72(Base):
    def test_projection_and_defaults(self):
        self.shift(ref=-8)  # ref no passado: padrão se repete a cada 4 dias
        cfg = sch.get_config(self.c)
        kinds = [a['kind'] for a in sch.availability_range(self.c, iso(0), iso(7), cfg)]
        self.assertEqual(kinds, ['Plantão', 'Pós-plantão', 'Folga', 'Folga'] * 2)
        av = sch.availability_range(self.c, iso(0), iso(3), cfg)
        self.assertEqual([a['minutes'] for a in av], [0, 120, 360, 360])

    def test_future_and_past_reference_agree(self):
        self.shift(ref=8)
        cfg = sch.get_config(self.c)
        self.assertEqual(sch.shift_kind(cfg, iso(0)), 'Plantão')
        self.assertEqual(sch.shift_kind(cfg, iso(-4)), 'Plantão')
        self.assertEqual(sch.shift_kind(cfg, iso(1)), 'Pós-plantão')

    def test_configurable_rest_and_availability(self):
        self.shift(post_shift_minutes=30, off_minutes=200, shift_minutes=60)
        av = sch.availability_range(self.c, iso(0), iso(3))
        self.assertEqual([a['minutes'] for a in av], [60, 30, 200, 200])

    def test_extraordinary_unavailability_and_extra_shift(self):
        self.shift()
        sch.set_override(self.c, iso(2), 'Viagem')
        sch.set_override(self.c, iso(3), 'Plantão extra')
        sch.set_override(self.c, iso(5), 'Disponibilidade', 90)
        av = {a['day']: a for a in sch.availability_range(self.c, iso(0), iso(5))}
        self.assertEqual(av[iso(2)]['minutes'], 0)
        self.assertTrue(av[iso(2)]['blocked'])
        self.assertEqual(av[iso(3)]['kind'], 'Plantão')
        self.assertEqual(av[iso(3)]['minutes'], 0)
        self.assertEqual(av[iso(5)]['minutes'], 90)

    def test_no_blocks_on_blocked_or_shift_days(self):
        self.shift()
        self.cycle(9)
        sch.set_override_range(self.c, iso(2), iso(3), 'Férias')
        pv = sch.preview(self.c, iso(0), days=8)
        used = {b['day'] for b in pv['blocks']}
        self.assertNotIn(iso(0), used)   # plantão: zero horas
        self.assertNotIn(iso(2), used)
        self.assertNotIn(iso(3), used)
        self.assertNotIn(iso(4), used)   # novo plantão
        self.assertIn(iso(1), used)

    def test_shift_cap_respects_max_plantao(self):
        self.shift(shift_minutes=600)
        self.assertEqual(sch.availability(self.c, iso(0))['minutes'], 120)


class CycleModel(Base):
    def test_sequence_not_tied_to_weekday_and_respects_capacity(self):
        self.shift()
        self.cycle(9)
        pv = sch.preview(self.c, iso(0), days=3)
        self.assertEqual([b['subject'] for b in pv['blocks']][:4], SUBJECTS[:4])
        per_day = {}
        for b in pv['blocks']:
            per_day[b['day']] = per_day.get(b['day'], 0) + b['minutes']
        self.assertLessEqual(per_day[iso(1)], 120)
        self.assertLessEqual(per_day[iso(2)], 360)

    def test_continuity_after_study_day_shift_and_long_gap(self):
        self.shift()
        ids = self.cycle(9)
        for s in ('c:1:%d:0' % i for i in ids[:3]):
            self.done_today(s)
        self.assertEqual(sch.next_block(self.c)['subject'], SUBJECTS[3])
        # após plantão / vários dias sem estudar: continua do item 4, sem reiniciar
        pv = sch.preview(self.c, iso(0), today=iso(0), days=2)
        self.assertEqual(pv['blocks'][0]['subject'], SUBJECTS[3])
        pv = sch.preview(self.c, iso(12), today=iso(12), days=5)
        self.assertEqual(pv['blocks'][0]['subject'], SUBJECTS[3])
        self.assertEqual(pv['blocks'][0]['run'], 1)

    def test_cycle_wraps_to_next_run_only_after_all_done(self):
        ids = self.cycle(2)
        self.done_today(f'c:1:{ids[0]}:0')
        self.assertEqual(sch.next_block(self.c)['uid'], f'c:1:{ids[1]}:0')
        self.done_today(f'c:1:{ids[1]}:0')
        nxt = sch.next_block(self.c)
        self.assertEqual((nxt['run'], nxt['item_id']), (2, ids[0]))

    def test_interrupt_and_resume(self):
        self.cycle(3)
        first = sch.next_block(self.c)['uid']
        sch.start_block(self.c)
        sch.pause_block(self.c, first, 12, day=iso(0))
        head = sch.next_block(self.c)
        self.assertEqual((head['uid'], head['resume']), (first, True))
        self.assertEqual(head['minutes'], 18)
        sch.start_block(self.c, first)
        sch.complete_block(self.c, first, 20, day=iso(0))
        self.assertEqual(sch.next_block(self.c)['subject'], SUBJECTS[1])
        total = self.c.execute("SELECT SUM(minutes),COUNT(*) FROM sessions WHERE source='schedule'").fetchone()
        self.assertEqual((total[0], total[1]), (32, 2))

    def test_pending_not_completed_automatically(self):
        self.shift()
        self.cycle(3)
        sch.apply(self.c, iso(0), confirm=True)
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM schedule_blocks WHERE status='Concluída'").fetchone()[0], 0)
        with self.assertRaises(ValueError):
            sch.complete_block(self.c, sch.next_block(self.c)['uid'], 0)

    def test_completion_counted_once(self):
        ids = self.cycle(2)
        uid = f'c:1:{ids[0]}:0'
        self.done_today(uid, 30)
        with self.assertRaises(ValueError):
            self.done_today(uid, 30)
        self.assertEqual(self.c.execute('SELECT SUM(minutes) FROM sessions').fetchone()[0], 30)

    def test_future_date_is_rejected_atomically(self):
        ids = self.cycle(2)
        uid = f'c:1:{ids[0]}:0'
        with self.assertRaises(ValueError):
            sch.complete_block(self.c, uid, 30, day=iso(2))
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM sessions').fetchone()[0], 0)
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM schedule_blocks WHERE status='Concluída'").fetchone()[0], 0)

    def test_reorder_preserves_history_and_changes_remaining_order(self):
        ids = self.cycle(5)
        self.done_today(f'c:1:{ids[0]}:0')
        sch.reorder_cycle(self.c, [ids[4], ids[2]])
        self.assertEqual(sch.next_block(self.c)['item_id'], ids[4])
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM schedule_blocks WHERE status='Concluída'").fetchone()[0], 1)
        order = [i['id'] for i in sch.list_cycle_items(self.c)]
        self.assertEqual(order[:2], [ids[4], ids[2]])

    def test_anticipate_and_deactivate_keep_history(self):
        ids = self.cycle(4)
        self.done_today(f'c:1:{ids[2]}:0')  # antecipa o 3º
        seq = []
        for _ in range(3):
            n = sch.next_block(self.c)
            seq.append(n['item_id'])
            self.done_today(n['uid'])
        self.assertEqual(seq, [ids[0], ids[1], ids[3]])
        sch.update_cycle_item(self.c, ids[0], active=0)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM schedule_blocks').fetchone()[0], 4)
        self.assertEqual(sch.next_block(self.c)['run'], 2)

    def test_no_duplicate_blocks_and_stable_ids(self):
        self.shift()
        self.cycle(9)
        sch.apply(self.c, iso(0), confirm=True)
        ids1 = dict(self.c.execute('SELECT uid,id FROM schedule_blocks').fetchall())
        r = sch.apply(self.c, iso(0), confirm=True)
        ids2 = dict(self.c.execute('SELECT uid,id FROM schedule_blocks').fetchall())
        self.assertEqual(ids1, ids2)
        self.assertEqual(r['created'], 0)
        sch.apply(self.c, iso(0), confirm=True)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM schedule_blocks').fetchone()[0], len(ids1))

    def test_replan_after_lost_day_moves_without_accumulating(self):
        self.shift()
        self.cycle(9)
        sch.apply(self.c, iso(0), days=10, confirm=True)
        n_before = self.c.execute('SELECT COUNT(*) FROM schedule_blocks').fetchone()[0]
        sch.set_override(self.c, iso(2), 'Compromisso')
        pv = sch.preview(self.c, iso(0), days=10)
        self.assertGreater(pv['moved'], 0)
        sch.apply(self.c, iso(0), days=10, confirm=True)
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM schedule_blocks WHERE day=?", (iso(2),)).fetchone()[0], 0)
        self.assertGreaterEqual(self.c.execute('SELECT COUNT(*) FROM schedule_blocks').fetchone()[0], 0)
        self.assertLessEqual(self.c.execute('SELECT COUNT(*) FROM schedule_blocks').fetchone()[0], n_before + 0)

    def test_replan_preserves_completed_and_open(self):
        self.shift()
        ids = self.cycle(4)
        sch.apply(self.c, iso(1), confirm=True)
        first = f'c:1:{ids[0]}:0'
        self.done_today(first)
        second = f'c:1:{ids[1]}:0'
        sch.start_block(self.c, second)
        sch.pause_block(self.c, second, 10, day=iso(0))
        sch.apply(self.c, iso(1), confirm=True)
        st = dict(self.c.execute('SELECT uid,status FROM schedule_blocks').fetchall())
        self.assertEqual(st[first], 'Concluída')
        self.assertEqual(st[second], 'Pausada')

    def test_weekly_target_caps_and_deficit_reported(self):
        self.shift()
        self.cycle(9)
        self.c.execute("UPDATE settings SET value='150' WHERE key='weekly_target_min'")
        self.c.commit()
        pv = sch.preview(self.c, iso(0), days=14)
        weeks = {}
        for b in pv['blocks']:
            wk = sch._monday(b['day']).isoformat()
            weeks[wk] = weeks.get(wk, 0) + b['minutes']
        self.assertTrue(all(v <= 150 for v in weeks.values()))
        # meta superior à disponibilidade: déficit exibido, nenhuma hora inventada
        self.c.execute("UPDATE settings SET value='99999' WHERE key='weekly_target_min'")
        self.c.commit()
        pv = sch.preview(self.c, iso(0), days=14)
        self.assertTrue(any(w['availability_deficit_minutes'] > 0 for w in pv['weeks']))
        self.assertLessEqual(pv['planned_minutes'], sum(a['minutes'] for a in pv['availability']))

    def test_duplicate_item_prevented_and_reactivation(self):
        i = sch.add_cycle_item(self.c, 'Direito Civil', block_minutes=30)
        with self.assertRaises(ValueError):
            sch.add_cycle_item(self.c, 'Direito Civil')
        sch.update_cycle_item(self.c, i, active=0)
        self.assertEqual(sch.add_cycle_item(self.c, 'Direito Civil', block_minutes=60), i)

    def test_large_block_for_long_pdf(self):
        self.shift()
        sch.add_cycle_item(self.c, 'Direito Civil', block_minutes=150)
        pv = sch.preview(self.c, iso(0), days=4)
        self.assertEqual(pv['blocks'][0]['minutes'], 150)
        self.assertEqual(pv['blocks'][0]['day'], iso(2))  # só cabe numa folga de 360 min
        self.assertTrue(any('excede' in w for w in pv['warnings']))


class FixedModel(Base):
    def setUp(self):
        super().setUp()
        monday = TODAY - timedelta(days=TODAY.weekday()) + timedelta(days=7)
        self.monday = monday
        sch.set_config(self.c, model='fixed')
        self.s1 = sch.add_fixed_slot(self.c, 0, 'Contabilidade Geral', 60)
        self.s2 = sch.add_fixed_slot(self.c, 0, 'Direito Tributário', 60, modality='Questões de fixação')
        self.s3 = sch.add_fixed_slot(self.c, 1, 'Direito Constitucional', 90, start_time='08:00')

    def plan(self, **kw):
        return sch.preview(self.c, self.monday.isoformat(), today=iso(0), days=7, **kw)

    def test_distribution_by_weekday(self):
        pv = self.plan()
        by = {}
        for b in pv['blocks']:
            by.setdefault(b['day'], []).append(b['subject'])
        self.assertEqual(by[self.monday.isoformat()], ['Contabilidade Geral', 'Direito Tributário'])
        self.assertEqual(by[(self.monday + timedelta(days=1)).isoformat()], ['Direito Constitucional'])
        self.assertEqual(len(by), 2)

    def test_availability_changes_and_blocked_days(self):
        sch.set_override(self.c, self.monday, 'Disponibilidade', 60)
        pv = self.plan()
        mon = [b for b in pv['blocks'] if b['day'] == self.monday.isoformat()]
        self.assertEqual([b['subject'] for b in mon], ['Contabilidade Geral'])
        self.assertTrue(pv['warnings'])
        sch.set_override(self.c, self.monday + timedelta(days=1), 'Descanso')
        pv = self.plan()
        self.assertNotIn((self.monday + timedelta(days=1)).isoformat(), {b['day'] for b in pv['blocks']})

    def test_order_start_time_and_modality_kept(self):
        sch.update_fixed_slot(self.c, self.s1, position=2)
        sch.update_fixed_slot(self.c, self.s2, position=1)
        pv = self.plan()
        mon = [b for b in pv['blocks'] if b['day'] == self.monday.isoformat()]
        self.assertEqual([b['subject'] for b in mon], ['Direito Tributário', 'Contabilidade Geral'])
        self.assertEqual(mon[0]['modality'], 'Questões de fixação')
        tue = [b for b in pv['blocks'] if b['start_time']]
        self.assertEqual(tue[0]['start_time'], '08:00')

    def test_shift_scale_applies_to_fixed(self):
        self.shift(ref=(self.monday - TODAY).days)  # segunda = plantão (zero horas)
        pv = self.plan()
        self.assertNotIn(self.monday.isoformat(), {b['day'] for b in pv['blocks']})

    def test_executed_tasks_preserved_and_slot_edits(self):
        past = TODAY
        slot = sch.add_fixed_slot(self.c, past.weekday(), 'Direito Civil', 45)
        sch.apply(self.c, iso(0), days=1, confirm=True)
        uid = f'f:{iso(0)}:{slot}'
        self.done_today(uid, 45)
        sch.update_fixed_slot(self.c, slot, minutes=60)
        sch.apply(self.c, iso(0), days=1, confirm=True)
        row = self.c.execute('SELECT status,minutes,actual_minutes FROM schedule_blocks WHERE uid=?', (uid,)).fetchone()
        self.assertEqual(tuple(row), ('Concluída', 45, 45))
        sch.update_fixed_slot(self.c, slot, active=0)
        sch.apply(self.c, iso(0), days=1, confirm=True)
        self.assertEqual(self.c.execute('SELECT status FROM schedule_blocks WHERE uid=?', (uid,)).fetchone()[0], 'Concluída')

    def test_validation(self):
        with self.assertRaises(ValueError):
            sch.add_fixed_slot(self.c, 7, 'X', 30)
        with self.assertRaises(ValueError):
            sch.add_fixed_slot(self.c, 1, 'X', 30, start_time='25:00')


class ModelSwitch(Base):
    def test_switch_preserves_history_and_never_deletes(self):
        self.shift()
        ids = self.cycle(4)
        sch.add_fixed_slot(self.c, TODAY.weekday(), 'Direito Civil', 30)
        sch.apply(self.c, iso(1), days=3, confirm=True)
        self.done_today(f'c:1:{ids[0]}:0')
        total_before = self.c.execute('SELECT COUNT(*) FROM schedule_blocks').fetchone()[0]
        sch.set_config(self.c, model='fixed')
        sch.apply(self.c, iso(1), days=3, confirm=True)
        self.assertGreaterEqual(self.c.execute('SELECT COUNT(*) FROM schedule_blocks').fetchone()[0], total_before)
        self.assertEqual(self.c.execute("SELECT status FROM schedule_blocks WHERE uid=?", (f'c:1:{ids[0]}:0',)).fetchone()[0], 'Concluída')
        sch.set_config(self.c, model='cycle')
        self.assertEqual(sch.next_block(self.c)['item_id'], ids[1])
        with self.assertRaises(ValueError):
            sch.set_config(self.c, model='x')

    def test_default_model_is_cycle(self):
        self.assertEqual(sch.get_config(self.c)['model'], 'cycle')


class CalendarTests(Base):
    def test_month_lengths_and_week_crossing(self):
        self.shift()
        self.assertEqual(len(sch.month_calendar(self.c, 2026, 2)), 28)
        self.assertEqual(len(sch.month_calendar(self.c, 2028, 2)), 29)
        self.assertEqual(len(sch.month_calendar(self.c, 2026, 12)), 31)
        self.assertEqual(len(sch.month_calendar(self.c, 2026, 11)), 30)

    def test_calendar_shows_blocks_and_done_minutes(self):
        self.shift()
        ids = self.cycle(3)
        sch.apply(self.c, iso(1), days=3, confirm=True)
        self.done_today(f'c:1:{ids[0]}:0', 25)
        cal = {d['day']: d for d in sch.calendar(self.c, iso(0), iso(3))}
        self.assertEqual(cal[iso(0)]['done_minutes'], 25)
        self.assertTrue(cal[iso(1)]['blocks'])
        self.assertEqual(cal[iso(0)]['kind'], 'Plantão')

    def test_week_report_crossing_months(self):
        self.shift()
        self.cycle(9)
        start = date(2027, 3, 29)  # semana 29/03–04/04 atravessa dois meses
        pv = sch.preview(self.c, start.isoformat(), today=start.isoformat(), days=7)
        self.assertEqual(len(pv['weeks']), 1)
        self.assertTrue(pv['weeks'][0]['covers_full_week'])


if __name__ == '__main__':
    unittest.main()

