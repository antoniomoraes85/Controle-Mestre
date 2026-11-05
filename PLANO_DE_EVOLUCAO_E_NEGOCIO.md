# CONTROLE MESTRE — Plano de produto e lançamento

## 1. Proposta de valor

**Promessa que podemos testar:** 'Abra o CONTROLE MESTRE e saiba, sem retrabalho, o que estudar hoje, por quê, quanto já avançou e o que corrigir para a próxima semana.'

Foco inicial: concurseiros que estudam por editais extensos, resolvem questões em plataformas externas, têm disponibilidade irregular e querem acompanhamento baseado em evidências. O produto não é apostila, curso ou promessa de aprovação.

## 2. Diferenciais a validar

- Consolidar Excel, Anki, cronômetro, questões e metas em uma única visão.
- Planejamento adaptativo **auditável**, com regras explícitas e possibilidade de reverter alterações.
- Disponibilidade real: plantões, pós-plantões, dias de recuperação e dias livres.
- Evitar contagem dupla entre sessões e Anki/Excel.
- Caderno de erros com ação corretiva e revisão automática.
- Independência do concurso: catálogos de disciplinas, assuntos e pesos configuráveis por edital.

## 3. Módulos, contrato de dados e status

| Módulo | Hoje (v0.1) | Próximo marco |
|---|---|---|
| Dashboard | KPIs, tendências, priorização | Filtros 7/30/90 dias e relatórios compartilháveis |
| Sessões e cronômetro | Registro por disciplina/tópico/ciclo | Cronômetro persistente após reconexão e pausa detalhada |
| Planejamento | Semanas com capacidade, pesos e heurística | Metas por assunto/aula e realocação por progresso real |
| Questões | Lotes, acertos ponderados, caderno de erros | Importador TEC/Qconcursos conforme formatos oficiais fornecidos |
| Anki | CSV agregado por data/baralho | AnkiConnect local opcional e integração segura de decks |
| Excel | Lê planilhas compatíveis, sem sobrescrever | Assistente visual de mapeamento de colunas + atualização incremental |
| Revisões | D+1/D+7/D+15/D+30 | Revisões condicionais por taxa de retenção e dificuldade |
| Ciclos | 1 a 10 e importação de totais | Rotação automática com respeitos à carga planejada |
| Comparações | Matérias do próprio usuário | Benchmarks coletados com consentimento e dados agregados suficientes |
| IA | Regras auditáveis (não modelo generativo) | Recomendações explicadas com validações e opção de desligar |
| Multiusuário | Não | Contas isoladas, autorização por usuário e políticas de acesso |
| Assinaturas | Não | Planos, pagamentos recorrentes, webhooks e gestão de cancelamento |

## 4. Métricas — especificação canônica

- **Horas líquidas**: soma de `sessions.minutes`, sem somar tempo do Anki por padrão para evitar duplicidade.
- **Questões realizadas**: soma de `questions.total`, excluindo estimativas e tópicos históricos.
- **Taxa de acerto**: `SUM(correct) / SUM(total)`, nunca média simples de taxas de lotes.
- **Aderência semanal**: `SUM(minutes de sessões na semana) / meta de minutos da semana`. Pode superar 100%.
- **Revisões vencidas**: revisões do CONTROLE MESTRE pendentes com data de vencimento anterior à data atual; não inclui o contador interno de cartões pendentes do Anki.
- **Progresso**: percentual de teoria por tópico, marcado/importado, não equivale a domínio comprovado.
- **Índice de necessidade**: `peso × (1 + 0,90*fraqueza + 0,65*negligência + 0,45*lacuna + 0,18*min(revisões_vencidas,5))`; pesos são parâmetros de produto sujeitos a calibração posterior.
- **Metas realizadas**: tarefas marcadas concluídas; não substituem registro de sessão, evitando inferir tempo estudado de checkboxes.

## 5. Ordem de evolução proposta (sem escopo artificial)

**Marco A — Confiabilidade pessoal**
- Validar, a partir de seus arquivos reais, os cabeçalhos dos CSVs Anki e das sessões VBA.
- Implementar importação incremental com mapeamento de campos, pré-visualização e deduplicação por identificador de evento quando houver.
- Adicionar log detalhado de importação por linha e função de desfazer.
- Testar casos de horário de verão, dias atravessando meia-noite, ciclos acumulados e timezone.
- Corrigir UX do cronômetro e do preenchimento após sessões reais.

**Marco B — Planejamento realmente adaptativo**
- Catálogo por edital (SEFAZ-RS como catálogo inicial), disciplina, assunto, aula e páginas de materiais fornecidas pelo próprio usuário.
- Metas de páginas/questões baseadas em produtividade medida, sem inventar duração.
- Roteiro diário com dependências: teoria → questões → análise de erros → revisão.
- Ajuste semanal que respeita tarefas já realizadas e capacidade de plantões; versão dos planos e auditoria de mudanças.
- Simulados, acurácia por assunto, sazonalidade e intervalos de confiança quando amostra suficiente.

**Marco C — Beta com usuários externos**
- Migrar de desktop para arquitetura API + front-end responsivo; PostgreSQL gerenciado.
- Cadastro, autenticação, e-mail verificado, isolamento por usuário em todas as consultas, auditoria de permissão e criptografia em trânsito.
- Backups automatizados, retenção, restauração testada e monitoramento de falhas.
- Convites e onboarding com dados fictícios identificados como demonstração; feedback qualitativo de usabilidade.
- Testes de carga, segurança e acessibilidade antes de acesso público.

**Marco D — Assinatura**
- Planos mensais e anuais, assinatura com status e histórico de cobrança.
- Integração de recorrência por API do provedor escolhido, verificação de assinatura/credenciais de webhooks, idempotência de eventos, suspensão após inadimplência e retomada segura.
- Tela clara de preço, limites, cancelamento, reembolso e suporte.
- Painel administrativo sem acesso irrestrito ao conteúdo pessoal do aluno.
- Termos de uso, política de privacidade, gestão de solicitações de titulares e avaliação LGPD antes do lançamento.

## 6. Arquitetura comercial recomendada

- **Front-end**: Next.js/React, design responsivo, PWA se necessário.
- **API**: Python FastAPI, domínio de estudos reaproveitando e evoluindo as regras do `core.py`.
- **Persistência**: PostgreSQL, com `user_id` em cada tabela de dados pessoais e políticas de autorização no serviço.
- **Jobs**: fila para importar grandes arquivos, gerar planos e consolidar métricas, com histórico de execuções.
- **Arquivos**: storage privado com acesso assinado e varredura/limite de uploads.
- **Segredos**: gerenciador de segredos do provedor; nenhum token no navegador ou repositório.
- **Observabilidade**: logs sem dados sensíveis, métricas de disponibilidade e alertas de erro.
- **Assinaturas**: provedor brasileiro de recorrência com webhooks e conciliação financeira.
- **Segurança**: MFA opcional, controle de sessão, rate limiting, testes de autorização, política de backup e exclusão de conta.

**Nunca expor diretamente este MVP Streamlit na internet**: ele é intencionalmente monousuário, não oferece login nem isolamento de dados.

## 7. Critérios objetivos antes de cobrar assinatura

1. Nenhum lançamento duplicado nas importações compatíveis.
2. Somas, taxas e revisões reconciliadas contra exemplos manuais e históricos reais.
3. Planejador ajusta-se a disponibilidade e não ultrapassa limite de plantão.
4. Contas de teste não conseguem ler ou alterar dados de outros usuários, inclusive por IDs diretos.
5. Backup/restore validados e com procedimentos operacionais documentados.
6. Proteções de privacidade, contratos e cobrança testados em ambiente de homologação.
7. Avaliações de utilidade com candidatos externos demonstram ganho prático sobre planilha/manual.

## 8. Dependências externas e riscos

- **Marca:** pesquisar disponibilidade do nome CONTROLE MESTRE no INPI e domínio antes de investir em publicidade; isso não foi verificado como disponível.
- **Dados de terceiros:** não reproduzir conteúdo de apostilas, bancos de questões, questões licenciadas ou layouts/identidade visual de concorrentes sem permissão.
- **LGPD:** dados de desempenho identificáveis são pessoais; não coletar saúde/medicação sem necessidade, finalidade e base legal adequadas.
- **Automação:** integração com serviços de questões/Anki deve respeitar interfaces e termos aplicáveis; importação por arquivo é opção inicial segura.
- **Monetização:** preço deve ser definido após entrevistas, testes de disposição a pagar e custos reais de infraestrutura/suporte.

### Referências oficiais
- INPI, marcas: https://www.gov.br/inpi/pt-br/servicos/marcas
- INPI, consulta: https://servicos.busca.inpi.gov.br/marcas/
- ANPD, guia de segurança: https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia-orientativo-sobre-seguranca-da-informacao-para-agentes-de-tratamento-de-pequeno-porte
- Mercado Pago, API de assinaturas: https://www.mercadopago.com.br/developers/pt/reference/online-payments/subscriptions/overview