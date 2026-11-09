"""Inicializador confiavel do CONTROLE MESTRE para instalacoes locais.

Nao instala dependencias, nao abre portas de rede publica e nao altera metricas.
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
HOST = '127.0.0.1'
PORTS = tuple(range(8771, 8781))  # 8765 reservado ao AnkiConnect
ESSENTIAL = ('core.py', 'web_server.py', 'assessments.py',
             'web/index.html', 'web/style.css', 'web/app.js',
             'web/modules/assessments.js', 'adaptive.py', 'web/modules/adaptive.js',
             'sources.py', 'backup_manager.py', 'web/modules/sources.js',
             'fiscal_path.py', 'web/modules/fiscal.js', 'anki_bridge.py',
             'web/modules/anki_bridge.js', 'error_tracking.py',
             'smart_reinforcement.py', 'web/modules/questions.js',
             'study_guide.py', 'study_time.py', 'bizu_seed.py', 'anki_analytics.py',
             'web/modules/study_guide.js', 'web/modules/study_time.js',
             'web/modules/study_timer.js', 'web/modules/anki_analytics.js',
             'assessment_insights.py', 'question_bank.py',
             'web/modules/assessment_insights.js', 'web/modules/question_bank.js',
             'lesson_question_links.py','curriculum_insights.py',
             'web/modules/curriculum.js','material_autolink.py','topic_importance.py',
             'cycle_planner.py','web/modules/cycle_planner.js',
             'priority_engine.py','curriculum_evidence.py','local_curriculum_import.py',
             'curriculum_topic_links.py','local_curriculum_topics.py')


def _existing_controle_mestre(port: int) -> bool:
    try:
        with urlopen(f'http://{HOST}:{port}/api/health', timeout=.45) as resp:
            info = json.load(resp)
            return (resp.status == 200 and info.get('ok') is True
                    and info.get('app') == 'CONTROLE MESTRE'
                    and info.get('mode') == 'private-local'
                    and info.get('version') == '0.8.8')
    except (OSError, HTTPError, URLError, ValueError, TypeError):
        return False


def _port_is_available(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((HOST, port))
            return True
    except OSError:
        return False


def select_port():
    """Return (port, already_running). Never interrupt another local service."""
    for port in PORTS:
        if _existing_controle_mestre(port):
            return port, True
        if _port_is_available(port):
            return port, False
    raise RuntimeError('Todas as portas locais 8771 a 8780 estao ocupadas.')


def check_environment():
    print('CONTROLE MESTRE — diagnostico local', flush=True)
    print(f'Python: {sys.version.split()[0]}')
    print(f'Pasta: {ROOT}')
    if sys.version_info < (3, 11):
        raise RuntimeError('Python 3.11 ou superior necessario.')
    missing = [f for f in ESSENTIAL if not (ROOT / f).is_file()]
    if missing:
        raise RuntimeError('Arquivos ausentes: ' + ', '.join(missing)
                           + '. Extraia o ZIP completo antes de executar.')
    import core
    import web_server  # noqa: F401
    from backup_manager import make_backup
    bkp = make_backup(core.DB_PATH, core.DB_PATH.parent / 'backups')
    if bkp: print(f'Backup diario verificado: {bkp.name}')
    print(f'Historico persistente: {core.DB_PATH.resolve()}')
    print(f'Backups automaticos: {(core.DB_PATH.parent / "backups").resolve()}')
    conn = core.connect()
    try:
        conn.execute('SELECT 1').fetchone()
        print('Banco SQLite: acesso OK (dados locais preservados)')
    finally:
        conn.close()
    port, running = select_port()
    print(f'Porta: {port} ' + ('(servidor ja aberto)' if running else '(disponivel)'))
    print('Verificacao concluida.', flush=True)
    return port, running


def _save_failure(exc):
    try:
        logs = ROOT / 'logs'
        logs.mkdir(parents=True, exist_ok=True)
        target = logs / 'ultimo_erro_inicializacao.log'
        target.write_text(f'{datetime.now().isoformat(timespec="seconds")}\n'
                          + ''.join(traceback.format_exception(exc)), encoding='utf-8')
        print(f'Log do problema: {target}', flush=True)
    except OSError:
        pass


def main(argv=None):
    parser = argparse.ArgumentParser(description='Inicializar o CONTROLE MESTRE local')
    parser.add_argument('--diagnostico', action='store_true', help='Verificar arquivos e servidor sem abrir a interface')
    args = parser.parse_args(argv)
    try:
        port, already = check_environment()
        if args.diagnostico:
            return 0
        url = f'http://{HOST}:{port}'
        if already:
            print(f'A plataforma ja esta executando em: {url}', flush=True)
            webbrowser.open(url)
            return 0
        print(f'ABRINDO: {url}', flush=True)
        print('Mantenha esta janela aberta enquanto usar a plataforma.', flush=True)
        from web_server import serve
        serve(host=HOST, port=port)
        return 0
    except Exception as exc:
        print('\nERRO AO INICIAR O CONTROLE MESTRE:', exc, file=sys.stderr, flush=True)
        _save_failure(exc)
        print('Verifique se extraiu o ZIP completo e se o Python foi instalado.', flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())