"""Atualizador Universal do CONTROLE MESTRE.

Executa atualização segura in-place em %LOCALAPPDATA%\\ControleMestre\\app
sem criar novas pastas de trabalho na Área de Trabalho.
Preserva permanentemente o banco de dados e arquivos do usuário em
%LOCALAPPDATA%\\ControleMestre\\dados.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime
import json
import os
from pathlib import Path, PurePosixPath
import re
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

DEFAULT_REPO = "antoniomoraes85/Controle-Mestre"
DEFAULT_BRANCH = "feat/usabilidade-catalogo-ciclos-v086"
OFFICIAL_MANIFEST_URL = (
    f"https://raw.githubusercontent.com/{DEFAULT_REPO}/{DEFAULT_BRANCH}/versao_oficial.json"
)
MAX_DOWNLOAD_BYTES = 120 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 250 * 1024 * 1024

REQUIRED_FILES = (
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


def persistent_paths() -> dict[str, Path]:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        local_appdata = str(Path.home() / "AppData" / "Local")
    root = Path(local_appdata) / "ControleMestre"
    app = root / "app"
    dados = root / "dados"
    db = dados / "controle_mestre.db"
    backups = dados / "backups"
    versoes = root / "versoes_anteriores"
    updater = root / "atualizador"
    
    desktop = None
    if os.name == "nt":
        try:
            import winreg
            key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
                raw, _ = winreg.QueryValueEx(handle, "Desktop")
            desktop = Path(os.path.expandvars(raw))
        except (ImportError, FileNotFoundError, OSError):
            pass
    if not desktop or not desktop.is_dir():
        desktop = Path.home() / "Desktop"

    desktop_cm = desktop / "CONTROLE MESTRE"
    desktop_cmd = desktop / "CONTROLE MESTRE.cmd"

    return {
        "root": root,
        "app": app,
        "dados": dados,
        "db": db,
        "backups": backups,
        "versoes": versoes,
        "updater": updater,
        "desktop": desktop,
        "desktop_cm": desktop_cm,
        "desktop_cmd": desktop_cmd,
    }


def sqlite_backup(source: Path, destination: Path) -> Path:
    """Backup transacional e consistente do banco SQLite.
    
    Protege transações WAL em andamento e verifica a integridade (quick_check)
    antes e depois do backup.
    """
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if not source.is_file():
        raise RuntimeError(f"Banco SQLite fonte não encontrado: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise RuntimeError(f"Arquivo de backup já existe e não será sobrescrito: {destination}")

    staging = destination.with_name(f"{destination.name}.parcial_{uuid.uuid4().hex}")
    try:
        with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True, timeout=30)) as src:
            status = src.execute("PRAGMA quick_check").fetchone()
            if not status or status[0] != "ok":
                raise RuntimeError("Banco existente falhou na verificação prévia de integridade.")
            with closing(sqlite3.connect(str(staging), timeout=30)) as dst:
                src.backup(dst)
                dst_status = dst.execute("PRAGMA quick_check").fetchone()
                if not dst_status or dst_status[0] != "ok":
                    raise RuntimeError("Cópia de segurança gerada falhou na verificação de integridade.")
        staging.replace(destination)
        return destination
    finally:
        if staging.exists():
            try:
                staging.unlink(missing_ok=True)
            except OSError:
                pass


def get_installed_version(app_dir: Path) -> dict:
    installed_manifest = app_dir / "versao_instalada.json"
    if installed_manifest.is_file():
        try:
            return json.loads(installed_manifest.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    version = "0.0.0"
    revision = "desconhecida"
    launch_py = app_dir / "launch.py"
    if launch_py.is_file():
        try:
            txt = launch_py.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"info\.get\(['\"]version['\"]\)\s*==\s*['\"]([^'\"]+)['\"]", txt)
            if m:
                version = m.group(1)
        except OSError:
            pass

    return {
        "produto": "CONTROLE MESTRE",
        "versao": version,
        "revisao": revision,
        "data_instalacao": "anterior",
        "status": "instalada"
    }


def fetch_official_manifest(url: str = OFFICIAL_MANIFEST_URL) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ControleMestre-UniversalUpdater/1.0",
            "Accept": "application/json, text/plain",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            return json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Erro HTTP ao consultar versão oficial no GitHub: {exc.code} {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Falha de conexão com o GitHub: {exc.reason}") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"Manifesto de versão oficial inválido ou corrompido: {exc}") from exc


def download_zipball(archive_url: str, destination: Path) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        archive_url,
        headers={
            "User-Agent": "ControleMestre-UniversalUpdater/1.0",
            "Accept": "application/vnd.github+json, application/zip",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response, destination.open("wb") as out:
            total = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise RuntimeError("Download excedeu o limite máximo de segurança (120MB).")
                out.write(chunk)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub retornou erro HTTP {exc.code} no download do pacote.") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Falha de rede ao baixar pacote do GitHub: {exc.reason}") from exc

    if not zipfile.is_zipfile(destination):
        raise RuntimeError("O arquivo baixado não é um ZIP válido.")
    return destination


def safe_extract_zip(archive: Path, destination: Path, required_files: tuple[str, ...]) -> Path:
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zipped:
        items = zipped.infolist()
        if not items:
            raise RuntimeError("O pacote recebido está vazio.")
        if sum(x.file_size for x in items) > MAX_UNCOMPRESSED_BYTES:
            raise RuntimeError("O pacote descompactado excede o limite máximo permitido.")

        roots = set()
        for info in items:
            name = info.filename
            pure = PurePosixPath(name)
            if (not name or name.startswith(("/", "\\")) or "\\" in name or
                ":" in pure.parts[0] or ".." in pure.parts or
                (not info.is_dir() and len(pure.parts) < 2)):
                raise RuntimeError(f"Caminho inválido detectado no pacote: {name}")
            roots.add(pure.parts[0])
            mode = (info.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(mode):
                raise RuntimeError(f"Link simbólico não permitido detectado: {name}")
            if info.is_dir():
                continue
            if info.file_size > 60 * 1024 * 1024:
                raise RuntimeError(f"Arquivo individual no pacote excede limite seguro: {name}")
            target = destination.joinpath(*pure.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipped.open(info) as src, target.open("wb") as out:
                shutil.copyfileobj(src, out, length=1024 * 1024)

        if len(roots) != 1:
            raise RuntimeError(f"O pacote contém múltiplas raízes ({len(roots)}). Esperada raiz única.")
        extracted_root = destination / next(iter(roots))
        for needed in required_files:
            if not (extracted_root / needed).is_file():
                raise RuntimeError(f"Pacote incompleto recebido do GitHub: ausente '{needed}'")
        return extracted_root


def create_app_snapshot(app_dir: Path, versions_dir: Path, current_version: str) -> Path:
    versions_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_name = f"app_{stamp}_v{current_version.replace('.', '_')}"
    snapshot_path = versions_dir / snapshot_name
    if app_dir.exists():
        shutil.copytree(app_dir, snapshot_path)
    return snapshot_path


def validate_installation(app_dir: Path, python_exe: str = sys.executable) -> bool:
    launch_py = app_dir / "launch.py"
    if not launch_py.is_file():
        return False
    try:
        proc = subprocess.run(
            [python_exe, str(launch_py), "--diagnostico"],
            cwd=str(app_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return proc.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def rollback_last_version(app_dir: Path, versions_dir: Path) -> Path | None:
    if not versions_dir.is_dir():
        return None
    snapshots = sorted([p for p in versions_dir.iterdir() if p.is_dir() and p.name.startswith("app_")],
                       key=lambda p: p.stat().st_mtime, reverse=True)
    if not snapshots:
        return None
    target_snapshot = snapshots[0]
    if app_dir.exists():
        temp_bad = app_dir.with_name(f"app_failed_{uuid.uuid4().hex[:8]}")
        app_dir.replace(temp_bad)
        try:
            shutil.copytree(target_snapshot, app_dir)
            shutil.rmtree(temp_bad, ignore_errors=True)
        except Exception:
            if not app_dir.exists() and temp_bad.exists():
                temp_bad.replace(app_dir)
            raise
    else:
        shutil.copytree(target_snapshot, app_dir)
    return target_snapshot


def write_text_utf8(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\r\n")


def setup_desktop_folder(paths: dict[str, Path], interpreter: str = sys.executable) -> None:
    desktop_cm = paths["desktop_cm"]
    desktop_cm.mkdir(parents=True, exist_ok=True)
    root = paths["root"]
    app = paths["app"]
    updater_dir = paths["updater"]
    updater_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copiar atualizador autônomo para %LOCALAPPDATA%\ControleMestre\atualizador\atualizador.py
    this_file = Path(__file__).resolve()
    target_updater = updater_dir / "atualizador.py"
    try:
        if this_file != target_updater:
            shutil.copy2(this_file, target_updater)
    except OSError:
        pass

    # 2. Criar ABRIR_CONTROLE_MESTRE.bat na pasta da Área de Trabalho
    bat_abrir = desktop_cm / "ABRIR_CONTROLE_MESTRE.bat"
    bat_abrir_content = (
        "@echo off\r\n"
        "setlocal EnableExtensions\r\n"
        "chcp 65001 >nul\r\n"
        "title CONTROLE MESTRE - Estudos e Historico\r\n"
        "set \"CONTROLE_MESTRE_DB=%LOCALAPPDATA%\\ControleMestre\\dados\\controle_mestre.db\"\r\n"
        "cd /d \"%LOCALAPPDATA%\\ControleMestre\\app\"\r\n"
        f"\"{interpreter}\" -u launch.py\r\n"
        "if errorlevel 1 (\r\n"
        "  echo.\r\n"
        "  echo Nao foi possivel abrir o CONTROLE MESTRE. Verifique a mensagem acima.\r\n"
        "  pause\r\n"
        ")\r\n"
    )
    write_text_utf8(bat_abrir, bat_abrir_content)

    # Cópia também em %LOCALAPPDATA%\ControleMestre\ABRIR_CONTROLE_MESTRE.bat
    write_text_utf8(root / "ABRIR_CONTROLE_MESTRE.bat", bat_abrir_content)

    # 3. Criar ATUALIZAR_CONTROLE_MESTRE.bat na pasta da Área de Trabalho
    bat_atualizar = desktop_cm / "ATUALIZAR_CONTROLE_MESTRE.bat"
    bat_atualizar_content = (
        "@echo off\r\n"
        "setlocal EnableExtensions\r\n"
        "chcp 65001 >nul\r\n"
        "title CONTROLE MESTRE - Atualizador Oficial\r\n"
        "echo ============================================================\r\n"
        "echo CONTROLE MESTRE - Atualizacao Oficial e Segura\r\n"
        "echo ============================================================\r\n"
        "echo.\r\n"
        f"\"{interpreter}\" -u \"%LOCALAPPDATA%\\ControleMestre\\atualizador\\atualizador.py\"\r\n"
        "if errorlevel 1 (\r\n"
        "  echo.\r\n"
        "  echo A atualizacao encontrou um problema. O historico e o app foram preservados.\r\n"
        ")\r\n"
        "echo.\r\n"
        "pause\r\n"
    )
    write_text_utf8(bat_atualizar, bat_atualizar_content)

    # 4. Criar INSTRUCOES_DE_UTILIZACAO.txt na pasta da Área de Trabalho
    instrucoes = desktop_cm / "INSTRUCOES_DE_UTILIZACAO.txt"
    instrucoes_content = (
        "========================================================================\r\n"
        "CONTROLE MESTRE — PADRONIZACAO DEFINITIVA DA INSTALACAO E ACESSO\r\n"
        "========================================================================\r\n\r\n"
        "COMO USAR ESTA PASTA:\r\n\r\n"
        "1. PARA ABRIR O APLICATIVO:\r\n"
        "   - Clique duas vezes em 'ABRIR_CONTROLE_MESTRE.bat'.\r\n"
        "   - O painel abrirá automaticamente no navegador em http://127.0.0.1:8771\r\n\r\n"
        "2. PARA ATUALIZAR O APLICATIVO:\r\n"
        "   - Clique duas vezes em 'ATUALIZAR_CONTROLE_MESTRE.bat'.\r\n"
        "   - O atualizador universal consulta a versão oficial consolidada do GitHub,\r\n"
        "     cria backup automático e verificado do banco SQLite, atualiza o código\r\n"
        "     no mesmo local e preserva todo o seu histórico.\r\n"
        "   - NUNCA MAIS é necessário baixar ZIPs manuais nem criar novas pastas.\r\n\r\n"
        "3. ONDE FICAM SEUS DADOS E HISTORICO:\r\n"
        "   - Banco de dados ativo: %LOCALAPPDATA%\\ControleMestre\\dados\\controle_mestre.db\r\n"
        "   - Backups automáticos: %LOCALAPPDATA%\\ControleMestre\\dados\\backups\r\n"
        "   - Materiais e catálogos: %LOCALAPPDATA%\\ControleMestre\\dados\\materiais\r\n\r\n"
        "4. VERSOES ANTERIORES E SEGURANCA:\r\n"
        "   - Caso precise reverter para a versão anterior por qualquer motivo,\r\n"
        "     execute: py -3 \"%LOCALAPPDATA%\\ControleMestre\\atualizador\\atualizador.py\" --reverter\r\n"
        "   - A pasta 'instaladores_antigos' contém as pastas das versões anteriores\r\n"
        "     arquivadas de forma organizada e segura, sem perda de arquivos.\r\n\r\n"
        "Repositório oficial: https://github.com/antoniomoraes85/Controle-Mestre\r\n"
    )
    write_text_utf8(instrucoes, instrucoes_content)

    # 5. Atalho CONTROLE MESTRE.cmd na raiz da Área de Trabalho (para conveniência direta)
    desktop_cmd = paths["desktop_cmd"]
    cmd_content = (
        "@echo off\r\n"
        "call \"%~dp0CONTROLE MESTRE\\ABRIR_CONTROLE_MESTRE.bat\"\r\n"
    )
    try:
        write_text_utf8(desktop_cmd, cmd_content)
    except OSError:
        pass


def archive_legacy_directories(desktop_cm: Path) -> dict:
    """Arquiva pastas legadas na subpasta instaladores_antigos sem excluir nada
    e sem misturar bancos de dados.
    """
    target_archive = desktop_cm / "instaladores_antigos"
    target_archive.mkdir(parents=True, exist_ok=True)
    report_lines = [
        f"RELATÓRIO DE ARQUIVAMENTO SEGURO — {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "=" * 70,
        "Todas as pastas legadas foram movidas para 'instaladores_antigos'.",
        "Nenhum arquivo foi excluído. Nenhum banco de dados foi misturado ou alterado.",
        "",
        "BANCOS DE DADOS IDENTIFICADOS NAS PASTAS ARQUIVADAS:",
    ]

    moved_dirs = []
    found_databases = []

    # Procurar pastas irmãs dentro de desktop_cm
    for item in list(desktop_cm.iterdir()):
        if not item.is_dir():
            continue
        name_upper = item.name.upper()
        if item.name == "instaladores_antigos":
            continue
        if name_upper.startswith("ATUALIZADOR_CM_") or name_upper == "NOVA PASTA" or item.name == "CONTROLE_MESTRE":
            # Catalogar todos os .db antes de mover
            dbs = list(item.rglob("*.db"))
            for db in dbs:
                try:
                    size = db.stat().st_size
                    mtime = datetime.fromtimestamp(db.stat().st_mtime).strftime("%d/%m/%Y %H:%M:%S")
                    found_databases.append({"path": str(db), "size": size, "mtime": mtime})
                    report_lines.append(f" - {db.relative_to(desktop_cm)} ({size:,} bytes, modificado em {mtime})")
                except OSError:
                    pass

            dest = target_archive / item.name
            if dest.exists():
                dest = target_archive / f"{item.name}_{uuid.uuid4().hex[:6]}"
            try:
                shutil.move(str(item), str(dest))
                moved_dirs.append(item.name)
            except OSError as exc:
                report_lines.append(f"Aviso: Não foi possível mover {item.name}: {exc}")

    if not found_databases:
        report_lines.append(" (Nenhum banco de dados legado foi encontrado nas pastas arquivadas)")

    report_lines.extend([
        "",
        "PASTAS ARQUIVADAS COM SUCESSO:",
        *[f" - {d}" for d in moved_dirs],
        "",
        "BANCO DE DADOS ATIVO E OFICIAL EM USO:",
        f" - %LOCALAPPDATA%\\ControleMestre\\dados\\controle_mestre.db",
        "=" * 70,
    ])

    report_file = desktop_cm / "RELATORIO_ARQUIVAMENTO.txt"
    write_text_utf8(report_file, "\r\n".join(report_lines) + "\r\n")

    return {
        "moved": moved_dirs,
        "databases": found_databases,
        "report_path": report_file,
    }


def perform_update(
    paths: dict[str, Path],
    manifest: dict | None = None,
    archive_zip: Path | None = None,
    force: bool = False,
    auto_launch: bool = False,
) -> dict:
    app_dir = paths["app"]
    dados_dir = paths["dados"]
    db_path = paths["db"]
    backups_dir = paths["backups"]
    versoes_dir = paths["versoes"]
    root_dir = paths["root"]

    for d in (app_dir, dados_dir, backups_dir, versoes_dir):
        d.mkdir(parents=True, exist_ok=True)

    installed = get_installed_version(app_dir)
    print(f"\n[1/6] Versão instalada: {installed.get('versao')} (revisão: {installed.get('revisao', 'desconhecida')[:7]})")

    if manifest is None:
        print("[2/6] Consultando versão oficial consolidada no GitHub...")
        manifest = fetch_official_manifest()

    target_version = manifest.get("versao", "desconhecida")
    target_revision = manifest.get("revisao", "desconhecida")
    archive_url = manifest.get("archive_url") or f"https://api.github.com/repos/{DEFAULT_REPO}/zipball/{target_revision}"
    required = tuple(manifest.get("arquivos_obrigatorios", REQUIRED_FILES))

    print(f"      Versão oficial disponível: {target_version} (revisão: {target_revision[:7]})")

    is_same = (installed.get("versao") == target_version and 
               installed.get("revisao") == target_revision)

    if is_same and not force:
        print("\nO CONTROLE MESTRE já está atualizado na versão mais recente oficial.")
        setup_desktop_folder(paths)
        return {
            "updated": False,
            "version": target_version,
            "revision": target_revision,
            "message": "Já está na versão mais recente.",
        }

    # 3. Backup do banco SQLite ativo
    backup_file = None
    if db_path.is_file():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backups_dir / f"antes_atualizacao_{stamp}_v{installed.get('versao')}.sqlite3"
        print(f"\n[3/6] Criando backup online seguro do banco SQLite...")
        sqlite_backup(db_path, backup_file)
        print(f"      Backup verificado com sucesso: {backup_file.name}")
    else:
        print("\n[3/6] Nenhum banco de dados prévio localizado em 'dados'. Um novo será criado na abertura.")

    # 4. Criar snapshot de recuperação de app
    print("\n[4/6] Criando ponto de restauração da versão atual...")
    snapshot_path = create_app_snapshot(app_dir, versoes_dir, installed.get("versao", "0.0.0"))
    print(f"      Ponto de restauração salvo em: {snapshot_path.name}")

    # 5. Baixar e extrair nova versão
    with tempfile.TemporaryDirectory(prefix="cm_upd_", dir=root_dir) as td:
        temp_dir = Path(td)
        zip_target = temp_dir / "update.zip"

        if archive_zip is not None and archive_zip.is_file():
            shutil.copy2(archive_zip, zip_target)
        else:
            print(f"\n[5/6] Baixando atualização do GitHub...")
            download_zipball(archive_url, zip_target)

        print("      Verificando integridade e arquivos obrigatórios...")
        extracted_root = safe_extract_zip(zip_target, temp_dir / "extract", required)

        # Atualizar app_dir com proteção de rollback
        try:
            # Substituir arquivos na pasta app sem mexer em dados
            # Limpar app_dir com segurança preservando versao_instalada
            for item in list(app_dir.iterdir()):
                if item.name == "versao_instalada.json":
                    continue
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink(missing_ok=True)

            for item in extracted_root.iterdir():
                dest_item = app_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest_item)
                else:
                    shutil.copy2(item, dest_item)

            # Gravar versao_instalada.json
            record = {
                "produto": "CONTROLE MESTRE",
                "versao": target_version,
                "revisao": target_revision,
                "branch_origem": manifest.get("branch_origem", DEFAULT_BRANCH),
                "data_atualizacao": datetime.now().isoformat(),
                "status": "instalada",
            }
            write_text_utf8(app_dir / "versao_instalada.json", json.dumps(record, indent=2))

            # Validar diagnóstico
            print("\n[6/6] Validando integridade da instalação no ambiente Windows...")
            if not validate_installation(app_dir):
                raise RuntimeError("Falha no diagnóstico pós-atualização. Acionando reversão automática.")

        except Exception as exc:
            print(f"\nERRO DURANTE A ATUALIZAÇÃO: {exc}")
            print("Executando reversão imediata para a versão anterior...")
            if snapshot_path.is_dir():
                for item in list(app_dir.iterdir()):
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        item.unlink(missing_ok=True)
                for item in snapshot_path.iterdir():
                    d = app_dir / item.name
                    if item.is_dir():
                        shutil.copytree(item, d)
                    else:
                        shutil.copy2(item, d)
                print("Reversão concluída com sucesso. Seu ambiente está no estado anterior.")
            raise

    # Configurar pasta Desktop padronizada
    setup_desktop_folder(paths)

    print("\n" + "=" * 60)
    print("ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print(f"Versão atual instalada : {target_version} (revisão {target_revision[:7]})")
    print(f"Pasta do aplicativo    : {app_dir}")
    print(f"Banco de dados ativo   : {db_path}")
    if backup_file:
        print(f"Cópia de segurança     : {backup_file}")
    print(f"Atalho de abertura     : {paths['desktop_cm'] / 'ABRIR_CONTROLE_MESTRE.bat'}")
    print("=" * 60)

    if auto_launch and os.name == "nt":
        bat_launch = paths["desktop_cm"] / "ABRIR_CONTROLE_MESTRE.bat"
        print("\nIniciando o CONTROLE MESTRE...")
        subprocess.Popen(["cmd.exe", "/c", str(bat_launch)], cwd=str(app_dir), creationflags=subprocess.CREATE_NEW_CONSOLE)

    return {
        "updated": True,
        "version": target_version,
        "revision": target_revision,
        "backup": str(backup_file) if backup_file else None,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Atualizador Universal do CONTROLE MESTRE")
    parser.add_argument("--verificar", action="store_true", help="Apenas consultar se há atualização disponível")
    parser.add_argument("--forcar", action="store_true", help="Forçar atualização/reinstalação mesmo na mesma versão")
    parser.add_argument("--reverter", action="store_true", help="Reverter para o último snapshot salvo")
    parser.add_argument("--arquivar", action="store_true", help="Arquivar diretórios antigos na Área de Trabalho")
    parser.add_argument("--diagnostico", action="store_true", help="Exibir informações do ambiente")
    parser.add_argument("--abrir", action="store_true", help="Abrir a aplicação após atualizar")
    args = parser.parse_args(argv)

    paths = persistent_paths()

    if args.diagnostico:
        installed = get_installed_version(paths["app"])
        print("DIAGNÓSTICO DO CONTROLE MESTRE:")
        print(f"  Versão instalada    : {installed.get('versao')} ({installed.get('revisao', '')[:7]})")
        print(f"  Pasta de código     : {paths['app']}")
        print(f"  Banco de dados      : {paths['db']} ({'Existe' if paths['db'].is_file() else 'Não existe'})")
        print(f"  Pasta de dados      : {paths['dados']}")
        print(f"  Backups realizados  : {len(list(paths['backups'].glob('*.sqlite3'))) if paths['backups'].is_dir() else 0}")
        print(f"  Pasta Área Trabalho : {paths['desktop_cm']}")
        return 0

    if args.arquivar:
        print("Arquivando pastas legadas da Área de Trabalho...")
        res = archive_legacy_directories(paths["desktop_cm"])
        print(f"Pastas movidas: {', '.join(res['moved']) if res['moved'] else 'Nenhuma'}")
        print(f"Bancos identificados e preservados: {len(res['databases'])}")
        print(f"Relatório gerado em: {res['report_path']}")
        return 0

    if args.reverter:
        print("Revertendo para o último ponto de restauração...")
        try:
            snapshot = rollback_last_version(paths["app"], paths["versoes"])
            if snapshot:
                print(f"Sucesso: restaurado a partir de {snapshot.name}")
                setup_desktop_folder(paths)
                return 0
            else:
                print("Nenhum ponto de restauração encontrado em 'versoes_anteriores'.")
                return 1
        except Exception as exc:
            print(f"Falha na reversão: {exc}")
            return 1

    if args.verificar:
        installed = get_installed_version(paths["app"])
        print(f"Versão local: {installed.get('versao')} ({installed.get('revisao', '')[:7]})")
        try:
            official = fetch_official_manifest()
            print(f"Versão oficial: {official.get('versao')} ({official.get('revisao', '')[:7]})")
            if installed.get('versao') == official.get('versao') and installed.get('revisao') == official.get('revisao'):
                print("Status: 100% atualizado.")
            else:
                print("Status: Atualização disponível.")
            return 0
        except Exception as exc:
            print(f"Erro ao verificar versão remota: {exc}")
            return 1

    try:
        perform_update(paths, force=args.forcar, auto_launch=args.abrir)
        # Oferecer arquivamento se existirem pastas legadas
        desktop_cm = paths["desktop_cm"]
        has_legacy = any(
            item.is_dir() and item.name != "instaladores_antigos" and (
                item.name.upper().startswith("ATUALIZADOR_CM_") or 
                item.name.upper() == "NOVA PASTA" or 
                item.name == "CONTROLE_MESTRE"
            )
            for item in desktop_cm.iterdir()
        )
        if has_legacy:
            archive_legacy_directories(desktop_cm)
            print("\nPastas legadas anteriores arquivadas em 'instaladores_antigos' com sucesso.")
        return 0
    except Exception as exc:
        print(f"\nFALHA NO ATUALIZADOR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
