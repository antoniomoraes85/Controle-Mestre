"""Vinculação conservadora de PDFs por pasta, curso e catálogo pessoal.

Aplica APENAS campos vazios, nunca substitui vínculos manuais.
Não inventa disciplinas nem assuntos sem fonte inequívoca.
"""
from __future__ import annotations
import re
from collections import defaultdict,Counter
from pathlib import PurePosixPath
from core import norm, all_rows, DEFAULT_SUBJECTS

COURSE=re.compile(r'curso[-_\s]*(\d{4,10})',re.I)

def course_id(name):
    m=COURSE.search(str(name or ''))
    return m.group(1) if m else None

def folder_subject(relative_path):
    # A inferência exige nome EXATO da disciplina em um componente de pasta.
    folders=list(PurePosixPath(str(relative_path)).parts[:-1])
    subjects=[s[0] for s in DEFAULT_SUBJECTS]
    for folder in reversed(folders):
        raw=norm(folder)
        matches=[s for s in subjects if norm(s)==raw or
                 re.search(r'(?<![a-z])'+re.escape(norm(s))+r'(?![a-z])',raw)]
        # Ambiguidade explícita: "Direito Tributário e Constitucional", p.ex.
        if len(matches)==1:return matches[0]
    return ''

def infer(c,apply=True):
    from sources import prepare,detect_type
    from lesson_catalog import lessons
    prepare(c)
    rows=all_rows(c,"""SELECT id,relative_path,file_name,subject,topic,lesson,material_type
         FROM study_materials WHERE status='Disponível' ORDER BY id""")
    course_anchors=defaultdict(Counter)
    for item in rows:
        cid=course_id(item['file_name'])
        if cid and item['subject']:
            course_anchors[cid][item['subject']]+=1
        # Evidência explícita de pasta é independente de vínculo prévio.
        folder=folder_subject(item['relative_path'])
        if cid and folder:course_anchors[cid][folder]+=2
    course_subject={}
    for cid,counts in course_anchors.items():
        if len(counts)==1:
            subject,count=counts.most_common(1)[0]
            if count>=2:course_subject[cid]=subject
    indexed=defaultdict(list)
    for row in lessons():
        indexed[(norm(row['disciplina']),norm(row['aula']))].append(row['assunto'])
    result={'updated':0,'subjects_assigned':0,'topics_assigned':0,
            'types_assigned':0,'remaining_unlinked':0,'review':[]}
    for item in rows:
        subject=item['subject'] or folder_subject(item['relative_path'])
        if not subject:
            subject=course_subject.get(course_id(item['file_name']),'')
        lesson=item['lesson']
        topic=item['topic']
        if subject and lesson and not topic:
            candidates=indexed.get((norm(subject),norm(lesson)),[])
            if len(candidates)==1:topic=candidates[0]
        typ=item['material_type']
        identified=detect_type(str(PurePosixPath(item['relative_path']).parent)+' '+item['file_name'])
        if typ=='Teoria' and identified!='Teoria':
            typ=identified
        if not item['subject'] and not subject:
            result['remaining_unlinked']+=1
            if len(result['review'])<20:result['review'].append({'id':item['id'],'file':item['file_name'],'reason':'Disciplina sem evidência'})
        elif not topic:
            result['remaining_unlinked']+=1
            if len(result['review'])<20:result['review'].append({'id':item['id'],'file':item['file_name'],'reason':'Assunto sem correspondência na aula'})
        if subject!=item['subject'] or topic!=item['topic'] or typ!=item['material_type']:
            result['updated']+=1
            result['subjects_assigned']+=bool(subject and not item['subject'])
            result['topics_assigned']+=bool(topic and not item['topic'])
            result['types_assigned']+=typ!=item['material_type']
            if apply:
                c.execute("""UPDATE study_materials SET subject=?,topic=?,material_type=?
                             WHERE id=?""",(subject,topic,typ,item['id']))
    if apply:c.commit()
    return result
