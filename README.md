# CONTROLE MESTRE

Plataforma de planejamento e controle inteligente de estudos.

## Referência histórica

O projeto retoma a plataforma anterior apresentada pelo canal **Atrator Concursos** em 18/09/2023: [PLATAFORMA CONTROLE MESTRE](https://youtu.be/NAwtZ3KIxao). A descrição pública apresenta planejamento semanal, adaptação à rotina, metas diárias, estudos guiados, revisões, simulados, redações, desempenho por tópico e apostilas de apoio. O vídeo foi identificado por seus metadados; não houve auditoria visual de todas as telas.

## Versão atual: v0.6.1 (catálogo privado por aula e pasta externa compatível; homologação Windows pendente)

- **Painel web local + Python + SQLite**: execução local e monousuário; Streamlit permanece como interface legada.
- Metas semanais, cronômetro, ciclos de 1 a 10, questões, erros e revisões.
- Importação manual de Excel e CSV agregado do Anki.
- Planejamento por pesos de disciplinas e disponibilidade diária.
- Métricas calculadas sobre dados efetivamente registrados, não estimativas históricas.

**Ainda não existe** sincronização automática com Anki, autenticação, isolamento multiusuário, aplicação hospedada segura nem cobrança de assinatura.

## Como executar

Instale Python 3.11+ e rode:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m streamlit run app.py --server.address 127.0.0.1
```

Também há lançadores para Windows e Linux/macOS. O banco é criado localmente em `dados/controle_mestre.db`. Sem a base pessoal, as disciplinas padrão são cadastradas, mas os históricos começam vazios. Importe os arquivos próprios via interface.

## Privacidade e propriedade intelectual

**O repositório está público.** Nunca commitar bancos SQLite, planilhas, históricos de estudo/Anki, arquivos protegidos por direitos autorais, credenciais, segredos ou backups pessoais. O `.gitignore` cobre os formatos e diretórios locais mais frequentes. Para comercialização proprietária, considere tornar o repositório privado.

Esta versão **não deve ser publicada na internet para usuários externos**: ainda não possui autenticação nem separação segura de dados.

Consulte [PLANO_DE_EVOLUCAO_E_NEGOCIO.md](PLANO_DE_EVOLUCAO_E_NEGOCIO.md) para a estratégia de evolução e lançamento.

© Titular do projeto — todos os direitos reservados, salvo licença expressa futura.

## Manual original CM 1.0 — roteiro de reconstrução

O manual histórico de 53 páginas, fornecido pelo proprietário, documenta os dois modos de planejamento (**semanal** e **por ciclos de 30 minutos**), quadro geral, tarefas, catálogo de assuntos, questões, revisões, simulados e redações. Os comportamentos estão discriminados em:

- [Referência funcional histórica CM 1.0](docs/REFERENCIA_HISTORICA_CONTROLE_MESTRE_V1.md)
- [Matriz de paridade e backlog priorizado](docs/MATRIZ_DE_PARIDADE_E_BACKLOG.md)
- [ADR-001: estratégia de arquitetura e dados](docs/ADR-001-ESTRATEGIA_DE_EVOLUCAO.md)

**Atenção:** essas páginas são documentação dos requisitos do legado, não declaração de que todas as funcionalidades já estão implementadas no MVP. O PDF original permanece fora do repositório público por cautela com dados de identificação e direitos sobre conteúdos históricos.

## Interface v0.2 — contraste e legibilidade

Em resposta à avaliação visual da primeira versão, foi configurado o tema dark nativo do Streamlit e remodelado o Painel executivo, sem alterar os registros SQLite. Foram introduzidos cartões de indicadores com alto contraste, barra de meta semanal, prioridades em lista visual, aviso para primeiro uso, melhor aproveitamento da área útil e gráfico agregado em quatro semanas, sem eixo de 28 datas para períodos sem registros.

- [Notas e instruções da v0.2](NOTAS_V02.md)
- [Componentes e estilos](ui_theme.py)
- [Configuração do tema](.streamlit/config.toml)
- [Testes dos componentes](tests/test_ui_theme.py)

**Validação:** testes automatizados e compilação Python passaram. A aparência de uma prévia HTML estática foi inspecionada; a aplicação Streamlit completa ainda precisa de teste visual em navegador com as dependências instaladas.

## Painel Web Premium v0.3 (05/11/2026)

A experiência de uso foi reorganizada a partir das referências do usuário: **Meta atual → Atividades → Execução → Desempenho**. A interface agora é uma aplicação web local independente de Streamlit, com aparência responsiva para computador e celular. **Não copia marca ou componentes proprietários de terceiros.**

### Acesso local no Windows

1. Instale Python 3.11+ e extraia o pacote preservando o banco local em `dados/controle_mestre.db`.
2. Execute `iniciar_windows.bat` (ou `iniciar_painel_premium_windows.bat`).
3. Abra **http://127.0.0.1:8765**. A interface anterior permanece em `iniciar_streamlit_windows.bat`.

### Funções implementadas

Meta semanal com progresso por atividade e horas; cronômetro com registro de sessão; quadro de prioridades, planejamento semanal e tipos de dia, tarefas concluíveis, questões, revisões, desempenho por disciplina, histórico e configurações. É o mesmo SQLite e o mesmo motor do Streamlit. Dados ausentes permanecem ausentes.

**Testes automatizados:** 17 (12 do núcleo + 5 HTTP do painel). **Inspeção visual:** layout renderizado em viewport desktop 1440 px e móvel 390 px, sem rolagem horizontal; a navegação foi verificada em navegador automatizado usando dados locais fornecidos pela própria API como resposta interceptada. Os testes HTTP foram executados em SQLite temporário isolado. **Não foi realizada homologação em um Windows do usuário.**

⚠️ **Não hospede o servidor em público:** não existem autenticação, multiusuário, pagamentos, integrações automáticas Anki nem controles comerciais. O servidor escuta somente `127.0.0.1`.

Veja [GUIA_PAINEL_WEB_V03.md](GUIA_PAINEL_WEB_V03.md) para instruções, limites e evolução.

## v0.4 — Avaliações e componentes (05/11/2026)

**Esta é uma versão pessoal e local.** A interface original foi preservada e o JavaScript começou a ser separado em módulos nativos (`web/modules/`). Foram acrescentados os módulos de **simulados e redações**, recuperando parte das funcionalidades documentadas na versão histórica da plataforma.

- Simulados: acertos, erros, brancos, chutes e nota opcional. Validação de totais e edição pela exclusão + novo registro.
- Redações: tema, banca, nota e nota máxima.
- Banco SQLite: migração aditiva e idempotente, preserva registros existentes.
- Comparações: simulados não são somados às questões avulsas; notas de redações são normalizadas.
- API local com testes de origem, restrição a módulos estáticos e validação de entrada.

### Testes

`python -m unittest discover -s tests -v`

**25 testes automatizados** e checagem de sintaxe dos módulos JS. O navegador automatizado deste ambiente bloqueou navegação, portanto a inspeção visual final deve ser feita no computador do usuário.

### Como atualizar

Veja o [Guia v0.4](GUIA_CONTROLE_MESTRE_V04.md) e mantenha cópia do arquivo `dados/controle_mestre.db`. O banco pessoal **não** deve ser enviado ao GitHub.

### Futuro SaaS

Veja [ADR-002: migração para multiusuário](docs/ADR-002-CAMINHO-PARA-SAAS.md). **Autenticação, isolamento real por conta, cobrança e hospedagem pública ainda não estão implementados.** Não coloque o servidor local na internet.

## Correção de abertura no Windows — v0.4.1

Caso `http://127.0.0.1:8765` apresente `ERR_CONNECTION_REFUSED`, isso significa que o servidor web local não está respondendo. `127.0.0.1:8501` é a interface anterior do Streamlit e não substitui o painel web.

A v0.4.1 contém:

- Inicializador Windows que verifica Python 3.11+, arquivos e acesso ao banco antes de abrir o navegador.
- Seleção de porta local livre entre 8765 e 8770 e reutilização de instância existente.
- `diagnosticar_windows.bat` para emitir diagnóstico quando não abrir.
- Registro local de falhas em `logs/ultimo_erro_inicializacao.log`, excluído do Git.
- Cinco testes novos de seleção de porta e verificação de instalação (30 testes Python no total).

Execute `iniciar_windows.bat` da pasta **extraída** de dentro do ZIP. Mantenha a janela do terminal aberta. Use sempre o endereço exibido nela, que pode ser `8766` ou outra porta.

Consulte [Instruções de correção v0.4.1](CORRECAO_ABERTURA_V041.md).

**Não foi possível diagnosticar a causa precisa no Windows somente pelas imagens**; a correção adiciona diagnóstico e recuperação. Os testes HTTP foram realizados em ambiente Linux; teste manual final no Windows permanece necessário.

## v0.5 — Planejamento adaptativo por assunto (07/11/2026)

Nova seção web **Inteligência de estudos**, com heurísticas auditáveis e prévia semanal. Ainda é uma versão pessoal/local para testes.

- Diagnóstico por assunto com base nos últimos 90 dias de questões avulsas, pesos de disciplinas e incidência cadastrada, progresso, revisões pendentes e causas dos erros das baterias.
- Diferenciação explícita entre desempenho aferido e ausência de dados; amostras menores que 15 questões não são rotuladas como incompetência.
- Sugestões explicáveis de Teoria, Questões, Revisão ou Caderno de erros.
- Geração de prévia semanal sem alteração do banco e com aviso de falta de disponibilidade quando a carga horária cadastrada não alcança a meta.
- Aplicação apenas mediante confirmação explícita: substitui tarefas pendentes da semana em transação SQLite e preserva tarefas concluídas.
- Inicializador não reutiliza a porta de servidor antigo (somente instâncias v0.5).
- 40 testes automatizados passaram no ambiente de desenvolvimento; navegação automatizada por Chromium foi bloqueada por política administrativa, portanto a conferência visual no Windows permanece pendente.

### Instalação

Leia [Guia de atualização v0.5](GUIA_CONTROLE_MESTRE_V05.md). **Faça backup local de `dados/controle_mestre.db` antes de atualizar.** O repositório público não contém banco pessoal.

### Limitações

Esta heurística não está validada como equivalente ao Guruja nem ao acompanhamento de professores. Não há dados comparativos externos, integração automática Anki, usuário autenticado ou infraestrutura SaaS. **Nunca exponha o serviço local na internet.**

## Plano diretor 2026–2027 e 44 tarefas rastreáveis

**Pesquisa e backlog consolidados em 07/11/2026.** A referência funcional inclui Guruja, Estudei, Aprovado App, Estudaqui, TEC, Qconcursos, Anki, Estratégia, RemNote, StudyFetch e SuperMemo. Comparação não certifica equivalência pedagógica.

- [Plano diretor com 44 entregas e estimativas](docs/PLANO_DIRETOR_2026_2027.md)
- [Benchmark documentado de plataformas e vídeos](docs/BENCHMARK_PLATAFORMAS_2026.md)
- [Estratégia Concursos, Anki, IA/RL, domínio e marca](docs/ESTRATEGIA_ANKI_RL_MARCA.md)
- [Acompanhar **todas as issues de desenvolvimento**](https://github.com/antoniomoraes85/Controle-Mestre/issues)
- [Issues P0 prioritárias](https://github.com/antoniomoraes85/Controle-Mestre/issues?q=is%3Aissue+is%3Aopen+P0)

**Primeira etapa de execução:** CM-001 segurança/IP; CM-002 porta e AnkiConnect; CM-003 backup; CM-004 testes Windows. Depois: CM-009 edital, CM-015 causas de erros, CM-021/022 Anki, CM-024 índice do Estratégia. **Nenhuma das novas 44 issues deve ser considerada concluída sem critérios de aceite.**

A integração direta com cursos do Estratégia **não está implantada e depende do acesso/licença permitidos**. Na versão pessoal, favorecer links a aulas e metadados, sem redistribuir PDFs. O RL é pesquisa posterior ao baseline heurístico com retenção medida e avaliação offline. Domain/nome comercial só depois de triagem INPI; comprar endereço antes de concluir o SaaS é razoável após decidir nome.

## v0.5.1 — Biblioteca Estratégia e Qconcursos (07/11/2026)

**Uso local e pessoal, sem integração oficial de contas.** Novas funções:

- [Guia de atualização e uso v0.5.1](GUIA_CONTROLE_MESTRE_V051.md)
- [Changelog técnico](CHANGELOG.md)
- `sources.py`: catálogo de metadados de PDFs colocados pelo usuário em `dados/materiais/estrategia/` sem persistir textos ou arquivos no banco, com vínculo aula–disciplina–assunto na nova tela **Materiais e Qconcursos**.
- Registro de links HTTPS oficiais de cadernos Qconcursos. Não há login, scraping nem API oficial integrada.
- CSV preparado pelo estudante com resultados agregados da sua conta, sob `dados/importacoes/qconcursos/`; leitura, prévia, confirmação, transação atômica e deduplicação por ID/hash, **sem enunciados**.
- `backup_manager.py`: backup verificado do banco existente na primeira inicialização diária, antes de migrar, armazenado somente em `dados/backups/`.
- `launch.py`: portas 8771–8780. **8765 reservada ao AnkiConnect.** Testes automatizados de reserva.

**49 testes Python aprovados e sintaxe JS verificada.** A renderização em navegador automatizado foi bloqueada pela política do ambiente, portanto a interface **ainda precisa ser homologada no Windows**. PDFs reais do curso Estratégia ainda não foram fornecidos nesta etapa. Não há indexação RAG nem IA executando sobre materiais licenciados. O futuro SaaS não poderá redistribuir esses arquivos sem autorização.

O repositório permanece público; não suba materiais, PDFs, bancos locais, CSVs pessoais nem credenciais. Consulte as issues CM-002, CM-003, CM-004, CM-024, CM-026 e CM-027 para pendências e critérios de aceite.

## v0.6.0 — Ciclo Fiscal RS + SC e AnkiConnect local (07/11/2026)

**Primeiro ciclo conforme escolha do proprietário:** Contabilidade Geral; Contabilidade de Custos; Análise das Demonstrações Contábeis; Direito Tributário; Reforma Tributária (EC 132/2023 + LC 214/2025); Reforma Tributária (LC 227/2026); Direito Administrativo; Direito Civil; Direito Constitucional.

- [Guia de atualização v0.6.0](GUIA_CONTROLE_MESTRE_V06.md)
- **Trilha Fiscal RS+SC:** 50 assuntos iniciais, plano de teoria → questões → Passo Estratégico → revisão por questões → caderno de erros, com prévia e confirmação, registro de estudo real, bloqueio de passado e respeito ao teto diário informado. Não duplica tarefas em replanejamento da mesma semana. **Não é edital integral, nem motor pedagógico validado**.
- **Estratégia:** organização local por tipo (Teoria/Passo_Estrategico) e por disciplina; reconhecimento automático da disciplina pelo nome de pasta; vínculo ao assunto ainda manual. PDFs protegidos permanecem no computador.
- **AnkiConnect:** ponte local apenas de leitura, APIs v5 `version`, `deckNamesAndIds`, `findCards`, com retrato diário por perfil/disciplina (card_count, due, new, rated:1) sem alterar cartões, FSRS, histórico de horas ou grades. **Não há sincronização automática de eventos de revisão individual nesta versão**.
- **Qconcursos:** importação por CSV autorizado e atalhos da v0.5.1 mantidos; sem login ou API oficial.
- **Validação:** 64 testes Python passaram, JS validado sintaticamente; não houve acesso ao Anki do usuário nem homologação Windows. **O GitHub não contém histórico privado, PDFs, base SQLite ou credenciais**.

**Próxima frente:** testar no Windows com perfil Anki aberto e PDFs próprios, reconciliar eventos individuais sem duplicidades, mapear aulas aos 50 assuntos e avançar para o edital verticalizado versionado. Não publicar servidor local na internet.

## v0.6.1 — Catálogo particular por aulas e diretório externo (07/11/2026)

A aplicação reconhece a organização real do titular: `Controle-Mestre-main/CONTROLE_MESTRE/`, `Controle-Mestre-main/MATERIAL TEÓRICO/` e `Controle-Mestre-main/ANKI/`. **O software não move, renomeia nem copia o acervo original.** O caminho da pasta `MATERIAL TEÓRICO` é detectado automaticamente quando está ao lado da aplicação ou pode ser escolhido localmente pelo usuário com confirmação.

- [Guia de atualização v0.6.1](GUIA_CONTROLE_MESTRE_V061.md).
- Subpastas reconhecidas: `Teoria Principal`, `Simplificado`/`Teoria Simplificada`, `PASSO ESTRATÉGICO`, `QUESTÕES`, inclusive sob disciplinas numeradas.
- Novo planejador de aulas: utiliza as listas fornecidas, com 125 aulas em oito disciplinas; Direito Civil aguarda relação de aulas. As 50 entradas genéricas anteriores são mantidas para compatibilidade e históricos existentes.
- O catálogo detalhado é **privado**: `dados/catalogo/aulas_primeiro_ciclo.csv`, entregue somente no pacote pessoal, nunca publicado no repositório GitHub público.
- A vinculação exige o código correto da aula no nome do PDF ou preenchimento manual. Um PDF de Aula 29 não é apresentado como material da Aula 00.
- Testes: **70** Python em fixtures isoladas; validação de sintaxe JS. O acervo e o Anki reais não foram acessados no ambiente de desenvolvimento.
- Os arquivos existentes `ANKI/*.bas`, `ANKI/*.csv`, `ANKI/*.xlsm` e planilhas permanecem intactos. A integração AnkiConnect da v0.6.0 continua apenas de leitura.

**Pendências:** receber a lista de Direito Civil; testar localmente no Windows; vincular os PDFs reais (não enviados); concluir auditoria das macros/CSV Anki e correspondência entre aulas, assuntos e edital vigente.
