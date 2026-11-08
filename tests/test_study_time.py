"""Tempo: fontes únicas, períodos, saldo cumulativo e idempotência."""
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core,study_time


class StudyTimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.c=core.connect(Path(self.tmp.name)/'test.sqlite3')
        self.subject='Contabilidade Geral'
        self.today=date.today()
    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def store(self,minutes=42,day=None,session_id=None,subject=None):
        return study_time.save(self.c,{
            'session_id':session_id or str(uuid.uuid4()),
            'subject':subject or self.subject,
            'day':str(day or self.today),
            'minutes':minutes,
            'method':'Teoria'
        })

    def test_timer_cumulative_across_multiple_sessions(self):
        self.store(25)
        self.store(35)
        row=study_time.report(self.c,self.today)
        self.assertEqual(row['day_minutes'],60)
        self.assertEqual(row['week_minutes'],60)
        self.assertEqual(row['month_minutes'],60)
        self.assertEqual(row['total_minutes'],60)
        self.assertEqual(row['subjects'][0]['total_minutes'],60)

    def test_resubmission_does_not_duplicate(self):
        identity=str(uuid.uuid4())
        self.assertTrue(self.store(31,session_id=identity)['inserted'])
        self.assertFalse(self.store(31,session_id=identity)['inserted'])
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM sessions').fetchone()[0],1)
        self.assertEqual(study_time.report(self.c,self.today)['total_minutes'],31)

    def test_older_history_is_included(self):
        yesterday=self.today-timedelta(days=1)
        self.store(45,yesterday)
        self.store(60)
        result=study_time.report(self.c,self.today)
        self.assertEqual(result['total_minutes'],105)
        self.assertEqual(result['daily'][-1]['minutes'],60)
        self.assertEqual(result['daily'][-2]['minutes'],45)

    def test_unique_subjects_independently_accumulate(self):
        self.store(40)
        self.store(20,subject='Direito Tributário')
        result=study_time.report(self.c,self.today)
        self.assertEqual(result['total_minutes'],60)
        self.assertEqual(len(result['subjects']),2)

    def test_reject_invalid_and_future_data(self):
        with self.assertRaises(ValueError):self.store(-2)
        with self.assertRaises(ValueError):self.store(601)
        with self.assertRaises(ValueError):self.store(1,day=self.today+timedelta(days=1))
        with self.assertRaises(ValueError):study_time.save(self.c,{
            'session_id':'wrong','subject':'Contabilidade Geral','minutes':60})
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM sessions').fetchone()[0],0)


if __name__=='__main__':unittest.main()
