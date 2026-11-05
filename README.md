# CONTROLE MESTRE

Plataforma de planejamento e controle inteligente de estudos.

## Referência histórica

O projeto retoma a plataforma anterior apresentada pelo canal **Atrator Concursos** em 18/09/2023: [PLATAFORMA CONTROLE MESTRE](https://youtu.be/NAwtZ3KIxao). A descrição pública apresenta planejamento semanal, adaptação à rotina, metas diárias, estudos guiados, revisões, simulados, redações, desempenho por tópico e apostilas de apoio. O vídeo foi identificado por seus metadados; não houve auditoria visual de todas as telas.

## Versão atual: v0.2 (MVP pessoal com interface reformulada)

- **Streamlit + Python + SQLite**: execução local e monousuário.
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
