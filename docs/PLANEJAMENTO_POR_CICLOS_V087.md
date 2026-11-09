# Planejamento por ciclos — integração v0.8.7 (candidata)

## Problema corrigido

Na v0.8.6, a aba **Planejamento** tinha apenas cartões de disponibilidade por segunda–domingo e botão «Recalcular esta semana», mesmo quando o usuário preferia ciclos. A aba **Ciclos** tinha mecanismo básico separado. A referência funcional é o manual local da Plataforma Controle Mestre 1.0, em especial as páginas 17–25: escolher **SEMANAL / POR CICLOS**; por ciclos, definir matérias, sequência e tempo; botões de meia hora vermelho (pendente) / verde (concluído); conclusão reinicia marcadores e conta rodada.

## Fluxo agora

1. Acessar **Planejamento**.
2. Escolher **SEMANA FIXA** ou **POR CICLOS** (salvo em SQLite, tabela `planning_preferences`).
3. Se **SEMANA FIXA**, o planejamento anterior continua intacto, com cartões de dias, atividades e recálculo.
4. Se **POR CICLOS**, usar «+ Criar ciclo ou microciclo», atribuir nome, tipo e, se microciclo, ciclo principal.
5. No cartão criado, usar «+ Adicionar etapa ao ciclo», escolher disciplina, assunto, modalidade e número de blocos de 30 min.
6. Organizar a sequência com «Subir» / «Descer», editar os blocos ainda não executados, e arquivar etapas sem apagar histórico.
7. Marcar cada bloco de vermelho para verde conforme a execução. Ao completar todos os blocos ativos, incrementa a rodada e reinicia os marcadores, preservando `study_cycle_marks` e `study_cycle_rounds`.
8. Cronômetro e registros de sessões **são independentes** dos marcadores. Não contabilizar horas líquidas duas vezes.

## Integridade / migração

- Tabela `planning_preferences` criada aditivamente; ausente → «Semana fixa» sem mudar o comportamento legado.
- Coluna `study_cycle_segments.archived` adicionada por migração condicional; não deleta registros antigos.
- Alteração de atributos de etapa é bloqueada se já houver marcas de qualquer rodada, para preservar a autoria do histórico.
- Arquivar uma etapa com marcas preserva fisicamente as marcas, mas exclui etapa da rodada ativa.
- Tabelas de atividades semanais e sessões não são alteradas pela alternância.
- Não ler/escrever os bancos históricos de instalações anteriores.

## Validação

- Rodar `python -m unittest discover -s tests -v`.
- Rodar `node --check web/app.js` e `node --check web/modules/cycle_planner.js`.
- Interface Windows: abrir Planejamento (semana), alternar para ciclos, criar ciclo, adicionar duas disciplinas com assuntos e modalidades diferentes, alterar ordem, marcar blocos, reiniciar servidor e comprovar persistência, encerrar a rodada, verificar contagem de rodadas.
- Alternar para Semana fixa e comprovar que calendário e registros anteriores não desapareceram.
- Verificar que o histórico de horas líquidas não aumenta ao marcar blocos, somente ao registrar sessão/cronômetro.

## Distribuição

Branch de recurso `feat/planejamento-ciclico-integrado-v087`, PR dedicado (draft). Não alterar manifesto `versao_oficial.json` ou publicar atualização para Windows antes da homologação. Para liberar uma v0.8.7, a origem do atualizador precisa conter commit imutável com as alterações; depois o manifesto oficial deve apontar para esse commit, sem usar branch móvel.
