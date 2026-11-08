"""Isolamento hermético dos testes: nenhum arquivo privado do titular é lido.

Antes, os testes dependiam de (a) `dados/catalogo/aulas_primeiro_ciclo.csv`, que é privado e
não existe no GitHub, e (b) da pasta real `MATERIAL TEÓRICO`, encontrada ao lado do projeto
(352 PDFs), o que alterava as contagens. Aqui o catálogo é sintético e as pastas de PDFs
apontam para diretórios temporários. Nenhum PDF real é aberto, movido ou alterado.
"""
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch

import lesson_catalog
import sources

# Mesma forma do catálogo real (125 aulas, Direito Civil pendente), conteúdo fictício.
SYNTHETIC_COUNTS = {
    'Contabilidade Geral': 33, 'Contabilidade de Custos': 12,
    'Análise das Demonstrações Contábeis': 8, 'Direito Tributário': 23,
    'Reforma Tributária — EC 132 e LC 214': 10, 'Reforma Tributária — LC 227': 11,
    'Direito Administrativo': 10, 'Direito Civil': 0, 'Direito Constitucional': 18,
}


def synthetic_catalog_rows():
    rows = []
    for subject, n in SYNTHETIC_COUNTS.items():
        if subject == 'Contabilidade Geral':
            lessons = [(f'Aula {i:02d}', f'Tema sintético {i:02d}') for i in range(32)]
            lessons[29] = ('Aula 29', 'CPC 48 - Instrumentos Financeiros')
            lessons[0] = ('Aula 00', 'Conceitos, objetivos e finalidades da contabilidade')
            lessons.insert(2, ('Aula 01 - Parte II', 'Tema sintético 01 (parte II)'))
        else:
            lessons = [(f'Aula {i:02d}', f'Tema sintético {i:02d}') for i in range(n)]
        rows.extend((subject, a, t) for a, t in lessons)
    return rows


def write_synthetic_catalog(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['disciplina', 'aula', 'assunto'])
        w.writerows(synthetic_catalog_rows())
    return path


def isolate(testcase):
    """Aplica catálogo sintético e raízes de PDF temporárias; desfaz ao final do teste."""
    tmp = tempfile.TemporaryDirectory()
    testcase.addCleanup(tmp.cleanup)
    root = Path(tmp.name)
    catalog = write_synthetic_catalog(root / 'catalogo' / 'aulas_primeiro_ciclo.csv')
    for target, attr, value in (
        (lesson_catalog, 'CATALOG_FILE', catalog),
        (sources, 'PDF_ROOT', root / 'materiais'),
        (sources, 'QC_ROOT', root / 'qconcursos'),
        (sources, 'TEC_ROOT', root / 'tec'),
    ):
        p = patch.object(target, attr, value)
        p.start()
        testcase.addCleanup(p.stop)
    p = patch.object(sources, 'external_root', lambda c: None)
    p.start()
    testcase.addCleanup(p.stop)
    return root

