"""Instalador Oficial do CONTROLE MESTRE para Windows.

Padronização definitiva da instalação:
1. Código em: %LOCALAPPDATA%\\ControleMestre\\app
2. Dados e histórico em: %LOCALAPPDATA%\\ControleMestre\\dados
3. Pasta única de acesso na Área de Trabalho: CONTROLE MESTRE
4. Atualizador universal integrado (sem necessidade de novas pastas para atualizar).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from contextlib import closing
from datetime import datetime
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import uuid
import zipfile

REPO = "antoniomoraes85/Controle-Mestre"
REVISION = "4cc6d378ce5a42d95bfc32175320f2e0a0bc2c28"
DEFAULT_BRANCH = "feat/usabilidade-catalogo-ciclos-v086"
ARCHIVE_URL = f"https://api.github.com/repos/{REPO}/zipball/{REVISION}"

REQUIRED = (
    "launch.py", "core.py", "web_server.py", "iniciar_windows.bat",
    "error_tracking.py", "smart_reinforcement.py",
    "web/index.html", "web/app.js", "web/style.css",
    "web/modules/questions.js", "web/modules/http.js", "backup_manager.py",
    "assessment_insights.py", "question_bank.py", "lesson_question_links.py",
    "study_guide.py", "study_time.py", "anki_analytics.py", "bizu_seed.py",
    "web/modules/assessment_insights.js", "web/modules/question_bank.js",
    "web/modules/study_guide.js", "web/modules/study_time.js",
    "web/modules/study_timer.js", "web/modules/anki_analytics.js",
    "curriculum_insights.py", "web/modules/curriculum.js",
    "material_autolink.py", "topic_importance.py", "cycle_planner.py",
    "web/modules/cycle_planner.js",
)

MAX_DOWNLOAD = 120 * 1024 * 1024
MAX_UNCOMPRESSED = 250 * 1024 * 1024


def persistent_root() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        local_appdata = str(Path.home() / "AppData" / "Local")
    return Path(local_appdata) / "ControleMestre"


def get_desktop_path() -> Path:
    if os.name == "nt":
        try:
            import winreg
            key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
                raw, _ = winreg.QueryValueEx(handle, "Desktop")
            desktop = Path(os.path.expandvars(raw))
            if desktop.is_dir():
                return desktop
        except (ImportError, FileNotFoundError, OSError):
            pass
    return Path.home() / "Desktop"


def sqlite_backup(source: Path, destination: Path) -> None:
    source = Path(source)
    destination = Path(destination)
    if not source.is_file():
        raise RuntimeError(f"Banco não encontrado: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise RuntimeError(f"Backup já existe: {destination}")
    staging = destination.with_name(destination.name + ".parcial_" + uuid.uuid4().hex)
    try:
        with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True, timeout=25)) as src:
            if src.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise RuntimeError("Banco existente não passou na verificação de integridade.")
            with closing(sqlite3.connect(str(staging), timeout=25)) as dst:
                src.backup(dst)
                if dst.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    raise RuntimeError("Cópia de segurança falhou na verificação de integridade.")
        staging.replace(destination)
    finally:
        staging.unlink(missing_ok=True)


def download_archive(destination: Path, url: str = ARCHIVE_URL) -> None:
    print("Baixando versão oficial verificada do GitHub...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ControleMestre-Windows-Installer/3.0", "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response, destination.open("wb") as out:
            total = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_DOWNLOAD:
                    raise RuntimeError("Download excedeu o tamanho máximo permitido.")
                out.write(chunk)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub retornou erro {exc.code}. Confira sua conexão e acesso.") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Não foi possível conectar ao GitHub: {exc.reason}") from exc
    if not zipfile.is_zipfile(destination):
        raise RuntimeError("O GitHub não retornou um ZIP válido.")


def secure_extract(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zipped:
        items = zipped.infolist()
        if not items:
            raise RuntimeError("O pacote recebido está vazio.")
        if sum(x.file_size for x in items) > MAX_UNCOMPRESSED:
            raise RuntimeError("O pacote recebido excede o limite de tamanho.")
        roots = set()
        for info in items:
            name = info.filename
            pure = PurePosixPath(name)
            if (not name or name.startswith(("/", "\\")) or "\\" in name or
                ":" in pure.parts[0] or ".." in pure.parts or
                (not info.is_dir() and len(pure.parts) < 2)):
                raise RuntimeError(f"Pacote contém caminho inválido: {name}")
            roots.add(pure.parts[0])
            mode = (info.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(mode):
                raise RuntimeError("Pacote contém atalho simbólico não permitido.")
            if info.is_dir():
                continue
            if info.file_size > 60 * 1024 * 1024:
                raise RuntimeError("Arquivo individual grande demais no pacote.")
            target = destination.joinpath(*pure.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipped.open(info) as src, target.open("wb") as out:
                shutil.copyfileobj(src, out, length=1024 * 1024)
        if len(roots) != 1:
            raise RuntimeError("O pacote contém múltiplas raízes inesperadas.")
        root = destination / next(iter(roots))
        for needed in REQUIRED:
            if not (root / needed).is_file():
                raise RuntimeError(f"Pacote incompleto: faltando {needed}")
        return root


def prompt_previous_database(base: Path, installer_dir: Path, ask=input) -> Path | None:
    options = (
        base / "app" / "dados" / "controle_mestre.db",
        installer_dir / "dados" / "controle_mestre.db",
        Path.cwd() / "dados" / "controle_mestre.db",
        Path.home() / "Desktop" / "CONTROLE MESTRE" / "dados" / "controle_mestre.db",
        Path.home() / "Desktop" / "CONTROLE_MESTRE" / "dados" / "controle_mestre.db",
    )
    seen = set()
    for found in options:
        try:
            resolved = found.resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        print(f"\nEncontrei um banco de dados anterior: {resolved}")
        answer = ask("Importar esse histórico? [S/n]: ").strip().lower()
        if answer in ("", "s", "sim", "y", "yes"):
            return resolved
    print("\nSe você já possui registros de estudo, informe o caminho do controle_mestre.db antigo.")
    print("Se for sua primeira instalação ou preferir iniciar limpo, pressione ENTER.")
    answer = ask("Caminho do banco anterior (opcional): ").strip().strip('"').strip("'")
    if not answer:
        return None
    candidate = Path(os.path.expandvars(answer)).expanduser()
    if not candidate.is_file():
        raise RuntimeError(f"Banco anterior não encontrado: {candidate}.")
    return candidate


def transfer_personal_catalog_if_missing(data: Path, installer_dir: Path) -> None:
    dst = data / "catalogo" / "aulas_primeiro_ciclo.csv"
    if dst.is_file():
        print("Catálogo de aulas já presente no histórico persistente. Será preservado.")
        return
    candidates = [
        installer_dir / "dados" / "catalogo" / "aulas_primeiro_ciclo.csv",
        Path.home() / "Desktop" / "CONTROLE MESTRE" / "dados" / "catalogo" / "aulas_primeiro_ciclo.csv",
        Path.home() / "Desktop" / "CONTROLE_MESTRE" / "dados" / "catalogo" / "aulas_primeiro_ciclo.csv",
    ]
    for src in candidates:
        if not src.is_file():
            continue
        try:
            with src.open('r', encoding='utf-8-sig', newline='') as fh:
                head = next(csv.reader(fh, delimiter=';'))
            if not {'disciplina', 'aula', 'assunto'}.issubset({x.strip() for x in head}):
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            with src.open('rb') as inp, dst.open('xb') as out:
                shutil.copyfileobj(inp, out)
            print("Lista pessoal de aulas recuperada sem alteração do original:", src)
            return
        except (OSError, UnicodeError, StopIteration, csv.Error):
            continue


def write_text_utf8(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\r\n")


def setup_workspace(base: Path, interpreter: str = sys.executable) -> tuple[Path, Path]:
    desktop = get_desktop_path()
    desktop_cm = desktop / "CONTROLE MESTRE"
    desktop_cm.mkdir(parents=True, exist_ok=True)

    # 1. Launcher ABRIR resiliente
    bat_abrir = desktop_cm / "ABRIR_CONTROLE_MESTRE.bat"
    bat_abrir_text = (
        "@echo off\r\n"
        "setlocal EnableExtensions\r\n"
        "chcp 65001 >nul\r\n"
        "title CONTROLE MESTRE - Estudos e Historico\r\n"
        "set \"CONTROLE_MESTRE_DB=%LOCALAPPDATA%\\ControleMestre\\dados\\controle_mestre.db\"\r\n"
        "cd /d \"%LOCALAPPDATA%\\ControleMestre\\app\"\r\n"
        "py -3 -c \"import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)\" >nul 2>&1\r\n"
        "if not errorlevel 1 (\r\n"
        "    py -3 -u launch.py\r\n"
        "    goto FIM_ABRIR\r\n"
        ")\r\n"
        "python -c \"import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)\" >nul 2>&1\r\n"
        "if not errorlevel 1 (\r\n"
        "    python -u launch.py\r\n"
        "    goto FIM_ABRIR\r\n"
        ")\r\n"
        f"\"{interpreter}\" -u launch.py\r\n"
        ":FIM_ABRIR\r\n"
        "if errorlevel 1 (\r\n"
        "  echo.\r\n"
        "  echo Nao foi possivel abrir o CONTROLE MESTRE. Verifique o erro acima.\r\n"
        "  pause\r\n"
        ")\r\n"
    )
    write_text_utf8(bat_abrir, bat_abrir_text)
    write_text_utf8(base / "ABRIR_CONTROLE_MESTRE.bat", bat_abrir_text)

    # 2. Launcher ATUALIZAR resiliente
    bat_atualizar = desktop_cm / "ATUALIZAR_CONTROLE_MESTRE.bat"
    bat_atualizar_text = (
        "@echo off\r\n"
        "setlocal EnableExtensions\r\n"
        "chcp 65001 >nul\r\n"
        "title CONTROLE MESTRE - Atualizador Oficial\r\n"
        "echo ============================================================\r\n"
        "echo CONTROLE MESTRE - Atualizador Universal\r\n"
        "echo ============================================================\r\n"
        "echo.\r\n"
        "py -3 -c \"import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)\" >nul 2>&1\r\n"
        "if not errorlevel 1 (\r\n"
        "    py -3 -u \"%LOCALAPPDATA%\\ControleMestre\\atualizador\\atualizador.py\"\r\n"
        "    goto FIM_ATUALIZAR\r\n"
        ")\r\n"
        "python -c \"import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)\" >nul 2>&1\r\n"
        "if not errorlevel 1 (\r\n"
        "    python -u \"%LOCALAPPDATA%\\ControleMestre\\atualizador\\atualizador.py\"\r\n"
        "    goto FIM_ATUALIZAR\r\n"
        ")\r\n"
        f"\"{interpreter}\" -u \"%LOCALAPPDATA%\\ControleMestre\\atualizador\\atualizador.py\"\r\n"
        ":FIM_ATUALIZAR\r\n"
        "if errorlevel 1 (\r\n"
        "  echo.\r\n"
        "  echo A atualizacao falhou. Seu app e dados foram mantidos intactos.\r\n"
        ")\r\n"
        "echo.\r\n"
        "pause\r\n"
    )
    write_text_utf8(bat_atualizar, bat_atualizar_text)

    # 3. Instruções de utilização
    instrucoes = desktop_cm / "INSTRUCOES_DE_UTILIZACAO.txt"
    instrucoes_text = (
        "========================================================================\r\n"
        "CONTROLE MESTRE — PADRONIZAÇÃO DEFINITIVA DA INSTALAÇÃO\r\n"
        "========================================================================\r\n\r\n"
        "1. PARA ABRIR O APLICATIVO:\r\n"
        "   - Clique duas vezes em 'ABRIR_CONTROLE_MESTRE.bat'.\r\n"
        "   - O painel abrirá automaticamente em http://127.0.0.1:8771\r\n\r\n"
        "2. PARA ATUALIZAR O APLICATIVO:\r\n"
        "   - Clique duas vezes em 'ATUALIZAR_CONTROLE_MESTRE.bat'.\r\n"
        "   - O atualizador baixa a versão oficial consolidada do GitHub,\r\n"
        "     faz backup de segurança do SQLite e atualiza o código no mesmo local.\r\n"
        "   - Não é necessário baixar ZIPs manuais nem criar novas pastas.\r\n\r\n"
        "3. ONDE FICAM SEUS DADOS:\r\n"
        "   - Banco de dados: %LOCALAPPDATA%\\ControleMestre\\dados\\controle_mestre.db\r\n"
        "   - Backups diários: %LOCALAPPDATA%\\ControleMestre\\dados\\backups\r\n"
        "   - Materiais e PDFs: %LOCALAPPDATA%\\ControleMestre\\dados\\materiais\r\n\r\n"
        "4. SEGURANÇA E RECUPERAÇÃO:\r\n"
        "   - As versões anteriores do código são preservadas em %LOCALAPPDATA%\\ControleMestre\\versoes_anteriores\r\n"
        "   - Para reverter para o estado anterior, basta executar o atualizador com a opção --reverter\r\n\r\n"
        "Repositório oficial: https://github.com/antoniomoraes85/Controle-Mestre\r\n"
    )
    write_text_utf8(instrucoes, instrucoes_text)

    # 4. Atalho .cmd na raiz da Área de Trabalho
    entry = desktop / "CONTROLE MESTRE.cmd"
    try:
        write_text_utf8(entry, '@echo off\r\ncall "%~dp0CONTROLE MESTRE\\ABRIR_CONTROLE_MESTRE.bat"\r\n')
    except OSError:
        pass

    return bat_abrir, bat_atualizar


def install(*, base: Path, installer_dir: Path, archive: Path | None = None,
            ask=input, launch=True) -> Path:
    base = Path(base)
    app = base / "app"
    dados = base / "dados"
    db = dados / "controle_mestre.db"
    backups = dados / "backups"
    versions = base / "versoes_anteriores"
    updater_dir = base / "atualizador"

    for p in (base, dados, backups, versions, updater_dir):
        p.mkdir(parents=True, exist_ok=True)

    print("\nCONTROLE MESTRE — Padronização Definitiva da Instalação")
    print(f"Código em: {app}")
    print(f"Dados e histórico em: {db}")

    if db.is_file():
        print("Banco de dados ativo localizado. Histórico será 100% preservado.")
    else:
        prev = prompt_previous_database(base, installer_dir, ask)
        if prev:
            print("Importando histórico anterior com integridade SQLite verificada...")
            sqlite_backup(prev, db)
            print("Histórico importado com sucesso.")
        else:
            print("Nenhum histórico anterior informado. Novo banco será criado na primeira abertura.")

    if db.is_file():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dest = backups / f"antes_instalacao_{stamp}.sqlite3"
        sqlite_backup(db, backup_dest)
        print(f"Backup de segurança gerado: {backup_dest.name}")

    transfer_personal_catalog_if_missing(dados, installer_dir)

    with tempfile.TemporaryDirectory(prefix="cm_install_", dir=base) as td:
        temp = Path(td)
        target = temp / "codigo.zip"
        if archive is None:
            download_archive(target)
        else:
            shutil.copy2(archive, target)

        print("Verificando integridade e arquivos obrigatórios...")
        source = secure_extract(target, temp / "extracao")

        archived = None
        if app.exists():
            archived = versions / ("app_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
            app.replace(archived)
        try:
            source.replace(app)
        except Exception:
            if archived is not None and archived.exists() and not app.exists():
                archived.replace(app)
            raise

    # Copiar atualizador autônomo
    updater_script_source = app / "atualizador.py"
    if not updater_script_source.is_file():
        updater_script_source = installer_dir / "atualizador.py"
    if updater_script_source.is_file():
        shutil.copy2(updater_script_source, updater_dir / "atualizador.py")

    # Gravar versao_instalada.json
    installed_record = {
        "produto": "CONTROLE MESTRE",
        "versao": "0.8.7",
        "revisao": REVISION,
        "branch_origem": DEFAULT_BRANCH,
        "data_instalacao": datetime.now().isoformat(),
        "status": "instalada"
    }
    write_text_utf8(app / "versao_instalada.json", json.dumps(installed_record, indent=2))

    bat_abrir, bat_atualizar = setup_workspace(base, sys.executable)

    print("\nINSTALAÇÃO CONCLUÍDA COM SUCESSO!")
    print(f"Pasta única na Área de Trabalho : {bat_abrir.parent}")
    print(f"Atalho para abrir               : {bat_abrir}")
    print(f"Atalho para atualizar           : {bat_atualizar}")
    print(f"Banco de dados ativo            : {db}")

    if launch and os.name == "nt":
        print("Abrindo o CONTROLE MESTRE...")
        try:
            subprocess.Popen(["cmd.exe", "/c", str(bat_abrir)],
                             cwd=str(app), creationflags=subprocess.CREATE_NEW_CONSOLE)
        except OSError as exc:
            print("Não foi possível abrir automaticamente:", exc)
    return bat_abrir


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Instalador Padronizado do CONTROLE MESTRE")
    parser.add_argument("--diagnostico", action="store_true", help="Exibir caminhos sem instalar")
    args = parser.parse_args(argv)
    if sys.version_info < (3, 11):
        print("ERRO: Python 3.11 ou superior é obrigatório.")
        return 2
    root = persistent_root()
    if args.diagnostico:
        print("Código    :", root / "app")
        print("Histórico :", root / "dados" / "controle_mestre.db")
        print("Backups   :", root / "dados" / "backups")
        return 0
    try:
        install(base=root, installer_dir=Path(__file__).resolve().parent)
    except Exception as exc:
        print(f"\nFALHA NA INSTALAÇÃO: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
