"""CONTROLE MESTRE — painel pessoal, offline/local-first.
Inicie com: streamlit run app.py
"""
import csv
import io
import os
from datetime import date, datetime, timedelta

import streamlit as st
from core import (ROOT, connect, all_rows, metric_data, subject_metrics, get_days,
                  DAY_CAPS, METHODS, add_session, add_questions, save_topic, save_day,
                  generate_plan, backup_sqlite, export_json, import_excel, import_anki_csv, number)

st.set_page_config(page_title='CONTROLE MESTRE | Central de Estudos',page_icon='🎯',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*=st-] { font-family:Inter,Arial,sans-serif; }
.stApp {background: #0B1220; color:#E2E8F0;}
[data-testid="stSidebar"] {background: #111B30; border-right:1px solid #243249;}
[data-testid="stMetric"] {background:#142239; border:1px solid #293951; border-radius:16px; padding:17px 20px; min-height:112px;}
[data-testid="stMetricLabel"] p {font-size:.78rem; color:#AABCD4; font-weight:700;}
[data-testid="stMetricValue"] {color:#F8FAFC;}
[data-testid="stVerticalBlockBorderWrapper"] {border-color:#2B3D59;}
.stButton>button[kind="primary"] {background:#08A88A; color:#041D1A; border-color:#08A88A; font-weight:800;}
h1,h2,h3 {letter-spacing:-.035em;}
h1 {font-size:2.35rem !important; margin-bottom:.1em;}
h2 {font-size:1.3rem !important;}
.cm-sub {color:#9CB0CB;font-size:1rem;margin-bottom:1rem;}
.cm-chip {padding:.27em .65em;border:1px solid #315477;background:#15384D;border-radius:999px;color:#8BE4D3;font-size:.73rem;letter-spacing:.08em;font-weight:800;}
.cm-micro {color:#91A8C7;font-size:.82rem;}
</style>''',unsafe_allow_html=True)

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
    st.markdown('<span class="cm-chip">CONTROLE MESTRE · EDIÇÃO PESSOAL</span>',unsafe_allow_html=True)
    st.title(title);st.markdown(f'<div class="cm-sub">{subtitle}</div>',unsafe_allow_html=True)
def plot(values,mark,x,y,color='#18C7A5',height=260,title=None):
    if not values: st.info('Sem dados registrados para este gráfico.');return
    enc={'x':{'field':x,'type':'ordinal','axis':{'labelColor':'#BFD1E4','title':None}},
         'y':{'field':y,'type':'quantitative','axis':{'labelColor':'#BFD1E4','title':None}},
         'tooltip':[{'field':x,'type':'nominal'},{'field':y,'type':'quantitative'}]}
    spec={'mark':{'type':mark,'color':color,'cornerRadiusTopLeft':4,'cornerRadiusTopRight':4},'encoding':enc,
          'data':{'values':values},'height':height,'background':'transparent',
          'config':{'view':{'stroke':None},'axis':{'gridColor':'#22344B','domainColor':'#31445D'}}}
    st.vega_lite_chart(spec,use_container_width=True)

st.sidebar.markdown('## ◈ CONTROLE MESTRE')
st.sidebar.caption('Planejar • Executar • Medir • Melhorar')
sections=['Visão geral','Estudar hoje','Planejamento semanal','Ciclos de estudos','Disciplinas e assuntos','Questões e erros','Revisões e Anki','Importação','Configurações']
page=st.sidebar.radio('Navegação',sections,label_visibility='collapsed')
st.sidebar.divider()
st.sidebar.caption('DADOS PRIVADOS · SALVOS NESTE COMPUTADOR')
st.sidebar.caption('SEFAZ-RS · Plano provisório, ajustável ao próximo edital.')

if page=='Visão geral':
    banner('Painel executivo','Prioridades, produtividade e lacunas reais — sem métricas inventadas.')
    m=metric_data(c);rank=subject_metrics(c)
    a,b,d,e=st.columns(4)
    a.metric('Horas líquidas · semana',rs(m['weekly_minutes']/60)+' h',delta=f'{int(m["weekly_minutes"])} / {m["weekly_target"]} min',delta_color='off')
    b.metric('Aderência semanal',perc(m['adherence']))
    d.metric('Questões · semana',str(m['week_questions']['total']),delta=f'{m["week_questions"]["correct"]} acertos',delta_color='off')
    e.metric('Rendimento · 30 dias',perc(m['last30_questions']['rate']))
    a,b,d,e=st.columns(4)
    a.metric('Horas líquidas · mês',rs(m['monthly_minutes']/60)+' h')
    b.metric('Questões · mês',str(m['month_questions']['total']))
    d.metric('Revisões vencidas',str(m['overdue_reviews']))
    e.metric('Cartões Anki · semana',str(m['anki_cards']))
    if rank:
        leader=rank[0]
        st.info('**Recomendação de prioridade:** ' + leader['disciplina'] + '. ' +
                (f'Resolver questões e reforçar os erros: taxa atual de {perc(leader["rendimento"])}.' if leader['questoes']>=15 and leader['rendimento'] is not None else 'Iniciar diagnóstico com questões e registrar desempenho, pois ainda faltam evidências suficientes.'))
    st.divider()
    col1,col2=st.columns([1.4,1])
    with col1:
        st.subheader('Atividade das últimas 4 semanas')
        first=date.today()-timedelta(days=27)
        act={x['day']:round(x['mins']/60,2) for x in all_rows(c,'SELECT day,SUM(minutes) mins FROM sessions WHERE day>=? GROUP BY day',(first.isoformat(),))}
        vals=[{'dia':(first+timedelta(days=i)).strftime('%d/%m'),'horas':act.get((first+timedelta(days=i)).isoformat(),0)} for i in range(28)]
        plot(vals,'bar','dia','horas')
        st.caption('Tempo do Anki aparece separado e não é somado às horas líquidas para evitar contagem dupla.')
    with col2:
        st.subheader('Prioridades calculadas')
        st.dataframe([{'Disciplina':r['disciplina'],'Necessidade':r['prioridade'],
                      'Acertos':perc(r['rendimento']),'Questões':r['questoes']} for r in rank[:8]],
                     hide_index=True,use_container_width=True)
        st.caption('Ordenação por peso, desempenho, falta de estudo, progresso e revisões vencidas.')
    col1,col2=st.columns([1,1])
    with col1:
        st.subheader('Horas por disciplina')
        plot([{'disciplina':r['disciplina'][:24],'horas':r['horas']} for r in rank if r['horas']>0][:10],
             'bar','disciplina','horas',height=245)
    with col2:
        st.subheader('Próximas atividades')
        tasks=all_rows(c,"SELECT day,subject,topic,method,target_minutes FROM plans WHERE status='Pendente' AND day>=? ORDER BY day,priority DESC LIMIT 7",(date.today().isoformat(),))
        if tasks:st.dataframe(tasks,hide_index=True,use_container_width=True)
        else:st.info('Acesse Planejamento semanal e gere seu primeiro plano.')

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
st.caption('CONTROLE MESTRE · MVP local v0.1 · Dados no seu computador · Não reproduz código, identidade visual ou conteúdo proprietário de terceiros.')