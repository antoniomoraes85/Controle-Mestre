# CONTROLE MESTRE — matriz de paridade e backlog

Atualizada: 2026-11-04. Fonte histórica: manual CM 1.0 (53 páginas). Base comparada: MVP v0.1 Streamlit/SQLite documentado no repositório. **Estado é documental: não implica que a interface atual foi validada em navegador.**

| Capacidade | Original 1.0 | MVP v0.1 | Ação prioritária |
|---|---|---|---|
| Quadro geral (horas, questões, rendimento) | Sim, com outros indicadores | Parcial | Integrar progresso do edital, simulado, redação e contagem da prova |
| Semanas fixas e ciclos como modos explícitos | Sim | Parcial | Seletor configurável, sem perda de dados |
| Ciclo de 30 min com rodada e reset visual | Sim | Parcial | Entidade cycle_round + cycle_unit, contagem persistente |
| Disponibilidade semanal por dia e tarefas ordenadas | Sim | Parcial | UX com cards, edição de ordem/duração, categorias de dia |
| Catálogo de assuntos com incidência e conclusão | Sim | Sim, base de assuntos | Versionamento por edital; seleção granular e origem da incidência |
| Questões por assunto e evolução | Sim | Sim, registro básico | Histórico editável e correções com trilha de auditoria |
| Revisões por assunto | Sim | Sim, D+1/7/15/30 | Relacionar revisão real ao agendamento e ao Anki |
| Simulados, histórico e gráficos | Sim | Não identificado como módulo completo | Implementar dados e telas, validação de totais |
| Redações, notas e evolução | Sim | Não identificado como módulo completo | Implementar rubrica parametrizável, notas e histórico |
| Material guiado e comunidade | Mencionado | Não | Não priorizar sem requisitos/artefatos |
| Integração Excel + VBA | Não comprovada | Importação manual | Corrigir mapeamentos, rastrear idempotência, exportar |
| Integração Anki | Não comprovada | CSV agregado manual | Conector local opt-in com AnkiConnect (se disponível) |
| Planejamento adaptativo por desempenho | Parcial/manual | Heurístico | Calibrar recomendações, explicar motivos, medir utilidade |
| Plantões e recuperação | Não comprovado | Limites por tipo de dia | Regras configuráveis por usuário e calendário |
| Multiusuário e pagamento | Site com contas no legado | Não | Só após segurança, LGPD e testes com usuários |

## P0 — consistência e uso pessoal

- [ ] P0.1: importar bases legadas preservando as origens, sem contaminar métricas realizadas com planejadas.
- [ ] P0.2: documentar origem, unidade e denominador de cada KPI.
- [ ] P0.3: converter a agenda diária num fluxo de execução de no máximo três cliques por tarefa.
- [ ] P0.4: criar/editar tarefa sem apagar histórico; testar geração de plano com plantão e pós-plantão.
- [ ] P0.5: introduzir rotina de backup/restauração com teste de integridade, e exportação pessoal.
- [ ] P0.6: corrigir eventuais discrepâncias entre DB e arquivos importados através de auditoria de origem.

## P1 — paridade das funções do CM 1.0

- [ ] P1.1: modo **Semanal** ou **Por ciclos**, independente do modelo de acompanhamento.
- [ ] P1.2: blocos de 30 minutos, estados por rodada, reinício visual e contador imutável de rodadas encerradas.
- [ ] P1.3: tarefas sequenciais com duração, modalidade e questões-alvo, respeitando disponibilidade.
- [ ] P1.4: tela **Simulados** com nota, total, acertos, erros, chutes e branco; gráficos e histórico editável.
- [ ] P1.5: tela **Redações** com nota máxima/obtida, banca, tema, rubrica e histórico.
- [ ] P1.6: painel com indicadores integrados, progresso por assunto e data da prova configurável.
- [ ] P1.7: lista de revisões por assunto e ligações com tarefa e importações.

## P2 — diferenciais do CONTROLE MESTRE atual

- [ ] P2.1: integração opt-in com Anki sem duplicidade de minutos ou revisões.
- [ ] P2.2: planilha Excel → importação incremental por identidade de linha + atualização segura.
- [ ] P2.3: sugestão semanal baseada em prioridade, rendimento com confiança amostral e histórico de revisões.
- [ ] P2.4: detalhamento de metas por aula/páginas somente quando a referência do curso estiver disponível.
- [ ] P2.5: planejamento por escala, feriados e indisponibilidade real.
- [ ] P2.6: indicadores de consistência, incluindo dias sem estudo, sem punição por descanso planejado.

## P3 — produto por assinatura

- [ ] P3.1: API em camadas e PostgreSQL; separar usuários e respectivos concursos.
- [ ] P3.2: autenticação forte, segregação de dados, recuperação de senha e políticas de acesso.
- [ ] P3.3: cobrança com webhooks idempotentes, controle de assinatura e cancelamento.
- [ ] P3.4: backups cifrados, restauração, exclusão/exportação de dados e observabilidade.
- [ ] P3.5: versão beta com grupo pequeno, instrumentação de erros e avaliação de retenção.
- [ ] P3.6: documentação de termos, política de privacidade, LGPD e direitos sobre conteúdo de cursos.

## Definição de pronto para cada entrega

1. Critério de aceite explícito e dados de teste.
2. Testes unitários passando; testes de integração onde houver dados/serviços.
3. Sem publicar credenciais, dados de estudo, imagens do manual ou bancos pessoais.
4. Documentação de instalação e migração atualizada.
5. Commit no repositório oficial, preferindo branch de desenvolvimento/PR quando alterar fluxo crítico.

## Primeira sprint recomendada

1. Modelo de simulado e redação, com validações e testes.
2. Persistência de rodadas e unidades de ciclo de 30 minutos.
3. Interface de planejamento Semanal/Ciclos e histórico.
4. Regressão com os dados reais, sem sobrescrever banco da versão pessoal.

O foco da primeira sprint é **restaurar paridade operacional** com o legado, não criar recursos de cobrança antes de validar o uso diário.
