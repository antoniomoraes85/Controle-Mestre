# AUDITORIA CRÍTICA DAS PESQUISAS 01–03 — CONTROLE MESTRE
Data: 2026-11-07 | Escopo: revisão técnica dos relatórios Work/Astra sobre Guruja e conferência seletiva do código atual em `main`.

## Estado documental
- [01 — Planejamento](01_GURUJA_PLANEJAMENTO.md): publicada, 22.469 caracteres; pesquisa documental sem teste em conta autenticada nem auditoria de telas.
- [02 — Erros e reforços](02_GURUJA_REFORCOS_INTELIGENTES.md): publicada, 40.361 caracteres; apresenta especificação independente com ressalvas e métricas; critérios numéricos são hipóteses de engenharia.
- [03 — Arena, IA e MCP](03_GURUJA_ARENA_IA_MCP.md): publicada, 28.857 caracteres; integra AnkiConnect/FSRS e MCP com controles de acesso; há lacuna factual quanto à fala pública sobre MCP.
- Pesquisa 04–08: documentos ainda não verificados nos nomes previstos. As **44 issues existentes permanecem abertas**; criação do relatório não conclui nenhuma.

## Qualidade e limites por pesquisa
| Pesquisa | Pontos fortes | Limitações e ação |
|---|---|---|
| 01 | Rastreabilidade do fluxo e correspondência direta entre componentes CM e funcionalidades Guruja | Não viu telas autenticadas; vídeo analisado apenas por transcrição, sem screenshots verificados. Preservar classificações declarado/desconhecido. |
| 02 | Modelo tentativa–questão–intervenção; separação de causa, prioridade e dose; retestes e incerteza; evita falsos dados individuais | Beta(1,1), n≥15, T=0,80, escore e doses são hipóteses. Não ativar sem calibração e avaliação de séries reais. |
| 03 | Especifica integração read-only, isolamento, idempotência, carga FSRS e permissões MCP; dados sem IA ainda válidos | Trecho 37–41min ficou não transcrito nessa execução. A afirmação de que não foi confirmado sequer anúncio de MCP é incompleta diante de transcrição anterior da mesma live. |

## Correção factual prioritária sobre o vídeo (pesquisa 03)
**Evidência:** transcrição da live https://www.youtube.com/watch?v=OOpSWIqsNvo — trecho aproximado 38:49–40:58, recuperado anteriormente na conversa do projeto. O apresentador diz que lançaram uma integração MCP para conectar IA, cita ChatGPT, Claude e Gemini, e descreve a possibilidade de IA consultar planejamento, atividades, taxas de acerto por tema/disciplina, comparar resultados e confrontar conteúdo de edital. Outro apresentador descreve acesso a dados despersonalizados de outros alunos para comparação.
**Classificação correta:** existe **anúncio/demonstração verbal pública**, não especificação técnica independente nem teste funcional. Isso corrige a frase da pesquisa 03 segundo a qual não havia base para confirmar um anúncio. Continuam sem comprovação externa: endpoint, ferramentas MCP, escopos, consentimento, dados reais disponíveis por plano, limites, autenticação, implantação e prontidão geral. Não confundir o sistema homônimo 'Guru' (getguru.com) com Guruja Concursos (guruja.com.br).
**Ação ao consolidar na tarefa 08:** atualizar a pesquisa 03 com adendo citado e confirmar detalhes técnicos apenas com fonte da própria Guruja ou acesso legítimo de teste. Não atribuir ao concorrente os contratos propostos para o CM.

## Falhas técnicas confirmadas por leitura estática no código atual
1. **Preservação de identidade:** `adaptive.py/apply_plan` executa `DELETE FROM plans` para pendentes da semana e recria linhas. Isso elimina IDs estáveis e impede vínculos futuros seguros com sessões, conteúdo e resultados. A rota convencional possui comportamento distinto. [CM-012](https://github.com/antoniomoraes85/Controle-Mestre/issues/12) e [CM-013](https://github.com/antoniomoraes85/Controle-Mestre/issues/13).
2. **Dois caminhos de plano:** `core.py/generate_plan` e `adaptive.py/preview_plan`/`apply_plan` precisam contrato único de prévia, confirmação, redistribuição conservadora e desfazer. Nunca planejar retroativamente sem intenção explícita. [CM-012](https://github.com/antoniomoraes85/Controle-Mestre/issues/12).
3. **Granularidade da questão:** `core.py/add_questions` armazena agregados de bateria e apenas uma causa geral. Não suporta discriminar erro por tentativa e não pode inferir tal detalhe do legado. [CM-015](https://github.com/antoniomoraes85/Controle-Mestre/issues/15) e [CM-027](https://github.com/antoniomoraes85/Controle-Mestre/issues/27).
4. **Motivo versus intervenção:** a heurística v0.5 exibe causa na justificativa, mas não seleciona necessariamente ação pela causa individual e não vincula um reteste posterior ao reforço. [CM-016](https://github.com/antoniomoraes85/Controle-Mestre/issues/16), [CM-044](https://github.com/antoniomoraes85/Controle-Mestre/issues/44).
5. **Sincronização Anki:** a implementação atual suporta CSV agregado; AnkiConnect em leitura incremental e anti-dupla-contagem permanecem não implementados. [CM-021](https://github.com/antoniomoraes85/Controle-Mestre/issues/21), [CM-022](https://github.com/antoniomoraes85/Controle-Mestre/issues/22).
6. **Ambiente:** funcionalidades v0.5.1 foram testadas automaticamente; o app ainda carece de homologação real no Windows e teste de restauração de banco. [CM-003](https://github.com/antoniomoraes85/Controle-Mestre/issues/3), [CM-004](https://github.com/antoniomoraes85/Controle-Mestre/issues/4).

## Decisão de engenharia proposta
**F0 - Antes de aprofundar algoritmos:** homologação Windows, backup/rollback; preservar IDs de tarefa e unificar a prévia/confirmar em todos os modos. Bloquear alteração que destrua vínculos futuros.
**F1 - Dados:** modelar tópico versionado, questão, tentativa e causa (incluindo desconhecida), origem e reconciliação com agregados Qconcursos; manter dados ausentes distintos de taxa 0%.
**F1 - Aprendizagem:** recomendação por causa + objetivo verificável + material vinculado ao Estratégia quando autorizado; episódio com resultado imediato e retestes posteriores.
**F2 - Revisões:** AnkiConnect read-only, proveniência, cursor incremental, estimativa de tempo e reconciliação de sessões; Anki continua agendando FSRS.
**F3 - IA:** relatórios determinísticos auditáveis antes de MCP/LLM; acesso pessoal mínimo, opt-in, fontes e data de atualização.
**F4 - RL:** fase opcional posterior a dados de resultado temporal, baseline e avaliação offline; sem alegação de superioridade sobre Guruja.

## Três critérios de aceite essenciais para o primeiro lote Codex
- **Planejamento**: bloquear terça por plantão; prévia move tarefa pendente de 50min preservando o ID; concluída e iniciada continuam íntegros; sem espaço mostra déficit; cancelar não grava; desfazer não apaga sessões já realizadas.
- **Questões**: registrar duas tentativas da mesma questão em datas diferentes e classificações distintas; reimportar a mesma tentativa não soma novamente; bateria legada agregada não é fragmentada ficticiamente.
- **Reforço**: erro relatado gera atividade com material autorizado e causa; após execução, estado permanece 'aguardando reteste'; sem resultado posterior não exibir ganho nem domínio confirmado.

## Status da revisão
- Resultado: **pesquisas úteis para refinamento**, mas ainda não bastam para declarar plataforma equivalente ou pronta para comercialização.
- Não foram modificadas as pesquisas 01–03 nem as 44 issues nesta auditoria; esse trabalho cabe à tarefa de consolidação (08/08).
- Nenhuma mudança de código, nenhuma conclusão de testes Windows, nenhuma instalação comercial e nenhuma importação de PDFs particulares realizada aqui.