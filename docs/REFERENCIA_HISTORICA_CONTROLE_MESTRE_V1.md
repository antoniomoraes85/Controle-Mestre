# Controle Mestre 1.0 — referência histórica funcional

**Fonte primária:** manual “Plataforma Controle Mestre 1.0.pdf” (53 páginas), fornecido pelo proprietário do projeto em novembro de 2026. **Não é uma especificação técnica do código antigo:** descreve comportamentos apresentados no manual. A implementação atual deve preservar conceitos e comportamento, sem presumir acesso ao código-fonte original.

**Contexto:** a versão original era orientada ao concurso PRF; o produto atual deve generalizar a arquitetura para concursos diferentes, iniciando pela SEFAZ-RS. O vídeo de referência da primeira plataforma é https://youtu.be/NAwtZ3KIxao.

## Inventário funcional comprovado pelo manual

| Código | Componente | Comportamento documentado | Evidência (páginas do PDF) |
|---|---|---|---|
| CM-LEG-01 | Quadro geral | Progresso percentual do edital, contagem regressiva da prova, médias de simulados e redações recentes, questões (total/acertos/erros), gráficos de conclusão e aproveitamento por matéria. | 13–16 |
| CM-LEG-02 | Modos de estudo | Usuário escolhe **semana fixa** ou **por ciclos**. Os menus e fluxos de execução variam conforme o modo. | 17–18, 21, 24 |
| CM-LEG-03 | Catálogo de conteúdos | Matérias e assuntos do edital, incidência do assunto, rendimento, estado de conclusão, comandos de revisão e questões. | 18–20 |
| CM-LEG-04 | Ciclos | Sequência de disciplinas configurável; cada marcador representa 30 minutos; ao completar todos, uma rodada é contabilizada e os marcadores voltam ao estado inicial para permitir novo ciclo. | 21, 23, 25 |
| CM-LEG-05 | Disponibilidade semanal | Cadastro por dia da semana: horas disponíveis e meta de questões; editar/excluir; ordem de tarefas. | 22, 27–31 |
| CM-LEG-06 | Tarefas diárias | Disciplinas ordenadas, tempo previsto e tipo (teoria, questões ou revisão); consulta por assunto e registro direto de resultados. | 30–38 |
| CM-LEG-07 | Questões | Lançamentos datados de quantidade e acertos por assunto; histórico e gráficos por matéria; alternância da série visualizada. | 26, 32–34, 39–41 |
| CM-LEG-08 | Revisões | Registro por assunto e histórico vertical de revisões; manual indica agendamento automático de revisões de tópicos previamente estudados. | 38, 42–44 |
| CM-LEG-09 | Simulados | Cadastro de data, nota, total, acertos, erros, chutes e em branco; gráficos de últimas provas e evolução; editar/excluir histórico. | 45–49 |
| CM-LEG-10 | Redações | Cadastro de desempenho/nota, visualizações históricas e evolução. | 50–51 |
| CM-LEG-11 | Conteúdos auxiliares | Manual menciona apostilas-guia, estratégias, dicas de estudo e comunidade; não há detalhamento técnico suficiente para reimplementação fiel. | 4–6 |

## Regras funcionais a preservar

1. **Semanas e ciclos são modalidades de planejamento, não dados concorrentes.** Uma única sessão efetiva poderá estar vinculada a tarefa e a uma rodada de ciclo. A conclusão de marcador não pode registrar minutos adicionais quando uma sessão vinculada já os contabilizou.
2. **Ciclo de 30 minutos:** unidades completadas são persistidas como eventos; a conclusão de todas as unidades encerra uma rodada, incrementa contador de rodadas concluídas e disponibiliza uma nova. Um reset visual jamais apaga histórico.
3. **Metas de tarefas:** cada registro de tarefa possui data prevista, disciplina, assunto, tipo, duração, meta opcional de questões, ordem, estado e data efetiva de conclusão. O replanejamento não apaga tarefas concluídas.
4. **Assuntos possuem identificadores estáveis** vinculados a uma versão do edital/curso. Rendimento é calculado por total de acertos / total de questões, sem médias simples entre lotes.
5. **Questões, simulados e redações são entidades distintas.** Uma questão de simulado só compõe estatística geral de questões quando associada por origem, sem duplicação.
6. **Revisões:** é necessário distinguir agendamento, realização e vencimento, preservando datas reais e origem.
7. **Prova sem data definida:** a contagem regressiva deve permanecer indisponível, não assumir data hipotética.
8. **Incidência:** indicar fonte, banca/edital e confiança. Histórico de PRF não deve ser reutilizado silenciosamente como incidência da SEFAZ-RS.

## Distinção entre legado e evolução planejada

**Recursos legados descritos** não provam acesso ao banco, APIs ou código do sistema de 2023. A versão atual usa infraestrutura própria. Anki, importações Excel, adaptação a plantões, pontuação de prioridade, sugestões automatizadas e multiusuário são **evoluções propostas**, não funções comprovadas do sistema 1.0.

## Identidade visual e direitos

O manual mostra tema escuro com menu lateral preto, gradientes roxo/azul, acentos amarelos e identidade histórica Atrator/CM. A interface nova pode manter a identidade CONTROLE MESTRE, com acessibilidade e experiência mobile, sem copiar material de terceiros. O PDF original **não está incluído** no repositório público para não expor desnecessariamente dados de identificação, contatos e materiais históricos. Deve ser mantido em arquivo privado do proprietário.

## Critérios gerais de aceite

- Todas as funcionalidades marcadas como “reimplementadas” devem ter teste funcional automatizado ou roteiro de teste manual documentado.
- Não usar dados de exemplo como desempenho verdadeiro.
- Toda importação tem rastreabilidade por fonte e prevenção de duplicidade.
- Histórico de horas e resultados nunca é destruído por alterações de metas, ordem ou modo de estudo.
- Migrações e backups testados antes da abertura para assinantes.
