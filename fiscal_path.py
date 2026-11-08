"""Trilha fiscal inicial RS+SC: edital historico, materiais locais e metas auditaveis.

Aulas/assuntos abaixo são pontos de entrada CURADOS, nao edital verticalizado
integral, pesos oficiais nem estatisticas de incidencia. Sem IA ou scraping.
"""
from __future__ import annotations
from datetime import date, datetime, timedelta
from collections import defaultdict

from core import all_rows, connect, get_days, norm, parse_day
from sources import prepare as sources_prepare
from lesson_catalog import lessons as listed_lessons

TRACK_ID = 'base_rs_sc_2026'
# Fonte: editais AFRE/RS 2018 (Cebraspe) e AFRE/SC 2018 (FCC), em suas partes comuns.
# Nao atribuir a ordem proposta a nenhum edital; e curadoria pedagogica inicial.
SOURCES = {
    'rs': 'https://cdn.cebraspe.org.br/concursos/SEFAZ_RS_18_AUDITOR/arquivos/ED%201%202018%20SEFAZ_RS_AUDITOR_18%20-%20Abertura.pdf',
    'sc': 'https://concursossc.com.br/wp-content/uploads/2018/09/edital-sefaz-sc-2018.pdf',
}
# Identificadores de disciplina preservam os nomes canônicos do banco existente;
# rótulos de Reforma Tributária aparecem completos na interface.
SEED = [
 ('Contabilidade Geral', 1, ['Patrimônio e equação patrimonial', 'Contas e partidas dobradas', 'Lançamentos e fatos contábeis', 'Regime de competência e ajustes', 'Estoques e operações com mercadorias', 'Balanço patrimonial e DRE']),
 ('Contabilidade de Custos', 2, ['Conceitos e classificação dos custos', 'Custeio por absorção e custeio variável', 'Departamentalização e rateios', 'Custo dos produtos vendidos e estoques', 'Margem de contribuição e ponto de equilíbrio']),
 ('Análise das Demonstrações Contábeis', 3, ['Estrutura e comparabilidade das demonstrações', 'Análise vertical e horizontal', 'Índices de liquidez', 'Índices de endividamento e estrutura', 'Rentabilidade e análise integrada']),
 ('Direito Tributário', 4, ['Conceito e espécies de tributos', 'Competência tributária e limitações', 'Legislação tributária: vigência e interpretação', 'Obrigação tributária e fato gerador', 'Responsabilidade tributária', 'Crédito tributário e lançamento']),
 ('Reforma Tributária — EC 132 e LC 214', 5, ['EC 132/2023: arquitetura da reforma', 'IBS e CBS: materialidade e sujeitos', 'Fato gerador, base de cálculo e alíquotas', 'Créditos e não cumulatividade', 'Imposto Seletivo e regimes diferenciados', 'Regras de transição e vigência']),
 ('Reforma Tributária — LC 227', 6, ['Comitê Gestor do IBS: competências e organização', 'Distribuição da arrecadação do IBS', 'Processo administrativo tributário do IBS', 'ITCMD e normas gerais', 'Alterações da LC 214/2025 e do CTN']),
 ('Direito Administrativo', 7, ['Princípios e organização administrativa', 'Atos administrativos', 'Poderes administrativos', 'Agentes públicos', 'Responsabilidade civil do Estado', 'Controle e improbidade administrativa']),
 ('Direito Civil', 8, ['LINDB e aplicação das normas', 'Pessoas naturais e jurídicas', 'Bens e fatos jurídicos', 'Prescrição e decadência', 'Obrigações e contratos', 'Responsabilidade civil']),
 ('Direito Constitucional', 9, ['Princípios e direitos fundamentais', 'Organização do Estado e competências', 'Administração pública constitucional', 'Poder Legislativo e processo legislativo', 'Sistema tributário na Constituição']),
]
SUBJECT_DISPLAY = {
  'Reforma Tributária — EC 132 e LC 214': 'Reforma Tributária (EC nº 132/2023 e LC nº 214/2025)',
  'Reforma Tributária — LC 227': 'Reforma Tributária (LC nº 227/2026)',
}

STEPS = [('Teoria', 70, 0, 0), ('Questões de fixação', 45, 1, 12),
         ('Passo Estratégico', 40, 2, 0), ('Revisão por questões', 35, 2, 12),
         ('Caderno de erros', 30, 1, 0)]
# (modalidade, min planejados, dias min depois da etapa anterior, questões-alvo)
# Os tempos são hipóteses de planejamento, não doses pedagogicas comprovadas.


def prepare(c):
    c.executescript('''
    CREATE TABLE IF NOT EXISTS fiscal_tracks (
      id TEXT PRIMARY KEY, name TEXT NOT NULL, activated_at TEXT NOT NULL,
      source_note TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS fiscal_topics (
      id INTEGER PRIMARY KEY, track_id TEXT NOT NULL, subject TEXT NOT NULL,
      title TEXT NOT NULL, subject_order INTEGER NOT NULL, topic_order INTEGER NOT NULL,
      origin TEXT NOT NULL DEFAULT 'Referência histórica RS/SC 2018 — curadoria inicial',
      UNIQUE(track_id, subject, title));
    CREATE TABLE IF NOT EXISTS fiscal_tasks (
      id INTEGER PRIMARY KEY, track_id TEXT NOT NULL, topic_id INTEGER NOT NULL,
      week_start TEXT NOT NULL, day TEXT NOT NULL, step INTEGER NOT NULL,
      method TEXT NOT NULL, minutes INTEGER NOT NULL, target_questions INTEGER NOT NULL DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'Pendente', actual_minutes INTEGER NOT NULL DEFAULT 0,
      completed_at TEXT, question_total INTEGER, question_correct INTEGER,
      UNIQUE(track_id, week_start, topic_id, step),
      FOREIGN KEY(topic_id) REFERENCES fiscal_topics(id));
    CREATE INDEX IF NOT EXISTS idx_fiscal_tasks_day ON fiscal_tasks(track_id,day,status);
    ''')



def _ensure_topics(c):
    """Migração aditiva da trilha; nunca apaga tópicos ou tarefas anteriores."""
    inserted=0
    for subject, order, titles in SEED:
        for idx,title in enumerate(titles,1):
            already=c.execute('SELECT 1 FROM fiscal_topics WHERE track_id=? AND subject=? AND title=?',(TRACK_ID,subject,title)).fetchone()
            if already:continue
            cur=c.execute("""INSERT OR IGNORE INTO fiscal_topics
                (track_id,subject,title,subject_order,topic_order) VALUES(?,?,?,?,?)""",
                (TRACK_ID,subject,title,order,idx))
            inserted+=cur.rowcount
    # Aulas realmente fornecidas pelo titular substituem a curadoria genérica
    # nas próximas prévias; tópicos antigos continuam para preservar histórico.
    lessons=listed_lessons()
    by_subject={name:order for name,order,_ in SEED}
    for idx,row in enumerate(lessons,1):
        title=row['aula']+' — '+row['assunto']
        if c.execute('SELECT 1 FROM fiscal_topics WHERE track_id=? AND subject=? AND title=?',
                     (TRACK_ID,row['disciplina'],title)).fetchone():continue
        cur=c.execute("""INSERT OR IGNORE INTO fiscal_topics
            (track_id,subject,title,subject_order,topic_order,origin)
            VALUES(?,?,?,?,?,'Catálogo de aulas informado pelo titular')""",
            (TRACK_ID,row['disciplina'],title,by_subject[row['disciplina']],idx))
        inserted+=cur.rowcount
    if inserted:c.commit()
    return inserted

def activate(c):
    prepare(c)
    if c.execute('SELECT 1 FROM fiscal_tracks WHERE id=?',(TRACK_ID,)).fetchone():
        return {'active': True, 'created': _ensure_topics(c)}
    c.execute('''INSERT INTO fiscal_tracks VALUES(?,?,?,?)''',
              (TRACK_ID, 'Base Fiscal comum RS + SC', datetime.now().isoformat(timespec='seconds'),
               'Editais 2018; sequência pedagógica inicial, sem pesos estatísticos'))
    c.commit()
    count=_ensure_topics(c)
    return {'active': True, 'created': count}



def _week(week_start=None):
    w=date.fromisoformat(parse_day(week_start or date.today()))
    return w-timedelta(days=w.weekday())


def _recorded(c, start, end):
    return all_rows(c, '''SELECT t.id,t.track_id,t.topic_id,t.week_start,t.day,t.step,t.method,t.minutes,
      t.target_questions,t.status,t.actual_minutes,t.question_total,t.question_correct,
      x.subject,x.title AS topic,x.subject_order,x.topic_order
      FROM fiscal_tasks t JOIN fiscal_topics x ON x.id=t.topic_id
      WHERE t.track_id=? AND t.day BETWEEN ? AND ? ORDER BY t.day,x.subject_order,x.topic_order,t.step,t.id''',
      (TRACK_ID,start,end))


def _subject_materials(c, subject, topic, kind):
    """Vincular PDFs à AULA correta, não ao primeiro PDF solto da disciplina."""
    if kind=='Passo Estratégico':types=('Passo Estratégico',)
    elif kind in ('Questões de fixação','Revisão por questões','Caderno de erros'):
        types=('Questões',)
    else:types=('Teoria','Simplificado')
    requested=topic.split(' — ',1)[0] if topic.startswith('Aula ') else ''
    candidates=all_rows(c,'''SELECT id,file_name,lesson,relative_path,topic,subject,material_type
      FROM study_materials WHERE status='Disponível' AND subject=?
      ORDER BY id LIMIT 500''',(subject,))
    eligible=[]
    for item in candidates:
        if item['material_type'] not in types:continue
        if requested:
            if norm(item['lesson'])!=norm(requested):continue
        elif not item['topic'] or norm(item['topic'])!=norm(topic):
            continue
        eligible.append(item)
    eligible.sort(key=lambda x:(types.index(x['material_type']),x['id']))
    return eligible[:3]


def status(c, today=None, week_start=None):
    prepare(c)
    active=bool(c.execute('SELECT 1 FROM fiscal_tracks WHERE id=?',(TRACK_ID,)).fetchone())
    ws=_week(week_start);end=ws+timedelta(days=6)
    cur=date.fromisoformat(parse_day(today or date.today()))
    days=get_days(c,ws)
    if not active:
        return {'active':False,'week_start':ws.isoformat(),'week_end':end.isoformat(),
                'days':days,'subjects':[r[0] for r in SEED], 'subject_display':SUBJECT_DISPLAY, 'source_refs':SOURCES,
                'tasks':[], 'pending_older':0,'capacity_minutes':sum(d['cap_minutes'] for d in days)}
    _ensure_topics(c)
    sources_prepare(c)
    rows=_recorded(c,ws.isoformat(),end.isoformat())
    for row in rows:
        row['materials']=_subject_materials(c,row['subject'],row['topic'],row['method'])
    topics=all_rows(c,'''SELECT x.id,x.subject,x.title AS topic,x.subject_order,x.topic_order,
         COALESCE(MAX(CASE WHEN t.status='Concluída' THEN t.step END),-1) AS max_completed_step,
         SUM(CASE WHEN t.status='Pendente' THEN 1 ELSE 0 END) AS pending
         FROM fiscal_topics x LEFT JOIN fiscal_tasks t ON t.topic_id=x.id
         WHERE x.track_id=? GROUP BY x.id ORDER BY x.subject_order,x.topic_order''',(TRACK_ID,))
    old=c.execute('''SELECT COUNT(*) FROM fiscal_tasks
         WHERE track_id=? AND day<? AND status='Pendente' ''',(TRACK_ID,ws.isoformat())).fetchone()[0]
    target=int(c.execute("SELECT value FROM settings WHERE key='weekly_target_min'").fetchone()[0])
    return {'active':True,'week_start':ws.isoformat(),'week_end':end.isoformat(),
      'today':cur.isoformat(),'days':days,'tasks':rows,'topics':topics,
      'pending_older':old,'source_refs':SOURCES,'capacity_minutes':sum(d['cap_minutes'] for d in days),
      'target_minutes':target,'planned_minutes':sum(x['minutes'] for x in rows),
      'completed_minutes':sum(x['actual_minutes'] for x in rows if x['status']=='Concluída'),
      'subjects':[r[0] for r in SEED],'subject_display':SUBJECT_DISPLAY}


def preview_week(c,week_start=None,today=None):
    """Proposta somente leitura. Preserva agendas e dados existentes."""
    prepare(c)
    if not c.execute('SELECT 1 FROM fiscal_tracks WHERE id=?',(TRACK_ID,)).fetchone():
        raise ValueError('Ative primeiro a Trilha Fiscal RS+SC.')
    _ensure_topics(c)
    if not listed_lessons():
        raise ValueError('Catálogo local de aulas ausente. Copie dados/catalogo/aulas_primeiro_ciclo.csv para usar o planejamento por aulas.')
    ws=_week(week_start);end=ws+timedelta(days=6)
    cur=date.fromisoformat(parse_day(today or date.today()))
    if ws+timedelta(days=6)<cur:
        raise ValueError('Não é possível criar tarefas retroativas em semana encerrada.')
    exists=c.execute('SELECT COUNT(*) FROM fiscal_tasks WHERE track_id=? AND week_start=?',
                     (TRACK_ID,ws.isoformat())).fetchone()[0]
    if exists:raise ValueError('Esta semana já possui uma trilha; pendências e registros serão preservados.')
    days=get_days(c,ws)
    if not days:raise ValueError('Nenhuma disponibilidade cadastrada')
    # Respeitar horas já planejadas no antigo motor para evitar sobre-reserva inadvertida.
    allocations={}
    for d in days:
        if d['day']<cur.isoformat():continue
        used=c.execute('SELECT COALESCE(SUM(target_minutes),0) FROM plans WHERE day=?',(d['day'],)).fetchone()[0]
        allocations[d['day']]=max(0,int(d['cap_minutes'])-int(used or 0))
    target=int(c.execute("SELECT value FROM settings WHERE key='weekly_target_min'").fetchone()[0])
    # Deduzir horas efetivas já registradas nesta semana e proteger o orçamento da semana.
    actual=c.execute('''SELECT COALESCE(SUM(minutes),0) FROM sessions WHERE day BETWEEN ? AND ?''',
                     (ws.isoformat(),end.isoformat())).fetchone()[0]
    available=min(max(0,target-int(actual)),sum(allocations.values()))
    candidates=[]
    topics=all_rows(c,'''SELECT id,subject,title,subject_order,topic_order
         FROM fiscal_topics WHERE track_id=? AND origin='Catálogo de aulas informado pelo titular'
         ORDER BY subject_order,topic_order''',(TRACK_ID,))
    by_subject=defaultdict(list)
    enabled={row[0] for row in SEED}
    for x in topics:
        if x['subject'] not in enabled:continue
        existing=c.execute('''SELECT step,status FROM fiscal_tasks WHERE topic_id=?
                ORDER BY week_start,step''',(x['id'],)).fetchall()
        if any(v['status']=='Pendente' for v in existing):continue # antigo pendente nao é duplicado
        seen={v['step'] for v in existing if v['status']=='Concluída'}
        next_step=next((i for i in range(4) if i not in seen),None)
        if next_step is None and 4 not in seen:
            open_errors=c.execute('''SELECT COUNT(*) FROM errors WHERE subject=? AND topic=? AND status='Aberto' ''',
                                  (x['subject'],x['title'])).fetchone()[0]
            if open_errors:next_step=4
        if next_step is not None:by_subject[x['subject']].append((x,next_step))
    for subject,_,__ in SEED:
        # Prioriza o tópico iniciado e depois até dois tópicos por disciplina.
        ts=sorted(by_subject[subject],key=lambda t:(t[1]==0,t[0]['topic_order']))[:2]
        for topic,step in ts:
            candidates.append({'topic':topic,'step':step,'ready':max(cur,ws),
                               'subject':subject,'planned':0})
    planned=[]; spent=0
    for day in sorted(allocations):
        left=allocations[day]
        if spent>=available:break
        current=date.fromisoformat(day)
        while left>=30 and spent<available:
            eligible=[x for x in candidates if x['step']<len(STEPS) and x['ready']<=current
                      and STEPS[x['step']][1]<=min(left,available-spent)]
            if not eligible:break
            # Disciplinas equilibradas dentro do orçamento, sem pressupor pesos de banca.
            usage=defaultdict(int)
            for entry in planned:usage[entry['subject']]+=entry['minutes']
            eligible.sort(key=lambda x:(usage[x['subject']],x['topic']['subject_order'],
                                        x['topic']['topic_order'],x['step']))
            entry=eligible[0];s=entry['step'];method,minutes,delay,qty=STEPS[s]
            planned.append({'day':day,'topic_id':entry['topic']['id'],'subject':entry['subject'],
                'topic':entry['topic']['title'],'step':s,'method':method,
                'minutes':minutes,'target_questions':qty})
            left-=minutes;spent+=minutes
            entry['step']+=1
            if entry['step']<len(STEPS):
                entry['ready']=current+timedelta(days=STEPS[entry['step']][2])
        allocations[day]=left
    return {'week_start':ws.isoformat(),'week_end':end.isoformat(),
            'target_minutes':target,'other_studied_minutes':int(actual),
            'available_for_trail_minutes':available,'planned_minutes':spent,
            'unallocated_minutes':max(0,available-spent),
            'tasks':planned,'task_count':len(planned),
            'note':'Metas baseadas nas aulas do seu catálogo privado, com tempos estimados; estudo dos erros só após erros registrados. Não significa aula concluída.'}


def apply_week(c,week_start=None,confirm=False,today=None):
    if confirm is not True:raise ValueError('Confirmação explícita obrigatória.')
    p=preview_week(c,week_start,today)
    try:
        c.execute('BEGIN IMMEDIATE')
        for x in p['tasks']:
            c.execute('''INSERT INTO fiscal_tasks(track_id,topic_id,week_start,day,step,method,minutes,target_questions)
                VALUES(?,?,?,?,?,?,?,?)''',(TRACK_ID,x['topic_id'],p['week_start'],x['day'],x['step'],x['method'],x['minutes'],x['target_questions']))
        c.commit()
    except Exception:
        c.rollback();raise
    return {'inserted':len(p['tasks']), 'week_start':p['week_start'], 'planned_minutes':p['planned_minutes']}


def complete_task(c,task_id,minutes=0,total=None,correct=None,error_type='',notes='',done_day=None):
    """Registra tarefa e, se informado, sessao e resultado proprio, uma unica vez."""
    if isinstance(task_id,bool) or not isinstance(task_id,int):raise ValueError('ID de tarefa inválido')
    task=c.execute('''SELECT t.*,x.subject,x.title AS topic FROM fiscal_tasks t
          JOIN fiscal_topics x ON x.id=t.topic_id WHERE t.id=? AND t.track_id=?''',(task_id,TRACK_ID)).fetchone()
    if not task or task['status']!='Pendente':raise ValueError('Tarefa inexistente ou já concluída')
    minutes=int(minutes)
    if not 0<=minutes<=600:raise ValueError('Minutos devem estar entre 0 e 600')
    if (total is None)!=(correct is None):raise ValueError('Informe o total e os acertos juntos')
    if total is not None:
        total=int(total);correct=int(correct)
        if task['method'] not in ('Questões de fixação','Revisão por questões'):
            raise ValueError('Resultado de questões só é aceito em tarefa de questões')
        if not 1<=total<=500 or not 0<=correct<=total:
            raise ValueError('Totais de questões inválidos')
    subj,topic=task['subject'],task['topic']
    actual_day=parse_day(done_day or date.today())
    if not actual_day or actual_day>date.today().isoformat():raise ValueError('Data real inválida ou futura')
    if task['day']>actual_day:raise ValueError('A atividade está prevista para data futura')
    kind=c.execute('SELECT kind FROM day_types WHERE day=?',(actual_day,)).fetchone()
    day_type=kind[0] if kind else 'Livre leve'
    if minutes and day_type=='Plantão':
        old=c.execute('SELECT COALESCE(SUM(minutes),0) FROM sessions WHERE day=?',(actual_day,)).fetchone()[0]
        if old+minutes>120:raise ValueError('Limite de 120 minutos em dia de plantão.')
    method={'Teoria':'Teoria','Questões de fixação':'Questões','Passo Estratégico':'Revisão',
            'Revisão por questões':'Questões','Caderno de erros':'Caderno de erros'}[task['method']]
    try:
        c.execute('BEGIN IMMEDIATE')
        if minutes:
            c.execute('''INSERT INTO sessions(day,subject,topic,method,minutes,day_type,notes,source,fingerprint)
             VALUES(?,?,?,?,?,?,?,?,?)''',(actual_day,subj,topic,method,minutes,day_type,
                 ('Trilha fiscal: '+task['method'])[:250],'fiscal-trail',f'fiscal-session:{task_id}'))
        if total is not None:
            c.execute('''INSERT INTO questions(day,subject,topic,bank,platform,total,correct,error_type,notes,source,fingerprint)
              VALUES(?,?,?,?,?,?,?,?,?,?,?)''',(actual_day,subj,topic,'','Qconcursos/manual',total,correct,
               str(error_type)[:80],str(notes)[:250],'fiscal-trail',f'fiscal-questions:{task_id}'))
            if correct<total:
                c.execute('''INSERT INTO errors(day,subject,topic,reason,correction,status)
                  VALUES(?,?,?,?,?,?)''',(actual_day,subj,topic,
                  (str(error_type or 'Não identificado')+' — '+str(notes)).strip(' — ')[:230],'','Aberto'))
        c.execute('''UPDATE fiscal_tasks SET status='Concluída',actual_minutes=?,
           completed_at=?,question_total=?,question_correct=? WHERE id=?''',
           (minutes,datetime.now().isoformat(timespec='seconds'),total,correct,task_id))
        c.commit()
    except Exception:
        c.rollback();raise
    return {'ok':True,'task_id':task_id,'recorded_minutes':minutes,'question_total':total}