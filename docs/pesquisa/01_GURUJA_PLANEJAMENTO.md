# CONTROLE MESTRE — Pesquisa 01/08: planejamento da Guruja

**Data:** 07/11/2026. **Referência do produto:** v0.5.1. **Status:** pesquisa documental concluída, com verificação parcial da interface e das regras operacionais da Guruja.

Escopo exclusivo: planejamento semanal, metas, atividades diárias, disponibilidade, reorganização, execução e navegação. Não houve implementação, comparação com outras plataformas nem alteração das 44 issues.

## 1. Método, referências e evidências

Foram utilizadas três fontes principais da Guruja, incluindo o vídeo solicitado. As páginas institucionais confirmam declarações do fornecedor, não resultados de testes. O vídeo foi analisado por transcrição com timestamps, exclusivamente entre **26:00 e 35:00**; suas telas não foram inspecionadas diretamente. Não houve acesso autenticado à plataforma.

### Fontes externas

| ID | Fonte e localização | Evidência pertinente | Limitação |
|---|---|---|---|
| G1 | [Plataforma Guruja](https://guruja.com.br/plataforma-guruja/), seções Planejamento Personalizado, Metas Semanais e Atividades Diárias, Acompanhamento e Nossas Fases | O aluno informa carga e nível por disciplina; o professor prepara e ajusta o plano. Há metas semanais, atividades diárias, painel de desempenho e distinção pré/pós-edital. | Página comercial, sem especificação de algoritmos ou contrato de dados. Contém blocos promocionais de épocas distintas; não permite datar cada tela. |
| G2 | [Página oficial da área fiscal](https://lp.guruja.com.br/fiscal), seção de personalização, “Mesma prova. Orientações diferentes.” | Nível, disponibilidade, desempenho, dificuldades e objetivo participam da definição das metas pelo professor. | Não informa pesos, limiares ou frequência exata dos ajustes. |
| G3 | [Vídeo indicado — início do recorte](https://www.youtube.com/watch?v=OOpSWIqsNvo&t=1560s), 26:00–35:00 | Apresentação de interface, registro de erros, reforços, aprofundamentos, organizador e análises. | Evidência verbal recuperada por transcrição; pode conter erros de reconhecimento. Publicação e versão exata da demonstração não foram verificadas. |

### Localizadores do vídeo

| ID | Trecho | O que sustenta |
|---|---|---|
| V1 | [27:14–28:03](https://www.youtube.com/watch?v=OOpSWIqsNvo&t=1634s) | Apresentadores descrevem renovação visual, blocos coloridos, uso em celular/tablet e atalho na tela inicial. Isso não comprova instalação como PWA, funcionamento offline ou acessibilidade. |
| V2 | [28:03–29:23](https://www.youtube.com/watch?v=OOpSWIqsNvo&t=1683s) | Perfil do professor com características de atendimento e canais de contato, como entrada na orientação personalizada. |
| V3 | [29:23–30:26](https://www.youtube.com/watch?v=OOpSWIqsNvo&t=1763s) | Registro das questões erradas, assunto, causa declarada do erro e informações sobre revisão prévia e consulta de comentários. |
| V4 | [30:43–31:31](https://www.youtube.com/watch?v=OOpSWIqsNvo&t=1843s) | Reforços apresentados como direcionados aos erros, com intensidades e consideração da importância da disciplina. A geração de novo caderno a partir dos erros é descrita como novidade ainda em preparação nesse momento. |
| V5 | [32:02–33:26](https://www.youtube.com/watch?v=OOpSWIqsNvo&t=1922s) | Aprofundamento por disciplina/tópico e modalidade: questões, teoria, anotações, lei seca ou jurisprudência; orientação relacionada à banca. |
| V6 | [33:41–34:29](https://www.youtube.com/watch?v=OOpSWIqsNvo&t=2021s) | Organizador reúne atividades, reforços e aprofundamentos. Marcar dias sem estudo reorganiza a meta; é possível mover itens para outros dias. Não é explicado se a movimentação usa arrastar e soltar. |
| V7 | [34:29–35:00](https://www.youtube.com/watch?v=OOpSWIqsNvo&t=2069s) | “Minhas análises” é apresentada como recurso em teste, com previsão de análise mensal e comparações temporais. Não tratar como recurso disponível a todos na data da pesquisa. |

**Distinção central:** a elaboração pedagógica com professor e a redistribuição pelo organizador são capacidades diferentes. A participação humana descrita em G1/G2 é compatível com a automação operacional relatada em V6; não há evidência de planejamento inteiramente autônomo.

### Base interna consultada

Inspeção estática do repositório oficial em `main`, commit **`a5c5ee4c0c71be4c84f9cc1ca6b7587fd43d03f8`**. O guia e o servidor identificam v0.5.1; não foi confirmada uma tag de release. A consulta da listagem de tags foi recusada pelo conector. Não foram executados testes de software ou homologação visual nesta pesquisa documental.

| ID | Referência imutável | O que foi conferido |
|---|---|---|
| C1 | [Guia v0.5.1](https://github.com/antoniomoraes85/Controle-Mestre/blob/a5c5ee4c0c71be4c84f9cc1ca6b7587fd43d03f8/GUIA_CONTROLE_MESTRE_V051.md) | Produto local e monousuário; catálogo de PDFs e vínculos manuais, atalhos e importação CSV. |
| C2 | [core.py](https://github.com/antoniomoraes85/Controle-Mestre/blob/a5c5ee4c0c71be4c84f9cc1ca6b7587fd43d03f8/core.py) — tabelas, `save_day`, `get_days`, `generate_plan`, `metric_data` | Persistência das atividades, capacidades por dia, geração convencional e métricas. |
| C3 | [adaptive.py](https://github.com/antoniomoraes85/Controle-Mestre/blob/a5c5ee4c0c71be4c84f9cc1ca6b7587fd43d03f8/adaptive.py) — `diagnose`, `preview_plan`, `apply_plan` | Diagnóstico explicável, distribuição com prévia e substituição confirmada das pendências. |
| C4 | [web/app.js](https://github.com/antoniomoraes85/Controle-Mestre/blob/a5c5ee4c0c71be4c84f9cc1ca6b7587fd43d03f8/web/app.js) — `goalPanel`, `todayView`, `planView`, `handleAction` | Menus, tabelas, progresso, edição de dia e conclusão de tarefa. |
| C5 | [web_server.py](https://github.com/antoniomoraes85/Controle-Mestre/blob/a5c5ee4c0c71be4c84f9cc1ca6b7587fd43d03f8/web_server.py) — `overview` e rotas de planejamento/execução | Dois caminhos de geração; salvar disponibilidade não dispara replanejamento; conclusão e sessão são registros separados. |

As [44 issues abertas](https://github.com/antoniomoraes85/Controle-Mestre/issues) foram consultadas somente para relacionar propostas ao backlog. Issue aberta não é evidência de ausência total de implementação; as conclusões abaixo priorizam o código. A matriz histórica do repositório compara o MVP v0.1 e não deve substituir a inspeção da v0.5.1.

## 2. Funcionalidades identificadas

Legenda: **declarado** = afirmação pública da Guruja; **desconhecido** = sem confirmação nas fontes; **proposta** = decisão independente sugerida para o CONTROLE MESTRE. Dados descritos para a Guruja são entradas/saídas mencionadas publicamente, não seu esquema interno.

### 2.1 Planejamento semanal

- **O que faz / interação:** transforma o perfil do aluno em orientação semanal acompanhada por professor. O aluno fornece informações de preparação e consulta o plano. **Evidências:** G1/G2.
- **Dados identificados:** disponibilidade, nível por disciplina, objetivo, dificuldades e desempenho.
- **Regra comprovada documentalmente:** personalização com participação do professor. Não se comprovou fórmula de distribuição.
- **Desconhecido:** dia de liberação, prazo de validade da meta, duração obrigatória de sete dias, quantidade mínima de atividades e regras de passagem à próxima meta.
- **Alternativa independente:** separar objetivo semanal, capacidade efetiva e tarefas; mostrar a carga que cabe e o déficit, com prioridades explicadas.
- **CONTROLE MESTRE já possui:** semana de segunda a domingo, meta em minutos, capacidades diárias e duas rotas de geração. A adaptativa considera desempenho por assunto e revisões [C2/C3].
- **Melhorar:** unificar a experiência das duas rotas, tornar visível o orçamento e evitar alocação retroativa. Os geradores percorrem os sete dias, sem excluir explicitamente datas passadas da semana.

### 2.2 Estrutura das metas

- **O que faz / interação:** o organizador apresenta atividades, reforços e aprofundamentos; o aluno pode escolher um aprofundamento por disciplina, tópico e modalidade. **Evidências:** V5/V6.
- **Dados identificados:** disciplina, tópico, modalidade, banca e pertencimento ao planejamento; erros alimentam reforços conforme V3/V4.
- **Regra comprovada documentalmente:** esses três tipos de item são mencionados na organização da meta. Não foi demonstrado se pertencem à mesma entidade persistida.
- **Desconhecido:** campos obrigatórios, estimativa de duração, hierarquia interna, limites de extras e efeito de um aprofundamento sobre a meta original.
- **Alternativa independente:** uma atividade com identidade estável, disciplina/assunto, modalidade, duração estimada, origem e critério de conclusão; distinguir carga essencial e opcional.
- **CONTROLE MESTRE já possui:** `plans` guarda data, disciplina, assunto, método, minutos e questões-alvo, prioridade, justificativa, status e lote [C2]. Há catálogo de materiais separado [C1].
- **Melhorar:** vincular material e instrução executável à tarefa; registrar origem, ordem e carga opcional sem confundir método de estudo com motivo da recomendação.

### 2.3 Organização das atividades diárias

- **O que faz / interação:** permite distribuir e mover itens entre dias no organizador. **Evidência:** V6.
- **Dados identificados:** itens da meta, dias de estudo e dia de destino.
- **Regra comprovada documentalmente:** o usuário consegue alterar a distribuição entre dias.
- **Desconhecido:** ordenação dentro do dia, horários fixos, arrastar e soltar, divisão de tarefas e comportamento de atividade parcialmente executada.
- **Alternativa independente:** agenda diária ordenada, ação “Mover para…” e execução diretamente a partir da tarefa; arraste apenas como opção adicional.
- **CONTROLE MESTRE já possui:** tela “Estudar hoje”, tabela das tarefas do dia, conclusão/reabertura e cronômetro; a consulta ordena por data, prioridade e ID [C4/C5].
- **Melhorar:** edição individual de data/ordem/duração, destaque da próxima ação e continuidade de tarefas iniciadas. Não foi identificada rota de movimentação individual nos arquivos examinados.

### 2.4 Ajustes de disponibilidade

- **O que faz / interação:** o aluno marca dias em que não estuda e o organizador redistribui a meta. **Evidência:** V6.
- **Dados identificados:** dias indisponíveis e meta corrente; a carga do perfil também é informada ao professor [G1].
- **Regra comprovada documentalmente:** excluir dias da distribuição é uma ação apresentada no vídeo.
- **Desconhecido:** limites em minutos por dia, recorrência semanal, exceção por data, fusos, plantões ou suporte específico a escalas.
- **Alternativa independente:** disponibilidade padrão com exceções por data, descanso e limites configuráveis; sempre exibir capacidade restante.
- **CONTROLE MESTRE já possui:** tipo de dia e minutos por data; `Reset` permite zero. `save_day` limita a duração ao teto do tipo, como 120 minutos para Plantão e 90 para Pós-plantão [C2].
- **Melhorar:** recorrência de escala, exceções e aviso de impacto. Salvar o dia apenas persiste a disponibilidade; recalcular exige outra ação [C5].

### 2.5 Reorganização automática do calendário

- **O que faz / interação:** após indicar dias sem estudo, o organizador altera a distribuição; também admite mudança manual de dia. **Evidência:** V6.
- **Dados identificados:** meta, atividades e disponibilidade declarada. Não há acesso a prioridades internas.
- **Regra comprovada documentalmente:** redistribuição em resposta à indisponibilidade. A apresentação não detalha uma confirmação intermediária.
- **Desconhecido:** preservação de concluídas/iniciadas, identidade das pendências, excesso de carga, transferência entre semanas, dependências, desfazer e resolução de conflitos.
- **Alternativa independente:** separar **mover tarefas existentes** de **substituir recomendações**; oferecer prévia das mudanças, preservar histórico e explicitar o que ficou sem espaço.
- **CONTROLE MESTRE já possui:** ambos os geradores preservam concluídas e descontam seus minutos planejados da capacidade. O adaptativo tem prévia, confirmação e transação; porém apaga e recria pendentes [C2/C3].
- **Melhorar:** preservar IDs e vínculos das pendências, impedir perda de trabalho parcial, manter versões e desfazer. O botão “Recalcular esta semana” chama a geração convencional diretamente; não oferece a mesma confirmação da rota adaptativa [C4/C5].

### 2.6 Controle de progresso e execução

- **O que faz / interação:** coleta informações dos erros para orientar reforços. O aluno identifica questões erradas e informa causas e contexto de resolução. **Evidências:** V3/V4; painel de evolução declarado em G1.
- **Dados identificados:** questão, assunto, causa declarada, revisão prévia, consulta de comentários e importância da disciplina.
- **Regra comprovada documentalmente:** há distinção entre causas e intensidades de reforço na apresentação. Os critérios numéricos não são publicados.
- **Desconhecido:** cálculo do percentual concluído, validação da execução, associação entre tempo e tarefa e gatilho exato de cada intensidade. A novidade de cadernos em V4 e as análises em V7 não foram assumidas como amplamente disponíveis.
- **Alternativa independente:** separar conclusão de tarefa, minutos reais e aprendizagem aferida; ligar recomendação, atividade e resultado posterior sem converter ausência de dados em baixo desempenho.
- **CONTROLE MESTRE já possui:** progresso por quantidade de tarefas, horas de sessões e resultados de questões separados; concluir tarefa não cria minutos. `diagnose` usa janela de 90 dias, amostra mínima de 15 questões e justificativas por assunto [C2–C5].
- **Melhorar:** vínculo persistente tarefa–sessão–resultado, conclusão parcial e estimativa de esforço restante. O cadastro de questões recebe uma causa por bateria, não o detalhamento individual descrito no vídeo.

### 2.7 Navegação e apresentação visual

- **O que faz / interação:** a apresentação descreve blocos coloridos e uso adaptado a dispositivos móveis; o perfil do professor auxilia a escolha inicial. **Evidências:** V1/V2.
- **Dados identificados:** informações das atividades e características/canais do professor. A correspondência entre cores e estados não foi verificada.
- **Regra comprovada documentalmente:** melhoria de uso móvel declarada pelos apresentadores. Não é uma homologação independente de usabilidade.
- **Desconhecido:** estrutura exata do menu, legibilidade real, estados vazios, navegação por teclado, contraste, responsividade e quantidade de cliques.
- **Alternativa independente:** interface própria com visão semanal, foco do dia, estado textual e hierarquia consistente; testar celular e desktop sem depender apenas de cor.
- **CONTROLE MESTRE já possui:** “Minha meta”, “Estudar hoje”, “Planejamento”, indicadores, filtros e cartões de disponibilidade no código do painel [C4].
- **Melhorar:** continuidade entre essas telas, ações por tarefa e validação visual. A análise estática não comprova qualidade de uso no navegador; tampouco a pesquisa justifica copiar identidade visual ou conteúdo da Guruja.

## 3. Fluxos de utilização

### Fluxos da Guruja sustentados pelas fontes

1. **Preparar a semana:** informar perfil → receber orientação do professor → consultar meta e atividades. A etapa exata de aceite/liberação não foi observada [G1/G2].
2. **Adaptar a agenda:** abrir organizador → marcar dias sem estudo → receber distribuição ajustada → mover itens, se necessário. Cliques exatos e confirmação são desconhecidos [V6].
3. **Complementar estudos:** selecionar disciplina/tópico → escolher modalidade de aprofundamento → receber orientação ou caderno relacionado à banca. Seu consumo de orçamento não foi esclarecido [V5].
4. **Alimentar acompanhamento:** registrar erros e contexto → receber orientação de reforço. Automatismos, latência e validação pelo professor não foram determinados [V3/V4].

### Fluxo independente sugerido para o CONTROLE MESTRE

Definir meta e disponibilidade → conferir orçamento → revisar proposta semanal → executar tarefa com sessão vinculada → registrar resultado → visualizar progresso → simular redistribuição de pendências → confirmar nova versão.

Exemplo de aceite, com dados sintéticos: uma tarefa pendente de 50 minutos estava na terça-feira. Ao tornar a terça indisponível, a prévia propõe outro dia com capacidade, mantendo o ID e os vínculos. Se não houver espaço, mostra 50 minutos não alocados; não apaga a tarefa nem altera uma concluída. Essa é uma regra proposta, não uma descrição comprovada da Guruja.

## 4. Oportunidades de melhoria prioritárias

| Prioridade | Oportunidade | Motivo e limite da conclusão |
|---|---|---|
| P0 | Reorganizar preservando tarefas | A v0.5.1 já calcula uma nova distribuição, mas recria pendentes. Preservar identidade é necessário para permitir execução parcial, vínculos e histórico. Não se afirma que a Guruja já resolve esses casos. |
| P0 | Tornar capacidade e déficit visíveis | Reaproveitar o orçamento da prévia adaptativa e comunicar o efeito de indisponibilidades, inclusive quando toda a semana estiver bloqueada. |
| P0 | Unificar prévia e confirmação | Os caminhos convencional e adaptativo têm comportamentos diferentes; o usuário precisa distinguir simples movimentação de substituição do conteúdo recomendado. |
| P1 | Conectar planejar e executar | Partir da tarefa para o cronômetro/registro reduz preenchimento repetido e permite medir estimado versus realizado. |
| P1 | Separar obrigatório e opcional | Evitar que reforços ou aprofundamentos aumentem silenciosamente a carga essencial. |
| P1 | Homologar navegação móvel | Validar agenda e ações com teclado, toque e estados textuais. A existência de código de interface não garante facilidade de uso. |

## 5. Requisitos sugeridos para o CONTROLE MESTRE

Propostas documentais para refinamento futuro do backlog existente. Nenhuma issue foi criada, editada ou encerrada.

| ID local | Requisito e critério de aceite | Relação com issues existentes |
|---|---|---|
| R01 | **Orçamento semanal:** mostrar meta, capacidade, concluído planejado, tempo real e déficit separadamente; tratar capacidade zero sem tarefas novas nem divisão por zero. | [#8](https://github.com/antoniomoraes85/Controle-Mestre/issues/8), [#12](https://github.com/antoniomoraes85/Controle-Mestre/issues/12) |
| R02 | **Disponibilidade por data e recorrência:** configurar escala e exceções; bloqueio deve impedir novas alocações no dia e mostrar conflitos com trabalho já realizado. | [#12](https://github.com/antoniomoraes85/Controle-Mestre/issues/12) |
| R03 | **Redistribuição conservadora:** mover pendências sem trocar seus IDs, conteúdos ou vínculos; preservar concluídas/iniciadas; não criar tarefas em datas passadas; explicitar excedentes. | [#12](https://github.com/antoniomoraes85/Controle-Mestre/issues/12), [#13](https://github.com/antoniomoraes85/Controle-Mestre/issues/13) |
| R04 | **Prévia única e histórico:** apresentar antes/depois em todas as rotas; cancelar não altera dados; confirmar aplica uma versão atômica; desfazer preserva registros de execução posteriores. | [#13](https://github.com/antoniomoraes85/Controle-Mestre/issues/13) |
| R05 | **Atividade acionável:** permitir editar dia, ordem e estimativa; exibir modalidade, material e resultado esperado quando cadastrados; separar origem essencial/reforço/opcional. | [#10](https://github.com/antoniomoraes85/Controle-Mestre/issues/10), [#12](https://github.com/antoniomoraes85/Controle-Mestre/issues/12), [#16](https://github.com/antoniomoraes85/Controle-Mestre/issues/16) |
| R06 | **Execução vinculada:** iniciar sessão pela tarefa e registrar conclusão parcial; reenvio não duplica minutos; reabrir tarefa não apaga sessões; conclusão sem sessão não inventa estudo. | [#14](https://github.com/antoniomoraes85/Controle-Mestre/issues/14) |
| R07 | **Carga de reforço transparente:** explicar recomendação e sua evidência; reservar orçamento explicitamente ou apontar necessidade de substituir outra tarefa; medir resultado posterior. | [#13](https://github.com/antoniomoraes85/Controle-Mestre/issues/13), [#16](https://github.com/antoniomoraes85/Controle-Mestre/issues/16) |
| R08 | **Navegação consistente:** manter seleção de semana/dia entre telas; oferecer “Mover para…” utilizável sem arraste; validar larguras 390/1440, foco de teclado e estados não dependentes de cor. | [#4](https://github.com/antoniomoraes85/Controle-Mestre/issues/4), [#7](https://github.com/antoniomoraes85/Controle-Mestre/issues/7), [#44](https://github.com/antoniomoraes85/Controle-Mestre/issues/44) |

Ordem sugerida de discussão: R01–R04, depois R05–R08. Reutilizar o motor existente antes de introduzir outro mecanismo de recomendação. Nenhuma inferência sobre algoritmo, banco de dados ou tecnologia privada da Guruja é necessária para esses requisitos.

## 6. Dúvidas para investigação posterior

1. O organizador mantém o conteúdo e a identidade das atividades ou pode regenerá-las? Como trata iniciado, concluído e execução parcial?
2. Indisponibilidade é recorrente ou por data? Há duração diária configurável e limites individuais?
3. O excesso é redistribuído dentro da meta, levado à próxima semana ou devolvido ao professor? É possível não conseguir acomodar tudo?
4. Mover manualmente requer arraste, menu ou ambos? Existem ordem intradiária, tarefas fixadas e desfazer?
5. Como metas são liberadas e encerradas? Uma meta equivale obrigatoriamente a uma semana civil?
6. Como são calculados progresso, estimativa de esforço e intensidades de reforço? Como extras afetam a meta principal?
7. Quais novidades de V4/V7 já chegaram a todos os alunos? A demonstração corresponde à interface atualmente oferecida?
8. A navegação anunciada para celular funciona com teclado, leitores de tela, orientação horizontal e conexão instável?

**Pendência de evidência:** inspeção visual direta das telas do vídeo e, se houver acesso autorizado posteriormente, teste dos fluxos no produto. A transcrição confirma o que foi dito, não o comportamento executado na interface. O acesso pelo leitor web ao YouTube falhou; a transcrição foi recuperada pelo conector de vídeo. Não se ampliou a pesquisa para outros vídeos ou plataformas.

**Conclusão:** os sete eixos foram analisados. A principal contribuição para o CONTROLE MESTRE é evoluir o planejamento já existente para uma agenda que preserve tarefas, explicite capacidade e conecte execução ao plano. A redistribuição descrita pela Guruja é uma referência funcional; seus detalhes internos permanecem desconhecidos.

