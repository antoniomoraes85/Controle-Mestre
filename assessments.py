"""Avaliações independentes: simulados e redações da plataforma histórica CM 1.0.

Não soma resultados de simulados à tabela 'questions': são populações distintas.
Migração aditiva, idempotente, preserva banco de versões anteriores.
"""
from __future__ import annotations
from datetime import date
import math
from core import all_rows, parse_day


def ensure_schema(c):
    c.executescript('''
    CREATE TABLE IF NOT EXISTS mock_exams (
      id INTEGER PRIMARY KEY, day TEXT NOT NULL, title TEXT NOT NULL,
      bank TEXT NOT NULL DEFAULT '', total INTEGER NOT NULL CHECK(total>0),
      correct INTEGER NOT NULL CHECK(correct>=0), wrong INTEGER NOT NULL CHECK(wrong>=0),
      blank INTEGER NOT NULL CHECK(blank>=0), guesses INTEGER NOT NULL CHECK(guesses>=0),
      grade REAL, maximum_grade REAL, notes TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      CHECK (correct+wrong+blank=total), CHECK (guesses<=correct+wrong),
      CHECK (grade IS NULL OR maximum_grade IS NOT NULL),
      CHECK (maximum_grade IS NULL OR maximum_grade>0),
      CHECK (grade IS NULL OR (grade>=0 AND grade<=maximum_grade))
    );
    CREATE TABLE IF NOT EXISTS essays (
      id INTEGER PRIMARY KEY, day TEXT NOT NULL, topic TEXT NOT NULL,
      bank TEXT NOT NULL DEFAULT '', grade REAL NOT NULL CHECK(grade>=0),
      maximum_grade REAL NOT NULL CHECK(maximum_grade>0), notes TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      CHECK(grade<=maximum_grade)
    );
    CREATE INDEX IF NOT EXISTS idx_mock_exams_day ON mock_exams(day);
    CREATE INDEX IF NOT EXISTS idx_essays_day ON essays(day);
    ''')


def _valid_day(day):
    value=parse_day(day)
    if not value: raise ValueError('Data inválida')
    date.fromisoformat(value)
    return value


def _text(value,label,limit):
    s=str(value or '').strip()
    if not s: raise ValueError(f'{label} obrigatório')
    if len(s)>limit: raise ValueError(f'{label} acima do limite de {limit} caracteres')
    return s


def _nonnegative_int(obj,key):
    value=obj.get(key,0)
    if isinstance(value,bool): raise ValueError(f'{key} inválido')
    try:
        n=int(value)
        if float(value)!=n or n<0:raise ValueError()
        return n
    except (TypeError,ValueError,OverflowError):raise ValueError(f'{key} deve ser inteiro não negativo')


def _grade(value,label):
    if value is None or value=='':return None
    try:
        n=float(value)
        if not math.isfinite(n) or n<0:raise ValueError()
    except (TypeError,ValueError):raise ValueError(f'{label} deve ser número não negativo')
    return n


def insert_mock(c,obj):
    ensure_schema(c)
    total=_nonnegative_int(obj,'total');correct=_nonnegative_int(obj,'correct')
    wrong=_nonnegative_int(obj,'wrong');blank=_nonnegative_int(obj,'blank')
    guesses=_nonnegative_int(obj,'guesses')
    if not 1<=total<=1000:raise ValueError('Total entre 1 e 1000')
    if correct+wrong+blank!=total:raise ValueError('Acertos + erros + branco deve ser igual ao total')
    if guesses>correct+wrong:raise ValueError('Chutes não podem exceder questões respondidas')
    grade=_grade(obj.get('grade'),'Nota');maximum=_grade(obj.get('maximum_grade'),'Nota máxima')
    if (grade is None)!=(maximum is None):raise ValueError('Informe nota e nota máxima juntas, ou deixe ambas em branco')
    if maximum is not None and not (maximum>0 and grade<=maximum):raise ValueError('Nota deve estar entre zero e nota máxima')
    row=( _valid_day(obj.get('day')), _text(obj.get('title'),'Título',160),str(obj.get('bank',''))[:80],
           total,correct,wrong,blank,guesses,grade,maximum,str(obj.get('notes',''))[:1200])
    cur=c.execute('''INSERT INTO mock_exams(day,title,bank,total,correct,wrong,blank,guesses,grade,maximum_grade,notes)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)''',row)
    c.commit();return cur.lastrowid


def insert_essay(c,obj):
    ensure_schema(c)
    grade=_grade(obj.get('grade'),'Nota');maximum=_grade(obj.get('maximum_grade'),'Nota máxima')
    if grade is None or maximum is None or maximum<=0 or grade>maximum:
        raise ValueError('Informe nota válida de 0 até a nota máxima')
    row=(_valid_day(obj.get('day')),_text(obj.get('topic'),'Tema',240),str(obj.get('bank',''))[:80],
         grade,maximum,str(obj.get('notes',''))[:1200])
    cur=c.execute('INSERT INTO essays(day,topic,bank,grade,maximum_grade,notes) VALUES(?,?,?,?,?,?)',row)
    c.commit();return cur.lastrowid


def delete_assessment(c,kind,ident):
    if kind not in ('mock_exams','essays'):raise ValueError('Tipo inválido')
    if not isinstance(ident,int) or isinstance(ident,bool) or ident<=0:raise ValueError('ID inválido')
    ensure_schema(c)
    cur=c.execute(f'DELETE FROM {kind} WHERE id=?',(ident,))
    if not cur.rowcount:raise ValueError('Registro inexistente')
    c.commit();return True


def assessment_summary(c):
    ensure_schema(c)
    mocks=all_rows(c,'SELECT * FROM mock_exams ORDER BY day DESC,id DESC LIMIT 100')
    essays=all_rows(c,'SELECT * FROM essays ORDER BY day DESC,id DESC LIMIT 100')
    totals=c.execute('SELECT COALESCE(SUM(total),0),COALESCE(SUM(correct),0),COUNT(*) FROM mock_exams').fetchone()
    count=totals[2]
    essay_mean=c.execute('SELECT AVG(100.0*grade/maximum_grade) FROM essays').fetchone()[0]
    return {'mocks':mocks,'essays':essays,'mock_count':count,'mock_questions':totals[0],
            'mock_rate':(totals[1]/totals[0]) if totals[0] else None,
            'essay_count':c.execute('SELECT COUNT(*) FROM essays').fetchone()[0],
            'essay_mean_pct':round(essay_mean,2) if essay_mean is not None else None,
            'definitions':{'mock_rate':'Acertos em simulados / total de questões em simulados (inclui brancos)',
                           'essay_mean_pct':'Média simples das notas percentuais por redação'}}