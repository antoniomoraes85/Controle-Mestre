# CONTROLE MESTRE

Plataforma de planejamento e controle inteligente de estudos.

## Referência histórica

O projeto retoma a plataforma anterior apresentada pelo canal **Atrator Concursos** em 18/09/2023: [PLATAFORMA CONTROLE MESTRE](https://youtu.be/NAwtZ3KIxao). A descrição pública apresenta planejamento semanal, adaptação à rotina, metas diárias, estudos guiados, revisões, simulados, redações, desempenho por tópico e apostilas de apoio. O vídeo foi identificado por seus metadados; não houve auditoria visual de todas as telas.

## Versão atual: v0.5 (motor heurístico pessoal; homologação pendente)

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
