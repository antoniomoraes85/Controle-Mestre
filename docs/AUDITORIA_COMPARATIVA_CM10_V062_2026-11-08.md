# CONTROLE MESTRE — Auditoria comparativa do legado 1.0 (2023) e evolução v0.6.2 → v0.7

**Data:** 08/11/2026. **Fonte primária:** “Manual da Plataforma CM — Versão 1.0” (53 páginas), entregue pelo titular; não reproduzir o arquivo no repositório público. **Fontes de código:** `main` v0.6.2; PRs [#46](https://github.com/antoniomoraes85/Controle-Mestre/pull/46) e [#45](https://github.com/antoniomoraes85/Controle-Mestre/pull/45). **Vídeo histórico:** https://youtu.be/NAwtZ3KIxao (referência contextual, não inspecionado quadro a quadro nesta auditoria; YouTube bloqueou a leitura e a ferramenta de transcrição disponível estava sem créditos).

> **Natureza:** especificação de produto e engenharia, NÃO declaração de entrega, homologação ou acurácia de previsão. O manual documenta comportamentos e imagens, não disponibiliza código-fonte ou banco legado. Evidência de tela e alegação de algoritmo devem permanecer distinguidas.

## 1. Veredicto

A versão 1.0 apresentava **densidade operacional e legibilidade de fluxo** importantes: edital verticalizado, prioridade de incidência por assunto visível, rendimento, estado, registro de questões/revisões junto ao tópico; escolha entre semana fixa e ciclo; ciclo com cliques de unidades de 30 minutos, conclusão da rodada e reset visual; tarefas ordenadas por dia, contagem de questões e indicadores de evolução. A versão atual possui motor de dados mais sólido, importações e heurísticas que não existiam no legado, mas ainda tem lacunas de **paridade do fluxo** e da visualização contextual.

**Decisão principal:** integrar e concluir `schedule.py` do PR #46; não criar um segundo planejador de ciclos. Reconstruir o «mapa de assuntos» com incidência auditável, rendimento e ações em contexto. Unificar sessões, tarefas e ciclos como visões da **mesma execução**, evitando dupla contagem. Preservar o banco pessoal por migrações aditivas, backups e testes.

## 2. Matriz de paridade funcional e visual

| Recurso original e páginas | Situação em `main` v0.6.2 | Situação de desenvolvimento | Decisão |
|---|---|---|---|
| Quadro geral com progresso edital, questões, médias e contagem da prova (13–16) | Métricas de minutos, questões, prioridades e progresso; não é paridade exata | Nenhuma homologação Windows final | Reestruturar painel por meta, tarefa, progresso no edital e desempenho comprovado |
| Dois modos: semanal e por ciclos (17–18, 21–24) | Sem seletor funcional equivalente integrado à web | PR #46 contém `schedule.py` com modos `fixed/cycle` | Integrar módulo nas rotas/UI com alternância sem apagar sessões |
| Edital hierarquizado e assuntos (18–20) | `topics` e `fiscal_topics` em estruturas separadas; base de 50 tópicos genéricos e catálogo pessoal de aulas; **não** edital completo | Issue CM-009 | Criar `exam_version` + mapeamento curricular estável; migrar aditivamente |
| Incidência «Nível 1–5», rendimento e status na mesma linha (20, 38) | `topics.incidence` com origem em `source`, heurística de prioridade em `adaptive.py`; interface não apresenta painel analítico equivalente | Issue CM-013 | Preservar badges 1–5, com origem, amostra e incerteza, e separar incidência de prioridade pessoal |
| Botões por assunto: questões e revisões (20, 26, 33–34, 38) | Registros e telas separados | Integrações TEC/Anki parcialmente disponíveis | Contextualizar ações e preservar vínculo de `topic_id` |
| Ciclo com unidades clicáveis de 30min, vermelho→verde (21, 23, 25) | Tela web de ciclos mostra apenas sessões acumuladas e anuncia recurso futuro; tabela `cycles` é histórica/agregada, não tem rodada/unidade | PR #46 introduziu itens, blocos e executor, **não integra API/UX** | Usar `schedule.py`, botões/timer, retomada, idempotência e histórico de rodadas |
| Reset visual e contador de ciclos concluídos (21, 23) | Não concluído na web | Lógica de ciclos do PR #46 precisa verificação integrada | Reset **somente da apresentação**, preservar eventos e rodadas |
| Planejamento com tempo + questões diárias, ordem e tipo (22, 27–35) | Meta semanal, disponibilidade, tarefas, modalidades; ajustes individuais limitados | `schedule.py` inclui fixo, ciclo, escala e exceções | Agenda ordenada, mover/adiar/partir tarefas, sem destruir IDs |
| Questões por assunto, histórico, gráficos seletivos (26, 39–41) | Registro de lote, histórico, métricas em disciplina | Importação TEC/CSV autorizada parcial | Integrar ao assunto, filtros banca/período e identificadores de origem |
| Revisões com histórico vertical e «revisar» contextual (38, 42–44) | Tabela de revisões, fila vencida; agendador D+1/7/15/30 opcional; Anki leitura agregada | Issue CM-017/022 | Fila unificada, agenda vs efetivação, FSRS pertence ao Anki, não dupla contagem |
| Simulados: nota, acertos, erros, chutes, brancos, gráficos (45–49) | Módulo desde v0.4 | Issue CM-018 | Modelar «chutes» como marcador que pode sobrepor acerto/erro, não categoria mutuamente exclusiva sem definição |
| Redações e notas (50–51) | Módulo desde v0.4 | Issue CM-019 | Evolução por critérios, tema e banca; opcional conforme edital |
| Apostilas-guia, dicas e comunidade (4–6) | Catálogo privado de materiais, sem comunidade | Não comprovado fluxo técnico no manual | Não priorizar comunidade; integrar materiais pessoais e guias de uso |

## 3. Incidência dos assuntos — requisito prioritário

### 3.1 O que a versão de 2023 efetivamente demonstrou
A captura na **página 20** mostra `Nível 1`, `Nível 2`, `Nível 4`, `Nível 5`, o rendimento em %, `Concluído/Em andamento` e botões `Revisões/Questões` por assunto. A explicação na **página 19** afirma que a relevância/frequência do tópico orienta prioridade. **O manual não apresenta dados amostrais, fórmula, margens de erro ou calibração dessas probabilidades.** Não afirmar que «Nível 5» implica 80–100% de chance de cair.

### 3.2 Modelo proposto e separação semântica
Para cada item de edital `t` e concurso/banca/versão `e`, exibir **quatro eixos distintos**:

1. **Incidência histórica (dados externos):** taxa observada de aparição em provas comparáveis, quantidade de provas, questões por prova e recorte temporal.
2. **Confiança na estimativa (metadado estatístico):** suficiente/parcial/insuficiente + intervalo, qualidade da correspondência banca/perfil e data de atualização.
3. **Domínio pessoal (dados do aluno):** acertos/n, intervalo de incerteza, retenção/revisões, progresso de conteúdo e última prática.
4. **Prioridade de estudo (decisão):** escore **não probabilístico**, ordem de execução, justificativa e custo estimado.

Uma prioridade de 87/100 **não** significa 87% de probabilidade de cobrança, domínio ou aprovação.

### 3.3 Fonte, método e versionamento
- `exam_version`, `exam_id`, `board`, `exam_year`, `subject_id`, `topic_id`, `syllabus_version`, `source_url/document`, `classification_method`, `analyzed_at`, `reviewer`.
- Estatística `appeared_exams / compared_exams` **por concurso/prova comparável**, com quantidade média/mediana de questões quando observável, normalização por número de questões da disciplina e recorte de banca.
- Separar **frequência de aparição** de **percentual de questões** (denominadores diferentes). Se uma prova tem 5 questões do mesmo tema, isso conta como 1 prova com presença, não como 5 provas.
- Caso estatístico permitisse estimativa probabilística, apresentar como **estimativa condicionada ao conjunto de provas históricas**, com intervalo e limitação; usar suavização parcial (p.ex. beta-binomial) somente com pressupostos documentados e amostra suficiente. Com poucas provas ou mudança de banca, sinalizar «base insuficiente».
- Assunto alterado/revogado por legislação recebe indicador «mudança normativa», sem converter novidade legal em probabilidade numérica fictícia.
- Nunca transplantar a incidência da PRF/Cebraspe 2023 à SEFAZ-RS/FCC. O edital vigente/previsão da banca exigem verificação e atualização de fonte.

### 3.4 Rubrica visual 1–5
Exibir cinco **faixas de evidência** configuráveis conforme distribuição observada e contexto da prova, mas não vincular faixas arbitrárias a “chances de cair” nem exigir cinco classes quando não há dados. Preferir `Nível não aferido` enquanto a base é insuficiente. Tooltip: recorte, números absolutos, fonte, método, confiança.

### 3.5 Prioridade auditável e multidimensional
Uma heurística inicial pode classificar necessidades por: peso oficial do componente; incidência observada quando verificável; déficit de domínio (evitar tratar 0/0 como 0%); esquecimento/sinal de revisão; prerequisitos; novidade legislativa; custo/tempo; utilidade estimada da atividade. Registrar versão dos pesos, componentes e explicações. Executar ablação/calibração e comparar com regras simples antes de RL/MPC.

**Teste mínimo:** 3 provas com 2 presenças do assunto = 2/3 de **provas**; 6 questões no total não transforma 2/3 em 6/3; amostra baixa marca confiança insuficiente. Sem prova observada: «sem dados», nunca «0% de chance».

## 4. Ciclo de estudo clicável: especificação de interação

### 4.1 Fluxo fiel ao legado com melhorias
- Tela **Meu ciclo** com sequência de disciplinas, modalidade, duração planejada, blocos de **30 min configuráveis** e progresso da rodada.
- Marcadores acessíveis, com **rótulos textuais** `Pendente`, `Em andamento`, `Concluído`, `Pausado`; vermelho/verde servem apenas como redundância visual.
- Clique em bloco pendente permite **iniciar cronômetro** ou **declarar execução real**. Não creditar 30 minutos simplesmente porque a cor mudou: requer tempo medido ou confirmação explícita de 30 min efetivos.
- Em parcial (ex.: 18 min), manter bloco em progresso com 12 min residuais; não registrar 30min e 18min simultaneamente.
- Ao completar todas as unidades da rodada, confirmar fechamento **atomicamente** e mostrar `Rodada #n concluída`; criar nova rodada visualmente pendente, sem apagar eventos.
- Botões `Desfazer`/corrigir lançamento com trilha de auditoria, sem decrementar histórico silenciosamente.
- Uma única sessão real alimenta simultaneamente: `horas líquidas`, `meta diária/semanal`, `progresso de bloco` e `histórico`. A projeção de diferentes telas **não cria quatro sessões**.
- Trocar modo Fixo ↔ Ciclos não modifica eventos históricos, não reseta rodada em curso e exige confirmação se mudar a fila futura.

### 4.2 Arquitetura: aproveitar o PR #46
`schedule.py` da branch `feat/cronogramas-identidade-v07` já possui: esquema aditivo `schedule_cycle_items` e `schedule_blocks`; configuração de ciclo/fixo; `add_cycle_item`, `reorder_cycle`, `next_block`, `preview`, `apply`, mecanismos de identificação e registro das sessões. **Ainda não há rotas HTTP e UI correspondentes, conforme PR #46**. O primeiro trabalho é revisão técnica, testes, integração e adaptação visual, **não reescrever o motor**.

### 4.3 Casos de teste obrigatórios
- Duplo clique e repetição de requisição não geram dois registros.
- 30m + 30m conclui rodada de dois blocos; nova rodada aparece pendente e contador aumenta em exatamente 1.
- 18m + 12m conclui um bloco, com 30m reais e sem duplicidade.
- Reiniciar servidor e trocar de modo não muda minutos ou rodada.
- Replanejamento preserva IDs de tarefas concluídas, pausadas e seus vínculos.
- Importar Anki, CSV e planilha repetidos não duplica minutos; registro de revisão no Anki só conta como sessão quando existir vínculo verificável e consentimento.
- Plantão/recuperação/indisponibilidade com meta semanal insuficiente mostram déficit, não atribuem fracasso a descanso planejado.
- Testar edição retroativa, horário local, reabertura, falha de SQLite e rollback em transação.

## 5. UX — preservar didatismo, evitar os defeitos do legado

### Preservar, com transformação própria
- Sidebar com rótulos claros e agrupamento consistente; o legado na página 20 é imediatamente localizável.
- Cabeçalho com **concurso** atual, ciclo ou semana selecionada e progresso.
- Tabela do edital com assunto, incidência, aproveitamento, estado, ações de questões/revisão no **mesmo contexto**.
- Cards semanais/dia e tarefas ordenadas com cor secundária e modalidade explícita (páginas 27–35).
- Semáforo do ciclo e contador de rodadas concluídas (página 21).
- Painel de simulado e evolução temporal, mas com eixos, legendas e filtros legíveis (páginas 45–49).

### Corrigir
- O antigo mistura roxo, azul, verde, vermelho e amarelo sem semântica fixa; definir tokens acessíveis, não depender de cor.
- Colunas densas e fonte pequena dificultariam celular; criar painel expandível por assunto e ações de toque >=44 px.
- Mistura visual de `incidência`, `rendimento` e `conclusão` pode induzir confusão; legenda permanente e tooltip com denominadores.
- Várias abas repetem informações sem continuidade; reduzir passos: `Hoje → Executar → Registrar resultado → Atualizar assunto`.
- Instruções longas do manual devem virar onboarding contextual curto, ajuda inline e estados vazios úteis.
- Animação do peão/identidade não substitui eficiência operacional; respeitar `prefers-reduced-motion` e disponibilizar pular introdução. PR #45 separado do motor pedagógico.

### Estrutura sugerida de navegação
1. **Hoje** — próxima atividade, cronômetro, meta, revisões pendentes.
2. **Planejamento** — modo semanal/ciclos, disponibilidade 24×72, prévia/reorganização.
3. **Meu ciclo** — blocos/rodadas e histórico (acesso direto).
4. **Edital & Prioridades** — tópicos, níveis 1–5, domínio, progressos e justificativa.
5. **Desempenho** — questões, erros, simulados, redações e evolução.
6. **Materiais & Integrações** — Anki, Estratégia/LDI, TEC/Qconcursos, importações autorizadas.
Menus podem ser agrupados sem eliminar recursos existentes.

## 6. Dependências pedagógicas e científicas

- **Estudos e rotina:** aceitar 25h líquidas semanais como meta editável; recorrência de plantões 24×72 e indisponibilidade por data, com teto por dia e proteção do descanso. Dia sem estudo programado não é falha.
- **Currículo:** separar assunto do edital de aula/arquivo. Uma aula pode abordar vários tópicos; um tópico pode existir em múltiplas aulas; vínculo m:n versionado, sem supor equivalência pela semelhança de nomes.
- **Integrações:** preservar Anki como scheduler FSRS; o CONTROLE MESTRE lê dados consentidos, associa tópicos e evita duplicação. TEC/Qconcursos com links e importação autorizada; Estratégia com metadados locais, sem republicação de PDFs.
- **Inteligência:** modelo heurístico interpretável → estimações estatísticas com dados suficientes → testes A/B ou acompanhamento longitudinal → bandit contextual em modo de observação → eventualmente MPC/RL com política segura. Sem prometer ganho ou acurácia sem validação.
- **Simulados:** modelo de nota, acertos, erros, brancos; `chute` precisa ser definido como marca de confiança sobre questão, não necessariamente partição exclusiva. Comparar desempenho por banca e assunto com comparabilidade de provas.
- **Revisão:** o manual anuncia agendamento automático (p. 43), mas as telas demonstram claramente registro por clique (pp. 38, 42–44). Não inferir fórmula de scheduler legado que não foi apresentada.

## 7. Ordem de execução (sem duplicar issues)

| Ordem | Issue existente | Entregável e gate verificável |
|---:|---|---|
| 0 | CM-003/004 e PR #46 | Backup/restore com base sintética; testes de `schedule.py`, migração, integração e abertura Windows; PR #45 dependente em branch distinta; **não fazer merge automático** |
| 1 | CM-011 | Rotas de ciclo + interface 30min + histórico de rodadas, com sessão única e 10 cenários de teste |
| 2 | CM-009 | Edital verticalizado por versão, árvore completa e relacionamento seguro aula↔tópico |
| 3 | CM-013 | Badges de incidência 1–5, painel de evidências, ranking explicável, dados ausentes e testes com diferentes denominadores |
| 4 | CM-012/014 | Drag opcional, mover/adiar, execução parcial, orçamento real 24×72 e replanejamento preservando ID |
| 5 | CM-017/015/016 | Revisões contextuais, caderno de erros por questão, vínculo fonte/resultado e fila sem duplicidade |
| 6 | CM-007 | Consolidação visual desktop/celular, acessibilidade, nomenclatura e testes de UX |
| 7 | CM-018/019 | Gráficos de avaliações, modelos de notas e filtros contextualizados |
| 8 | CM-021/022/024/026 | Ajustes das integrações Anki/TEC/Estratégia com identidade e consentimento, após dominar o fluxo local |

**Regra de execução:** limite WIP de 3 issues; uma PR por tema; critérios de aceite com evidências; artefatos privados não vão ao repositório; liberar somente após testes e homologação do usuário. A auditoria não muda código por si só.

## 8. Experimentos e métricas para demonstrar melhoria

- **UX:** tempo até localizar próximo tópico, número de cliques até sessão completa, taxa de tarefas concluídas com registro correto, erros de lançamento, uso em tela 390px e 1440px.
- **Dados:** nenhuma duplicação de minutos ou questões após importação/replanejamento, taxa de tópicos corretamente mapeados, proporção de incidências com fonte, inconsistência entre planejado e executado.
- **Estudos:** cobertura ponderada do edital e horas úteis, acurácia de acertos **em questões comparáveis**; medir retenção em testes com atraso sem tomar número de cartões como proxy de domínio.
- **Planejamento:** plano dentro das 25h/semana e tetos reais, qualidade de recuperação de tarefas não feitas, prioridades explicadas.
- **IA:** demonstrar primeiro benefício sobre baseline «peso de matéria + revisões vencidas», com incerteza e auditoria; evitar incentivo a estudar tópicos apenas porque são fáceis ou têm mais questões.

## 9. Lacunas a não mascarar

1. Não há código/banco original 2023; não é possível confirmar detalhes de persistência, fórmula de incidência ou engine de revisão do legado somente pelo manual.
2. O vídeo foi informado como fonte adicional, mas **não foi assistido/transcrito nesta auditoria**; YouTube limitou acesso e a integração de transcrição indicou ausência de créditos, sem cobrança. A análise visual baseou-se nas imagens do PDF.
3. `main` v0.6.2 e PR #46 são estados **diferentes**. Um recurso de `schedule.py` não está disponível no painel `main` sem integração/merge/homologação.
4. Fontes comparáveis de provas SEFAZ-RS, novo edital e incidências calibradas **não foram fornecidas/validadas nesta análise**. O sistema deverá apresentar `sem dados` em vez de fabricar pesos, percentuais ou previsão.

**Conclusão:** preservar o conteúdo funcional de 2023, mas elevar a precisão metodológica e evitar dupla contagem. Prioridade efetiva: **ciclos interativos → edital contextualizado → incidência rastreável → otimização auditável**, com UX coerente e integração ao motor já existente.
