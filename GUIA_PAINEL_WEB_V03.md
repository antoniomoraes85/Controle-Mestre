# CONTROLE MESTRE — Painel Web v0.3

## O que mudou

A interface anterior foi avaliada como distante do padrão profissional desejado. As referências de UX fornecidas pelo proprietário incluíram os módulos públicos do Guruja: Meta, Desempenho, Comparativo, Arquivo, Favoritos e outros elementos de navegação. Esta versão propõe **identidade original CONTROLE MESTRE**, com tema escuro e destaque limão, e reorganiza a experiência conforme **Meta → Atividades → Execução → Desempenho**. O layout foi inspecionado visualmente a 1440 px e 390 px e não apresentou rolagem horizontal.

O painel web **usa o mesmo `core.py` e o mesmo banco SQLite da versão Streamlit**. Não cria métricas fictícias nem altera dados históricos ao ser aberto. Os 22 grupos de disciplinas importados no pacote inicial são reais da planilha pré-existente; registros vazios aparecem vazios.

## Instalação — Windows

1. **Faça backup** do seu arquivo atual `dados/controle_mestre.db` (nunca entregue esse arquivo em público).
2. Extraia a v0.3 em uma **pasta nova**.
3. Para preservar o histórico, copie seu `dados/controle_mestre.db` antigo para a pasta `dados/` da v0.3 **com a plataforma fechada**.
4. Execute `iniciar_windows.bat`. Esse é o novo painel web (sem dependências adicionais além de Python 3.11+).
5. Abra `http://127.0.0.1:8765` no navegador. O servidor roda somente nesse computador.
6. Para usar a interface anterior, execute `iniciar_streamlit_windows.bat` (requer instalação de Streamlit).

Se a porta 8765 estiver ocupada, execute `python web_server.py --port 8766` e abra `http://127.0.0.1:8766`.

## O que funciona na v0.3 web

- **Meta ativa:** mostra progresso da semana por atividade concluída e por minutos de estudo, separadamente.
- **Atividades:** visualização e conclusão/reabertura sem excluir registros; histórico de horas não é gerado ao marcar tarefa como concluída.
- **Planejamento:** edição de disponibilidade diária (plantão, pós-plantão, dias livres etc.) e geração/replanejamento semanal.
- **Cronômetro:** iniciar, pausar, zerar e registrar sessão em segundos, com confirmação de disciplina, modalidade e minutos antes de salvar.
- **Questões:** cadastro com validação de total e acertos e acompanhamento do rendimento ponderado.
- **Revisões:** fila de vencidas e pendentes, com confirmação de conclusão.
- **Desempenho:** horas por semana, questões, priorização e desempenho por disciplina.
- **Arquivo:** últimas sessões; as importações completas e backup permanecem na interface Streamlit.
- **Configurações:** meta semanal de horas líquidas.

## Limitações declaradas

- Não há autenticação ou dados sincronizados entre computadores; não publicar o servidor na internet.
- A v0.3 **não implementa** módulo de assinatura, mentor humano, rankings de outros estudantes, integração automática do Anki ou marcas e materiais exclusivos de concorrentes.
- Os ciclos da v0.1 são visualizados por registros de tempo; o fluxo de blocos individuais de 30 minutos e reinício automático de rodada permanece no backlog.
- O cronômetro depende da aba aberta. Antes de sair, **salve sua sessão**.
- O botão de salvar sessão do cronômetro abre uma confirmação; cancelar preserva o tempo pausado.
- Os dados de demonstração não são usados no banco de produção. Se não houver questões ou horas registradas, o painel exibirá estado vazio.
- A interface comercial futura deverá ser construída com front-end componentizado, API, autenticação, banco PostgreSQL, backups e separação por usuário. Este painel web local é um **protótipo funcional para validação de UX**.

## Privacidade e desenvolvimento

- Manter `dados/`, arquivos `.db`, backups, questões baixadas e arquivos pessoais fora do GitHub público.
- O frontend usa arquivos estáticos em `web/` e um servidor HTTP Python (stdlib) restrito a `127.0.0.1`.
- Não tem dependências de CDN, Google Fonts ou aplicativos de terceiros.
- Testes: `python -m unittest discover -s tests -v`.
- Agradecimentos às referências de usabilidade do usuário; **nenhuma logo, nome ou conteúdo proprietário do Guruja foi copiado**.