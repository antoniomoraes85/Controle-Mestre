"""Importação LOCAL, auditável, das incidências extraídas dos PDFs particulares.

Uso:
  py -3 local_curriculum_import.py C:\\...\\incidencias_local.json
  py -3 local_curriculum_import.py C:\\...\\incidencias_local.json --apply
  py -3 local_curriculum_import.py C:\\...\\incidencias_local.json --apply --approve

Por padrão, apenas valida e apresenta estatísticas; nenhum histórico é alterado.
--apply persiste pendências não verificadas.
--approve exige PDFs presentes e comparação do trecho/percentual com a página.
O arquivo JSON e os documentos particulares NUNCA vão para o GitHub.
"""
from __future__ import annotations
import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from core import DB_PATH,connect,norm
from curriculum_evidence import register

def verify_reference(row):
    path=Path(str(row.get('document_reference') or ''))
    if not path.is_absolute() or not path.is_file() or path.suffix.lower()!='.pdf':
        return False,'Arquivo PDF local não encontrado'
    try:
        import fitz
    except ImportError:
        return False,'PyMuPDF indisponível para validar páginas'
    try:
        with fitz.open(path) as pdf:
            page_number=row.get('page')
            if not isinstance(page_number,int) or isinstance(page_number,bool) or not 1<=page_number<=len(pdf):
                return False,'Página inexistente no PDF'
            text=norm(pdf[page_number-1].get_text(sort=True))
    except Exception as exc:
        return False,'Não foi possível ler o PDF: '+type(exc).__name__
    snippet=norm(row.get('excerpt') or '')
    if not snippet or snippet not in text:
        return False,'Trecho de evidência não localizado na página'
    percentage=row.get('incidence_pct')
    if percentage is not None:
        pct=str(percentage).rstrip('0').rstrip('.') if isinstance(percentage,float) else str(percentage)
        pct_norm=norm(pct)
        # Presença de percentual em forma '8,41%' ou '8.41%' na mesma página.
        if not any(token in text for token in (pct_norm,pct_norm.replace(' ',''))):
            return False,'Percentual não encontrado na página'
    return True,''

def main(argv=None):
    parser=argparse.ArgumentParser(description='Auditoria local de incidência curricular')
    parser.add_argument('json_path',type=Path)
    parser.add_argument('--db',type=Path,default=DB_PATH)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--approve',action='store_true')
    args=parser.parse_args(argv)
    if args.approve and not args.apply:parser.error('--approve exige --apply')
    raw=json.loads(args.json_path.read_text(encoding='utf-8'))
    records=raw['evidences'] if isinstance(raw,dict) else raw
    if not isinstance(records,list):parser.error('Formato: lista ou objeto com campo evidences')
    verified=[];pending=[]
    for row in records:
        good,reason=verify_reference(row)
        if good:verified.append(row)
        else:pending.append((row,reason))
    print(f'Evidências: {len(records)} | PDFs verificados: {len(verified)} | Pendências: {len(pending)}')
    for item,reason in pending[:30]:
        print(f"  REVISAR: {item.get('subject')} / {item.get('topic')} — {reason}")
    if not args.apply:
        print('SIMULAÇÃO: nenhum arquivo ou registro foi modificado.')
        return 0
    db=args.db.expanduser()
    if not db.exists():raise SystemExit('Banco não encontrado: '+str(db))
    backup=db.parent/'backups'/('antes_importacao_incidencias_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.sqlite3')
    backup.parent.mkdir(parents=True,exist_ok=True)
    source=sqlite3.connect(str(db))
    try:
        if source.execute('PRAGMA quick_check').fetchone()[0]!='ok':
            raise SystemExit('Banco de origem não passou no quick_check')
        dest=sqlite3.connect(str(backup))
        try:
            source.backup(dest)
            if dest.execute('PRAGMA quick_check').fetchone()[0]!='ok':
                raise SystemExit('Backup não passou no quick_check')
        finally:dest.close()
    finally:source.close()
    print('Backup consistente:',backup)
    c=connect(db)
    try:
        if args.approve and pending:
            raise SystemExit('Aprovação bloqueada: todos os trechos precisam ser conferidos. '
                             'Importe como pendentes ou corrija a fonte.')
        result=register(c,records,verified=args.approve)
    finally:c.close()
    print('Importação concluída:',result)
    print('Status:', 'APROVADO COM EVIDÊNCIA' if args.approve else 'PENDENTE DE AUDITORIA')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
