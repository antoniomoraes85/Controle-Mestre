"""Testes de integridade e robustez do Atualizador Universal do CONTROLE MESTRE."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import atualizador
import INSTALAR_CONTROLE_MESTRE as instalador


class AtualizadorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.app = self.root / "app"
        self.dados = self.root / "dados"
        self.db = self.dados / "controle_mestre.db"
        self.backups = self.dados / "backups"
        self.versoes = self.root / "versoes_anteriores"
        self.desktop_cm = self.root / "Desktop_CM"
        for p in (self.app, self.dados, self.backups, self.versoes, self.desktop_cm):
            p.mkdir(parents=True, exist_ok=True)

        self.paths = {
            "root": self.root,
            "app": self.app,
            "dados": self.dados,
            "db": self.db,
            "backups": self.backups,
            "versoes": self.versoes,
            "updater": self.root / "atualizador",
            "desktop": self.root,
            "desktop_cm": self.desktop_cm,
            "desktop_cmd": self.root / "CONTROLE MESTRE.cmd",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_manifesto_rejeita_branch_movel(self):
        manifesto = json.loads((Path(__file__).resolve().parents[1] /
                                "versao_oficial.json").read_text(encoding="utf-8"))
        self.assertEqual(atualizador.validate_release_manifest(manifesto)[0], "0.8.6")
        instavel = dict(manifesto, archive_url=(
            "https://api.github.com/repos/antoniomoraes85/Controle-Mestre/"
            "zipball/feat/usabilidade-catalogo-ciclos-v086"))
        with self.assertRaises(ValueError):
            atualizador.validate_release_manifest(instavel)

    def test_manifesto_rejeita_sha_inexistente_sintaticamente(self):
        manifesto = json.loads((Path(__file__).resolve().parents[1] /
                                "versao_oficial.json").read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            atualizador.validate_release_manifest(dict(manifesto, revisao="nao-e-sha"))

    def test_revisao_inicial_coincide_com_manifesto_oficial(self):
        """Evita instalar ZIP de um commit inexistente ou obsoleto."""
        path = Path(__file__).resolve().parents[1] / "versao_oficial.json"
        manifesto = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(instalador.REVISION, manifesto["revisao"])
        self.assertTrue(instalador.ARCHIVE_URL.endswith("/" + manifesto["revisao"]))
        self.assertEqual(manifesto["archive_url"], instalador.ARCHIVE_URL)

    def test_sqlite_backup_transacional_e_quick_check(self):
        # Criar banco sqlite válido com tabela e dados
        conn = sqlite3.connect(str(self.db))
        conn.execute("CREATE TABLE estudos (id INTEGER PRIMARY KEY, materia TEXT)")
        conn.execute("INSERT INTO estudos (materia) VALUES ('Direito Tributário')")
        conn.commit()
        conn.close()

        dest_backup = self.backups / "backup_teste.sqlite3"
        atualizador.sqlite_backup(self.db, dest_backup)

        self.assertTrue(dest_backup.is_file())
        # Conferir se dados foram preservados e quick_check passa
        b_conn = sqlite3.connect(str(dest_backup))
        check = b_conn.execute("PRAGMA quick_check").fetchone()[0]
        self.assertEqual(check, "ok")
        count = b_conn.execute("SELECT COUNT(*) FROM estudos").fetchone()[0]
        self.assertEqual(count, 1)
        b_conn.close()

    def test_get_installed_version_com_manifesto(self):
        record = {
            "produto": "CONTROLE MESTRE",
            "versao": "0.8.6",
            "revisao": "abc1234",
            "status": "instalada"
        }
        (self.app / "versao_instalada.json").write_text(json.dumps(record), encoding="utf-8")
        ver = atualizador.get_installed_version(self.app)
        self.assertEqual(ver["versao"], "0.8.6")
        self.assertEqual(ver["revisao"], "abc1234")

    def test_get_installed_version_fallback_launch_py(self):
        launch_code = "if info.get('version') == '0.8.5': pass\n"
        (self.app / "launch.py").write_text(launch_code, encoding="utf-8")
        ver = atualizador.get_installed_version(self.app)
        self.assertEqual(ver["versao"], "0.8.5")

    def test_create_and_rollback_snapshot(self):
        (self.app / "test_file.py").write_text("print('v1')", encoding="utf-8")
        snap = atualizador.create_app_snapshot(self.app, self.versoes, "0.8.5")
        self.assertTrue(snap.is_dir())
        self.assertTrue((snap / "test_file.py").is_file())

        # Modifica app para simular atualização com falha
        (self.app / "test_file.py").write_text("print('v2_corrompido')", encoding="utf-8")
        # Executa rollback
        restored = atualizador.rollback_last_version(self.app, self.versoes)
        self.assertEqual(restored.name, snap.name)
        self.assertEqual((self.app / "test_file.py").read_text(encoding="utf-8"), "print('v1')")

    def test_archive_legacy_directories(self):
        # Criar pastas legadas simuladas
        v4 = self.desktop_cm / "ATUALIZADOR_CM_V4"
        v4.mkdir()
        (v4 / "INSTALAR.py").write_text("v4", encoding="utf-8")

        v5 = self.desktop_cm / "ATUALIZADOR_CM_V5"
        v5.mkdir()
        v5_dados = v5 / "dados"
        v5_dados.mkdir()
        v5_db = v5_dados / "controle_mestre.db"
        sqlite3.connect(str(v5_db)).close()

        res = atualizador.archive_legacy_directories(self.desktop_cm)
        self.assertIn("ATUALIZADOR_CM_V4", res["moved"])
        self.assertIn("ATUALIZADOR_CM_V5", res["moved"])
        self.assertTrue((self.desktop_cm / "instaladores_antigos" / "ATUALIZADOR_CM_V4").is_dir())
        self.assertTrue((self.desktop_cm / "instaladores_antigos" / "ATUALIZADOR_CM_V5").is_dir())
        self.assertTrue((self.desktop_cm / "RELATORIO_ARQUIVAMENTO.txt").is_file())
        self.assertEqual(len(res["databases"]), 1)

    def test_atualizador_permanente_recebe_codigo_novo(self):
        """Instalar app deve renovar script da pasta atualizador sem criar pasta extra."""
        novo = self.app / "atualizador.py"
        novo.write_text("# nova versão segura do atualizador\\n", encoding="utf-8")
        atualizador.setup_desktop_folder(self.paths)
        atual = self.paths["updater"] / "atualizador.py"
        self.assertEqual(atual.read_text(encoding="utf-8"), "# nova versão segura do atualizador\\n")
        self.assertTrue((self.desktop_cm / "ATUALIZAR_CONTROLE_MESTRE.bat").exists())

    def test_setup_desktop_folder(self):
        atualizador.setup_desktop_folder(self.paths)
        self.assertTrue((self.desktop_cm / "ABRIR_CONTROLE_MESTRE.bat").is_file())
        self.assertTrue((self.desktop_cm / "ATUALIZAR_CONTROLE_MESTRE.bat").is_file())
        self.assertTrue((self.desktop_cm / "INSTRUCOES_DE_UTILIZACAO.txt").is_file())


if __name__ == "__main__":
    unittest.main()
