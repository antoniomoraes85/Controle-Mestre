"""Backup online, verificado e local, do banco SQLite antes das migrações."""
from __future__ import annotations
import sqlite3
from datetime import datetime
from pathlib import Path


def make_backup(db_path: Path, backup_dir: Path, max_copies=15, force=False):
    db_path=Path(db_path)
    if not db_path.is_file():
        return None
    backup_dir=Path(backup_dir)
    backup_dir.mkdir(parents=True,exist_ok=True)
    current = datetime.now().strftime('%Y%m%d')
    if not force:
        matches=sorted(backup_dir.glob(f'controle_mestre_{current}_*.sqlite3'))
        if matches:return matches[-1]
    target = backup_dir/f'controle_mestre_{datetime.now():%Y%m%d_%H%M%S_%f}.sqlite3'
    src=sqlite3.connect(f'file:{db_path.resolve().as_posix()}?mode=ro',uri=True,timeout=10)
    try:
        dst=sqlite3.connect(str(target))
        try:
            src.backup(dst)
            health=dst.execute('PRAGMA quick_check').fetchone()[0]
            if health!='ok': raise RuntimeError(f'Backup inválido: {health}')
        finally:dst.close()
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:src.close()
    for old in sorted(backup_dir.glob('controle_mestre_*.sqlite3'),reverse=True)[max_copies:]:
        old.unlink()
    return target


def verify_backup(path):
    with sqlite3.connect(f'file:{Path(path).resolve().as_posix()}?mode=ro',uri=True) as c:
        return c.execute('PRAGMA quick_check').fetchone()[0]=='ok'