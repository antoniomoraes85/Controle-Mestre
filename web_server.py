"""CONTROLE MESTRE v0.5 — interface web local sobre o banco SQLite existente.
Sem serviços externos. Escuta somente 127.0.0.1; não é adequado para hospedagem pública.
"""
from __future__ import annotations
import json
import webbrowser
import mimetypes
import os
import re
import threading
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from anki_bridge import local_status as anki_status, detect as anki_detect, collect_snapshot as anki_collect, save_snapshot as anki_save
from adaptive import diagnose, preview_plan, apply_plan
from assessments import assessment_summary, insert_mock, insert_essay, delete_assessment
from sources import status as sources_status, scan_pdfs, assign_material, register_bookmark, register_tec_bookmark, preview_csv, import_csv, set_external_root, path_for_material
from fiscal_path import status as fiscal_status, activate as fiscal_activate, preview_week as fiscal_preview_week, apply_week as fiscal_apply_week, complete_task as fiscal_complete_task
from core import (ROOT, connect, all_rows, metric_data, subject_metrics,
                  get_days, save_day, generate_plan, add_session, add_questions,
                  DAY_CAPS, METHODS)
from error_tracking import (
    register_batch, register_question_item, get_batch,
    get_error_summary, get_caderno_erros, update_item_correction,
    feed_performance, finalize_batch, ERROR_CAUSES, ITEM_RESULTS, ITEM_DIFFICULTIES,
    CORRECTION_STATUSES, GABARITO_TIMINGS,
)

WEB = ROOT / 'web'


def current_week(d=None):
    d = d or date.today()
    return d - timedelta(days=d.weekday())


def overview(c, today=None):
    today = today or date.today()
    start = current_week(today)
    end = start + timedelta(days=6)
    start_iso, end_iso = start.isoformat(), end.isoformat()
    metrics = metric_data(c, today)
    ranked = subject_metrics(c, today)
    plans = all_rows(c, '''SELECT id, day, subject, topic, method, target_minutes,
          target_questions, priority, rationale, status FROM plans
          WHERE day BETWEEN ? AND ? ORDER BY day,priority DESC,id''', (start_iso,end_iso))
    done = sum(p['status'] == 'Concluída' for p in plans)
    history = all_rows(c, '''SELECT day, SUM(minutes) AS minutes FROM sessions
           WHERE day BETWEEN ? AND ? GROUP BY day ORDER BY day''',
           ((today-timedelta(days=83)).isoformat(),today.isoformat()))
    volumes={r['day']:int(r['minutes']) for r in history}
    weeks=[]
    for ix in range(12):
        w = start - timedelta(weeks=11-ix)
        minutes = sum(volumes.get((w+timedelta(days=j)).isoformat(), 0) for j in range(7))
        weeks.append({'period':f'{w:%d/%m}', 'minutes':minutes, 'hours':round(minutes/60,2)})
    sessions=all_rows(c, '''SELECT id,day,subject,topic,method,minutes,day_type
                             FROM sessions ORDER BY day DESC,id DESC LIMIT 80''')
    qq=all_rows(c, '''SELECT id,day,subject,topic,bank,total,correct FROM questions
                       ORDER BY day DESC,id DESC LIMIT 80''')
    revisions=all_rows(c, '''SELECT id,due_on,subject,topic,status FROM reviews
                           WHERE status='Pendente' ORDER BY due_on LIMIT 30''')
    anki=all_rows(c, '''SELECT day,subject,deck,cards,errors,minutes FROM anki ORDER BY day DESC LIMIT 20''')
    progress=all_rows(c, '''SELECT subject,COUNT(*) AS total,
         SUM(CASE WHEN progress>=100 THEN 1 ELSE 0 END) AS complete,
         ROUND(AVG(progress),1) AS pct FROM topics GROUP BY subject''')
    return dict(
        today=today.isoformat(), week_start=start_iso, week_end=end_iso,
        sources=sources_status(c), fiscal=fiscal_status(c,today), anki_live=anki_status(c),
        metrics=metrics, ranking=ranked, plans=plans, done=done, assessments=assessment_summary(c),
        adaptive=diagnose(c, today), adaptive_preview=preview_plan(c,start,today),
        weeks=weeks, sessions=sessions, question_history=qq, reviews=revisions,
        anki=anki, topic_progress=progress,
        cycles=all_rows(c, 'SELECT subject,cycle,ROUND(SUM(minutes),0) AS minutes FROM sessions WHERE cycle IS NOT NULL GROUP BY subject,cycle ORDER BY cycle,subject'),
        subjects=all_rows(c, 'SELECT name,weight,area FROM subjects ORDER BY weight DESC,name'),
        types=DAY_CAPS, methods=METHODS,
        days=get_days(c,start),
        focus_on=ranked[0]['disciplina'] if ranked else None,
    )


class AppHandler(BaseHTTPRequestHandler):
    server_version='ControleMestreLocal/0.6.2'
    def log_message(self, fmt, *args):
        # Do not log user payloads.
        pass

    def _reply(self, status, content, content_type='application/json; charset=utf-8'):
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(content)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Cache-Control','no-store')
        if content_type.startswith('text/html'):
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(content)

    def _json(self, status, obj):
        return self._reply(status, json.dumps(obj,ensure_ascii=False,default=str).encode('utf-8'))

    def _allowed_host(self):
        h=self.headers.get('Host','').split(':')[0].lower()
        return h in ('127.0.0.1','localhost')

    def do_GET(self):
        if not self._allowed_host():return self._json(403,{'error':'Host não permitido'})
        route=urlsplit(self.path).path
        if route=='/api/overview':
            with_db=connect()
            try: return self._json(200,overview(with_db))
            finally: with_db.close()
        if route=='/api/sources':
            c=connect()
            try:return self._json(200,sources_status(c))
            finally:c.close()
        if route=='/api/anki/check':
            try:return self._json(200,anki_detect())
            except ValueError as exc:return self._json(503,{'error':str(exc)})
        if route=='/api/adaptive':
            c=connect()
            try:return self._json(200,{'diagnosis':diagnose(c),'preview':preview_plan(c)})
            finally:c.close()
        if re.fullmatch(r'/api/fiscal/pdf/\d{1,12}',route):
            c=connect()
            try:
                path=path_for_material(c,int(route.rsplit('/',1)[-1]))
                size=path.stat().st_size
                self.send_response(200)
                for k,v in [('Content-Type','application/pdf'),('Content-Length',str(size)),
                            ('X-Content-Type-Options','nosniff'),('Cache-Control','no-store'),
                            ('Content-Security-Policy',"default-src 'none'; sandbox"),
                            ('Content-Disposition','inline')]:self.send_header(k,v)
                self.end_headers()
                with path.open('rb') as pdf:
                    for chunk in iter(lambda:pdf.read(1024*1024),b''):self.wfile.write(chunk)
                return
            except ValueError as exc:return self._json(404,{'error':str(exc)})
            finally:c.close()
        if route=='/api/health':return self._json(200,{'ok':True,'app':'CONTROLE MESTRE','version':'0.7.0','mode':'private-local','multiuser':False})
        # --- Rastreamento de erros ---
        if route=='/api/questions/caderno':
            c=connect()
            try:
                qs=urlsplit(self.path).query
                p={k:v[0] for k,v in parse_qs(qs).items()}
                nr=p.get('needs_reinforcement')
                return self._json(200,get_caderno_erros(c,
                    subject=p.get('subject'),topic=p.get('topic'),
                    primary_cause=p.get('primary_cause'),
                    correction_status=p.get('correction_status'),
                    needs_reinforcement=None if nr is None else nr=='1',
                    limit=int(p.get('limit','100'))))
            finally:c.close()
        if route=='/api/questions/summary':
            c=connect()
            try:
                qs=urlsplit(self.path).query
                p={k:v[0] for k,v in parse_qs(qs).items()}
                return self._json(200,get_error_summary(c,
                    subject=p.get('subject'),topic=p.get('topic'),
                    since=p.get('since')))
            finally:c.close()
        if re.fullmatch(r'/api/questions/batch/\d{1,12}',route):
            c=connect()
            try:
                bid=int(route.rsplit('/',1)[-1])
                return self._json(200,get_batch(c,bid))
            except ValueError as exc:return self._json(404,{'error':str(exc)})
            finally:c.close()
        if route=='/api/questions/constants':
            return self._json(200,{'error_causes':ERROR_CAUSES,'results':list(ITEM_RESULTS),
                'difficulties':list(ITEM_DIFFICULTIES),'correction_statuses':list(CORRECTION_STATUSES),
                'gabarito_timings':list(GABARITO_TIMINGS)})
        if route=='/':route='/index.html'
        static={'/index.html':'text/html; charset=utf-8','/style.css':'text/css; charset=utf-8',
                '/app.js':'text/javascript; charset=utf-8', '/favicon.ico':'image/x-icon'}
        # Só módulos e assets existentes em diretórios explícitos (sem traversal ou leitura arbitrária).
        if route.startswith('/modules/') and re.fullmatch(r'/modules/[a-z_]+\.js',route):
            static[route]='text/javascript; charset=utf-8'
        elif route.startswith('/assets/branding/') and re.fullmatch(r'/assets/branding/[a-zA-Z0-9_\-\.]+',route):
            ext=route.rsplit('.',1)[-1].lower()
            mimes={'svg':'image/svg+xml','png':'image/png','webp':'image/webp','ico':'image/x-icon'}
            if ext in mimes:
                static[route]=mimes[ext]
        if route not in static:return self._json(404,{'error':'Arquivo não encontrado'})
        path=WEB / route[1:]
        if not path.is_file():return self._json(404,{'error':'Arquivo não encontrado'})
        return self._reply(200,path.read_bytes(),static[route])

    def do_POST(self):
        if not self._allowed_host():return self._json(403,{'error':'Host não permitido'})
        # Require same-origin browser requests (and reject cross-site non-browser posts).
        origin=self.headers.get('Origin','')
        host=self.headers.get('Host','')
        if origin and origin not in (f'http://{host}',):return self._json(403,{'error':'Origem não permitida'})
        if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':
            return self._json(415,{'error':'Envie JSON'})
        length=int(self.headers.get('Content-Length','0') or 0)
        if not 0<length<=65536:return self._json(413,{'error':'Requisição inválida'})
        if self.headers.get('Sec-Fetch-Site','same-origin') not in ('same-origin','none'):return self._json(403,{'error':'Acesso de outro site bloqueado'})
        try: args=json.loads(self.rfile.read(length).decode('utf-8'))
        except (ValueError,UnicodeDecodeError):return self._json(400,{'error':'JSON inválido'})
        if not isinstance(args,dict):return self._json(400,{'error':'Objeto JSON obrigatório'})
        route=urlsplit(self.path).path
        c=connect()
        try:
            if route=='/api/anki/sync':
                if args.get('confirm') is not True:raise ValueError('Confirmação explícita necessária para sincronizar.')
                snap=anki_collect(args.get('profile','Principal'))
                return self._json(200,anki_save(c,snap,confirm=True))
            if route=='/api/fiscal/activate':
                if args.get('confirm') is not True:raise ValueError('Confirme a ativação da trilha.')
                return self._json(200,fiscal_activate(c))
            if route=='/api/fiscal/status':
                return self._json(200,fiscal_status(c,week_start=args.get('week')))
            if route=='/api/fiscal/preview':
                return self._json(200,fiscal_preview_week(c,args.get('week')))
            if route=='/api/fiscal/apply':
                return self._json(200,fiscal_apply_week(c,args.get('week'),args.get('confirm') is True))
            if route=='/api/fiscal/complete':
                return self._json(200,fiscal_complete_task(c,args['id'],args.get('minutes',0),
                    args.get('total'),args.get('correct'),args.get('error_type',''),args.get('notes',''),args.get('day')))
            if route=='/api/sources/root':
                return self._json(200,set_external_root(c,args.get('path',''),args.get('confirm') is True))
            if route=='/api/sources/scan':
                return self._json(200,scan_pdfs(c))
            if route=='/api/sources/material':
                return self._json(200,assign_material(c,args['id'], args.get('subject',''),
                    args.get('topic',''),args.get('course',''),args.get('lesson',''),args.get('material_type')))
            if route=='/api/tec/bookmark':
                return self._json(201,register_tec_bookmark(c,args['title'],args['url'],
                    args.get('subject',''),args.get('topic','')))
            if route=='/api/tec/preview':
                return self._json(200,preview_csv(c,args['file_name'],provider='TEC Concursos'))
            if route=='/api/tec/import':
                if args.get('confirm') is not True:
                    raise ValueError('Confirme a importação dos resultados TEC.')
                return self._json(200,import_csv(c,args['file_name'],provider='TEC Concursos'))
            if route=='/api/qconcursos/bookmark':
                return self._json(201,register_bookmark(c,args['title'],args['url'],
                    args.get('subject',''),args.get('topic','')))
            if route=='/api/qconcursos/preview':
                return self._json(200,preview_csv(c,args['file_name']))
            if route=='/api/qconcursos/import':
                if args.get('confirm') is not True:
                    raise ValueError('Confirme a importação dos resultados do CSV.')
                return self._json(200,import_csv(c,args['file_name']))
            if route=='/api/assessment/mock':
                return self._json(201,{'ok':True,'id':insert_mock(c,args)})
            if route=='/api/assessment/essay':
                return self._json(201,{'ok':True,'id':insert_essay(c,args)})
            if route=='/api/assessment/delete':
                kind=str(args['kind']);ident=args['id']
                if not isinstance(ident,int) or isinstance(ident,bool):raise ValueError('ID inválido')
                delete_assessment(c,kind,ident)
                return self._json(200,{'ok':True})
            if route=='/api/plan/adaptive':
                ws=date.fromisoformat(args.get('week') or current_week().isoformat())
                if args.get('confirm') is not True:
                    raise ValueError('É necessário confirmar a substituição das atividades pendentes.')
                return self._json(200,apply_plan(c,ws,confirm=True))
            if route=='/api/plan/generate':
                ws=date.fromisoformat(args.get('week') or current_week().isoformat())
                return self._json(200,generate_plan(c,ws))
            if route=='/api/day':
                day=date.fromisoformat(args['day'])
                kind=args['kind']
                if kind not in DAY_CAPS:raise ValueError('Tipo de dia inválido')
                cap=int(args['minutes'])
                save_day(c,day,kind,cap)
                return self._json(200,{'ok':True})
            if route=='/api/task/complete':
                taskid=int(args['id']);status=str(args['status'])
                if status not in ('Concluída','Pendente'):raise ValueError('Status inválido')
                cur=c.execute('UPDATE plans SET status=? WHERE id=?',(status,taskid));c.commit()
                if not cur.rowcount:raise ValueError('Atividade inexistente')
                return self._json(200,{'ok':True})
            if route=='/api/session':
                sub=str(args['subject']).strip()
                if not c.execute('SELECT 1 FROM subjects WHERE name=?',(sub,)).fetchone():raise ValueError('Disciplina não cadastrada')
                kind=str(args.get('kind','Livre leve'))
                if kind not in DAY_CAPS:raise ValueError('Tipo de dia inválido')
                method=str(args.get('method','Teoria'))
                if method not in METHODS:raise ValueError('Modalidade inválida')
                minutes=int(args['minutes'])
                if minutes<1 or minutes>600:raise ValueError('Duração inválida')
                add_session(c,date.fromisoformat(args.get('day') or date.today().isoformat()),sub,
                    str(args.get('topic',''))[:200],method,minutes,kind,
                    notes='Painel Web v0.3',source='web',
                    auto_review=bool(args.get('revisions')))
                return self._json(200,{'ok':True})
            if route=='/api/questions':
                sub=str(args['subject']).strip()
                if not c.execute('SELECT 1 FROM subjects WHERE name=?',(sub,)).fetchone():raise ValueError('Disciplina não cadastrada')
                add_questions(c,date.fromisoformat(args.get('day') or date.today().isoformat()),sub,
                    str(args.get('topic',''))[:200],int(args['total']),int(args['correct']),
                    str(args.get('bank',''))[:80],str(args.get('platform',''))[:80],
                    str(args.get('error_type',''))[:80],str(args.get('notes',''))[:250])
                return self._json(200,{'ok':True})
            if route=='/api/questions/batch':
                sub=str(args['subject']).strip()
                if not c.execute('SELECT 1 FROM subjects WHERE name=?',(sub,)).fetchone():raise ValueError('Disciplina não cadastrada')
                bid=register_batch(c,
                    day=args.get('day') or date.today().isoformat(),
                    subject=sub,
                    topic=str(args.get('topic',''))[:200],
                    platform=str(args.get('platform',''))[:80],
                    banca=str(args.get('banca',''))[:80],
                    total=int(args['total']),
                    correct=int(args['correct']),
                    unanswered=int(args.get('unanswered',0)),
                    time_used_min=float(args.get('time_used_min',0)),
                    had_prior_review=bool(args.get('had_prior_review',False)),
                    gabarito_timing=str(args.get('gabarito_timing','Não consultado')),
                    mode=str(args.get('mode','batch')),
                    cause_counts=args.get('cause_counts') or {},
                    notes=str(args.get('notes',''))[:500],
                    request_id=str(args.get('request_id',''))[:100] or None,
                )
                if str(args.get('mode','batch')) == 'batch':
                    perf=finalize_batch(c,bid)
                    return self._json(201,{'ok':True,'batch_id':bid,'status':'finalized','performance':perf})
                return self._json(201,{'ok':True,'batch_id':bid,'status':'draft'})
            if route=='/api/questions/batch/finalize':
                perf=finalize_batch(c,int(args['batch_id']))
                return self._json(200,{'ok':True,'status':'finalized','performance':perf})
            if route=='/api/questions/item':
                bid=int(args['batch_id'])
                iid=register_question_item(c,
                    batch_id=bid,
                    question_ref=str(args.get('question_ref',''))[:100],
                    subject=str(args.get('subject',''))[:200],
                    topic=str(args.get('topic',''))[:200],
                    subtopic=str(args.get('subtopic',''))[:200],
                    result=str(args['result']),
                    primary_cause=str(args.get('primary_cause','Não especificado')),
                    secondary_causes=list(args.get('secondary_causes') or []),
                    observation=str(args.get('observation',''))[:500],
                    difficulty=str(args.get('difficulty',''))[:40],
                    resolution_time_s=int(args.get('resolution_time_s',0)),
                    consulted_gabarito=bool(args.get('consulted_gabarito',False)),
                    needs_reinforcement=bool(args.get('needs_reinforcement',False)),
                    correction_status=str(args.get('correction_status','Aberto')),
                )
                return self._json(201,{'ok':True,'item_id':iid})
            if route=='/api/questions/item/correction':
                update_item_correction(c,int(args['id']),str(args['correction_status']),
                    args.get('observation'))
                return self._json(200,{'ok':True})
            if route=='/api/review/complete':
                id_=int(args['id'])
                cur=c.execute("UPDATE reviews SET status='Concluída',finished_on=? WHERE id=? AND status='Pendente'",(date.today().isoformat(),id_));c.commit()
                if not cur.rowcount:raise ValueError('Revisão pendente não encontrada')
                return self._json(200,{'ok':True})
            if route=='/api/setting':
                new=int(args['weekly_target_minutes'])
                if not 60<=new<=4800:raise ValueError('A meta deve estar entre 1 e 80 horas')
                c.execute("UPDATE settings SET value=? WHERE key='weekly_target_min'",(str(new),));c.commit()
                return self._json(200,{'ok':True})
            return self._json(404,{'error':'Ação não encontrada'})
        except (ValueError,KeyError,TypeError) as exc:
            return self._json(400,{'error':str(exc)})
        except Exception:
            return self._json(500,{'error':'Erro interno; confira os dados ou o terminal local.'})
        finally:c.close()


def serve(host='127.0.0.1',port=8771):
    db=connect();db.close()
    srv=ThreadingHTTPServer((host,port),AppHandler)
    url=f'http://{host}:{port}'
    print(f'CONTROLE MESTRE — Painel premium local: {url}')
    threading.Timer(0.8,lambda: webbrowser.open(url)).start()
    try:srv.serve_forever()
    except KeyboardInterrupt:pass
    finally:srv.server_close()

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8771)
    opts=parser.parse_args()
    if not 1024<=opts.port<=65535:parser.error('Porta deve estar entre 1024 e 65535')
    serve(port=opts.port)