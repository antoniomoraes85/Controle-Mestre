# Controle Mestre — Especificação dos módulos premium observados (08/11/2026)

**Origem:** oito capturas fornecidas pelo titular sobre apresentação pública de recursos da Guruja, captura atual do Controle Mestre e manual próprio de 2023 (53 páginas). **Escopo:** análise de requisitos e implementação independente. Capturas externas são referência funcional, **não** autorização para copiar interface, textos extensos, dados, marca ou código.

## 1. O que as imagens permitem concluir — e o que não permitem

| Tela apresentada | Evidência visual | Proposta independente | Limitação da evidência |
| --- | --- | --- | --- |
| Reforços inteligentes | Cartão «Reforço Intenso» com motivo e instruções; abas de conteúdo/material | Reforços em 3 níveis, explicação com evidências, materiais e reavaliação | Não comprova pesos, algoritmo interno ou acurácia |
| Detalhamento de erros | Cadastro por bateria e por questão; categorias «Desconhecimento», «Esquecimento», «Confusão conceitual», «Erro de interpretação», «Falta de atenção», «Falta de tempo» | Modelo por item com IDs internos, causa opcional, nota de correção e bateria associada | Não prova API pública de questões ou acesso ao catálogo interno |
| Orientações customizadas | Instruções por assunto/modalidade; citação de banca e exemplos de comando | Guia técnico contextual ao edital e à banca **somente com fontes**; orientação editável e versionada | Não transferir exemplos específicos entre bancas sem evidência |
| Organizador | Calendário semanal com atividades, reforços, dias indisponíveis e opções de distribuição | Agenda com drag opcional, acessível por teclado, prévia, preservação de IDs e orçamento | A captura não documenta regras de redistribuição/rollback |
| Minha meta em múltiplas telas | Layout responsivo de KPIs, atividade e calendário | Melhorar hierarquia «Meta → Fazer agora → Registrar → Entender» | KPIs exibidos na demonstração não refletem usuário atual |
| Minhas análises | Abas «Presente», «Variação», «Trajetória», «Causa», «Decisão» e histórico | Criar relatórios determinísticos com snapshot de fontes; comparações entre períodos | Na captura consta **Em breve**. Não afirmar disponível a todos |
| Arena / revisão | Novos, aprendendo, a revisar, streak e botão «Iniciar revisão» | Usar Anki/FSRS como motor de flashcards, consolidar fila e métricas | Não justificar criar scheduler concorrente ou copiar marca/interface |

## 2. Implementação inicial publicada neste PR

- `smart_reinforcement.py`: motor **somente leitura** que cruza questões por assunto (janela de 90 dias), revisões vencidas e erros abertos; categoriza em **Intenso**, **Moderado**, **Pendente** ou **Diagnóstico**, e monta instruções com regras transparentes.
- `web_server.py`: disponibiliza `reinforcements` no `overview` sem endpoint novo destrutivo.
- `web/modules/adaptive.js`: painel «Reforços inteligentes» dentro da seção de planejamento inteligente.
- `tests/test_smart_reinforcement.py`: oito testes sintéticos de triagem, amostra pequena, causas, pendências, janela histórica e ausência de mutações.
- **Critério conservador inicial:** intenso se >=15 questões e >=6 erros e taxa de erro >=45%; moderado se >=15 e >=4 erros e taxa de erro >=25%. São limiares **heurísticos provisórios, não validados pedagogicamente**. Sem amostra, não classificar como dificuldade.
- **Limite essencial:** campo atual `questions.error_type` guarda **uma causa por bateria**, não por questão. A interface explicita a limitação. Não extrapolar para contagem de causas individuais.

## 3. Próxima etapa P0 — detalhamento individual de erros

Modelo proposto (migração aditiva com backup):

`question_attempt`: ID estável; `question_batch_id`; `question_ref` opcional (plataforma/origem + identificador autorizado); `topic_id`; resultado (certo/errado/não resolvido); tempo observado opcional; origem; data; deduplicação e retificação auditável.

`error_reason`: tentativas erradas com zero ou mais causas explícitas (incluindo não especificado), principal/secundária, explicação, comentário do estudante, estágio (aberto/revisado/retestado), revisão antes de resolver, momento da consulta ao gabarito (por questão/ao fim).

**Validação:** acertos + erros + não resolvidas = total da bateria; «não resolvida» não é «errada» automaticamente sem regime de pontuação; chutes são indicador transversal. Contagens por causa não podem ultrapassar erros atribuíveis quando se usar uma causa principal por questão. Não usar IDs externos sem autorização/licença. Preserve dados de lotes anteriores, sem inventar granularidade.

## 4. Próxima etapa P1 — reforços com fechamento de ciclo

Fluxo: questão errada → causa declarada → associação ao assunto → evidência de recorrência → reforço por intensidade → material autorizado/questões próprias → reteste posterior → melhora/sem melhora → decisão de manter, intensificar ou encerrar. Marcar reforço «feito» não equivale a domínio. Guardar baseline, resultado do reteste e intervalo temporal; evitar reforço eterno sem avaliação.

Separar **recomendação** da **atividade executável**; criar somente com confirmação do usuário. Não somar minutos de cronômetro, ciclo, Anki e importação como sessões independentes.

## 5. Próxima etapa P1 — orientações customizadas

Fonte de recomendações na sequência: resultado individual → edital/assunto → banca comprovada → incidência Passo Estratégico (estatística identificada) → relevância editorial Bizu → material local correspondente → restrições da agenda.

Formato de orientação: «Por que», «O que estudar», «Como executar», «Quanto tempo», «Material», «Como verificar que aprendeu», «Fonte/limitações». Se faltam evidências, emitir orientação geral e sinalizar explicitamente a lacuna; não gerar jurisprudência, súmulas, atualizações legislativas ou frequência por banca sem validação atual.

## 6. Próxima etapa P1 — organizador sem perda de histórico

Calendário 7/14 dias + lista, com atividades **principais**, **reforços** e **aprofundamentos** visualmente distintos. Marcar indisponibilidade, drag-and-drop *opcional*, mover/adiar por menu e teclado, reorganizar com prévia e confirmação, respeitar 24×72 e teto efetivo por dia. IDs persistem; alterar o plano não apaga sessões, revisões, tarefas iniciadas nem ciclos.

## 7. Próxima etapa P2 — Minha análise e Anki

- **Presente:** desempenho real por assunto e amostra.
- **Variação:** comparação entre janelas com tamanhos e denominadores.
- **Trajetória:** retenção, progresso de conteúdos e aderência, sem usar horas como sinônimo de aprendizado.
- **Causa:** distribuição *realmente declarada* dos erros por item ou por bateria identificada.
- **Decisão:** cenário de metas/proximidade da prova, déficit de tempo e priorização fundamentada.
- **Histórico:** snapshots com data, versão do algoritmo e consulta que originou as conclusões.

**Arena alternativa:** integrar ao Anki FSRS existente; aba unificada de «Novos / Aprendendo / A revisar» e histórico; contador de sequência de estudo é opcional e deve excluir descansos programados. Não alterar FSRS nem assumir que revisão de flashcard conta como hora líquida.

## 8. Requisitos de qualidade

- Preservar a estética própria CONTROLE MESTRE e não clonar visual Guruja.
- Nenhum PDF protegido, credencial, banco privado ou histórico pessoal no GitHub.
- Inspecionar branches PR #45, #46, #47 antes de integrar: cadeia de dependências e código local divergente.
- O PR atual baseia-se em `main`; integrar/atualizar antes de merge se outros PRs mudarem os mesmos módulos.
- Rodar suíte completa, testar navegador real em Windows, observar migração/backup, perfis vazios, input malicious, responsividade 390/1440.
- Sem homologação em dados locais reais, não anunciar paridade pedagógica, ganho estatístico, sincronização Anki ou software pronto para SaaS.
