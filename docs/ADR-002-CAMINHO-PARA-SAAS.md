# ADR-002 — Plano de migração para multiusuário (não implementado)

Data: 2026-11-05. Status: proposta técnica, sem produção.

## Decisão

A versão pessoal continua local-first. A construção comercial deverá reutilizar domínio e contratos de negócios, migrando a persistência para PostgreSQL e incorporando identidades por conta. **Não basta expor o servidor local em 0.0.0.0.**

## Modelo de domínio futuro

- `users`: identificador opaco, autenticação externa/gerenciada, estado de conta.
- `organizations`/`workspaces`: delimita propriedade de preparações (apenas se grupos forem necessários).
- `preparations`: pertencem a um usuário (e uma versão de edital); não reutilizar identificador global na API sem autorização.
- `subjects`, `topics`, `sessions`, `questions`, `reviews`, `exams`, `essays`, `plans`, `anki_imports`: todas as entidades pessoais vinculadas a `preparation_id`, com posse conferida a cada consulta e mutação.
- `payments` e `subscriptions`: dados mínimos de acesso; números completos de cartão nunca entram no aplicativo.
- `audit_events`: ator, operação, alvo, data, identificador de correlação e antes/depois quando necessário.

## Requisitos de segurança obrigatórios antes de qualquer acesso público

1. Serviço de identidade confiável (OIDC), sessão em cookie seguro HttpOnly, SameSite, HTTPS.
2. Autorizações por usuário/preparação, testes de acesso cruzado para cada endpoint, política de menor privilégio.
3. Migrações versionadas e rollback testado, backups cifrados, restauração exercitada.
4. Isolamento adicional no PostgreSQL (RLS quando aplicável), limites por usuário e logs sem conteúdo sensível.
5. Proteção CSRF e XSS, rate limiting, headers e CSP, verificação de dependências.
6. Processo de exportação e exclusão de dados, minimização de coleta, transparência LGPD.
7. Cobrança por provedor certificado com webhook idempotente e controle de assinatura do lado do servidor.
8. Observabilidade com indicadores de erros, uptime, tempos e monitoramento de acessos anômalos.

## Migração incremental

**Fase A — motor local:** banco atual compatível e frontend modular, simulado/redação independentes (v0.4).
**Fase B — API independente:** contratos DTO, camada de serviço, mapeamento de IDs, esquema multi-tenant em PostgreSQL apenas em dev/staging.
**Fase C — contas piloto:** autenticação, isolamento, importação consentida, testes de segurança e política de privacidade.
**Fase D — beta fechado:** 5–20 pessoas com métricas de erro, usabilidade e retenção; pagamento apenas após estabilidade.
**Fase E — produto:** deploy protegido, escala, suporte e cobrança.

## Controle de fontes

- Excel e Anki poderão ser fontes de importação. Sempre manter `source_system`, `external_key`, `imported_at` e deduplicação idempotente.
- Dados importados não são automaticamente iguais a estudo ocorrido, e estatísticas agregadas não podem duplicar sessões efetivamente registradas.
- Nenhum dado pessoal deve ser enviado ao GitHub, inclusive em prints e fixtures de testes.

## Não metas / não alegar

A v0.4 **não fornece SaaS, login, assinatura, sincronização em tempo real, conectores automáticos** nem comunidade de alunos. As informações desta ADR são projeto de evolução e requisitos de aceite, não funções entregues.