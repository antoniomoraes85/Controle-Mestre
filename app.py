"""CONTROLE MESTRE — painel pessoal, offline/local-first.
Inicie com: streamlit run app.py
"""
import csv
import io
import os
from datetime import date, datetime, timedelta

import streamlit as st
from ui_theme import STYLES, card, progress, note, empty, priorities, tasks as task_cards
from core import (ROOT, connect, all_rows, metric_data, subject_metrics, get_days,
                  DAY_CAPS, METHODS, add_session, add_questions, save_topic, save_day,
                  generate_plan, backup_sqlite, export_json, import_excel, import_anki_csv, number)

st.set_page_config(page_title='CONTROLE MESTRE | Central de Estudos',page_icon='🎯',layout='wide',initial_sidebar_state='expanded')
st.markdown(STYLES, unsafe_allow_html=True)

if 'db_connection' not in st.session_state:
    st.session_state.db_connection=connect()
c=st.session_state.db_connection

def rs(v): return f'{v:,.1f}'.replace(',','X').replace('.',',').replace('X','.')
def perc(v): return '—' if v is None else f'{100*v:.1f}%'.replace('.',',')
def subj_opts(): return [x['name'] for x in all_rows(c,'SELECT name FROM subjects ORDER BY weight DESC,name')]
def topics_for(subject):return [x['topic'] for x in all_rows(c,'SELECT DISTINCT topic FROM topics WHERE subject=? ORDER BY progress,topic',(subject,))]
def today_ws(day=None):
    day=day or date.today();return day-timedelta(days=day.weekday())
def banner(title,subtitle):
    st.markdown('<span class="cm-eyebrow">CONTROLE MESTRE · SEFAZ-RS</span>',unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="cm-sub">{subtitle}</div>',unsafe_allow_html=True)

def plot(values,mark,x,y,color='#24D6A5',height=240,title=None):
    if not values:
        st.markdown(empty('Sem dados ainda','Registre sua primeira atividade para visualizar a evolução.'),unsafe_allow_html=True)
        return
    enc={
        'x':{'field':x,'type':'ordinal','axis':{'labelColor':'#BED0E6','labelAngle':0,'title':None,'labelFontSize':11,'labelLimit':110,'tickSize':0,'labelPadding':10}},
        'y':{'field':y,'type':'quantitative','scale':{'zero':True},'axis':{'labelColor':'#B9CCE4','title':None,'labelFontSize':11,'tickCount':4,'format':'.1f'}},
        'tooltip':[{'field':x,'type':'nominal'},{'field':y,'type':'quantitative','format':'.2f'}]
    }
    spec={'mark':{'type':mark,'color':color,'cornerRadiusTopLeft':4,'cornerRadiusTopRight':4},'encoding':enc,
          'data':{'values':values},'height':height,'background':'transparent',
          'padding':{'left':6,'right':12,'top':6,'bottom':6},
          'config':{'view':{'stroke':None},'axis':{'gridColor':'#26364F','domainColor':'#2E4762'}}}
    st.vega_lite_chart(spec,use_container_width=True)

def weekly_activity(c, today=None):
    """Quatro blocos completos de sete dias até a data de referência."""
    today=today or date.today()
    first=today-timedelta(days=27)
    rows=all_rows(c,'SELECT day,SUM(minutes) mins FROM sessions WHERE day BETWEEN ? AND ? GROUP BY day',
                  (first.isoformat(),today.isoformat()))
    if not rows:
        return []
    daily={row['day']:float(row['mins'])/60 for row in rows}
    out=[]
    for i in range(4):
        start=first+timedelta(days=i*7)
        end=start+timedelta(days=6)
        hours=sum(daily.get((start+timedelta(days=j)).isoformat(),0) for j in range(7))
        out.append({'semana':f'{start:%d/%m} – {end:%d/%m}','horas':round(hours,2)})
    return out

st.sidebar.markdown('''<div class="cm-brand"><div class="cm-logo"><div class="cm-logo-mark">CM</div><div class="cm-logo-title">CONTROLE<br>MESTRE</div></div><small>SEU CENTRO DE ESTUDOS</small></div>''', unsafe_allow_html=True)
sections=['Visão geral','Estudar hoje','Planejamento semanal','Ciclos de estudos','Disciplinas e assuntos','Questões e erros','Revisões e Anki','Importação','Configurações']
page=st.sidebar.radio('Navegação',sections,label_visibility='collapsed',key='navigation')
st.sidebar.divider()
st.sidebar.caption('SEFAZ-RS · PLANEJAMENTO PESSOAL')
st.sidebar.caption('Dados armazenados localmente. Sem assinatura.')

if page=='Visão geral':
    banner('Painel executivo','Seu progresso, o que precisa de atenção e a próxima ação de estudo.')
    m=metric_data(c)
    rank=subject_metrics(c)
    weekly_target=m['weekly_target']
    has_records=bool(m['weekly_minutes'] or m['monthly_minutes'] or
                     m['week_questions']['total'] or m['month_questions']['total'])

    st.markdown('<div class="cm-section">Indicadores da preparação</div>',unsafe_allow_html=True)
    a,b,d,e=st.columns(4,gap='small')
    a.markdown(card('Horas líquidas · semana',rs(m['weekly_minutes']/60)+' h',
                    f'Meta: {rs(weekly_target/60)} horas','green'),unsafe_allow_html=True)
    b.markdown(card('Meta semanal cumprida',perc(m['adherence']),
                    'Tempo realizado ÷ meta prevista','blue'),unsafe_allow_html=True)
    d.markdown(card('Questões · semana',str(m['week_questions']['total']),
                    f'{m["week_questions"]["correct"]} acertos registrados','blue'),unsafe_allow_html=True)
    e.markdown(card('Precisão · 30 dias',perc(m['last30_questions']['rate']),
                    'Sem dados' if m['last30_questions']['rate'] is None else 'Acertos ÷ questões','green'),unsafe_allow_html=True)
    st.markdown('<div style="height:8px"></div>',unsafe_allow_html=True)
    a,b,d,e=st.columns(4,gap='small')
    a.markdown(card('Horas líquidas · mês',rs(m['monthly_minutes']/60)+' h',
                    'Sessões efetivamente registradas','neutral'),unsafe_allow_html=True)
    b.markdown(card('Questões · mês',str(m['month_questions']['total']),
                    'Questões respondidas','neutral'),unsafe_allow_html=True)
    d.markdown(card('Revisões vencidas',str(m['overdue_reviews']),
                    'Pendências anteriores a hoje','amber' if m['overdue_reviews'] else 'neutral'),unsafe_allow_html=True)
    e.markdown(card('Flashcards Anki · semana',str(m['anki_cards']),
                    'Registros do Anki importados','neutral'),unsafe_allow_html=True)
    st.markdown('<div style="height:12px"></div>',unsafe_allow_html=True)
    st.markdown(progress('Progresso da meta semanal',m['weekly_minutes'],weekly_target),unsafe_allow_html=True)

    if not has_records:
        st.markdown(note('COMECE POR AQUI','Seu painel está pronto para receber dados',
            'Defina os dias de plantão, gere seu planejamento e registre a primeira sessão. A pontuação inicial é provisória até existirem questões e estudos registrados.'),
            unsafe_allow_html=True)
        if st.button('Criar meu primeiro planejamento →',type='primary',on_click=lambda:st.session_state.__setitem__('navigation','Planejamento semanal')):
            pass
    elif rank:
        lead=rank[0]
        explanation=(f'Rendimento atual: {perc(lead["rendimento"])} em {lead["questoes"]} questões. Priorize erros e revisões.'
                     if lead['questoes']>=15 and lead['rendimento'] is not None else
                     'Prioridade calculada com poucos registros; resolva questões para calibrar a recomendação.')
        st.markdown(note('RECOMENDAÇÃO ATUAL',lead['disciplina'],explanation),unsafe_allow_html=True)

    left,right=st.columns([1.35,1],gap='large')
    with left:
        st.markdown('<div class="cm-section">Evolução das últimas 4 semanas</div>',unsafe_allow_html=True)
        values=weekly_activity(c)
        if values:
            plot(values,'bar','semana','horas',height=240)
        else:
            st.markdown(empty('Nenhuma sessão registrada nesse período',
                    'Quando você começar a estudar, suas horas líquidas aparecerão aqui, agrupadas por semana.'),
                    unsafe_allow_html=True)
        st.caption('Tempo importado do Anki é exibido à parte para evitar contagem dupla.')
    with right:
        st.markdown('<div class="cm-section">Prioridades estratégicas</div>',unsafe_allow_html=True)
        st.markdown(priorities(rank,perc),unsafe_allow_html=True)
        st.caption('Pontuação relativa: peso, conteúdo pendente, rendimento e revisões. Sem dados suficientes, classificação provisória.')

    left,right=st.columns([1.35,1],gap='large')
    with left:
        st.markdown('<div class="cm-section">Horas por disciplina</div>',unsafe_allow_html=True)
        studied=[r for r in rank if r['horas']>0]
        if studied:
            studied=sorted(studied,key=lambda r:-r['horas'])[:6]
            plot([{'disciplina':r['disciplina'][:27],'horas':r['horas']} for r in studied],
                 'bar','disciplina','horas',height=245)
        else:
            st.markdown(empty('Ainda não há horas por disciplina',
                       'Registre as sessões pelo cronômetro ou importe sua planilha de estudos.'),unsafe_allow_html=True)
    with right:
        st.markdown('<div class="cm-section">Próximas atividades</div>',unsafe_allow_html=True)
        next_tasks=all_rows(c,"SELECT day,subject,topic,method,target_minutes FROM plans WHERE status='Pendente' AND day>=? ORDER BY day,priority DESC LIMIT 5",(date.today().isoformat(),))
        st.markdown(task_cards(next_tasks),unsafe_allow_html=True)

elif page=='Estudar hoje':
    banner('Estudar hoje','Execute as metas e registre resultados com o menor atrito possível.')
    today=date.today().isoformat();kindrow=c.execute('SELECT kind FROM day_types WHERE day=?',(today,)).fetchone()
    kind=kindrow['kind'] if kindrow else 'Livre leve'
    st.info(f'Hoje: {date.today():%d/%m/%Y} · Tipo de dia: **{kind}**. Configure plantões no Planejamento semanal.')
    tasks=all_rows(c,"SELECT id,subject,topic,method,target_minutes,target_questions,status FROM plans WHERE day=? ORDER BY priority DESC",(today,))
    if tasks:
        st.subheader('Metas de hoje')
        st.dataframe(tasks,hide_index=True,use_container_width=True)
        st.caption('Concluir uma meta não registra automaticamente tempo estudado; utilize o cronômetro ou formulário de sessões.')
        with st.form('complete_task'):
            task=st.selectbox('Marcar tarefa concluída',options=tasks,format_func=lambda r:f'{r["subject"]} · {r["method"]} ({r["target_minutes"]} min)')
            if st.form_submit_button('Concluir meta',type='primary'):
                c.execute("UPDATE plans SET status='Concluída' WHERE id=?",(task['id'],));c.commit();st.success('Meta atualizada.');st.rerun()
    else:st.warning('Ainda não há metas para hoje. Gere o planejamento semanal.')
    st.divider()
    st.subheader('Cronômetro de estudo')
    subjects=subj_opts()
    top1,top2,top3=st.columns([1,1,1])
    with top1:timer_subject=st.selectbox('Disciplina do cronômetro',subjects,key='timer_subject')
    with top2:timer_topic=st.selectbox('Assunto', ['(não especificado)']+topics_for(timer_subject),key='timer_topic')
    with top3:timer_method=st.selectbox('Atividade',METHODS,key='timer_method')
    timer_cycle=st.selectbox('Ciclo de estudos (para registrar no histórico)',list(range(1,11)),key='timer_cycle')
    if 'timer_start' not in st.session_state:st.session_state.timer_start=None
    if 'timer_elapsed' not in st.session_state:st.session_state.timer_elapsed=0
    if 'timer_metadata' not in st.session_state:st.session_state.timer_metadata={}
    @st.fragment(run_every='1s')
    def stopwatch():
        if st.session_state.timer_start:
            total=st.session_state.timer_elapsed+(datetime.now()-st.session_state.timer_start).total_seconds()
        else:total=st.session_state.timer_elapsed
        st.markdown(f'### ⏱ {int(total//3600):02d}:{int((total%3600)//60):02d}:{int(total%60):02d}')
        left,middle,right,reset_col=st.columns(4)
        if left.button('▶ Iniciar / retomar',disabled=st.session_state.timer_start is not None):
            if not st.session_state.timer_elapsed:
                st.session_state.timer_metadata={'subject':st.session_state.timer_subject,'topic':st.session_state.timer_topic,'method':st.session_state.timer_method,'cycle':st.session_state.timer_cycle}
            st.session_state.timer_start=datetime.now();st.rerun(scope='fragment')
        if middle.button('Ⅱ Pausar',disabled=st.session_state.timer_start is None):
            st.session_state.timer_elapsed+=(datetime.now()-st.session_state.timer_start).total_seconds()
            st.session_state.timer_start=None;st.rerun(scope='fragment')
        if right.button('■ Finalizar e registrar',disabled=total<30):
            elapsed=total;data=st.session_state.timer_metadata
            try:
                add_session(c,date.today().isoformat(),data.get('subject',st.session_state.timer_subject),
                  data.get('topic','').replace('(não especificado)',''),data.get('method','Teoria'),max(1,round(elapsed/60)),kind,
                  notes='Cronômetro interno',source='cronômetro',auto_review=data.get('method') in ('Teoria','Lei seca'),cycle=data.get('cycle'))
                st.session_state.timer_start=None;st.session_state.timer_elapsed=0
                st.success(f'Sessão registrada: {round(elapsed/60)} min.');st.rerun()
            except ValueError as ex:st.error(str(ex))
        if reset_col.button('↺ Zerar',help='Descartar cronômetro sem registrar tempo'):
            st.session_state.timer_start=None;st.session_state.timer_elapsed=0
            st.session_state.timer_metadata={};st.rerun(scope='fragment')
    stopwatch()
    st.caption('O cronômetro funciona enquanto a página permanece aberta. Use registro manual se a sessão não tiver sido salva.')
    st.divider()
    st.subheader('Registro manual de estudo')
    with st.form('session_form'):
        col1,col2,col3=st.columns(3)
        d=col1.date_input('Data',date.today());subject=col2.selectbox('Disciplina',subjects,key='s_subject')
        method=col3.selectbox('Tipo de estudo',METHODS,key='s_method')
        col1,col2,col3=st.columns(3)
        topic=col1.text_input('Assunto',placeholder='Ex.: Obrigação tributária',key='s_topic')
        mins=col2.number_input('Minutos líquidos',min_value=1,max_value=900,value=50)
        dtype=col3.selectbox('Tipo de dia',list(DAY_CAPS),index=list(DAY_CAPS).index(kind))
        cycle=st.selectbox('Ciclo de estudos',list(range(1,11)),key='manual_cycle')
        notes=st.text_input('Observações (opcional)')
        auto=st.checkbox('Agendar revisões D+1, D+7, D+15 e D+30',value=method in ('Teoria','Lei seca'))
        if st.form_submit_button('Registrar estudo',type='primary'):
            try:
                add_session(c,d,subject,topic,method,mins,dtype,notes,auto_review=auto,cycle=cycle)
                st.success('Estudo registrado.');st.rerun()
            except ValueError as ex:st.error(str(ex))

elif page=='Planejamento semanal':
    banner('Planejamento semanal','Distribuição adaptativa por prioridades, desempenho e disponibilidade.')
    wk=st.date_input('Semana de referência (qualquer dia)',value=today_ws())
    wk=today_ws(wk)
    m=metric_data(c)
    st.caption(f'Meta semanal atual: **{m["weekly_target"]/60:.1f} horas**. Ajuste em Configurações.')
    days=get_days(c,wk)
    with st.form('calendar'):
        st.markdown('**Disponibilidade semanal — configure plantões e recuperação**')
        selected=[]
        daylabels=['Segunda','Terça','Quarta','Quinta','Sexta','Sábado','Domingo']
        for i,d in enumerate(days):
            a,b,e=st.columns([1.3,2,1.3])
            a.write(f'{daylabels[i]} · {date.fromisoformat(d["day"]):%d/%m}')
            kind=b.selectbox('Tipo de dia',list(DAY_CAPS),index=list(DAY_CAPS).index(d['kind']),key='kind_'+d['day'],label_visibility='collapsed')
            cap=e.number_input('Minutos disponíveis',0,DAY_CAPS[kind],min(d['cap_minutes'],DAY_CAPS[kind]),step=10,key='cap_'+d['day'],label_visibility='collapsed')
            selected.append((d['day'],kind,cap))
        if st.form_submit_button('Salvar disponibilidade'):
            for d,k,cap in selected:save_day(c,d,k,cap)
            st.success('Disponibilidade salva.');st.rerun()
    st.divider()
    if st.button('Gerar / recalcular plano da semana',type='primary'):
        summary=generate_plan(c,wk)
        st.success(f'Criadas {summary["activities"]} atividades · {summary["planned_minutes"]/60:.1f} horas planejadas.')
        if summary['target_minutes']>summary['capacity_minutes']:
            st.warning('Capacidade informada inferior à meta semanal. O planejador respeitou a capacidade e não criou sobrecarga.')
    period_end=(wk+timedelta(days=6)).isoformat()
    tasks=all_rows(c,'SELECT day,subject,topic,method,target_minutes,target_questions,status,rationale FROM plans WHERE day BETWEEN ? AND ? ORDER BY day,priority DESC',(wk.isoformat(),period_end))
    if tasks:
        st.subheader('Plano gerado')
        st.dataframe(tasks,hide_index=True,use_container_width=True)
        st.caption('Recalcular substitui apenas atividades pendentes na semana; concluidas permanecem registradas.')
    else:st.info('Defina o calendário e clique em Gerar plano da semana.')
    st.caption('Algoritmo determinístico e auditável (não é inteligência artificial generativa nesta versão).')

elif page=='Ciclos de estudos':
    banner('Ciclos de estudos','Dez ciclos, disciplina por disciplina, preservando os valores da planilha legada.')
    actual=all_rows(c,'SELECT subject,cycle,SUM(minutes) minutes FROM sessions WHERE cycle BETWEEN 1 AND 10 GROUP BY subject,cycle')
    legacy=all_rows(c,'SELECT subject,cycle_number cycle,MAX(minutes) minutes FROM cycles GROUP BY subject,cycle_number')
    st.warning('Tempo das sessões com data e totais legados da planilha são exibidos separadamente: podem se sobrepor e não são somados.')
    if actual:
        st.subheader('Tempos de ciclos registrados no CONTROLE MESTRE')
        st.dataframe([{'Disciplina':x['subject'],'Ciclo':int(x['cycle']),'Horas':round(x['minutes']/60,2)} for x in actual],hide_index=True,use_container_width=True)
    if legacy:
        st.subheader('Totais históricos importados do Excel')
        st.dataframe([{'Disciplina':x['subject'],'Ciclo':int(x['cycle']),'Horas no Excel':round(x['minutes']/60,2)} for x in legacy],hide_index=True,use_container_width=True)
    if not actual and not legacy:st.info('Registre sessões associadas a um ciclo ou importe sua planilha com colunas CICLO 1 a CICLO 10.')
    st.caption('Cada registro do cronômetro é salvo como sessão com data, matéria, atividade e número do ciclo. A célula original do Excel não é alterada.')

elif page=='Disciplinas e assuntos':
    banner('Disciplinas e assuntos','Matriz estratégica e controle granular de todo o conteúdo programático.')
    rank=subject_metrics(c)
    st.dataframe([{'Disciplina':r['disciplina'],'Área':r['bloco'],'Peso':r['peso'],'Horas':r['horas'],
                   'Questões':r['questoes'],'Acerto':perc(r['rendimento']),
                   'Teoria média':('—' if r['progresso'] is None else f'{r["progresso"]}%'),
                   'Necessidade':r['prioridade']} for r in rank],hide_index=True,use_container_width=True)
    st.divider()
    a,b=st.columns([1,1])
    with a:
        st.subheader('Atualizar progresso de assunto')
        with st.form('topic_form'):
            sub=st.selectbox('Disciplina',subj_opts(),key='topic_subject')
            t=st.text_input('Assunto',placeholder='Digite o assunto para cadastrar ou atualizar')
            new='' 
            pct=st.slider('Progresso da teoria (%)',0,100,0)
            lesson=st.text_input('Aula/referência (opcional)')
            if st.form_submit_button('Salvar progresso',type='primary'):
                chosen=t.strip()
                if chosen:save_topic(c,sub,chosen,lesson,pct);st.success('Assunto atualizado.');st.rerun()
                else:st.error('Informe o nome do assunto.')
    with b:
        st.subheader('Conteúdo por disciplina')
        filter_subject=st.selectbox('Filtrar disciplina',subj_opts(),key='filter_sub')
        entries=all_rows(c,'SELECT lesson,topic,progress,incidence FROM topics WHERE subject=? ORDER BY progress,lesson',(filter_subject,))
        if entries:st.dataframe(entries,hide_index=True,use_container_width=True,height=350)
        else:st.info('Cadastre tópicos ou importe sua planilha de aulas.')

elif page=='Questões e erros':
    banner('Questões e caderno de erros','Desempenho ponderado pelo total de questões — não pela média simples de percentuais.')
    with st.form('question_entry'):
        a,b,d=st.columns(3)
        dt=a.date_input('Data',date.today());subject=b.selectbox('Disciplina',subj_opts(),key='qsub');topic=d.text_input('Assunto',placeholder='Digite o assunto',key='qtopic')
        a,b,d=st.columns(3)
        n=a.number_input('Total de questões',1,1000,30);good=b.number_input('Acertos',0,1000,20)
        bank=d.text_input('Banca',value='FCC')
        a,b=st.columns(2);platform=a.text_input('Plataforma',value='TEC / Qconcursos / Estratégia')
        errtype=b.selectbox('Tipo de erro',['','Conceito','Atenção','Lei seca','Interpretação','Cálculo','Decoreba','Chute'])
        why=st.text_area('Aprendizado / erro encontrado (opcional)')
        if st.form_submit_button('Salvar lote de questões',type='primary'):
            try:
                add_questions(c,dt,subject,topic,n,good,bank,platform,errtype,why)
                st.success('Questões contabilizadas.');st.rerun()
            except ValueError as ex:st.error(str(ex))
    st.divider()
    history=all_rows(c,'SELECT day,subject,topic,bank,platform,total,correct,(total-correct) wrong FROM questions ORDER BY day DESC,id DESC LIMIT 200')
    if history:
        st.subheader('Histórico de questões')
        st.dataframe(history,hide_index=True,use_container_width=True)
        series=all_rows(c,'SELECT day,SUM(total) total,SUM(correct) correct FROM questions GROUP BY day ORDER BY day DESC LIMIT 40')
        series.reverse(); plot([{'dia':x['day'][5:],'acerto_pct':round(100*x['correct']/x['total'],1)} for x in series if x['total']],'line','dia','acerto_pct',height=260)
    st.subheader('Caderno de erros')
    rows=all_rows(c,"SELECT id,day,subject,topic,reason,correction,status FROM errors ORDER BY CASE status WHEN 'Aberto' THEN 0 ELSE 1 END, day DESC LIMIT 200")
    if rows:
        st.dataframe(rows,hide_index=True,use_container_width=True)
        with st.form('close_error'):
            task=st.selectbox('Erro que deseja corrigir',rows,format_func=lambda r:f'#{r["id"]} · {r["subject"]} · {r["topic"][:45]}')
            correction=st.text_area('Regra correta / ação corretiva')
            done=st.checkbox('Marcar como resolvido',value=True)
            if st.form_submit_button('Salvar correção'):
                c.execute('UPDATE errors SET correction=?,status=? WHERE id=?',(correction,'Resolvido' if done else 'Aberto',task['id']));c.commit();st.rerun()
    else:st.info('Nenhum erro registrado ainda.')

elif page=='Revisões e Anki':
    banner('Revisões e Anki','Revisão espaçada e dados de flashcards, sem misturar métricas distintas.')
    m=metric_data(c)
    a,b,d=st.columns(3)
    a.metric('Revisões do sistema vencidas',m['overdue_reviews'])
    b.metric('Anki · cartões na semana',m['anki_cards'])
    d.metric('Anki · tempo informado',rs(m['anki_minutes'])+' min')
    pending=all_rows(c,"SELECT id,due_on,subject,topic,created_on FROM reviews WHERE status='Pendente' ORDER BY due_on LIMIT 150")
    st.subheader('Fila de revisões')
    if pending:
        st.dataframe(pending,hide_index=True,use_container_width=True)
        with st.form('rev_done'):
            task=st.selectbox('Concluir revisão',pending,format_func=lambda r:f'{r["due_on"]} · {r["subject"]} · {r["topic"][:40]}')
            if st.form_submit_button('Marcar revisada',type='primary'):
                c.execute("UPDATE reviews SET status='Concluída',finished_on=? WHERE id=?",(date.today().isoformat(),task['id']));c.commit();st.rerun()
    else:st.info('Sem revisões pendentes no banco local.')
    st.divider()
    anki=all_rows(c,'SELECT day,deck,subject,cards,errors,ROUND(minutes,1) minutes FROM anki ORDER BY day DESC LIMIT 200')
    st.subheader('Anki · histórico importado')
    if anki:st.dataframe(anki,hide_index=True,use_container_width=True)
    else:st.info('Importe um CSV agregado por data e baralho na seção Importação.')

elif page=='Importação':
    banner('Central de importação','Impossibilita misturar estimativas planejadas com dados reais de execução.')
    st.warning('Não importe dois controles diferentes contendo as mesmas sessões: arquivos distintos podem representar o mesmo estudo. Mantenha backups antes de qualquer integração.')
    st.subheader('1 · Excel fiscal e cronômetro')
    st.caption('Compatível inicialmente com BASE_AULAS, LANÇAMENTO DIÁRIO, QUESTÕES, Sessoes, Registro_Tempos (VBA V6) e CICLO em .xlsx/.xlsm. Outras abas são preservadas no arquivo original, mas não interpretadas como registros.')
    wbfile=st.file_uploader('Selecione sua planilha',type=['xlsx','xlsm'],key='wbfile')
    if wbfile and st.button('Analisar e importar Excel',type='primary'):
        try:
            data=wbfile.getvalue()
            if len(data)>30_000_000:raise ValueError('Arquivo muito grande: limite recomendado 30 MB.')
            r=import_excel(c,data,wbfile.name)
            st.success(f'Conteúdos processados: {r["assuntos"]}; sessões: {r["sessoes"]}; questões: {r["questoes"]}; valores de ciclos: {r["ciclos"]}.')
            st.write('Abas encontradas:',', '.join(r['abas']))
            for note in r['observacoes']:st.info(note)
        except Exception as ex:st.error(f'Falha de importação: {ex}')
    st.divider();st.subheader('2 · Estatísticas do Anki')
    st.caption('CSV agregado com: data/date, baralho/deck, revisoes/reviews, erros/errors e minutos/minutes. CSV bruto revlog sem baralho não permite identificação da disciplina.')
    ankifile=st.file_uploader('Selecione o CSV de revisões do Anki',type=['csv','txt'],key='ankifile')
    if ankifile and st.button('Importar CSV do Anki',type='primary'):
        try:st.success(str(import_anki_csv(c,ankifile.getvalue(),ankifile.name)))
        except ValueError as ex:st.error(str(ex))
    st.divider();st.subheader('3 · Backup completo')
    st.download_button('Baixar backup completo SQLite',data=backup_sqlite(c),file_name='controle_mestre_backup.sqlite',mime='application/vnd.sqlite3',type='primary')
    st.download_button('Exportar dados legíveis JSON',data=export_json(c),file_name='controle_mestre_export.json',mime='application/json')
    st.caption('Para restaurar o backup SQLite, feche o aplicativo e substitua data/controle_mestre.db pelo arquivo baixado (renomeado). Guarde-o em local privado e protegido.')
    logs=all_rows(c,'SELECT stamp,filename,inserted,skipped,notes FROM import_log ORDER BY id DESC LIMIT 25')
    if logs:st.dataframe(logs,hide_index=True,use_container_width=True)

elif page=='Configurações':
    banner('Configurações','Ajuste metas e pesos sem alterar os registros históricos.')
    m=metric_data(c)
    with st.form('setting_form'):
        hours=st.number_input('Meta semanal de horas líquidas',min_value=1,max_value=80,value=int(m['weekly_target']/60))
        if st.form_submit_button('Salvar meta',type='primary'):
            c.execute("UPDATE settings SET value=? WHERE key='weekly_target_min'",(str(hours*60),));c.commit();st.rerun()
    st.divider();st.subheader('Pesos estratégicos por matéria')
    with st.form('weight_form'):
        sb=st.selectbox('Disciplina',subj_opts(),key='wsub')
        old=c.execute('SELECT weight FROM subjects WHERE name=?',(sb,)).fetchone()['weight']
        weight=st.slider('Peso estratégico',1,10,int(old))
        if st.form_submit_button('Atualizar peso'):
            c.execute('UPDATE subjects SET weight=? WHERE name=?',(weight,sb));c.commit();st.rerun()
    st.info('O índice de necessidade combina peso estratégico, rendimento observado, tempo sem estudar, progresso da teoria e revisões vencidas. Quando há poucos dados, utiliza um valor provisório e não presume domínio.')
    st.markdown('**Fórmula v0.1:** `peso × (1 + 0,90 × fraqueza + 0,65 × negligência + 0,45 × lacuna + 0,18 × min(revisões_vencidas, 5))`.')
    st.caption('Esta pontuação é heurística ajustável, não uma probabilidade de aprovação.')

st.divider()
st.caption('CONTROLE MESTRE · v0.2 visual · Dados privados no seu computador · Preparação SEFAZ-RS')