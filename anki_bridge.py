"""AnkiConnect local: inventário de baralhos sem ler conteúdo ou alterar FSRS.

Somente ações explicitamente permitidas: version, deckNamesAndIds, findCards.
Snapshot local idempotente, não é histórico de revisões nem horas de estudo.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime
from http.client import HTTPConnection

from core import all_rows, map_subject, norm, DEFAULT_SUBJECTS

HOST, PORT, API_VERSION = '127.0.0.1', 8765, 5
ALLOWED = {'version', 'deckNamesAndIds', 'findCards', 'cardReviews'}
MAX_DECKS, MAX_CARDS = 90, 150000
SUBJECTS = tuple(name for name, _weight, _area in DEFAULT_SUBJECTS)


def invoke(action, params=None):
    if action not in ALLOWED:
        raise ValueError('Ação AnkiConnect não autorizada para esta integração.')
    req={'action':action,'version':API_VERSION,'params':params or {}}
    if os.environ.get('ANKICONNECT_API_KEY'):
        req['key']=os.environ['ANKICONNECT_API_KEY']
    payload = json.dumps(req,ensure_ascii=False).encode('utf-8')
    conn = HTTPConnection(HOST, PORT, timeout=7)
    try:
        conn.request('POST', '/', body=payload, headers={'Content-Type':'application/json'})
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError(f'AnkiConnect respondeu HTTP {response.status}.')
        body = response.read(24 * 1024 * 1024 + 1)
        if len(body) > 24 * 1024 * 1024:
            raise ValueError('Resposta do Anki grande demais; limite de segurança excedido.')
        data = json.loads(body)
        if not isinstance(data, dict) or 'result' not in data:
            raise ValueError('Resposta AnkiConnect inválida.')
        if data.get('error'):
            raise ValueError('AnkiConnect: '+str(data['error'])[:200])
        return data['result']
    except (OSError, TimeoutError) as exc:
        raise ValueError('Não foi possível conectar ao AnkiConnect local (127.0.0.1:8765). Abra o Anki e confira o complemento.') from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError('AnkiConnect devolveu conteúdo inválido.') from exc
    finally:
        conn.close()


def prepare(c):
    c.execute('''CREATE TABLE IF NOT EXISTS anki_live_snapshots (
      profile TEXT NOT NULL, day TEXT NOT NULL, subject TEXT NOT NULL,
      deck_names TEXT NOT NULL, card_count INTEGER NOT NULL,
      due_count INTEGER NOT NULL, new_count INTEGER NOT NULL,
      rated_24h_count INTEGER NOT NULL, checked_at TEXT NOT NULL,
      PRIMARY KEY(profile,day,subject))''')
    c.commit()


def local_status(c):
    prepare(c)
    rows = all_rows(c,'''SELECT profile,day,subject,deck_names,card_count,due_count,
      new_count,rated_24h_count,checked_at FROM anki_live_snapshots
      WHERE (profile,day) IN (SELECT profile,MAX(day) FROM anki_live_snapshots GROUP BY profile)
      ORDER BY profile,subject''')
    return {'snapshots':rows,'mode':'Dados de inventário; sem importação de horas, notas ou intervalos FSRS',
            'live':False}


def detect():
    version=invoke('version')
    if not isinstance(version,int) or version < API_VERSION:
        raise ValueError('AnkiConnect incompatível: versão de API 5 ou superior necessária.')
    decks=invoke('deckNamesAndIds')
    if not isinstance(decks,dict):
        raise ValueError('Lista de baralhos inesperada.')
    mapped=[]
    for name,ident in sorted(decks.items()):
        x=norm(name)
        # Reformas devem ser desambiguadas antes do mapeamento genérico.
        if 'reforma tributaria' in x and '227' in x:sub='Reforma Tributária — LC 227'
        elif 'reforma tributaria' in x and ('132' in x or '214' in x):sub='Reforma Tributária — EC 132 e LC 214'
        else:sub=map_subject(name)
        if sub not in SUBJECTS:
            # Nomes completos como SEFAZ-RS::Matemática Financeira
            # podem não existir na tabela histórica de apelidos.
            sub=next((candidate for candidate in
                      sorted(SUBJECTS,key=len,reverse=True) if norm(candidate) in x),sub)
        if sub not in SUBJECTS:continue
        mapped.append({'deck':name,'deck_id':ident,'subject':sub})
    return {'connected':True,'version':version,'decks':mapped,
            'all_decks':len(decks),'selected_decks':len(mapped),
            'note':'Baralhos sem disciplina identificável permanecem fora do cálculo. Nenhum conteúdo foi lido.'}


def _card_ids(query):
    data=invoke('findCards',{'query':query})
    if not isinstance(data,list):raise ValueError('AnkiConnect retornou IDs inválidos.')
    if len(data)>MAX_CARDS:raise ValueError('Coleção acima do limite de segurança deste importador.')
    return {x for x in data if isinstance(x,int) and not isinstance(x,bool)}


def collect_snapshot(profile='Principal'):
    profile=str(profile).strip()
    if not 1 <= len(profile) <= 50 or any(ord(ch)<32 for ch in profile):
        raise ValueError('Perfil Anki inválido (1 a 50 caracteres).')
    d=detect()
    if not d['decks']:
        return {'profile':profile,'subjects':[],'decks':0,'warnings':['Nenhum baralho foi associado às disciplinas.']}
    if len(d['decks'])>MAX_DECKS:
        raise ValueError(f'Foram encontrados mais de {MAX_DECKS} baralhos relevantes; revise a árvore antes de sincronizar.')
    per={}
    # Conjuntos (não somas) evitam duplicar cartões quando um deck pai inclui subdecks.
    for item in d['decks']:
        name=item['deck']
        if '"' in name or '\\' in name:
            continue  # Não construir expressão de busca malformada.
        base='deck:"'+name+'"'
        sub=item['subject']
        row=per.setdefault(sub,{'subject':sub,'decks':[], 'all':set(),'due':set(), 'new':set(),'rated':set()})
        row['decks'].append(name)
        for label,qualifier in [('all',''),('due',' is:due'),('new',' is:new'),('rated',' rated:1')]:
            row[label].update(_card_ids(base+qualifier))
            if len(row[label])>MAX_CARDS:
                raise ValueError('Excesso de cartões na categoria; sincronização interrompida.')
    outputs=[]
    seen=set()
    for subject in SUBJECTS:
        row=per.get(subject)
        if not row:continue
        # Deduplicação interdisciplina: mesma identidade não contribui a dois temas.
        allowed=row['all']-seen
        seen.update(allowed)
        outputs.append({'subject':subject,'deck_names':row['decks'],'card_count':len(allowed),
          'due_count':len(row['due']&allowed),'new_count':len(row['new']&allowed),
          'rated_24h_count':len(row['rated']&allowed)})
    return {'profile':profile,'subjects':outputs,'decks':len(d['decks']),
            'warnings':['rated:1 representa cartões revisados nas últimas 24h, não número de revisões, horas ou retenção.']}


def save_snapshot(c,snapshot,confirm=False):
    if confirm is not True:raise ValueError('Confirme a importação do retrato local do Anki.')
    prepare(c)
    day=date.today().isoformat()
    stamp=datetime.now().isoformat(timespec='seconds')
    profile=snapshot['profile']
    try:
        c.execute('BEGIN IMMEDIATE')
        for item in snapshot['subjects']:
            c.execute('''INSERT INTO anki_live_snapshots
              (profile,day,subject,deck_names,card_count,due_count,new_count,rated_24h_count,checked_at)
              VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(profile,day,subject) DO UPDATE SET
              deck_names=excluded.deck_names,card_count=excluded.card_count,
              due_count=excluded.due_count,new_count=excluded.new_count,
              rated_24h_count=excluded.rated_24h_count,checked_at=excluded.checked_at''',
              (profile,day,item['subject'],json.dumps(item['deck_names'],ensure_ascii=False),
               item['card_count'],item['due_count'],item['new_count'],item['rated_24h_count'],stamp))
        c.commit()
    except Exception:
        c.rollback()
        raise
    return {'ok':True,'profile':profile,'subject_count':len(snapshot['subjects']),
       'checked_at':stamp,'note':'Retrato informativo. Nenhum tempo ou nota foi acrescentado aos indicadores históricos.'}