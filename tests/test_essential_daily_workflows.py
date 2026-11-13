"""Regressões de uso diário e preservação do histórico — dados apenas sintéticos."""
from __future__ import annotations

import json
from contextlib import closing
import os
import sqlite3
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import core
from _isolation import isolate
from backup_manager import make_backup, verify_backup
from web_server import AppHandler


class StableHistoryPathsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "checkout"
        self.win = Path(self.temp.name) / "appdata"
        self.root.mkdir()
        self.win.mkdir()

    def test_path_explicit_override_wins(self):
        explicit = Path(self.temp.name) / "custom" / "my_history.sqlite"
        with patch.object(core, "ROOT", self.root), patch.dict(os.environ, {
            "CONTROLE_MESTRE_DB": str(explicit),
            "LOCALAPPDATA": str(self.win)}, clear=True):
            self.assertEqual(core._default_db_path(), explicit)

    def test_existing_legacy_history_wins_over_new_windows_directory(self):
        old = self.root / "dados" / "controle_mestre.db"
        old.parent.mkdir()
        old.write_bytes(b"legacy history sentinel")
        (self.win / "ControleMestre" / "dados").mkdir(parents=True)
        with patch.object(core, "ROOT", self.root), patch.dict(
            os.environ, {"LOCALAPPDATA": str(self.win)}, clear=True):
            self.assertEqual(core._default_db_path(), old)

    def test_existing_persistent_windows_database_keeps_precedence(self):
        old = self.root / "dados" / "controle_mestre.db"
        old.parent.mkdir()
        old.write_bytes(b"old")
        current = self.win / "ControleMestre" / "dados" / "controle_mestre.db"
        current.parent.mkdir(parents=True)
        current.write_bytes(b"current")
        with patch.object(core, "ROOT", self.root), patch.dict(
            os.environ, {"LOCALAPPDATA": str(self.win)}, clear=True):
            self.assertEqual(core._default_db_path(), current)

    def test_new_windows_install_uses_stable_location(self):
        expected = self.win / "ControleMestre" / "dados" / "controle_mestre.db"
        with patch.object(core, "ROOT", self.root), patch.dict(
            os.environ, {"LOCALAPPDATA": str(self.win)}, clear=True):
            self.assertEqual(core._default_db_path(), expected)


class EssentialDailyHTTPTests(unittest.TestCase):
    def setUp(self):
        isolate(self)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.original_db = core.DB_PATH
        core.DB_PATH = Path(self.temp.name) / "daily.sqlite"
        self.addCleanup(setattr, core, "DB_PATH", self.original_db)
        with closing(core.connect()):
            pass
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), AppHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def call(self, route, data=None):
        headers = {}
        encoded = None
        if data is not None:
            encoded = json.dumps(data).encode("utf-8")
            headers = {"Content-Type": "application/json", "Origin": self.url}
        req = Request(self.url + route, data=encoded, headers=headers)
        try:
            with urlopen(req, timeout=5) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_real_session_and_questions_survive_independent_http_requests(self):
        status, initial = self.call("/api/overview")
        self.assertEqual(status, 200)
        self.assertEqual(initial["metrics"]["weekly_minutes"], 0)
        self.assertIsNone(initial["metrics"]["last30_questions"]["rate"])
        payload = {"subject": "Direito Tributário", "method": "Teoria",
                   "minutes": 35, "kind": "Livre leve"}
        self.assertEqual(self.call("/api/session", payload)[0], 200)
        q = {"subject": "Direito Tributário", "topic": "Obrigação tributária",
             "day": initial["today"], "mode": "batch", "total": 10,
             "correct": 8, "request_id": "stable-check-0001"}
        status, batch = self.call("/api/questions/batch", q)
        self.assertEqual(status, 201)
        self.assertEqual(batch["status"], "finalized")
        self.assertEqual(
            self.call("/api/questions/batch", q)[1]["batch_id"], batch["batch_id"]
        )
        current = self.call("/api/overview")[1]
        self.assertEqual(current["metrics"]["weekly_minutes"], 35)
        self.assertEqual(current["metrics"]["week_questions"]["total"], 10)
        self.assertEqual(current["metrics"]["week_questions"]["correct"], 8)
        history = self.call("/api/questions/history")[1]["items"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["total"], 10)
        # Every endpoint uses a new SQLite connection. Also reopen independently.
        with closing(core.connect()) as conn:
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0], 1)
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0], 1)

    def test_online_backup_keeps_saved_history(self):
        self.call("/api/session", {"subject": "Contabilidade Geral",
            "method": "Teoria", "minutes": 45, "kind": "Livre leve"})
        backup = make_backup(core.DB_PATH, Path(self.temp.name) / "backup", force=True)
        self.assertTrue(backup)
        self.assertTrue(verify_backup(backup))
        with sqlite3.connect(backup) as conn:
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0], 1)

    def test_essential_navigation_and_focus_page_are_available(self):
        req = Request(self.url + "/app.js")
        with urlopen(req, timeout=5) as response:
            source = response.read().decode("utf-8")
        self.assertIn("Foco RS + SC/TI", source)
        self.assertIn("commonStudyTopics", source)
        self.assertIn("total=commonWeeklyHours.reduce", source.replace("const ", ""))
        self.assertIn("function focusView()", source)
        self.assertIn("if(action==='questions-form'){navigate('questions');return}", source)
        nav = source[source.index("const nav=["):source.index("];",source.index("const nav=["))]
        for inactive in ["'insights'", "'cycle'", "'guide'", "'assess'", "'sources'"]:
            self.assertNotIn(inactive, nav)


if __name__ == "__main__":
    unittest.main()
