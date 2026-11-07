# CONTROLE MESTRE v0.6.0 — Ciclo fiscal de 9 disciplinas + AnkiConnect (local)

Data: 07/11/2026. **Estado:** versão pessoal em desenvolvimento, não homologada no Windows do titular. Sem SaaS, autenticação, IA sobre PDFs ou sincronização de contas do Estratégia/Qconcursos.

## Atualização sem perder dados
1. **Feche completamente** os servidores antigos; deixe o Anki aberto apenas quando quiser sincronizar.
2. Faça **cópia independente** de `dados/controle_mestre.db` da instalação atual. Não use a mesma pasta da versão anterior.
3. Extraia o novo ZIP em pasta própria, com todos os arquivos.
4. Copie apenas o banco antigo para `CONTROLE_MESTRE/dados/controle_mestre.db` na pasta nova.
5. Execute `iniciar_windows.bat`. O servidor usa 127.0.0.1:8771–8780; porta 8765 é do AnkiConnect.
6. Abra `Trilha Fiscal RS + SC` e clique **Ativar trilha comum**, caso ainda não esteja ativa. A ativação é aditiva: não elimina dados antigos.
7. Configure seu calendário, plantões e meta de horas em Planejamento. Use `Prévia desta/próxima semana` antes de confirmar; tarefas da trilha não sobrescrevem tarefas do planejador antigo.
8. Se você já usou uma versão experimental com a trilha antiga de cinco disciplinas, as tarefas existentes são preservadas e os assuntos novos são acrescentados. Não há remoção automática de registros anteriores.

## Currículo inicial — 9 disciplinas definidas pelo usuário
1. Contabilidade Geral.
2. Contabilidade de Custos.
3. Análise das Demonstrações Contábeis.
4. Direito Tributário.
5. Reforma Tributária (EC nº 132/2023 e LC nº 214/2025).
6. Reforma Tributária (LC nº 227/2026).
7. Direito Administrativo.
8. Direito Civil.
9. Direito Constitucional.

A versão traz **50 assuntos iniciais** distribuídos entre essas disciplinas. São curadoria preliminar para planejamento, não edital verticalizado integral, incidências ou pesos oficiais. Os nomes internos das duas disciplinas de Reforma Tributária preservam os identificadores já existentes no banco para evitar duplicidade. Português, Auditoria e matérias estaduais permanecem disponíveis fora do primeiro ciclo.

## Sequência planejada por assunto
**Teoria (70 min) → Questões de fixação (45 min / referência 12 questões) → Passo Estratégico (40 min) → Revisão por questões (35 min / referência 12 questões) → Caderno de erros (30 min se houver erros abertos)**.

São **tempos experimentais**, não doses pedagógicas validadas. O usuário deve registrar minutos e acertos **efetivamente realizados**. A trilha não inventa estudo, desempenho nem materiais. A implementação inicial exige etapas anteriores concluídas para passar à seguinte; o caderno de erros depende de registros de erro existentes. O planejamento respeita dias não disponíveis, bloqueia datas passadas e só aplica mediante confirmação. Quando o tempo cadastrado é inferior à meta semanal, o sistema não cria horas fictícias (configuração padrão: 7 × 180 min = 21h, embora a meta possa ser 25h).

## Organização de seus PDFs do Estratégia
Coloque os arquivos que você possui legalmente nas subpastas de sua nova instalação:

`CONTROLE_MESTRE/dados/materiais/estrategia/Teoria/<Disciplina>/aula_00.pdf`

`CONTROLE_MESTRE/dados/materiais/estrategia/Passo_Estrategico/<Disciplina>/aula_00.pdf`

As pastas das nove disciplinas já vêm **vazias no ZIP**, cada uma com um arquivo explicativo. Prefira os nomes de pasta que estão no pacote. Não coloque PDFs dentro de `web/`, GitHub, nem na raiz do projeto. A varredura em **Materiais e Qconcursos → Atualizar biblioteca** identifica automaticamente o tipo de material e a disciplina quando o nome de pasta corresponder a uma das nove. Revise o assunto e a aula pelo botão `Vincular`: **a associação PDF ↔ assunto ainda é manual**. Os arquivos são abertos localmente, não são copiados para o banco nem enviados a provedores de IA.

## AnkiConnect: configuração no seu computador
1. Abra o **Anki Desktop** com seu perfil correto e faça o backup habitual do Anki antes de testar novas ferramentas.
2. Se não estiver instalado: **Ferramentas → Complementos → Obter complementos** e informe o código AnkiConnect **2055492159**; reinicie o Anki. Fonte: https://github.com/amikey/anki-connect
3. Confira que AnkiConnect responde em `http://127.0.0.1:8765` com Anki aberto. A versão usa apenas a API local v5.
4. No CONTROLE MESTRE, abra **Revisões e Anki → Verificar conexão**. O sistema listará os baralhos das nove disciplinas cujos nomes permitirão associação automática.
5. Para gravar um retrato do inventário, clique **Sincronizar retrato**, confirme e informe um nome identificador do perfil. Use **outro nome** caso tenha alternado o perfil do Anki. O CM guarda somente nome do baralho, disciplina e contagens de cartões, devidos, novos e cartões com avaliação nas últimas 24h.
6. Em caso de uso de chave opcional de AnkiConnect, configure a variável de ambiente `ANKICONNECT_API_KEY` **somente no seu Windows**, nunca no repositório ou em prompts compartilhados.

### Limitações deliberadas do Anki na v0.6.0
- A conexão é **somente de leitura**: ações permitidas `version`, `deckNamesAndIds` e `findCards`. Não cria, move ou exclui cartões; não altera intervalos FSRS nem responde revisões.
- Os totais são um **retrato diário do inventário**, não histórico `revlog` por evento. `rated:1` indica cartões com alguma resposta nas últimas 24 horas, não quantidade de respostas, taxa de erro nem minutos.
- Horas de estudo, revisões individuais e desempenho não são importados do AnkiConnect nesta fase. O CSV histórico do Anki permanece **separado**, sem somar números duas vezes.
- A coleção Anki real não foi acessada deste ambiente. Sua primeira sincronização deve ser homologada no Windows. O mapeamento por nome de baralho exige revisão quando houver nomes ambíguos; não há acesso a tags ou conteúdo de notas.
- A API local do AnkiConnect requer que o Anki esteja aberto. Não exponha a porta 8765 à rede/internet.

## Qconcursos
Mantido o cadastro de atalhos do Qconcursos e CSV de resultados **preparado/autorizado** pelo usuário. Não há API automática documentada, scraping ou sincronização da conta. Não redistribua enunciados.

## Diagnóstico e atualização no GitHub
- Rodar `python -m unittest discover -s tests -q` e verificar sintaxe de JS com Node quando disponível.
- A atualização é preservadora: trilha em tabelas próprias, sincronização Anki em `anki_live_snapshots`, sem alterações de desempenho histórico.
- **Antes de considerar homologado:** testar no Windows a abertura de PDFs reais, AnkiConnect com subbaralhos e cópia/restauração do banco. O Chromium do ambiente anterior esteve bloqueado por política de navegação, portanto não há garantia de UI real testada.
- Issues relacionadas: CM-002, CM-003, CM-004, CM-009, CM-010, CM-011, CM-012, CM-014, CM-015, CM-016, CM-017, CM-021, CM-022, CM-024, CM-025.

## Direitos autorais
Somente uso pessoal autorizado dos arquivos do Estratégia. O acervo e o banco pessoal não acompanham o código e não podem ser publicados no SaaS ou GitHub sem licença própria.