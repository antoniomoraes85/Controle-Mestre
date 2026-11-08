"""AnkiConnect: revisão real e deduplicação de revlog sintético, sem acessar Anki pessoal."""
import sys,tempfile,unittest
from datetime import datetime,timedelta,date
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core,anki_analytics

class AnkiAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.c=core.connect(Path(self.tmp.name)/'test.db')
    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def data(self):
        now=datetime.now().astimezone()
        time0=int((now-timedelta(hours=1)).timestamp()*1000)
        # 20 revisões programadas, 5 Again => índice não-Again 75%.
        logs=[[time0+i,111+i,-1,1 if i<5 else 3,4,3,2500,20000,1] for i in range(20)]
        # Dois baralhos pai/filho retornam os MESMOS eventos, não podem duplicar.
        decks={'decks':[{'deck':'Contabilidade Geral','subject':'Contabilidade Geral'},
                        {'deck':'Contabilidade Geral::Questões','subject':'Contabilidade Geral'}],
               'all_decks':2}
        return logs,decks

    def test_dedup_and_rate_no_fabricated_mastery(self):
        logs,decks=self.data()
        with patch.object(anki_analytics,'detect',return_value=decks), \
             patch.object(anki_analytics,'invoke',return_value=logs):
            result=anki_analytics.collect('Principal')
        self.assertEqual(result['events'],20)
        anki_analytics.save(self.c,result)
        report=anki_analytics.report(self.c)
        self.assertEqual(report['total_answers'],20)
        self.assertEqual(report['total_again'],5)
        self.assertEqual(report['subjects'][0]['review_success_rate'],0.75)
        anki_analytics.save(self.c,result)
        self.assertEqual(anki_analytics.report(self.c)['total_answers'],20)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM sessions').fetchone()[0],0)

    def test_insufficient_sample_is_explicit(self):
        logs,decks=self.data()
        with patch.object(anki_analytics,'detect',return_value=decks), \
             patch.object(anki_analytics,'invoke',return_value=logs[:9]):
            result=anki_analytics.collect('Principal')
        anki_analytics.save(self.c,result)
        row=anki_analytics.report(self.c)['subjects'][0]
        self.assertIsNone(row['review_success_rate'])
        self.assertFalse(row['review_sample_sufficient'])

    def test_invalid_profile(self):
        with self.assertRaises(ValueError):anki_analytics.collect('')
        with self.assertRaises(ValueError):anki_analytics.report(self.c,'\x00')

    def test_no_decks_no_statistics(self):
        with patch.object(anki_analytics,'detect',return_value={'decks':[],'all_decks':0}):
            r=anki_analytics.collect('Principal')
        self.assertEqual(r['events'],0)
        anki_analytics.save(self.c,r)
        self.assertEqual(anki_analytics.report(self.c)['total_answers'],0)

if __name__=='__main__':unittest.main()
