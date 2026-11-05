import os
import sys
import tempfile
import io
import zipfile
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import (connect,add_session,add_questions,metric_data,generate_plan,save_day,
                  import_anki_csv,save_topic,all_rows,subject_metrics,import_excel)

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.c=connect(Path(self.temp.name)/'test.sqlite')
    def tearDown(self):
        self.c.close();self.temp.cleanup()
    def test_study_review_and_no_double_import(self):
        n=add_session(self.c,'2026-11-04','Direito Tributário','Obrigação','Teoria',60,
                      fingerprint='once',auto_review=True,cycle=2)
        self.assertEqual(n,1)
        self.assertEqual(add_session(self.c,'2026-11-04','Direito Tributário','Obrigação','Teoria',60,fingerprint='once'),0)
        self.assertEqual(self.c.execute('select count(*) from reviews').fetchone()[0],4)
        self.assertEqual(self.c.execute('select cycle from sessions').fetchone()[0],2)
    def test_rate_is_weighted(self):
        add_questions(self.c,'2026-11-03','Direito Tributário','A',100,50)
        add_questions(self.c,'2026-11-04','Direito Tributário','B',1,1)
        d=metric_data(self.c,date(2026,11,4))
        self.assertEqual(d['week_questions']['total'],101)
        self.assertAlmostEqual(d['week_questions']['rate'],51/101,places=7)
    def test_plantao_limit(self):
        add_session(self.c,'2026-11-04','Direito Tributário','','Revisão',100,'Plantão')
        with self.assertRaises(ValueError):add_session(self.c,'2026-11-04','Direito Tributário','','Revisão',21,'Plantão')
    def test_plan_respects_availability_and_finished_tasks(self):
        monday=date(2026,11,2)
        for i in range(7):save_day(self.c, str(monday.fromordinal(monday.toordinal()+i)), 'Reset')
        save_day(self.c,'2026-11-02','Plantão',120)
        save_day(self.c,'2026-11-04','Livre forte',180)
        r=generate_plan(self.c,'2026-11-03')
        self.assertLessEqual(r['planned_minutes'],300)
        self.assertEqual(r['capacity_minutes'],300)
        by_day=all_rows(self.c,'select day,sum(target_minutes) total from plans group by day')
        self.assertTrue(all(x['day'] in ('2026-11-02','2026-11-04') for x in by_day))
        first=self.c.execute('select id from plans limit 1').fetchone()
        self.c.execute("update plans set status='Concluída' where id=?",(first[0],));self.c.commit()
        again=generate_plan(self.c,'2026-11-02')
        self.assertEqual(self.c.execute("select count(*) from plans where status='Concluída'").fetchone()[0],1)
        self.assertLessEqual(again['planned_minutes'],300)
    def test_anki_csv_import_idempotent(self):
        csv=b'date,deck,reviews,errors,minutes\n2026-11-04,Direito Tributario::Lei seca,45,5,20\n'
        self.assertEqual(import_anki_csv(self.c,csv)['importados'],1)
        self.assertEqual(import_anki_csv(self.c,csv)['importados'],0)
        self.assertEqual(self.c.execute('select sum(cards) from anki').fetchone()[0],45)
    def test_excel_vba_log_import(self):
        # Log compatível com o VBA V6: apenas PAUSADO/ENCERRADO, nunca ZERADO.
        book=b'''<?xml version="1.0" encoding="UTF-8"?>
        <workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
        <sheets><sheet name="Registro_Tempos" sheetId="1" r:id="rId1"/></sheets></workbook>'''
        rels=b'''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
        <Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/></Relationships>'''
        header=['Inicio','Fim','Disciplina','Ciclo','Tempo da sessao','Celula','Situacao','Aba']
        import xml.sax.saxutils as sax
        def cell(col,row,value):
            return f'<c r="{col}{row}" t="inlineStr"><is><t>{sax.escape(value)}</t></is></c>'
        header_xml=''.join(cell(chr(65+i),1,v) for i,v in enumerate(header))
        data=[('2026-11-04','Direito Tributário','CICLO 2','0.0416666667','ENCERRADO'),
              ('2026-11-04','Direito Tributário','CICLO 2','0.0','ZERADO')]
        rows=[f'<row r="1">{header_xml}</row>']
        for i,(day,sub,cycle,dur,status) in enumerate(data,2):
            cols={'A':day,'B':day,'C':sub,'D':cycle,'F':'G5','G':status,'H':'CICLO'}
            cs=''.join(cell(k,i,v) for k,v in cols.items())+f'<c r="E{i}"><v>{dur}</v></c>'
            rows.append(f'<row r="{i}">{cs}</row>')
        sh=('''<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'''+''.join(rows)+'''</sheetData></worksheet>''').encode()
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:
            z.writestr('xl/workbook.xml',book)
            z.writestr('xl/_rels/workbook.xml.rels',rels)
            z.writestr('xl/worksheets/sheet1.xml',sh)
        report=import_excel(self.c,buf.getvalue(),'teste_vba.xlsx')
        self.assertEqual(report['sessoes'],1)
        r=self.c.execute('SELECT day,subject,cycle,minutes FROM sessions').fetchone()
        self.assertEqual((r['day'],r['subject'],r['cycle'],r['minutes']),('2026-11-04','Direito Tributário',2,60))
        again=import_excel(self.c,buf.getvalue(),'teste_vba.xlsx')
        self.assertEqual(again['sessoes'],0)
    def test_topic_import_is_not_a_study_session(self):
        save_topic(self.c,'Direito Tributário','Obrigação Tributária',progress=100)
        self.assertEqual(self.c.execute('select count(*) from topics where progress=100').fetchone()[0],1)
        self.assertEqual(self.c.execute('select count(*) from sessions').fetchone()[0],0)
    def test_undefined_accuracy_not_zero(self):
        r=next(x for x in subject_metrics(self.c,date(2026,11,4)) if x['disciplina']=='Direito Tributário')
        self.assertIsNone(r['rendimento'])

if __name__=='__main__':unittest.main()