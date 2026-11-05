"""CONTROLE MESTRE v0.3 — interface web local sobre o banco SQLite existente.
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

from core import (ROOT, connect, all_rows, metric_data, subject_metrics,
                  get_days, save_day, generate_plan, add_session, add_questions,
                  DAY_CAPS, METHODS)

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
        metrics=metrics, ranking=ranked, plans=plans, done=done,
        weeks=weeks, sessions=sessions, question_history=qq, reviews=revisions,
        anki=anki, topic_progress=progress,
        cycles=all_rows(c, 'SELECT subject,cycle,ROUND(SUM(minutes),0) AS minutes FROM sessions WHERE cycle IS NOT NULL GROUP BY subject,cycle ORDER BY cycle,subject'),
        subjects=all_rows(c, 'SELECT name,weight,area FROM subjects ORDER BY weight DESC,name'),
        types=DAY_CAPS, methods=METHODS,
        days=get_days(c,start),
        focus_on=ranked[0]['disciplina'] if ranked else None,
    )


class AppHandler(BaseHTTPRequestHandler):
    server_version='ControleMestreLocal/0.3'
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
        if route=='/api/health':return self._json(200,{'ok':True,'app':'CONTROLE MESTRE','version':'0.3'})
        if route=='/':route='/index.html'
        static={'/index.html':'text/html; charset=utf-8','/style.css':'text/css; charset=utf-8',
                '/app.js':'text/javascript; charset=utf-8'}
        if route not in static:return self._json(404,{'error':'Arquivo não encontrado'})
        path=WEB / route[1:]
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
        try: args=json.loads(self.rfile.read(length).decode('utf-8'))
        except (ValueError,UnicodeDecodeError):return self._json(400,{'error':'JSON inválido'})
        if not isinstance(args,dict):return self._json(400,{'error':'Objeto JSON obrigatório'})
        route=urlsplit(self.path).path
        c=connect()
        try:
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


def serve(host='127.0.0.1',port=8765):
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
    parser.add_argument('--port',type=int,default=8765)
    opts=parser.parse_args()
    if not 1024<=opts.port<=65535:parser.error('Porta deve estar entre 1024 e 65535')
    serve(port=opts.port)