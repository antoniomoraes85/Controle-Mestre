"""Auditoria local SOMENTE DE LEITURA da catalogação v0.8.8.

Não importa PDFs/JSON, não recalcula prioridades, não cria banco, não faz commit,
não substitui versão e não modifica tabelas. Execute em um checkout do GitHub:
    py -3 tools/auditoria_local_v088.py
    py -3 tools/auditoria_local_v088.py --pdf-root "C:\...\MATERIAL TEÓRICO"

Imprime apenas contagens e metadados. Não publica dados privados.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen


TABLES = (
    "study_materials",
    "curriculum_topic_links",
    "curriculum_evidence",
    "topic_importance",
    "topic_importance_v2",
    "planning_preferences",
)
COLUMN_EXPECTATIONS = {
    "study_materials": ("subject", "lesson", "relative_path", "file_name"),
    "curriculum_topic_links": ("material_id", "subject", "topic", "subtopic",
                               "page_from", "page_to", "verified"),
    "curriculum_evidence": ("subject", "topic", "incidence_pct", "qualitative",
                            "document_reference", "page", "verified"),
    "topic_importance_v2": ("subject_key", "topic_key", "level"),
}


def cmd(*args: str, cwd: Path) -> str:
    try:
        proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                              timeout=12, check=False)
        return proc.stdout.strip() if proc.returncode == 0 else (
            f"INACESSÍVEL (exit={proc.returncode}): {proc.stderr.strip()[:120]}")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"INACESSÍVEL ({type(exc).__name__})"


def json_file(path: Path) -> dict:
    if not path.is_file():
        return {"exists": False}
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        return {"exists": True, "error": type(exc).__name__}
    if isinstance(d, list):
        return {"exists": True, "form": "array", "entries": len(d)}
    if isinstance(d, dict):
        for key in ("topic_links", "evidences", "records"):
            if isinstance(d.get(key), list):
                return {"exists": True, "form": f"object.{key}",
                        "entries": len(d[key])}
        return {"exists": True, "form": "object",
                "fields": sorted(d)[:15]}
    return {"exists": True, "form": type(d).__name__}


def table_columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in con.execute(f'PRAGMA table_info("{table}")')}


def count(con: sqlite3.Connection, table: str, where: str = "") -> int:
    # Nomes e cláusulas vêm exclusivamente de constantes deste script.
    return con.execute(f'SELECT COUNT(*) FROM "{table}" {where}').fetchone()[0]


def count_distinct(con: sqlite3.Connection, table: str, field: str) -> int:
    return con.execute(
        f'SELECT COUNT(DISTINCT "{field}") FROM "{table}" '
        f'WHERE TRIM(COALESCE("{field}", "")) <> ""'
    ).fetchone()[0]


def audit_database(path: Path) -> dict:
    if not path.is_file():
        return {"exists": False, "error": "Banco oficial não encontrado"}
    try:
        # mode=ro impede CREATE/INSERT/UPDATE/DELETE, inclusive por acidente.
        con = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True,
                              timeout=12)
        con.execute("PRAGMA query_only=ON")
        with con:
            tables = {x[0] for x in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            out = {"exists": True,
                   "integrity_check": con.execute(
                       "PRAGMA integrity_check").fetchone()[0],
                   "tables": {}}
            for table in TABLES:
                if table not in tables:
                    out["tables"][table] = {"exists": False}
                    continue
                columns = table_columns(con, table)
                row = {"exists": True, "rows": count(con, table),
                       "columns": sorted(columns)}
                expected = COLUMN_EXPECTATIONS.get(table, ())
                row["missing_expected_columns"] = sorted(set(expected)-columns)
                if table == "study_materials":
                    for column in ("subject", "discipline", "lesson", "aula"):
                        if column in columns:
                            row["distinct_" + column] = count_distinct(
                                con, table, column)
                elif table == "curriculum_topic_links":
                    for column in ("subject", "topic", "subtopic"):
                        if column in columns:
                            row["distinct_" + column] = count_distinct(
                                con, table, column)
                    if "verified" in columns:
                        row["verified_1"] = count(
                            con, table, "WHERE verified=1")
                    row["has_stored_priority_column"] = "priority" in columns
                elif table == "curriculum_evidence":
                    if "verified" in columns:
                        row["verified_1"] = count(
                            con, table, "WHERE verified=1")
                    if "incidence_pct" in columns:
                        row["numeric_incidence"] = count(
                            con, table, "WHERE incidence_pct IS NOT NULL")
                    if "qualitative" in columns:
                        row["qualitative_nonempty"] = count(
                            con, table,
                            "WHERE qualitative IS NOT NULL "
                            "AND TRIM(CAST(qualitative AS TEXT)) NOT IN ('', '0')")
                out["tables"][table] = row
        con.close()
        return out
    except (OSError, sqlite3.Error) as exc:
        return {"exists": True, "error": f"{type(exc).__name__}: {exc}"}


def local_health() -> dict:
    try:
        with urlopen("http://127.0.0.1:8771/api/health", timeout=3) as response:
            body = response.read(4096)
        d = json.loads(body)
        return {"reachable": True, "body": d}
    except (OSError, ValueError) as exc:
        return {"reachable": False, "error": type(exc).__name__}


def source_check(repo: Path) -> dict:
    d = {}
    for name in ("priority_engine.py", "local_curriculum_topics.py",
                 "local_curriculum_import.py", "curriculum_topic_links.py"):
        path = repo / name
        if not path.is_file():
            d[name] = {"exists": False}
            continue
        source = path.read_text(encoding="utf-8")
        d[name] = {
            "exists": True,
            "has_recompute_flag": "--recompute" in source,
            "has_simulate_flag": "--simulate" in source,
            "has_main_entrypoint": 'if __name__' in source,
            "declares_priority_column": (
                "priority REAL" in source or "priority INTEGER" in source),
        }
    return d


def audit(repo: Path, db: Path, app: Path, pdf_root: Path | None = None) -> dict:
    output = {
        "notice": "Auditoria somente de leitura; não configura homologação dos PDFs",
        "git": {
            "branch": cmd("git", "branch", "--show-current", cwd=repo),
            "head": cmd("git", "rev-parse", "HEAD", cwd=repo),
            "working_tree_clean": not bool(
                cmd("git", "status", "--porcelain", cwd=repo)),
            # Não expor nomes de arquivos privados do diretório de trabalho.
            "remote_head": cmd(
                "git", "ls-remote", "origin",
                "refs/heads/feat/prioridade-inteligente-catalogo-v088",
                cwd=repo),
        },
        "manifest": json_file(repo/"versao_oficial.json"),
        "installed_version": json_file(app/"versao_instalada.json"),
        "health": local_health(),
        "sqlite": audit_database(db),
        "json_payloads": {
            filename: json_file(repo/filename)
            for filename in ("assuntos_locais.json", "incidencias_local.json")
        },
        "source_contracts": source_check(repo),
    }
    for key, path in (("manifest", repo/"versao_oficial.json"),
                      ("installed_version", app/"versao_instalada.json")):
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                output[key].update({
                    "versao": data.get("versao"),
                    "revisao": data.get("revisao"),
                    "archive_url": data.get("archive_url") if key == "manifest" else None,
                })
            except (OSError, ValueError):
                pass
    if pdf_root:
        output["pdf_library"] = (
            {"exists": True, "pdf_count": sum(
                1 for p in pdf_root.rglob("*") if p.is_file() and p.suffix.lower()==".pdf"
            )} if pdf_root.is_dir() else {"exists": False})
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path,
                        default=Path(__file__).resolve().parents[1])
    home = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
    parser.add_argument("--db", type=Path,
                        default=home/"ControleMestre"/"dados"/"controle_mestre.db")
    parser.add_argument("--app", type=Path,
                        default=home/"ControleMestre"/"app")
    parser.add_argument("--pdf-root", type=Path)
    args = parser.parse_args(argv)
    result = audit(args.repo.resolve(), args.db.resolve(), args.app.resolve(),
                   args.pdf_root.resolve() if args.pdf_root else None)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True,
                     default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
