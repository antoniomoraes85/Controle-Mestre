"""CONTROLE MESTRE | Motor local de estudos. Python stdlib + SQLite.
Regras auditáveis; sem decisões opacas de IA nem métricas sintéticas.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
import tempfile
import os
import re
import sqlite3
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _default_db_path() -> Path:
    """Uma instalação não pode trocar silenciosamente o histórico por pasta nova.

    Ordem: caminho explícito > banco persistente Windows já existente >
    banco legado local já existente > destino persistente Windows >
    destino legado (Linux/macOS). Nunca move nem apaga arquivos.
    """
    env_db = os.environ.get('CONTROLE_MESTRE_DB')
    if env_db:
        return Path(env_db).expanduser()
    legacy = ROOT / 'dados' / 'controle_mestre.db'
    local_appdata = os.environ.get('LOCALAPPDATA')
    if local_appdata:
        persistent = Path(local_appdata) / 'ControleMestre' / 'dados' / 'controle_mestre.db'
        if persistent.is_file():
            return persistent
        if legacy.is_file():
            return legacy
        return persistent
    return legacy


DB_PATH = _default_db_path()
DEFAULT_SUBJECTS = [
 ('Legislação Tributária RS I',10,'Fiscal'), ('Legislação Tributária RS II',10,'Fiscal'),
 ('Direito Tributário',10,'Fiscal'), ('Reforma Tributária — EC 132 e LC 214',10,'Fiscal'),
 ('Reforma Tributária — LC 227',10,'Fiscal'), ('Contabilidade Geral',10,'Contábil'),
 ('Contabilidade de Custos',9,'Contábil'), ('Análise das Demonstrações Contábeis',9,'Contábil'),
 ('Contabilidade Avançada',9,'Contábil'), ('Auditoria',9,'Fiscal'),
 ('Direito Administrativo',7,'Jurídico'), ('Direito Civil',7,'Jurídico'),
 ('Direito Constitucional',7,'Jurídico'), ('Direito Empresarial',7,'Jurídico'),
 ('Direito Penal',6,'Jurídico'), ('Português',7,'Geral'),
 ('Estatística',4,'Exatas'), ('RLM',4,'Exatas'), ('Matemática Financeira',4,'Exatas'),
 ('Tecnologia da Informação',4,'TI'), ('Ciência de Dados',4,'TI'), ('Fluência em Dados',4,'TI'),
]
DAY_CAPS = {'Plantão':120, 'Pós-plantão':90, 'Livre forte':360, 'Livre leve':180,
            'Mestrado':90, 'Aula particular':150, 'Reset':0}
METHODS = ['Teoria','Questões','Lei seca','Revisão','Flashcards','Anki','Caderno de erros','Simulado','Aula particular']
REVIEW_DELAYS = (1,7,15,30)

def norm(s):
    return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode().lower()).strip()

def number(v, default=0):
    if v is None or v == '': return default
    if isinstance(v,(int,float)): return float(v)
    a=str(v).strip().replace(' ','').replace('%','')
    try:
        if ',' in a and '.' in a: a=a.replace('.','').replace(',','.')
        elif ',' in a: a=a.replace(',','.')
        return float(a)
    except (TypeError,ValueError): return default

def parse_day(v):
    if isinstance(v,date): return v.isoformat()
    if isinstance(v,(int,float)) or (str(v).replace('.','',1).isdigit() and len(str(v))<=6):
        try: return (datetime(1899,12,30)+timedelta(days=float(v))).date().isoformat()
        except (OverflowError,ValueError): pass
    s = str(v or '').strip()
    for f in ('%Y-%m-%d','%d/%m/%Y','%d-%m-%Y','%Y/%m/%d','%d/%m/%y'):
        try: return datetime.strptime(s[:10],f).date().isoformat()
        except ValueError: pass
    try: return datetime.fromisoformat(s).date().isoformat()
    except ValueError: return ''

def connect(path=None):
    p=Path(path or DB_PATH); p.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(str(p),timeout=20,check_same_thread=False)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA journal_mode=WAL')
    c.executescript('''
    CREATE TABLE IF NOT EXISTS subjects (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, weight REAL NOT NULL, area TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS topics (id INTEGER PRIMARY KEY, subject TEXT NOT NULL, topic TEXT NOT NULL, lesson TEXT DEFAULT '', progress REAL NOT NULL DEFAULT 0, incidence REAL NOT NULL DEFAULT 1, source TEXT DEFAULT '', UNIQUE(subject,topic,lesson));
    CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY, day TEXT NOT NULL, subject TEXT NOT NULL, topic TEXT NOT NULL DEFAULT '', method TEXT NOT NULL, minutes INTEGER NOT NULL CHECK(minutes>0), day_type TEXT NOT NULL, notes TEXT DEFAULT '', source TEXT NOT NULL, fingerprint TEXT UNIQUE);
    CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY, day TEXT NOT NULL, subject TEXT NOT NULL, topic TEXT NOT NULL DEFAULT '', bank TEXT DEFAULT '', platform TEXT DEFAULT '', total INTEGER NOT NULL CHECK(total>=0), correct INTEGER NOT NULL CHECK(correct>=0 AND correct<=total), error_type TEXT DEFAULT '', notes TEXT DEFAULT '', source TEXT NOT NULL, fingerprint TEXT UNIQUE);
    CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY, created_on TEXT NOT NULL, due_on TEXT NOT NULL, subject TEXT NOT NULL, topic TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'Pendente', finished_on TEXT, source TEXT NOT NULL, fingerprint TEXT UNIQUE);
    CREATE TABLE IF NOT EXISTS anki (id INTEGER PRIMARY KEY, day TEXT NOT NULL, deck TEXT NOT NULL, subject TEXT NOT NULL, cards INTEGER NOT NULL, errors INTEGER NOT NULL, minutes REAL NOT NULL DEFAULT 0, fingerprint TEXT UNIQUE);
    CREATE TABLE IF NOT EXISTS errors (id INTEGER PRIMARY KEY, day TEXT NOT NULL, subject TEXT NOT NULL, topic TEXT NOT NULL DEFAULT '', reason TEXT NOT NULL DEFAULT '', correction TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'Aberto');
    CREATE TABLE IF NOT EXISTS day_types (day TEXT PRIMARY KEY, kind TEXT NOT NULL, cap_minutes INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS cycles (id INTEGER PRIMARY KEY, subject TEXT NOT NULL, cycle_number INTEGER NOT NULL CHECK(cycle_number BETWEEN 1 AND 10), minutes REAL NOT NULL, source TEXT NOT NULL, UNIQUE(subject,cycle_number,source));
    CREATE TABLE IF NOT EXISTS plans (id INTEGER PRIMARY KEY, day TEXT NOT NULL, subject TEXT NOT NULL, topic TEXT NOT NULL DEFAULT '', method TEXT NOT NULL, target_minutes INTEGER NOT NULL, target_questions INTEGER NOT NULL DEFAULT 0, priority REAL NOT NULL, rationale TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Pendente', batch TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS import_log (id INTEGER PRIMARY KEY, stamp TEXT NOT NULL, filename TEXT NOT NULL, digest TEXT NOT NULL, inserted INTEGER NOT NULL, skipped INTEGER NOT NULL, notes TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS question_batches (id INTEGER PRIMARY KEY, day TEXT NOT NULL, subject TEXT NOT NULL, topic TEXT NOT NULL DEFAULT '', platform TEXT NOT NULL DEFAULT '', banca TEXT NOT NULL DEFAULT '', total INTEGER NOT NULL CHECK(total>=1), correct INTEGER NOT NULL CHECK(correct>=0 AND correct<=total), unanswered INTEGER NOT NULL DEFAULT 0 CHECK(unanswered>=0), time_used_min REAL NOT NULL DEFAULT 0, had_prior_review INTEGER NOT NULL DEFAULT 0, gabarito_timing TEXT NOT NULL DEFAULT 'Não consultado', mode TEXT NOT NULL DEFAULT 'batch' CHECK(mode IN ('batch','individual')), cause_counts TEXT NOT NULL DEFAULT '{}', notes TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT 'web', created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS question_items (id INTEGER PRIMARY KEY, batch_id INTEGER NOT NULL REFERENCES question_batches(id), question_ref TEXT NOT NULL DEFAULT '', subject TEXT NOT NULL, topic TEXT NOT NULL DEFAULT '', subtopic TEXT NOT NULL DEFAULT '', result TEXT NOT NULL CHECK(result IN ('Correta','Incorreta','Não resolvida')), primary_cause TEXT NOT NULL DEFAULT 'Não especificado', secondary_causes TEXT NOT NULL DEFAULT '[]', observation TEXT NOT NULL DEFAULT '', difficulty TEXT NOT NULL DEFAULT '', resolution_time_s INTEGER NOT NULL DEFAULT 0, consulted_gabarito INTEGER NOT NULL DEFAULT 0, needs_reinforcement INTEGER NOT NULL DEFAULT 0, correction_status TEXT NOT NULL DEFAULT 'Aberto', created_at TEXT NOT NULL);
    ''')
    # Evolução aditiva das baterias: registros históricos preexistentes permanecem
    # identificados como 'legacy', sem reconstruir ou duplicar o feed anterior.
    batch_cols={row[1] for row in c.execute('PRAGMA table_info(question_batches)').fetchall()}
    if 'status' not in batch_cols:
        c.execute("ALTER TABLE question_batches ADD COLUMN status TEXT NOT NULL DEFAULT 'legacy'")
    if 'legacy_question_id' not in batch_cols:
        c.execute('ALTER TABLE question_batches ADD COLUMN legacy_question_id INTEGER')
    if 'request_id' not in batch_cols:
        c.execute('ALTER TABLE question_batches ADD COLUMN request_id TEXT')
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_qb_request_id ON question_batches(request_id) WHERE request_id IS NOT NULL')
    c.execute('CREATE INDEX IF NOT EXISTS idx_qi_batch ON question_items(batch_id)')
    columns={r[1] for r in c.execute('PRAGMA table_info(sessions)').fetchall()}
    if 'cycle' not in columns:c.execute('ALTER TABLE sessions ADD COLUMN cycle INTEGER')
    for name,weight,area in DEFAULT_SUBJECTS:
        c.execute('INSERT OR IGNORE INTO subjects(name,weight,area) VALUES (?,?,?)',(name,weight,area))
    for k,v in [('weekly_target_min','1500'),('max_plantao_min','120'),('planning_mode','Equilibrado')]:
        c.execute('INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)',(k,v))
    c.commit();return c

def all_rows(c,sql,args=()): return [dict(x) for x in c.execute(sql,args).fetchall()]

def add_session(c,day,subject,topic,method,minutes,day_type='Livre leve',notes='',source='manual',fingerprint=None,auto_review=False,cycle=None):
    minutes=int(round(number(minutes)))
    if not parse_day(day) or minutes<=0: raise ValueError('Data válida e minutos positivos são obrigatórios.')
    if day_type=='Plantão':
        day_sum=c.execute('SELECT COALESCE(SUM(minutes),0) FROM sessions WHERE day=?',(parse_day(day),)).fetchone()[0]
        if day_sum+minutes>120: raise ValueError('Limite de 120 minutos para dia de plantão.')
    if cycle is not None and int(cycle) not in range(1,11):raise ValueError('Ciclo inválido: escolha de 1 a 10.')
    cur=c.execute('INSERT OR IGNORE INTO sessions(day,subject,topic,method,minutes,day_type,notes,source,fingerprint,cycle) VALUES (?,?,?,?,?,?,?,?,?,?)',
        (parse_day(day),subject.strip(),topic.strip(),method,minutes,day_type,notes,source,fingerprint,cycle))
    inserted=cur.rowcount
    if inserted and auto_review:
        for delay in REVIEW_DELAYS:
            due=(date.fromisoformat(parse_day(day))+timedelta(days=delay)).isoformat()
            c.execute('INSERT OR IGNORE INTO reviews(created_on,due_on,subject,topic,status,source,fingerprint) VALUES(?,?,?,?,?,?,?)',
                (parse_day(day),due,subject.strip(),topic.strip(),'Pendente','auto',f'session:{cur.lastrowid}:D{delay}'))
    c.commit();return inserted

def add_questions(c,day,subject,topic,total,correct,bank='',platform='',error_type='',notes='',source='manual',fingerprint=None):
    total=int(round(number(total)));correct=int(round(number(correct)))
    if not parse_day(day) or total<=0 or not (0<=correct<=total):raise ValueError('Dados de questões inválidos.')
    cur=c.execute('INSERT OR IGNORE INTO questions(day,subject,topic,bank,platform,total,correct,error_type,notes,source,fingerprint) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
        (parse_day(day),subject.strip(),topic.strip(),bank,platform,total,correct,error_type,notes,source,fingerprint))
    if cur.rowcount and correct<total and (error_type or notes):
        c.execute('INSERT INTO errors(day,subject,topic,reason,correction,status) VALUES(?,?,?,?,?,?)',
            (parse_day(day),subject.strip(),topic.strip(),(error_type+' — '+notes).strip(' — '),'','Aberto'))
    c.commit();return cur.rowcount

def save_topic(c,subject,topic,lesson='',progress=0,incidence=1,source='manual'):
    subject=subject.strip();topic=topic.strip();lesson=lesson.strip()
    if not topic or not subject: return 0
    c.execute('INSERT OR IGNORE INTO subjects(name,weight,area) VALUES(?,?,?)',(subject,4,'Outros'))
    progress=max(0,min(100,float(number(progress))));incidence=max(0.1,float(number(incidence,1)))
    c.execute('INSERT INTO topics(subject,topic,lesson,progress,incidence,source) VALUES(?,?,?,?,?,?) ON CONFLICT(subject,topic,lesson) DO UPDATE SET progress=MAX(topics.progress,excluded.progress),incidence=excluded.incidence',
              (subject,topic,lesson,progress,incidence,source));c.commit();return 1

def metric_data(c,today=None):
    today=today or date.today();today=date.fromisoformat(parse_day(today));start=(today-timedelta(days=today.weekday())).isoformat()
    month=today.replace(day=1).isoformat();last30=(today-timedelta(days=29)).isoformat()
    def sum_study(start_day):return c.execute('SELECT COALESCE(SUM(minutes),0) FROM sessions WHERE day BETWEEN ? AND ?',(start_day,today.isoformat())).fetchone()[0]
    def q_stats(start_day):
        r=c.execute('SELECT COALESCE(SUM(total),0),COALESCE(SUM(correct),0) FROM questions WHERE day BETWEEN ? AND ?',(start_day,today.isoformat())).fetchone()
        return {'total':int(r[0]),'correct':int(r[1]),'rate':float(r[1])/r[0] if r[0] else None}
    overdue=c.execute("SELECT COUNT(*) FROM reviews WHERE status='Pendente' AND due_on<?",(today.isoformat(),)).fetchone()[0]
    anki=c.execute('SELECT COALESCE(SUM(cards),0),COALESCE(SUM(errors),0),COALESCE(SUM(minutes),0) FROM anki WHERE day BETWEEN ? AND ?',(start,today.isoformat())).fetchone()
    target=int(c.execute("SELECT value FROM settings WHERE key='weekly_target_min'").fetchone()[0])
    return {'weekly_minutes':sum_study(start),'monthly_minutes':sum_study(month),'weekly_target':target,
      'adherence':sum_study(start)/target if target>0 else None,'week_questions':q_stats(start),
      'month_questions':q_stats(month),'last30_questions':q_stats(last30),'overdue_reviews':overdue,
      'anki_cards':int(anki[0]),'anki_errors':int(anki[1]),'anki_minutes':round(float(anki[2]),1)}

def subject_metrics(c,today=None):
    today=date.fromisoformat(parse_day(today or date.today()));q=all_rows(c,'SELECT subject,SUM(total) total,SUM(correct) correct FROM questions GROUP BY subject')
    s=all_rows(c,'SELECT subject,SUM(minutes) minutes,MAX(day) lastday FROM sessions GROUP BY subject')
    d=all_rows(c,'SELECT subject,COUNT(*) cnt,AVG(progress) progress FROM topics GROUP BY subject')
    rev=all_rows(c,"SELECT subject,COUNT(*) overdue FROM reviews WHERE status='Pendente' AND due_on<? GROUP BY subject",(today.isoformat(),))
    qm={x['subject']:x for x in q};sm={x['subject']:x for x in s};dm={x['subject']:x for x in d};rm={x['subject']:x for x in rev}
    out=[]
    for item in all_rows(c,'SELECT name,weight,area FROM subjects ORDER BY weight DESC,name'):
        name=item['name']; questions=qm.get(name,{});session=sm.get(name,{});topics=dm.get(name,{});reviews=rm.get(name,{})
        n=int(questions.get('total') or 0);good=int(questions.get('correct') or 0);rate=good/n if n else None
        last=session.get('lastday'); gap=(today-date.fromisoformat(last)).days if last else None
        progress=topics.get('progress')
        weakness=(1-rate) if n>=15 else (0.35 if n else 0.25)
        neglect=min(1,max(0,(gap or 0)-5)/14) if gap is not None else .35
        incomplete=1-(float(progress)/100 if progress is not None else 0)
        overdue=int(reviews.get('overdue') or 0)
        score=item['weight']*(1+.9*weakness+.65*neglect+.45*incomplete+.18*min(overdue,5))
        out.append({'disciplina':name,'bloco':item['area'],'peso':item['weight'],
                    'horas':round(int(session.get('minutes') or 0)/60,2),'questoes':n,
                    'acertos':good,'rendimento':rate,'progresso':round(float(progress),1) if progress is not None else None,
                    'dias_sem_estudar':gap,'revisoes_vencidas':overdue,'prioridade':round(score,2)})
    return sorted(out,key=lambda x:-x['prioridade'])

def save_day(c,day,kind,cap=None):
    if kind not in DAY_CAPS:raise ValueError('Tipo de dia inválido')
    max_cap=DAY_CAPS[kind]
    cap=max(0,min(max_cap,int(cap if cap is not None else max_cap)))
    c.execute('INSERT INTO day_types(day,kind,cap_minutes) VALUES(?,?,?) ON CONFLICT(day) DO UPDATE SET kind=excluded.kind,cap_minutes=excluded.cap_minutes',(parse_day(day),kind,cap));c.commit()

def get_days(c,week_start):
    ws=date.fromisoformat(parse_day(week_start));days=[]
    for i in range(7):
        day=(ws+timedelta(days=i)).isoformat();r=c.execute('SELECT kind,cap_minutes FROM day_types WHERE day=?',(day,)).fetchone()
        days.append({'day':day,'kind':r['kind'] if r else 'Livre leve','cap_minutes':r['cap_minutes'] if r else DAY_CAPS['Livre leve']})
    return days

def generate_plan(c,week_start):
    ws=date.fromisoformat(parse_day(week_start));ws=ws-timedelta(days=ws.weekday());start=ws.isoformat();end=(ws+timedelta(days=6)).isoformat()
    days=get_days(c,ws);target=int(c.execute("SELECT value FROM settings WHERE key='weekly_target_min'").fetchone()[0]);capacity=sum(d['cap_minutes'] for d in days)
    # Replanejamento preserva metas concluídas e desconta a carga já reservada por dia.
    completed=all_rows(c,"SELECT day,SUM(target_minutes) minutes FROM plans WHERE day BETWEEN ? AND ? AND status='Concluída' GROUP BY day",(start,end))
    finished={x['day']:int(x['minutes']) for x in completed}
    already=sum(finished.values())
    days=[{**d,'cap_minutes':max(0,d['cap_minutes']-finished.get(d['day'],0))} for d in days]
    capacity=sum(d['cap_minutes'] for d in days)
    budget=min(max(0,target-already),capacity)
    if capacity<=0 or budget<=0:
        c.execute('DELETE FROM plans WHERE day BETWEEN ? AND ? AND status="Pendente"',(start,end));c.commit()
        return {'activities':0,'planned_minutes':already,'capacity_minutes':capacity+already,'target_minutes':target}
    sub=subject_metrics(c,ws);slots=[]
    # A distribuição favorece os dias mais produtivos e respeita os limites configurados.
    slots=[{**d,'allow':int(budget*d['cap_minutes']//capacity)} for d in days]
    remaining=budget-sum(x['allow'] for x in slots)
    for x in sorted(slots,key=lambda x:-(budget*x['cap_minutes']/capacity-x['allow'])):
        if remaining<=0:break
        if x['allow']<x['cap_minutes']:x['allow']+=1;remaining-=1
    c.execute('DELETE FROM plans WHERE day BETWEEN ? AND ? AND status="Pendente"',(start,end))
    n=0;planned=0;use_count={x['disciplina']:0 for x in sub}
    topic_rows=all_rows(c,'SELECT subject,topic,lesson,progress,incidence FROM topics WHERE progress<100 ORDER BY progress ASC,incidence DESC,id')
    topics={}
    for row in topic_rows:topics.setdefault(row['subject'],[]).append(row)
    batch=f'plan:{start}:{datetime.now().isoformat(timespec="seconds")}'
    for d in sorted(slots,key=lambda x:x['day']):
        left=d['allow'];i=0
        while left>=25:
            viable=sorted(sub,key=lambda x:-(x['prioridade']/(1+.48*use_count[x['disciplina']])))
            item=viable[0];name=item['disciplina'];use_count[name]+=1
            mins=min(left,70 if d['kind']=='Livre forte' else 50)
            if left-mins < 25:mins=left
            if d['kind']=='Plantão':method=['Flashcards','Lei seca','Revisão'][i%3]
            elif d['kind'] in ('Pós-plantão','Mestrado'):method=['Revisão','Questões'][i%2]
            else:method=['Teoria','Questões','Revisão'][i%3]
            subtopics=topics.get(name,[]);t=subtopics[i%len(subtopics)]['topic'] if subtopics else 'Definir assunto'
            reason=f'Peso {item["peso"]}; desempenho '+(f'{item["rendimento"]:.0%}' if item['rendimento'] is not None else 'aferir')+f'; {item["revisoes_vencidas"]} revisões vencidas'
            questions=int(mins/2.5) if method=='Questões' else 0
            c.execute('INSERT INTO plans(day,subject,topic,method,target_minutes,target_questions,priority,rationale,status,batch) VALUES(?,?,?,?,?,?,?,?,?,?)',
                (d['day'],name,t,method,mins,questions,item['prioridade'],reason,'Pendente',batch))
            left-=mins;n+=1;planned+=mins;i+=1
    c.commit();return {'activities':n,'planned_minutes':planned+already,'capacity_minutes':capacity+already,'target_minutes':target}

def backup_sqlite(c):
    with tempfile.TemporaryDirectory() as td:
        target=Path(td)/'controle_mestre.sqlite'
        dest=sqlite3.connect(str(target))
        try:c.backup(dest)
        finally:dest.close()
        return target.read_bytes()

def export_json(c):
    tables=['subjects','topics','sessions','questions','reviews','anki','errors','cycles','day_types','plans','settings','import_log']
    return json.dumps({'product':'CONTROLE MESTRE','version':'0.1','exported_at':datetime.now().isoformat(timespec='seconds'),
        'tables':{t:all_rows(c,f'SELECT * FROM {t}') for t in tables}},ensure_ascii=False,indent=2).encode('utf-8')

# Leitura XLSX baseada apenas em bibliotecas padrão. NÃO altera a planilha fonte.
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def xlsx_sheets(data):
    f=zipfile.ZipFile(io.BytesIO(data))
    names=f.namelist();wb=ET.fromstring(f.read('xl/workbook.xml'))
    rels=ET.fromstring(f.read('xl/_rels/workbook.xml.rels'))
    relationships={a.attrib['Id']:a.attrib['Target'].lstrip('/') for a in rels}
    shared=[]
    if 'xl/sharedStrings.xml' in names:
        sh=ET.fromstring(f.read('xl/sharedStrings.xml'))
        shared=[''.join(t.text or '' for t in si.findall('.//m:t',NS)) for si in sh.findall('m:si',NS)]
    result={}
    for s in wb.findall('.//m:sheets/m:sheet',NS):
        name=s.attrib['name'];rel=s.attrib.get('{'+NS['r']+'}id','');loc=relationships.get(rel,'')
        if loc.startswith('xl/'):path=loc
        else:path='xl/'+loc
        if path not in names:continue
        root=ET.fromstring(f.read(path));rows=[]
        for rr in root.findall('.//m:sheetData/m:row',NS):
            mapping={}
            for cell in rr.findall('m:c',NS):
                ref=cell.attrib.get('r','A1');letters=re.match(r'[A-Z]+',ref)
                if not letters:continue
                idx=0
                for ch in letters.group():idx=idx*26+ord(ch)-64
                idx-=1
                raw=cell.find('m:v',NS);typ=cell.attrib.get('t')
                if typ=='inlineStr':val=''.join(t.text or '' for t in cell.findall('.//m:t',NS))
                elif raw is None:val=''
                elif typ=='s':
                    try:val=shared[int(raw.text)]
                    except (IndexError,ValueError,TypeError):val=''
                elif typ in ('str','e'):val=raw.text or ''
                else:val=number(raw.text,raw.text)
                mapping[idx]=val
            if mapping:
                width=max(mapping)+1;rows.append([mapping.get(i,'') for i in range(width)])
        result[name]=rows
    return result

def sheet_table(rows,heads):
    # Encontra a linha de cabeçalho por nomes, sem assumir primeira linha.
    heads={norm(h) for h in heads}
    for i,row in enumerate(rows[:15]):
        found={norm(x) for x in row};
        if len(found & heads)>=min(2,len(heads)):
            keys=[norm(x) for x in row]
            for j,r in enumerate(rows[i+1:]):
                if not any(str(v).strip() for v in r):continue
                yield i+j+2,{k:r[x] if x<len(r) else '' for x,k in enumerate(keys) if k}
            return

def field(d,*alts,default=''):
    for x in alts:
        n=norm(x)
        if n in d and d[n] not in ('',None): return d[n]
    return default

def import_excel(c,data,filename='planilha.xlsx'):
    digest=hashlib.sha256(data).hexdigest();found=xlsx_sheets(data)
    summary={'assuntos':0,'sessoes':0,'questoes':0,'ciclos':0,'ignorados':0,'abas':list(found),'observacoes':[]}
    # BASE_AULAS: somente conteúdos e status; questões históricas não são lançamentos reais.
    for name,rows in found.items():
        n=norm(name)
        if n=='base aulas':
            for rowid,r in sheet_table(rows,['Disciplina','Assunto/Tópico']):
                if norm(field(r,'Usar no Planejamento',default='Sim')) not in ('sim','yes','true','1'):continue
                subject=map_subject(str(field(r,'Disciplina','Matéria')))
                topic=str(field(r,'Assunto/Tópico','Assunto'))[:500].strip()
                lesson=str(field(r,'Aula'))[:80].strip()
                status=norm(field(r,'Status'))
                p=100 if status in ('concluido','concluida') else number(field(r,'Nível de domínio',default=0))
                if 0<p<=1:p*=100
                if save_topic(c,subject,topic,lesson,p,source=filename):summary['assuntos']+=1
        elif n in ('ciclo','ciclo de estudos'):
            for rowid,r in sheet_table(rows,['DISCIPLINAS','CICLO 1','CICLO 10']):
                subject=map_subject(str(field(r,'Disciplinas','Disciplina')))
                if not subject or norm(subject) in ('total','total horas'):continue
                for idx in range(1,11):
                    val=number(field(r,f'CICLO {idx}',f'CICLO{idx}'))
                    if val<=0:continue
                    # O VBA de cronômetro armazena durações como frações de dia do Excel.
                    mins=round(val*1440,1)
                    c.execute('INSERT INTO cycles(subject,cycle_number,minutes,source) VALUES(?,?,?,?) ON CONFLICT(subject,cycle_number,source) DO UPDATE SET minutes=excluded.minutes',
                        (subject,idx,mins,filename))
                    summary['ciclos']+=1
            c.commit()
        elif n=='registro tempos':
            # Log real do CronometroCiclos_V6_Painel_ABC.bas (aba Registro_Tempos).
            for rowid,r in sheet_table(rows,['Inicio','Disciplina','Tempo da sessao']):
                status=norm(field(r,'Situacao'))
                if status not in ('pausado','encerrado'):continue
                day=parse_day(field(r,'Inicio','Fim'))
                sub=map_subject(str(field(r,'Disciplina')))
                minutes=int(round(number(field(r,'Tempo da sessao'))*1440))
                if not day or not sub or minutes<1:
                    summary['ignorados']+=1;continue
                value=str(field(r,'Ciclo'));match=re.search(r'(?:ciclo\s*)?(\d{1,2})',norm(value))
                cycle=int(match.group(1)) if match and int(match.group(1)) in range(1,11) else None
                try:
                    if add_session(c,day,sub,'','Estudo cronometrado',minutes,'Livre leve',
                                   notes=f'VBA {status.upper()} / {field(r,"Celula")}',
                                   source=filename,fingerprint=f'{digest}:{name}:{rowid}:vba',cycle=cycle):
                        summary['sessoes']+=1
                    else:summary['ignorados']+=1
                except ValueError:summary['ignorados']+=1
        elif n in ('lancamento diario','sessoes','registro de estudo'):
            for rowid,r in sheet_table(rows,['Data','Matéria','Tempo líquido']):
                day=parse_day(field(r,'Data','Início','Inicio'))
                subject=map_subject(str(field(r,'Matéria','Disciplina')))
                minutes=number(field(r,'Tempo líquido','Minutos','Duração min',default=0))
                if minutes and minutes<1:minutes*=1440 # Excel duration fractions
                if not day and minutes<1:continue
                if not day or not subject or minutes<1:summary['ignorados']+=1;continue
                try:
                    if add_session(c,day,subject,str(field(r,'Assunto','Subassunto')),
                        str(field(r,'Tipo estudo','Atividade',default='Teoria')),int(round(minutes)),
                        str(field(r,'Tipo de dia',default='Livre leve')),source=filename,
                        fingerprint=f'{digest}:{name}:{rowid}:session'):
                        summary['sessoes']+=1
                    else:summary['ignorados']+=1
                except ValueError:summary['ignorados']+=1
        elif n in ('questoes','questoes feitas'):
            for rowid,r in sheet_table(rows,['Data','Matéria','Quantidade']):
                day=parse_day(field(r,'Data'));subject=map_subject(str(field(r,'Matéria','Disciplina')))
                total=int(number(field(r,'Quantidade','Questões feitas','Total','Questões')))
                correct=int(number(field(r,'Acertos','Corretas','Questões corretas')))
                if not day and total<=0:continue
                if not day or not subject or total<=0:summary['ignorados']+=1;continue
                try:
                    if add_questions(c,day,subject,str(field(r,'Assunto')),total,correct,
                         bank=str(field(r,'Banca')),platform=str(field(r,'Plataforma')),
                         error_type=str(field(r,'Tipo erro')),source=filename,
                         fingerprint=f'{digest}:{name}:{rowid}:question'):
                        summary['questoes']+=1
                    else:summary['ignorados']+=1
                except ValueError:summary['ignorados']+=1
    summary['observacoes'].append('Ciclos antigos são tratados como totais acumulados, sem somar novamente às horas líquidas de sessões com data.')
    summary['observacoes'].append('Campos antigos de rendimento/questões em BASE_AULAS não entram como questões efetivamente resolvidas.')
    c.execute('INSERT INTO import_log(stamp,filename,digest,inserted,skipped,notes) VALUES(?,?,?,?,?,?)',
              (datetime.now().isoformat(timespec='seconds'),filename,digest,sum(summary[k] for k in ['assuntos','sessoes','questoes','ciclos']),summary['ignorados'],'Excel'))
    c.commit();return summary

def map_subject(raw):
    x=norm(raw)
    aliases=[
      (('legislacao tributaria estadual modulo ii','legislacao tributaria estadual 2','legislacao tributaria rs ii'),'Legislação Tributária RS II'),
      (('legislacao tributaria estadual','legislacao tributaria rs 1','legislacao tributaria rs i'),'Legislação Tributária RS I'),
      (('reforma tributaria lc 227','lc 227'),'Reforma Tributária — LC 227'),
      (('reforma tributaria','ibs e cbs','lc 214'),'Reforma Tributária — EC 132 e LC 214'),
      (('analise das demonstracoes','analise de demonstracoes'),'Análise das Demonstrações Contábeis'),
      (('contabilidade de custos',),'Contabilidade de Custos'),
      (('contabilidade avancada',),'Contabilidade Avançada'),
      (('contabilidade geral','contabilidade'),'Contabilidade Geral'),
      (('direito tributario',),'Direito Tributário'), (('direito administrativo',),'Direito Administrativo'),
      (('direito constitucional',),'Direito Constitucional'), (('direito empresarial',),'Direito Empresarial'),
      (('direito penal',),'Direito Penal'), (('direito civil',),'Direito Civil'),
      (('estatistica',),'Estatística'),(('tecnologia da informacao',),'Tecnologia da Informação'),
      (('raciocinio logico','rlm'),'RLM'),(('portugues',),'Português'),
      (('fluencia em dados',),'Fluência em Dados'),(('auditoria',),'Auditoria'),
    ]
    for patterns,mapped in aliases:
        if any(a in x for a in patterns):return mapped
    return raw.strip()

def import_anki_csv(c,data,filename='anki.csv'):
    # CSV agregado por baralho/dia. Revlog bruto sem baralho NÃO oferece mapeamento seguro.
    txt=data.decode('utf-8-sig',errors='replace')
    try: dialect=csv.Sniffer().sniff(txt[:4096],delimiters=',;\t')
    except csv.Error:dialect=csv.excel
    reader=csv.DictReader(io.StringIO(txt),dialect=dialect)
    if not reader.fieldnames:raise ValueError('CSV sem cabeçalho.')
    headers={norm(k) for k in reader.fieldnames}
    if not headers.intersection({'deck','baralho','disciplina','subject','materia'}):
        raise ValueError('CSV não possui baralho/disciplina. Para importar revisões por matéria, exporte data, baralho, revisões, erros e tempo.')
    digest=hashlib.sha256(data).hexdigest();n=0;skipped=0;errors=0
    for idx,r in enumerate(reader,2):
        rr={norm(k):v for k,v in r.items() if k}
        rawdeck=str(field(rr,'deck','baralho','disciplina','subject','materia'))
        if not rawdeck:skipped+=1;continue
        subject=map_subject(rawdeck.split('::')[0].split(' > ')[0])
        day=parse_day(field(rr,'date','data','day'))
        cards=int(number(field(rr,'reviews','revisoes','cards','cartoes','total','count','n_reviews')))
        wrong=int(number(field(rr,'errors','erros','again','wrong','incorrect','lapsos')))
        mins=number(field(rr,'minutes','minutos','tempo_min','time_minutes'))
        if mins==0:
            mins=number(field(rr,'time_ms'))/60000 or number(field(rr,'seconds','time_seconds'))/60
        if not day or cards<=0 or wrong>cards or wrong<0:skipped+=1;continue
        f=f'{digest}:{idx}:anki'
        cursor=c.execute('INSERT OR IGNORE INTO anki(day,deck,subject,cards,errors,minutes,fingerprint) VALUES(?,?,?,?,?,?,?)',
            (day,rawdeck,subject,cards,wrong,mins,f))
        if cursor.rowcount:n+=1
        else:skipped+=1
    c.execute('INSERT INTO import_log(stamp,filename,digest,inserted,skipped,notes) VALUES(?,?,?,?,?,?)',
              (datetime.now().isoformat(timespec='seconds'),filename,digest,n,skipped,'Anki CSV'))
    c.commit();return {'importados':n,'ignorados':skipped,'avisos':['Os minutos do Anki são exibidos separadamente para evitar duplicidade com o cronômetro.']}