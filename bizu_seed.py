"""Dados históricos de incidência dos Bizus Estratégicos para SEFAZ-RS.

Somente números factuais e rótulos sintéticos, não reproduz materiais protegidos.
O edital oficial completo e o Passo Estratégico NÃO estão presentes nestes PDFs.
"""
from __future__ import annotations

# (disciplina, aula, ano, página PDF, [(assunto sintético, incidência), ...])
SETS=[
 ('Português','05',2025,3,[('Interpretação de textos',27.39),('Classes de palavras',15.54),('Reescrita de frases',12.86),('Semântica',10.23),('Coesão e coerência',8.41),('Sintaxe',8.41)]),
 ('RLM','06',2025,3,[('Equivalências lógicas',24.59),('Estruturas lógicas',23.77),('Lógica de argumentação',13.93),('Problemas de lógica',8.20),('Raciocínio sequencial',8.20),('Diagramas lógicos',7.38)]),
 ('Direito Empresarial','07',2025,3,[('Registro, escrituração, preposto e nome empresarial',21.93),('Sociedade simples e limitada',14.04),('Sociedade anônima',12.28),('Tipos societários',11.40),('Falência e recuperação',11.40)]),
 ('Direito Civil','08',2025,4,[('Pessoas jurídicas',15.04),('LINDB',12.03),('Pessoas naturais',7.52),('Fatos jurídicos',6.77)]),
 ('Direito Penal','09',2025,3,[('Crimes contra a administração pública',35.25),('Crimes contra a ordem tributária',18.71),('Teoria do crime',15.83)]),
 ('Tecnologia da Informação','10',2025,3,[('PMBOK 7',18.23),('Data warehouse, ETL e BI',13.02),('Modelagem de dados relacional',12.50),('COBIT 2019',7.81)]),
 ('Matemática Financeira','11',2025,3,[('Juros simples e compostos',27.39),('Sistemas de amortização',17.84),('Operações de desconto',14.77),('Análise de investimentos',12.42),('Equivalência de capitais',12.42),('Taxas',9.19)]),
 ('Matemática','12',2025,3,[('Geometria plana',23.41),('Análise combinatória',20.55),('Frações, razões e proporções',15.86),('Porcentagens',12.65),('Conjuntos',10.74),('Operações básicas e resolução de problemas',8.97)]),
 ('Contabilidade Geral','13',2025,3,[('Demonstração do resultado do exercício',9),('Balanço patrimonial e CPC',7),('Equação patrimonial e fatos contábeis',6),('Lançamentos, partidas dobradas e livros',5),('Patrimônio líquido',5),('Demonstração dos fluxos de caixa',5)]),
 ('Análise das Demonstrações Contábeis','14',2025,3,[('Índices de liquidez',37),('Indicadores de endividamento',25),('Análise do capital de giro',22)]),
 ('Contabilidade de Custos','15',2025,3,[('Relação custo-volume-lucro',22),('Tipos de custeio',19),('Apuração do custo de produção',15)]),
 ('Direito Administrativo','16',2025,3,[('Licitações',20.45),('Agentes públicos',13.26),('Organização administrativa',11.75),('Atos administrativos',11.36),('Poderes administrativos',10.98),('Serviços públicos',7.20)]),
 ('Direito Constitucional','17',2025,3,[('Organização do Estado',19.17),('Direitos fundamentais individuais e coletivos',12.68),('Administração pública',12.68),('Poder Legislativo',10.91),('Controle de constitucionalidade',9.44),('Teoria geral da Constituição',7.37)]),
 ('Direito Tributário','18',2025,3,[('Tributos estaduais',12.34),('Princípios tributários',8.60),('Obrigação tributária',8.41),('Simples Nacional',8.04),('Extinção do crédito tributário',5.79)]),
 # O Bizu de Legislação Tributária RS destaca ICMS mas NÃO fornece %.
 ('Legislação Tributária RS I','01',2025,3,[('ICMS: incidência',None),('ICMS: regras e obrigações',None)]),
 # O Bizu de Reforma Tributária informa expressamente que falta amostra histórica.
 ('Reforma Tributária — EC 132 e LC 214','04',2025,3,[('Emenda Constitucional 132/2023',None),('Lei Complementar 214/2025: IBS e CBS',None)])
]

def rows():
    out=[]
    for subject,lesson,year,page,topics in SETS:
        for topic,incidence in topics:
            out.append({
                'subject':subject,'topic':topic,'incidence_pct':incidence,
                'source_type':'Bizu Estratégico',
                'source_reference':f'SEFAZ-RS / Bizu Estratégico / Aula {lesson} / {year}',
                'source_page':page
            })
    return out

def provenance():
    return {
        'producer':'Estratégia Concursos (material do usuário)',
        'scope':'Estatísticas históricas informadas pelos Bizus (bancas e concursos fiscais variados)',
        'not_a_full_notice':True,
        'not_passo_estrategico':True,
        'unknown_percentages_not_zero':True,
        'count':len(rows()),
        'source_notice':'Os percentuais são reproduzidos como fatos estatísticos informados pelas fontes, sem validação da amostragem original e sem garantia para o próximo concurso.'
    }
