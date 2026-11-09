"""Importador LOCAL de sumários: múltiplos assuntos para o mesmo PDF.

Entrada JSON: {"topic_links":[{"material_id":123,"subject":"...","topic":"...",
 "subtopic":"...","page_from":2,"page_to":5,"excerpt":"texto curto da página"}]}

Padrão: simulação, sem escrever. --apply registra pendências. --apply --approve
exige que o trecho esteja no PDF na página correspondente. Sempre faz backup
consistente antes de alterações. Não envia nenhum documento à nuvem.
"""
from __future__ import annotations
import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from core import norm,DB_PATH,connect
from curriculum_topic_links import register
from sources import path_for_material

def check_link(c,record):
    ident=record.get('material_id')
    if not isinstance(ident,int) or isinstance(ident,bool) or ident<1:
        return False,'Identificador de PDF inválido'
    try:
        path=path_for_material(c,ident)
        import fitz
        with fitz.open(path) as pdf:
            page=record.get('page_from')
            if not isinstance(page,int) or isinstance(page,bool) or not 1<=page<=len(pdf):
                return False,'Página inexistente'
            excerpt=norm(record.get('excerpt') or '')
            if not excerpt:
                return False,'Trecho obrigatório para aprovação'
            text=norm(pdf[page-1].get_text(sort=True))
            if excerpt not in text:
                return False,'Trecho não encontrado na página'
        return True,''
    except (ValueError,OSError,RuntimeError,ImportError) as exc:
        return False,'Falha na conferência: '+str(exc)[:140]

def backup_database(db):
    dest=db.parent/'backups'/(
        'antes_catalogacao_topicos_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.sqlite3')
    dest.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(str(db))
    try:
        if con.execute('PRAGMA quick_check').fetchone()[0]!='ok':
            raise RuntimeError('Banco ativo falhou no quick_check')
        out=sqlite3.connect(str(dest))
        try:
            con.backup(out)
            if out.execute('PRAGMA quick_check').fetchone()[0]!='ok':
                raise RuntimeError('Backup falhou no quick_check')
        finally:out.close()
    finally:con.close()
    return dest

def main(argv=None):
    parser=argparse.ArgumentParser(description='Catalogar vários tópicos de um mesmo PDF')
    parser.add_argument('input',type=Path)
    parser.add_argument('--db',type=Path,default=DB_PATH)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--approve',action='store_true')
    args=parser.parse_args(argv)
    if args.approve and not args.apply:parser.error('--approve exige --apply')
    payload=json.loads(args.input.read_text(encoding='utf-8'))
    rows=payload.get('topic_links',[]) if isinstance(payload,dict) else payload
    if not isinstance(rows,list) or not rows:
        parser.error('O JSON deve conter uma lista não vazia topic_links')
    print(f'Assuntos/subassuntos propostos: {len(rows)}')
    if not args.apply:
        print('Simulação: nenhuma alteração realizada. Use --apply somente após revisar as fontes.')
        return 0
    db=args.db.expanduser()
    if not db.is_file():raise SystemExit('Banco ativo não encontrado: '+str(db))
    print('Backup verificado:',backup_database(db))
    c=connect(db)
    try:
        if args.approve:
            pending=[]
            for item in rows:
                ok,reason=check_link(c,item)
                if not ok:pending.append((item,reason))
            if pending:
                for item,why in pending[:25]:
                    print('PENDENTE:',item.get('material_id'),item.get('topic'),why)
                raise SystemExit('Aprovação recusada: documento/página/trecho não verificáveis')
        result=register(c,rows,verified=args.approve)
        print('Importação realizada:',result)
        return 0
    finally:c.close()

if __name__=='__main__':
    raise SystemExit(main())
