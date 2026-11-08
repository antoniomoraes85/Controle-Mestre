# Cronogramas — Entrega 1 (núcleo Fixo + Ciclos + escala 24×72)

Módulo: `schedule.py` · Testes: `tests/test_schedule.py` (36 testes, bancos temporários).

## 1. Diagnóstico do planejador existente (auditoria)

| Mecanismo | Onde | Metas | Tempo disponível | Distribuição | Concluídas / não feitas |
|---|---|---|---|---|---|
| Plano legado | `core.generate_plan` → `plans` | `weekly_target_min` | `day_types.cap_minutes` (tipo de dia manual) | proporcional à capacidade; disciplina por prioridade | preserva `Concluída`; `DELETE` das `Pendente` da semana |
| Agenda adaptativa | `adaptive.preview_plan/apply_plan` → `plans` | idem | idem | diagnóstico heurístico por assunto (N≥15) | preview + `apply` com confirmação; apaga/reinsere pendentes (ids mudam) |
| Trilha fiscal | `fiscal_path` → `fiscal_tasks` | idem, deduz `sessions` da semana | `get_days` menos `plans` | 5 etapas por aula (teoria→…→erros), 2 aulas/disciplina | nunca duplica pendente; semana já planejada é bloqueada; sem replanejar |

Lacunas: (a) dias de semana presos a `day_types` preenchido à mão — **não há escala recorrente 24×72**;
(b) não há ciclo contínuo: a ordem das disciplinas é recalculada a cada semana (reinicia);
(c) três tabelas de tarefas sem identificador comum; (d) planos legados apagam/recriam pendentes;
(e) não há modelo de cronograma fixo; (f) sem calendário mensal.
Issues CM-008/009/011/012/013: **não foi possível consultá-las** (ver §7).

## 2. O que a Entrega 1 acrescenta (aditivo, sem terceiro planejador de metas)

`schedule.py` é uma camada de **disponibilidade + sequenciamento** que reutiliza `sessions` como fonte
única de horas e `settings.weekly_target_min` como meta. Não escreve em `plans`, `fiscal_tasks` ou `day_types`.

Tabelas novas (migração idempotente, backup antes de criar): `schedule_config`, `schedule_cycle_items`,
`schedule_fixed_slots`, `schedule_overrides`, `schedule_blocks`, `schedule_versions`.

### Escala 24×72
`configure_shift(ref_date, shift_minutes=0, post_shift_minutes, off_minutes, period_days=4)`.
Plantão = dia do início; dia seguinte = Pós-plantão; demais = Folga. Minutos de cada tipo são
**configuração do estudante** (padrões editáveis: 0 / 120 / 360). Ocorrências pontuais
(`set_override`): Férias, Viagem, Compromisso, Descanso, Indisponível, Plantão extra, Disponibilidade.
Prioridade: ocorrência > escala > padrão diário (0). Plantão limitado a `max_plantao_min` (120), regra já existente.

### Modelo B — Ciclos (padrão do usuário)
Itens: disciplina+modalidade, ordem, peso, minutos e quantidade de blocos. Bloco = `uid` estável `c:<ciclo>:<item>:<k>`.
- O ciclo atual é determinado **só por execução real** (blocos concluídos/em andamento); calendário e segunda-feira não reiniciam.
- Retomada: bloco `Pausada`/`Em andamento` é o primeiro da fila; minutos restantes = planejado − realizado.
- Antecipar: `start_block(uid)` em qualquer bloco válido; adiar: simplesmente não executar.
- Reordenar/desativar/ajustar não apaga nada; progresso e histórico permanecem.
- Projeção respeita disponibilidade diária, meta semanal (nunca aumenta carga) e dias bloqueados.
  Bloco maior que a disponibilidade do dia gera aviso e segue para um dia que comporte.

### Modelo A — Fixo
`schedule_fixed_slots` (dia da semana, ordem, disciplina, modalidade, minutos, horário opcional HH:MM).
Com escala/ocorrências configuradas, a disponibilidade limita os slots (excedentes são listados como aviso);
sem escala, vale a soma dos slots do dia. Edições posteriores não alteram blocos concluídos.

### Preview / aplicação / execução
`preview()` (somente leitura: novo/movido/mantido/retomada, liberados, déficit por semana ISO) →
`apply(confirm=True)` (backup + transação + `schedule_versions`). Cancelar = não aplicar. Nunca há `DELETE` de blocos:
pendentes migram de dia, ficam sem dia (ciclo) ou `Cancelada` (fixo). Trocar de modelo (`set_config(model=…)`) preserva histórico.
`start_block` / `pause_block` / `complete_block` gravam horas em `sessions` com fingerprint
`schedule-block:<uid>:<segmento>` (sem dupla contagem); conclusão exige tempo real > 0 e data não futura.
`calendar()` / `month_calendar()` fornecem dados semanais/mensais (dias reais do mês).

## 3. Pendências (próximas entregas)
Metas mensais/semanais/diárias detalhadas por modalidade (E2); API HTTP e telas Estudar Hoje, calendários e
configuração (E3); vínculo aula↔PDF↔modalidade (E4); AnkiConnect e carga de revisões (E5); sincronização
opcional com `day_types` para os planejadores legados; consolidação final dos três mecanismos.

## 4. Banco e migrações
Testes usam bancos sintéticos. Nenhum acesso de escrita ao banco pessoal; migração só ocorre quando
`schedule.migrate()` for chamado numa conexão real, sempre precedida de backup verificado em `dados/backups`.

## 5. Problemas pré-existentes observados
7 testes anteriores falham (os mesmos antes e depois desta entrega) neste computador porque leem os 352 PDFs reais em vez de pasta sintética
(`test_sources`, `test_anki_bridge`, `test_fiscal_path`, `test_material_folder_and_catalog`, `test_web_server`):
isolamento de testes será tratado na Entrega 4.
