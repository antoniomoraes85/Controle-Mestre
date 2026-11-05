"""Apresentação do CONTROLE MESTRE: componentes visuais sem dependências adicionais.

Toda variável interpolada em HTML de usuário passa por escape; os componentes
são somente de leitura e os registros continuam no SQLite.
"""
from html import escape


def safe(value):
    return escape(str(value), quote=True)


STYLES = """
<style>
:root { --cm-bg:#0B1120; --cm-card:#131F33; --cm-border:#263751;
        --cm-text:#F1F6FE; --cm-muted:#A9BCD4; --cm-green:#24D6A5;
        --cm-blue:#80AFFF; --cm-amber:#FFCA72; }
html, body, [class*="st-"] {font-family:system-ui,-apple-system,'Segoe UI',Arial,sans-serif;}
.stApp, [data-testid="stAppViewContainer"] {background:#0B1120 !important;color:#F1F6FE !important;}
[data-testid="stHeader"] {background:rgba(11,17,32,.96) !important;box-shadow:none !important;}
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer {display:none !important;}
[data-testid="stAppViewBlockContainer"] {padding-top:3.35rem; padding-bottom:3.5rem; max-width:1370px;}
[data-testid="stSidebar"] {background:#101A2D !important;border-right:1px solid #283650 !important;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stSidebar"] label, [data-testid="stSidebar"] label p,
[data-testid="stSidebar"] .stCaption {color:#DCE7F7 !important;opacity:1 !important;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {gap:.25rem !important;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label {
    border-radius:10px; padding:.54rem .65rem; transition:background .14s ease;
    border:1px solid transparent; background:transparent;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:hover {background:#1A2D46;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
    background:#143E42 !important; border-color:#276A69 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p {color:#86FFE0 !important;font-weight:700;}
[data-testid="stSidebar"] hr {border-color:#283650 !important;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color:#9BB0C9 !important;}
h1,h2,h3,h4 {color:#F1F6FE !important;letter-spacing:-.025em;}
h1 {font-size:2rem !important;font-weight:800 !important;margin-bottom:.2rem !important;}
h2 {font-size:1.34rem !important; font-weight:750 !important;}
h3 {font-size:1.12rem !important;font-weight:750 !important;}
p, [data-testid="stMarkdownContainer"] p {color:#C7D7EC;}
[data-testid="stCaptionContainer"] p {color:#A8BCD7 !important;}
[data-testid="stMetric"] {background:#131F33 !important;border:1px solid #263751;border-radius:16px;padding:18px !important;}
[data-testid="stMetricLabel"] p {color:#B3C7E0 !important;}
[data-testid="stMetricValue"] {color:#F1F6FE !important;}
[data-testid="stAlert"] {background:#14263B !important;color:#DCEBFA !important;border:1px solid #28435A;border-radius:13px;}
[data-testid="stAlert"] p {color:#DCEBFA !important;}
[data-testid="stDataFrame"] {border:1px solid #30415A;border-radius:12px;overflow:hidden;}
[data-testid="stVerticalBlockBorderWrapper"] {border-color:#2A3C57 !important;}
.stButton>button {border-radius:10px !important;border:1px solid #3C5676 !important;color:#EDF7FE !important;
                  background:#1B304D !important;font-weight:650 !important; min-height:2.6rem;}
.stButton>button:hover {border-color:#27D4AB !important;color:#FFFFFF !important;}
.stButton>button[kind="primary"] {background:#24D6A5 !important;color:#06291E !important;border-color:#24D6A5 !important;font-weight:800 !important;}
[data-testid="stForm"], [data-testid="stExpander"] {background:#111C2E;border:1px solid #273952;border-radius:14px;}
[data-testid="stWidgetLabel"] p {color:#D1E1F5 !important;}
input,textarea {color:#F1F6FE !important;}
.cm-brand {padding:8px 1px 14px;}
.cm-logo {display:flex;align-items:center;gap:11px;margin-bottom:7px;}
.cm-logo-mark {width:38px;height:38px;border-radius:12px;display:grid;place-items:center;
               background:linear-gradient(145deg,#22D5AA,#328CE3);color:#062034;font-size:1rem;font-weight:900;}
.cm-logo-title {font-size:1.18rem;line-height:1.18;font-weight:850;letter-spacing:.02em;color:#F5FAFF;}
.cm-brand small {display:block;color:#9FB5D1;font-size:.76rem;letter-spacing:.035em;margin-left:49px;}
.cm-eyebrow {display:inline-block;padding:5px 11px;border:1px solid #2B655E;border-radius:999px;
             background:#133930;color:#7DF3CF;font-weight:800;font-size:.69rem;letter-spacing:.10em; margin-bottom:9px;}
.cm-sub {color:#ACBFDA;font-size:.97rem;margin-top:.2rem;margin-bottom:1.4rem;line-height:1.5;}
.cm-section {font-size:1.15rem;color:#F2F7FF;font-weight:790;margin:.55rem 0 .75rem;letter-spacing:-.025em;}
.cm-card {min-height:130px;padding:18px 19px;background:#141F33;border:1px solid #2C3C56;border-radius:16px;
          box-shadow:0 2px 12px rgba(0,0,0,.12);}
.cm-card-label {color:#B7CAE1;font-size:.81rem;font-weight:650;line-height:1.38;}
.cm-card-value {color:#F7FAFF;font-size:1.9rem;font-weight:810;letter-spacing:-.03em;line-height:1.36;margin:7px 0 8px;}
.cm-card-note {color:#A8BAD1;font-size:.75rem;}
.cm-card-note strong {color:#E6F9FA;}
.cm-card.green {border-top:3px solid #27DBA9;}
.cm-card.blue {border-top:3px solid #73A9FF;}
.cm-card.amber {border-top:3px solid #FFCA72;}
.cm-card.neutral {border-top:3px solid #62738D;}
.cm-progress-box {background:#141F33;border:1px solid #293B57;border-radius:16px;padding:17px 20px;margin:.1rem 0 1.1rem;}
.cm-progress-top {display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px;}
.cm-progress-label {font-weight:750;color:#F1F6FE;font-size:.9rem;}
.cm-progress-value {color:#7FE9C8;font-size:.88rem;font-weight:750;}
.cm-track {height:9px;background:#2A3950;border-radius:999px;overflow:hidden;}
.cm-track-fill {height:100%;background:linear-gradient(90deg,#12B28E,#2CE2AD);border-radius:999px;}
.cm-note {background:linear-gradient(108deg,#173C47 0%,#14283F 100%);
          border:1px solid #2B696D;border-radius:15px;padding:17px 20px;margin:.3rem 0 1.25rem;}
.cm-note-kicker {font-size:.70rem;letter-spacing:.10em;font-weight:800;color:#6FF0C5;margin-bottom:6px;}
.cm-note-title {font-size:1.05rem;font-weight:800;color:#F2FAFF;}
.cm-note-body {color:#C8DFEC;font-size:.85rem;margin-top:5px;line-height:1.48;}
.cm-empty {background:#121F34;border:1px dashed #385471;border-radius:14px;padding:23px 18px;min-height:145px;
           display:flex;flex-direction:column;justify-content:center;}
.cm-empty-title {font-size:.94rem;font-weight:800;color:#DCE8F8;margin-bottom:7px;}
.cm-empty-msg {color:#AFC2DC;font-size:.84rem;line-height:1.55;}
.cm-priority-list {background:#131F33;border:1px solid #2B3D55;border-radius:14px;padding:5px 14px;}
.cm-priority-row {padding:13px 0;border-bottom:1px solid #293A52;}
.cm-priority-row:last-child {border-bottom:0;}
.cm-priority-head {display:flex;align-items:center;justify-content:space-between;gap:12px;}
.cm-priority-title {color:#E9F2FF;font-size:.85rem;font-weight:720;min-width:0;}
.cm-priority-score {color:#84E6CB;font-size:.79rem;font-weight:750;white-space:nowrap;}
.cm-priority-foot {display:flex;align-items:center;gap:9px;margin-top:8px;}
.cm-priority-track {height:5px;border-radius:5px;background:#2D415D;flex:1;overflow:hidden;}
.cm-priority-fill {height:100%;background:linear-gradient(90deg,#207B92,#22D7A7);border-radius:5px;}
.cm-priority-hint {font-size:.70rem;color:#A9BFD9;white-space:nowrap;}
.cm-task {display:flex;justify-content:space-between;gap:14px;border-bottom:1px solid #2B3D55;padding:13px 0;}
.cm-task:last-child {border-bottom:0;}
.cm-task strong {color:#E8F4FF;font-size:.87rem;}
.cm-task small {display:block;color:#B0C4DD;font-size:.76rem;margin-top:4px;}
.cm-task-time {white-space:nowrap;color:#84E6CB;font-weight:750;font-size:.84rem;}
.cm-task-box {background:#131F33;border:1px solid #2B3D55;padding:6px 15px;border-radius:14px;}
@media (max-width:1024px) {[data-testid="stAppViewBlockContainer"]{padding-top:2.7rem;}}
@media (max-width:720px) {.cm-card{min-height:108px;padding:14px;} .cm-card-value{font-size:1.65rem;}
 .cm-progress-top{flex-direction:column;align-items:flex-start;} h1{font-size:1.65rem!important;}}
</style>
"""


def card(label, value, note, accent="green"):
    if accent not in ("green", "blue", "amber", "neutral"):
        accent = "neutral"
    return (f'<div class="cm-card {accent}"><div class="cm-card-label">{safe(label)}</div>'
            f'<div class="cm-card-value">{safe(value)}</div>'
            f'<div class="cm-card-note">{safe(note)}</div></div>')


def progress(label, minutes, target):
    ratio = min(100.0, max(0.0, (100.0 * float(minutes) / float(target)) if target else 0.0))
    return (f'<div class="cm-progress-box"><div class="cm-progress-top">'
            f'<span class="cm-progress-label">{safe(label)}</span>'
            f'<span class="cm-progress-value">{minutes/60:.1f} de {target/60:.1f} h</span>'
            f'</div><div class="cm-track"><div class="cm-track-fill" style="width:{ratio:.1f}%"></div>'
            f'</div></div>')


def note(kicker, title, message):
    return (f'<div class="cm-note"><div class="cm-note-kicker">{safe(kicker)}</div>'
            f'<div class="cm-note-title">{safe(title)}</div>'
            f'<div class="cm-note-body">{safe(message)}</div></div>')


def empty(title, message):
    return f'<div class="cm-empty"><div class="cm-empty-title">{safe(title)}</div><div class="cm-empty-msg">{safe(message)}</div></div>'


def priorities(rows, rate_display):
    if not rows:
        return empty('Nenhuma disciplina cadastrada', 'Cadastre disciplinas para obter prioridades.')
    maximum = max(float(r['prioridade']) for r in rows) or 1.0
    parts = ['<div class="cm-priority-list">']
    for r in rows[:6]:
        score = float(r['prioridade'])
        width = max(2.0, min(100.0, 100.0 * score / maximum))
        hint = f'{r["questoes"]} questões · {rate_display(r["rendimento"])}' if r['questoes'] else 'Aguardando diagnóstico'
        parts.append(f'<div class="cm-priority-row"><div class="cm-priority-head">'
                     f'<div class="cm-priority-title">{safe(r["disciplina"])}</div>'
                     f'<div class="cm-priority-score">{score:.1f}</div></div>'
                     f'<div class="cm-priority-foot"><div class="cm-priority-track"><div class="cm-priority-fill" style="width:{width:.1f}%"></div></div>'
                     f'<div class="cm-priority-hint">{safe(hint)}</div></div></div>')
    parts.append('</div>')
    return ''.join(parts)


def tasks(rows):
    if not rows:
        return empty('Nenhuma atividade programada', 'Configure sua disponibilidade e gere o planejamento da semana.')
    parts = ['<div class="cm-task-box">']
    for row in rows[:5]:
        on = str(row['day'])
        date_txt = on[8:10] + '/' + on[5:7] if len(on) >= 10 else on
        parts.append(f'<div class="cm-task"><div><strong>{safe(row["subject"])}</strong>'
                     f'<small>{safe(date_txt)} · {safe(row["method"])}'
                     + (f' · {safe(str(row["topic"])[:65])}' if row['topic'] else '')
                     + f'</small></div><div class="cm-task-time">{int(row["target_minutes"])} min</div></div>')
    parts.append('</div>')
    return ''.join(parts)