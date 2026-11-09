"""Regressões da auditoria somente leitura usada no Windows."""
from __future__ import annotations
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import auditoria_local_v088 as audit


class LocalAuditTests(unittest.TestCase):
    def test_schema_introspection_is_read_only_and_reports_true_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'active.sqlite3'
            c=sqlite3.connect(str(db))
            c.execute('CREATE TABLE study_materials(id INTEGER PRIMARY KEY, subject TEXT, lesson TEXT, relative_path TEXT, file_name TEXT)')
            c.execute('CREATE TABLE curriculum_topic_links(id INTEGER PRIMARY KEY, subject TEXT, topic TEXT, subtopic TEXT, verified INTEGER)')
            c.execute('CREATE TABLE curriculum_evidence(id INTEGER PRIMARY KEY, incidence_pct REAL, qualitative TEXT, verified INTEGER)')
            c.execute("INSERT INTO study_materials(subject,lesson,relative_path,file_name) VALUES('Direito Tributário','Aula 1','a','a.pdf')")
            c.execute("INSERT INTO curriculum_topic_links(subject,topic,subtopic,verified) VALUES('Direito Tributário','Obrigação','','1')")
            c.execute("INSERT INTO curriculum_evidence(incidence_pct,qualitative,verified) VALUES(8.41,'',1)")
            c.commit()
            c.close()
            before=db.read_bytes()
            info=audit.audit_database(db)
            self.assertEqual(info['integrity_check'],'ok')
            self.assertEqual(info['tables']['study_materials']['rows'],1)
            self.assertEqual(info['tables']['curriculum_topic_links']['verified_1'],1)
            self.assertFalse(info['tables']['curriculum_topic_links']['has_stored_priority_column'])
            self.assertIn('material_id',info['tables']['curriculum_topic_links']['missing_expected_columns'])
            self.assertEqual(info['tables']['curriculum_evidence']['numeric_incidence'],1)
            self.assertEqual(db.read_bytes(),before)

    def test_missing_database_does_not_create_empty_db(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'missing.db'
            info=audit.audit_database(db)
            self.assertFalse(info['exists'])
            self.assertFalse(db.exists())

    def test_json_counts_no_private_contents_exposed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'assuntos_locais.json'
            p.write_text(json.dumps({'topic_links':[{'secret_path':'C:/private/secret.pdf'}]}),encoding='utf-8')
            info=audit.json_file(p)
            self.assertEqual(info['entries'],1)
            self.assertNotIn('secret.pdf',repr(info))


if __name__=='__main__':
    unittest.main()
