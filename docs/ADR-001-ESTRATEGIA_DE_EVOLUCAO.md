# ADR-001 — Local-first, fonte de verdade e evolução para SaaS

**Status:** Proposta aceita para planejamento; implementar incrementalmente. **Data:** 2026-11-04.

## Contexto

O CONTROLE MESTRE será usado individualmente na preparação SEFAZ-RS antes da oferta por assinatura. O manual de 2023 contém planejamento semanal/ciclos, tarefas, questões, revisões, simulados e redações. A versão v0.1 utiliza Streamlit + SQLite e incorpora manualmente alguns dados externos.

## Decisão

1. **MVP:** execução local e banco SQLite, sem autenticação externa nem dados pessoais no GitHub.
2. **Fonte de verdade:** eventos de sessões, questões, revisões e avaliações efetivamente concluídos. Metas, importações brutas e totais acumulados são dados separados e não aditivos.
3. **Identidade de origem:** `source_system`, `external_key`, `content_hash`, `imported_at`, `occurred_at`. Importações reexecutadas não geram duplicidade; correções não somam registros.
4. **Domínio:** Pessoa → Preparação (concurso + versão do edital) → Disciplinas → Assuntos → Atividades → Eventos de execução → Indicadores derivados. No MVP pessoal, ID de usuário pode ser implícito; em SaaS será obrigatório.
5. **Estratégia:** manter adaptador de importação Excel e CSV Anki; criar conectores automáticos somente quando houver fonte disponível e consentimento, sem varredura silenciosa.
6. **Ciclos:** unidades 30 min e rodadas são estados de execução; totais e cronômetro não podem ser contados duas vezes. Guardar eventos e exibir progresso derivado.
7. **Segurança:** chaves, dados de uso, backups e PDFs privados fora do repositório público. Quando houver SaaS, exigir autenticação, autorização de dados, backups e recuperação auditada antes de publicar.
8. **Implementação comercial:** API e PostgreSQL após validação do modelo individual e do fluxo de estudo. Separar regras de negócio da camada visual desde já.

## Alternativas descartadas

- **Excel como fonte canônica:** útil como origem/importação, mas dificultaria idempotência, auditoria e múltiplos usuários.
- **SaaS primeiro:** adicionaria custo e risco de segurança antes da validação do produto.
- **Somar todas as fontes automaticamente:** causa duplicação entre cronômetro, Anki e registros do Excel.
- **Confundir indicador previsto com realizado:** gera métricas enganadoras.

## Qualidade e validação

- Taxas de acerto = soma de acertos / soma de questões efetivamente respondidas.
- Métricas sem denominador devem exibir “sem dados”, nunca 0%.
- Revisões vencidas são pendências com prazo anterior à data de referência.
- Descanso programado não representa meta não cumprida.
- Nenhuma revisão, simulado ou sessão efetiva é apagada por replanejamento.
- Indicadores e recomendações documentam fonte, data e regras.
- Migrar bancos com backup, script repetível e testes de regressão.

## Consequências

Pro: privacidade, custo inicial mínimo, autonomia do usuário, comportamento auditável. Contras: configuração local, integração incremental, esforço posterior de migração para multiusuário e necessidade de disciplina nas versões de banco.
