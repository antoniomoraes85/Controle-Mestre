# PLANO DIRETOR E REGISTRO DE PROGRESSO — CONTROLE MESTRE
Data: 2026-11-07 · Release verificado no repositório: v0.5 · Estado: roadmap, NÃO produto homologado
## Visão e regras
- Objetivo: sistema de decisão educacional para planejamento, execução, erros, reforços, retenção, simulados e melhoria por assunto.
- Usar referências funcionais concorrentes sem copiar layout, software, identidade, textos ou banco de questões.
- Fonte de verdade: GitHub Issues, PRs, testes, changelog e releases; issue aberta não é recurso concluído.
- Manter dados privados, PDFs e credenciais fora do GitHub. Repositório atual é PÚBLICO; rever visibilidade antes da monetização.
- Decisões adaptativas devem ser explicáveis e reversíveis, com confirmação antes de atualizar tarefas.
- Separar dados ausentes de baixo desempenho. Peso de disciplina e incidência precisam de fonte identificável.
- Anki administra FSRS; o CONTROLE MESTRE não deve duplicar revisões ou sobrescrever intervalos sem consentimento.
- Curso Estratégia: guardar links/índice e metadados para uso pessoal autorizado; nunca redistribuir PDFs num SaaS sem licença.
- 25h semanais reservadas aos estudos para SEFAZ-RS, fora do tempo de desenvolvimento.
## Diagnóstico técnico atual
| Área | Estado | Lacuna |
|---|---|---|
| Frontend e backend local v0.5 | Código e testes disponíveis | Não homologado visualmente em Windows |
| Metas, cronômetro, questões | Funcionalidades existentes | Precisam teste com dados representativos e importações |
| Simulados e redações | Módulos existentes da v0.4 | Refinar UX e consistência estatística |
| Motor por assunto | Heurística testada v0.5 | Dados de banca, calibração e avaliação pedagógica |
| Anki | CSV/manual | Sem conector online e anti-dupla contagem validado |
| Estratégia e TEC | Sem API documentada integrada | Integração pessoal e autorizada |
| SaaS e RL | Planejados | Não implementados |
## Fases e critérios de saída
| Fase | Meta | Esforço estimado de engenharia | Gate |
|---|---|---:|---|
| F0 Fundação | confiabilidade do aplicativo pessoal | 30–60h | Windows, teste E2E, backup e CI |
| F1 Núcleo | sistema pedagógico operacional | 60–120h | edital, ciclo, plantões, erros e revisão |
| F2 Integrações | fontes do aluno conectadas | 50–100h | Anki, CSV, cursos sem violar licenças |
| F3 Inteligência | decisões explicáveis e avaliadas | 60–120h | incerteza, relatórios, tutor IA com fontes |
| F4 RL opcional | pesquisa controlada | 40–100h+ | baseline, avaliação offline e aprovação humana |
| F5 SaaS | beta multiusuário seguro | 120–240h+ | autenticação, isolamento, LGPD e operação |
| F6 Marca | posicionamento e lançamento | 25–70h | INPI, domínio, identidade e vendas |
Essas faixas não são promessa de prazo, podem se sobrepor e pressupõem retrabalho. Equivalência de eficiência ao Guruja não é fato demonstrado.
## Backlog-mestre (acompanhar IDs nas Issues)
| ID | Prioridade | Fase | Entrega | Estado inicial |
|---|---|---|---|---|
| CM-001 | P0 | F0 | Segurança do repositório, licença e segredos | Backlog |
| CM-002 | P0 | F0 | Corrigir colisão de porta 8765 com AnkiConnect | Backlog |
| CM-003 | P0 | F0 | Backups, restauração e migrações idempotentes | Backlog |
| CM-004 | P0 | F0 | Testes E2E em Windows e telas desktop/mobile | Backlog |
| CM-005 | P1 | F0 | Contratos API e camadas de serviço independentes | Backlog |
| CM-006 | P1 | F0 | CI, versionamento e release reproduzível | Backlog |
| CM-007 | P1 | F0 | Design system e acessibilidade | Backlog |
| CM-008 | P0 | F1 | Onboarding SEFAZ-RS e meta de 25h | Backlog |
| CM-009 | P0 | F1 | Edital verticalizado versionado | Backlog |
| CM-010 | P1 | F1 | Catálogo de aulas e associação aos assuntos | Backlog |
| CM-011 | P1 | F1 | Ciclos de 30 minutos e modo semanal | Backlog |
| CM-012 | P0 | F1 | Agenda adaptativa com plantões | Backlog |
| CM-013 | P1 | F1 | Diagnóstico e priorização explicáveis | Backlog |
| CM-014 | P1 | F1 | Registro de horas e proveniência de sessões | Backlog |
| CM-015 | P0 | F1 | Classificação de erros por questão | Backlog |
| CM-016 | P0 | F1 | Reforços inteligentes com validação posterior | Backlog |
| CM-017 | P1 | F1 | Fila unificada de revisões | Backlog |
| CM-018 | P1 | F1 | Simulados e análise por prova | Backlog |
| CM-019 | P2 | F1 | Redações e evolução de notas | Backlog |
| CM-020 | P2 | F1 | Atualização legislativa por assunto | Backlog |
| CM-021 | P0 | F2 | AnkiConnect local read-only com consentimento | Backlog |
| CM-022 | P0 | F2 | Deduplicação e reconciliação de FSRS | Backlog |
| CM-023 | P2 | F2 | Propor flashcards com revisão humana | Backlog |
| CM-024 | P0 | F2 | Índice de aulas do Estratégia e links autorizados | Backlog |
| CM-025 | P1 | F2 | Metadados de PDFs locais sem redistribuição | Backlog |
| CM-026 | P1 | F2 | Importar exportações autorizadas de questões | Backlog |
| CM-027 | P1 | F2 | Importar Excel/CSV com origem e idempotência | Backlog |
| CM-028 | P0 | F3 | Estimar domínio de tópicos com incerteza | Backlog |
| CM-029 | P1 | F3 | Matriz de incidência por banca e edital | Backlog |
| CM-030 | P1 | F3 | Tutor IA com RAG e citações de fontes | Backlog |
| CM-031 | P1 | F3 | Relatórios comparativos e diagnósticos | Backlog |
| CM-032 | P2 | F3 | MCP de dados próprios com leitura controlada | Backlog |
| CM-033 | P1 | F4 | Telemetria, versões de política e consentimento | Backlog |
| CM-034 | P1 | F4 | Avaliação offline e baselines de planejamento | Backlog |
| CM-035 | P2 | F4 | Contextual bandit em modo sombra | Backlog |
| CM-036 | P3 | F4 | Experimentos controlados e rollback | Backlog |
| CM-037 | P2 | F5 | PostgreSQL, migração e posse por usuário | Backlog |
| CM-038 | P2 | F5 | Autenticação e autorização multiusuário | Backlog |
| CM-039 | P2 | F5 | LGPD, proteção e exportação de dados | Backlog |
| CM-040 | P3 | F5 | Assinaturas e cobrança via provedor | Backlog |
| CM-041 | P2 | F5 | Observabilidade, suporte e beta fechado | Backlog |
| CM-042 | P1 | F6 | Nome comercial, INPI e domínio | Backlog |
| CM-043 | P3 | F6 | Identidade visual, landing page e comunicação | Backlog |
| CM-044 | P1 | F3 | Avaliação pedagógica e usabilidade com indicadores | Backlog |
## Definição de pronto
1. Funcionalidade implementada, vinculada a issue/PR, com testes que passam.
2. Migrações idempotentes, backups e rollback definidos para qualquer alteração de dados.
3. Interface testada em navegador real no Windows e viewport móvel, com estados vazios, acessibilidade e erros.
4. Fontes/licenças verificadas; não subir conteúdo protegido, credenciais nem dados pessoais.
5. IA: custo, consentimento, fontes, revisão humana e fallback documentados.
6. Recomendação educacional: comparar com baseline sem prometer ganho causal sem experimento.
7. Guia e CHANGELOG atualizados; aceite do proprietário e checklist concluído antes de fechar.
## Controle de execução
- Limite WIP: três issues simultâneas. Fechar por critérios verificáveis.
- Revisar semanalmente o board e indicar: em desenvolvimento, bloqueado, em teste, homologado.
- A cada release: atualizar esta lista e documentação de arquitetura; não marcar concluído com base apenas em teste unitário.
- Issues com IDs CM-001 a CM-044 são a estrutura permanente, não subtítulos decorativos.
## Decisões iniciais
- Continuar no GitHub. Codex para refatoração e testes; Work para pesquisa e QA; Antigravity para UX quando conectado à base versionada.
- Domínio não é pré-requisito de programação: escolher nome após triagem de INPI, registrar cedo após escolha, sem antecipar hospedagem pública.
- RL somente após coleta ética de eventos e avaliação baseline. Começar com contextual bandit em shadow mode, não com treinamento online irrestrito.
## Documentos de referência
- [Benchmark de mercado](BENCHMARK_PLATAFORMAS_2026.md)
- [Integrações, RL e marca](ESTRATEGIA_ANKI_RL_MARCA.md)
- [Estratégia SaaS](ADR-002-CAMINHO-PARA-SAAS.md)
- [Matriz legado](MATRIZ_DE_PARIDADE_E_BACKLOG.md)
## Registro de avanço — release v0.5.1 (07/11/2026)

**Implementação local (não homologada pelo usuário):**

| Issue | Estado de engenharia | Evidência | Bloqueio remanescente |
|---|---|---|---|
| [CM-002](https://github.com/antoniomoraes85/Controle-Mestre/issues/2) | Parcial | App reservou faixa 8771–8780; porta 8765 preservada ao AnkiConnect; testes | Teste simultâneo no Windows |
| [CM-003](https://github.com/antoniomoraes85/Controle-Mestre/issues/3) | Parcial | `backup_manager.py` e testes SQLite | Homologar restauração/rollback com cópia do banco real |
| [CM-004](https://github.com/antoniomoraes85/Controle-Mestre/issues/4) | Bloqueado na inspeção visual | 49 testes Python; sintaxe JS; navegador automatizado bloqueado | E2E desktop/mobile no Windows |
| [CM-010](https://github.com/antoniomoraes85/Controle-Mestre/issues/10) | Parcial | `sources.py` cataloga PDF e permite vínculo manual aula–disciplina–assunto | Mapear curso completo contra edital e validar aula real |
| [CM-024](https://github.com/antoniomoraes85/Controle-Mestre/issues/24) | Parcial | Catálogo local Estratégia sem persistência de texto integral | PDFs do titular ainda não fornecidos nesta etapa |
| [CM-025](https://github.com/antoniomoraes85/Controle-Mestre/issues/25) | Preparatório | Metadados e hash; PyMuPDF opcional para páginas | Análise semântica/OCR dependem de escopo e licenças |
| [CM-026](https://github.com/antoniomoraes85/Controle-Mestre/issues/26) | Parcial | Links Qconcursos e importação CSV do aluno, com prévia | Sem API ou exportação nativa confirmada; testar dados autorizados |
| [CM-027](https://github.com/antoniomoraes85/Controle-Mestre/issues/27) | Parcial | CSV validado e deduplicado por ID/hash | Reconciliar importação com questões lançadas manualmente |

**Critério de conclusão:** issues acima permanecem abertas. Testes automatizados não substituem homologação no Windows e validação pedagógica. O ZIP v0.5.1 preserva o banco do usuário se copiado conforme guia; PDFs e CSVs pessoais não fazem parte do pacote nem do GitHub.

## Registro de avanço — release v0.6.0 (07/11/2026)

**Prioridade escolhida pelo proprietário:** primeiro ciclo com nove disciplinas: Contabilidade Geral, Contabilidade de Custos, Análise das Demonstrações Contábeis, Direito Tributário, Reforma Tributária EC 132/LC 214, Reforma Tributária LC 227/2026, Direito Administrativo, Direito Civil, Direito Constitucional.

| Issue | Avanço verificado em código | Pendência de aceite |
|---|---|---|
| CM-009/010 | Trilha independente com 50 assuntos preliminares e identificação de pasta/aula, sem pesos inventados | Verticalização integral do edital, mapeamento real aula↔assunto |
| CM-011/012/013 | Preview semanal com teoria, questões, Passo e revisão, respeito a plantões e confirmação; tabelas separadas preservam o planejador antigo | Homologar 25h, executar com agenda real, unificar geradores antigos sem apagar IDs |
| CM-014/015/016/017 | Registro explícito de minutos e acertos por tarefa; caderno de erros condicionado a registros | Erros individuais, retestes e política de reforços calibrada |
| CM-021/022 | Conector AnkiConnect local de leitura com resumo por baralho/assunto, snapshots idempotentes e contagens sem somar horas ao histórico | Testar com Anki do titular; sincronização de revisão por evento/revlog e reconciliação com CSV |
| CM-024/025 | Pastas privadas de Teoria e Passo Estratégico; identificação de disciplina ao escanear | Receber PDFs pessoais, vincular tópicos, direitos de indexação avançada |
| CM-026/027 | Importação autorizada de Qconcursos da v0.5.1 preservada | Importação real e anti-dupla-contagem de eventos individuais |

**Testes:** 64 casos de Python + análise sintática do JS em ambiente isolado. **Nenhuma funcionalidade que dependa do Anki/Windows reais foi homologada.** O ZIP distribuído contém 18 pastas vazias e nenhum dado pessoal. Veja [GUIA v0.6.0](../GUIA_CONTROLE_MESTRE_V06.md).
