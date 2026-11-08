# CONTROLE MESTRE — FASE 1: Registro Detalhado de Erros

**Branch:** `feat/cronogramas-identidade-v07`  
**Data:** 2026-11-08  
**Versão alvo:** 0.8.0 (pré-release)

---

## 1. Visão Geral

A FASE 1 implementa o módulo de **Registro Detalhado de Erros**, com dois modos
operacionais distintos e integração completa ao backend SQLite.

### Dois Modos de Registro

| | MODO A — Por Bateria | MODO B — Por Questão |
|---|---|---|
| **Uso** | Lançamento rápido de resultado total | Rastreamento individual de cada questão |
| **Causas** | Classificação geral da bateria (simplificação explícita) | Causa principal + causas secundárias por questão |
| **Precisão** | Adequada para baterias com volume alto | Alta precisão diagnóstica |
| **Recomendado** | Estudo corrente do dia a dia | Análise pós-prova, questões difíceis |

---

## 2. Arquitetura

### Novos Arquivos

| Arquivo | Responsabilidade |
|---|---|
| `error_tracking.py` | Módulo de domínio: schema, CRUD, análise |
| `web/modules/questions.js` | UI: toggle de modo, formulários, caderno |
| `tests/test_error_tracking.py` | 56 testes hermético-sintéticos |

### Novas Tabelas (SQLite)

```sql
-- Cabeçalho da bateria (Modo A e Modo B)
question_batches (
  id, day, subject, topic, platform, banca,
  total, correct, unanswered, time_used_min,
  had_prior_review, gabarito_timing, mode,
  cause_counts,  -- JSON: {causa: quantidade}
  notes, source, created_at
)

-- Itens individuais (Modo B)
question_items (
  id, batch_id → question_batches.id,
  question_ref, subject, topic, subtopic,
  result,              -- Correta | Incorreta | Não resolvida
  primary_cause,       -- Causa principal
  secondary_causes,    -- JSON: [causa, ...]
  observation, difficulty, resolution_time_s,
  consulted_gabarito, needs_reinforcement,
  correction_status, created_at
)
```

### Compatibilidade com Tabela `questions` Legada

Ao registrar uma bateria via `/api/questions/batch`, o sistema **também insere**
na tabela legada `questions` para manter compatibilidade com as análises existentes
(`subject_metrics`, `metric_data`, `get_error_summary` legado etc.).

---

## 3. API Endpoints

### GET

| Rota | Descrição |
|---|---|
| `GET /api/questions/constants` | Causas, resultados, dificuldades, status |
| `GET /api/questions/caderno` | Caderno de erros filtrado |
| `GET /api/questions/summary` | Estatísticas agregadas (separadas por origem) |
| `GET /api/questions/batch/:id` | Bateria com itens individuais |

#### Parâmetros de `/api/questions/caderno`

| Param | Tipo | Descrição |
|---|---|---|
| `subject` | string | Filtrar por disciplina |
| `topic` | string | Filtrar por assunto |
| `primary_cause` | string | Filtrar por causa principal |
| `correction_status` | string | `Aberto`, `Corrigida`, `Revisada` |
| `needs_reinforcement` | `0`/`1` | Filtrar marcados para reforço |
| `limit` | int | Máximo de itens (padrão 100, máximo 500) |

### POST

| Rota | Payload principal | Resposta |
|---|---|---|
| `POST /api/questions/batch` | `subject`, `total`, `correct`, `mode`, `cause_counts` | `{batch_id, performance}` |
| `POST /api/questions/item` | `batch_id`, `result`, `primary_cause` | `{item_id}` |
| `POST /api/questions/item/correction` | `id`, `correction_status` | `{ok}` |

---

## 4. Regras de Negócio

### Validações de Bateria

- `total >= 1` (obrigatório)
- `0 <= correct <= total`
- `correct + unanswered <= total`
- Soma das causas declaradas ≤ número de erros (`total - correct - unanswered`)
- `gabarito_timing` em: `['Antes da resolução', 'Após a resolução', 'Não consultado']`
- `mode` em: `['batch', 'individual']`

### Validações de Item

- `result` em: `['Correta', 'Incorreta', 'Não resolvida']`
- `primary_cause` validada contra as 8 causas canônicas (apenas quando `result = 'Incorreta'`)
- `secondary_causes`: cada item validado individualmente
- `batch_id` deve existir no banco

### Distinção Metodológica Explícita

O sistema **nunca** atribui automaticamente todos os erros de uma bateria à mesma
causa. As análises em `get_error_summary()` retornam:

```json
{
  "batch_declared_causes": {"Desconhecimento": 3},  // causa geral da bateria
  "item_primary_causes": {"Esquecimento": 1},         // verificada por questão
  "note": "..."  // explicação metodológica explícita
}
```

---

## 5. Causas Canônicas

1. Desconhecimento
2. Esquecimento
3. Confusão conceitual
4. Erro de interpretação
5. Falta de atenção
6. Falta de tempo
7. Outro motivo
8. Não especificado

---

## 6. Integração com Motor de Reforços (FASE 2)

O campo `needs_reinforcement` em `question_items` serve como sinal de entrada
para o motor de reforços (FASE 2). O método `feed_performance()` já retorna:

```python
{
  'batch_id': 42,
  'rate': 0.70,
  'has_individual_items': True,
  'needs_reinforcement_count': 2,  # sinal para FASE 2
  ...
}
```

---

## 7. Testes

**56 testes** em `tests/test_error_tracking.py`, cobrindo:

- `TestErrorCauses` — integridade das causas canônicas (3 testes)
- `TestRegisterBatch` — validações e registro de baterias (13 testes)
- `TestRegisterItem` — validações e registro de itens individuais (11 testes)
- `TestGetBatch` — recuperação de bateria com itens (4 testes)
- `TestGetErrorSummary` — estatísticas agregadas e filtros (8 testes)
- `TestGetCadernoErros` — caderno de erros e filtros (7 testes)
- `TestUpdateItemCorrection` — atualização de status de correção (5 testes)
- `TestFeedPerformance` — integração de desempenho (4 testes)
- `TestSchemaMigrationIdempotent` — idempotência do schema (1 teste)

**Todos os testes usam dados sintéticos.** Nenhum arquivo privado do titular
é lido.

---

## 8. Limitações e Decisões Conhecidas

> [!NOTE]
> A tabela legada `errors` continua existindo para compatibilidade retroativa.
> As novas tabelas `question_batches` e `question_items` são aditivas.

> [!WARNING]
> O modo POR QUESTÃO requer que o estudante crie uma bateria antes de lançar
> itens individuais. Não é possível lançar um item sem bateria vinculada.

> [!IMPORTANT]
> As causas declaradas em baterias (Modo A) são classificações gerais e podem
> representar uma simplificação. A plataforma comunica isso explicitamente ao
> estudante e nas análises estatísticas.

> [!TIP]
> Para maior precisão diagnóstica, prefira o Modo B (por questão) em provas
> diagnósticas e simulados. Use Modo A para o estudo corrente do dia a dia.

---

## 9. Próximo Passo — FASE 2

A FASE 2 implementará o motor de **Reforços Inteligentes** com 3 níveis
(Leve / Moderado / Intenso) e ciclo de reteste. Os sinais de entrada já
estão disponíveis a partir desta FASE 1:

- `question_items.needs_reinforcement`
- `question_items.primary_cause`
- `feed_performance().needs_reinforcement_count`
- `get_error_summary()` por disciplina e assunto
- `get_caderno_erros()` com filtro `needs_reinforcement=True`
