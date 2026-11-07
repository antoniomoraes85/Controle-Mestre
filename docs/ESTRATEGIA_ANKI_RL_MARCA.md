# ESTRATÉGIA, ANKI, RL, DOMÍNIO E MARCA — DECISÕES DE ENGENHARIA
Data: 2026-11-07. Documento de arquitetura exploratória, não comprova direito de uso de materiais nem eficiência pedagógica.

## 1. Integração com os cursos do Estratégia
**Conclusão:** é viável integrar seu próprio fluxo de estudo e metadados das aulas. Não foi identificada API pública oficial que conceda acesso programático ao catálogo, histórico do LDI e conteúdo protegido. Não presumir acesso com automação.
**Nível A — recomendado já:** registrar no CM nome do curso, disciplina, professor, aula, versão, URL da área do aluno e tópico(s) do edital. A tarefa oferece botão 'Abrir aula no Estratégia' e permite registrar leitura, páginas estudadas, horas, grifos próprios e questões. O aluno acessa diretamente sua conta.
**Nível B — importar dados seus:** exportar legalmente anotações, grifos ou planilha própria, com importador local opcional e campos de origem/data, sem gravar material protegido em GitHub. Respeitar o que o LDI permite exportar.
**Nível C — PDFs locais:** processar metadados e, caso os termos aplicáveis permitam, indexação privada para busca pessoal no dispositivo. Não enviar PDF integral para API de IA por padrão; autorização e avaliação de licença necessárias. Não disponibilizar ao SaaS ou usuários que não tenham licença.
**Nível D — API comercial:** negociar formalmente com Estratégia para permitir sincronização de matrículas, progresso e/ou material sob acordo. A ausência de API documentada não permite scraping de login, burlar DRM, interceptar endpoints internos ou redistribuir PDF.
**Arquitetura proposta:** StudyResource(id, provider, account_scope, course, lesson, title, version, type, source_url, local_path_optional, copyright_status, linked_topic_ids, checksum, imported_at). StudyActivity(resource_id, topic_id, expected_minutes, actual_minutes, result, external_key). Proveniência separa recurso, progresso e questão.
**Regras:** links abertos com autenticação no domínio do Estratégia; não armazenar senha; sem download automático em massa; opt-in para qualquer IA remota; revisão jurídica do contrato aplicável.
Fontes: https://www.estrategiaconcursos.com.br/pagina/termos-de-uso-20260731/ ; https://www.estrategiaconcursos.com.br/blog/ldi-livro-digital-interativo-saiba-tudo/ ; https://www.estrategiaconcursos.com.br/faq/
GitHub: CM-010, CM-024, CM-025.

## 2. Anki: integração técnica preferencial
AnkiConnect disponibiliza API HTTP LOCAL e sua porta padrão é **8765**; risco de colisão direta com porta padrão do atual CM. Reservar porta do CM distinta, testar handshake do serviço e restringir origem.
Passo 1: consulta somente leitura de decks, coleção e logs permitidos; consentimento por perfil; mapear disciplina/tópico usando prefixos de deck e tags.
Passo 2: importar incremental com external_key/card_id, timestamps e source_system=anki; apenas uma origem computa cada atividade. Um estudo em CM e uma revisão do Anki não devem ser somados como se fossem duas sessões diferentes.
Passo 3: sugerir cards a partir dos erros, revisar manualmente e só então adicionar ao Anki; não alterar intervalos FSRS por conta própria.
FSRS já é algoritmo de agendamento sofisticado; para a plataforma própria, é preferível consumi-lo a reinventar a repetição espaçada.
Fontes: https://github.com/ankicommunity/anki-desktop-addon-connect ; https://faqs.ankiweb.net/what-spaced-repetition-algorithm.html
GitHub: CM-002, CM-021, CM-022, CM-023.

## 3. Questões e incidência por banca
Priorizar métricas do próprio usuário: disciplina, assunto, banca, data, acerto, tempo, causa de erro, revisão prévia e documento de origem. Importação de exportações autorizadas e links a cadernos, sem baixar conteúdo de terceiros ou republicar questões.
Incidência por edital deve mostrar fonte, período, denominador, número de provas e incerteza; preferir cálculo próprio em dados com uso autorizado. Não converter taxa simples de acerto em probabilidade de aprovação.
GitHub: CM-015, CM-016, CM-026, CM-028, CM-029.

## 4. IA generativa: recurso de apoio, não motor autônomo
RAG híbrido: recuperar lei oficial, edital e anotações pessoais licenciadas; resposta traz fonte e data; IA pode explicar erro, organizar revisão e propor um plano, mas NUNCA reescreve o cronograma sem confirmação.
Camadas: documentos locais autorizados → indexação com ACL → busca e filtros por vigência → LLM opcional → validação e citações → intervenção do usuário. Separar custos/latência/limites e não dar acesso por padrão ao acervo pessoal.
Começar com modelos via API de forma opcional. A assinatura do ChatGPT não equivale a crédito de API. Servidor MCP pessoal poderá expor leituras agregadas com permissão explícita; evitar escrita inicial.
GitHub: CM-030, CM-032.

## 5. Reinforcement Learning: quando faria sentido
**É possível pesquisar, mas é prematuro utilizá-lo como planejador principal.** O CM possui hoje heurística de prioridades e dados históricos ainda insuficientes para identificar ganho causal de uma política.
Formulação: estado/contexto x(t) = confiança de domínio, desempenho recência, peso do edital, atraso de revisão, causa de erro, tempo disponível e restrições do dia; ação a(t) = escolher tópico, modalidade e duração; recompensa r(t+k) = retenção medida em questão posterior/simulado equivalente, ajustada por tempo, fadiga e cobertura de edital; restrições pedagógicas e limite semanal.
Sequência recomendada:
1. v0.5 heurístico auditado com baseline fixo e pesos do edital; registrar decisão, contexto, versão e justificativa.
2. Medir retenção a 7/14/30 dias e evolução em bancos/simulados comparáveis. Atraso entre ação e resultado exige cuidado com atribuição.
3. Introduzir modelo supervisionado/calibração de probabilidade por tema, com validação temporal e tratamento cold-start.
4. Com dataset adequado e consentimento, avaliar **contextual bandits** offline, com IPS/DR e análise de suporte/propensities; um histórico determinístico sem exploração não permite inferir contrafactuais de modo confiável.
5. Modo sombra: modelo sugere sem alterar a semana; comparar estabilidade e segurança.
6. Experimentação prospectiva autorizada em grupo, com randomização limitada, baseline, mínimo de dados, guardrails e rollback. Não otimizar exclusivamente horas, cliques ou % concluído.
7. Só se houver evidência sustentada considerar RL sequencial mais complexo (MPC/RL, PPO, DQN etc.), com auditoria de causalidade, proteção contra reward hacking e custo computacional.
Referências científicas (contexto, NÃO evidência sobre o Guruja ou CM): https://pubsonline.informs.org/doi/10.1287/ited.2025.0174 ; https://proceedings.iclr.cc/paper_files/paper/2025/hash/87eb265e8898a7e245d61f01cea4d906-Abstract-Conference.html ; https://www.nber.org/papers/w34950 .
GitHub: CM-033, CM-034, CM-035, CM-036, CM-044.

## 6. Domínio e exposição pública
**Não é necessário domínio agora para desenvolver em localhost ou GitHub.** Registrar logo após escolha e triagem do nome, sem aguardar a plataforma completa, para reduzir risco de perder endereço desejado. Domínio é independente de hospedagem, login e SSL.
Registro.br informa R$ 40/ano para domínio .br no momento da pesquisa; confirmar valor e disponibilidade no checkout. Não foi feita consulta definitiva de disponibilidade de nomes no Registro.br.
Fluxo: shortlist → buscas semelhantes INPI (classes pertinentes, p.ex. software/serviço tecnológico e educação) → domínio .com.br/.com/redes → revisão jurídica → reservar 1–3 anos → manter DNS estacionado → SaaS apenas quando seguro.
Fontes: https://registro.br/dominio ; https://www.gov.br/inpi/pt-br/servicos/marcas/guia-basico ; https://www.gov.br/inpi/pt-br/plataforma-integrada-de-atendimento/marca-x-nome-empresarial-x-dominio

## 7. Nome comercial — opções PROVISÓRIAS
- CONTROLE MESTRE: reconhecível para o proprietário e histórico de 2023, porém descritivo/genérico e pouco diferenciado; manter como codinome do GitHub.
- **ESTUDEXA**: minha hipótese de marca preferida; sonoridade direta para estudos, memorável e boa para expansão a outros exames. Precisa busca INPI, registros e homônimos.
- **TRILHORA**: reforça a ideia de trilha e controle de tempo; avaliar compreensão e grafia.
- **METRIAVA**: evoca métricas e evolução, menos explícita sobre educação; demanda explicação do produto.
Busca geral na web não encontrou presença dominante óbvia de Estudexa/Trilhora/Metriava no recorte realizado, o que **não prova** disponibilidade jurídica nem de domínio. Não existe parecer de registrabilidade; não comprar marca sem pesquisa de anterioridade.
Evitar nomes já muito usados como Nexora, Cognivra, Ritma e Ciclora (busca identificou usos comerciais).
Subtítulo sugerido se o nome for aprovado: 'Estudexa — Planejamento inteligente de estudos'. Nome interno da aplicação permanece CM até decisão formal.
GitHub: CM-042, CM-043.

## 8. Custos e equipe — decisões
Versão pessoal local pode permanecer sem mensalidade de servidor; há custo de tempo, manutenção, IA opcional, domínio e possivelmente aconselhamento jurídico/serviços.
Futuro SaaS: orçamento separado de nuvem, storage, autenticação, monitoramento, pagamentos, suporte e curadoria; não prometer substituição integral de mentoria humana.
Próxima execução: P0 CM-002, CM-004, CM-003 antes de conectar Anki; em paralelo CM-009, CM-015, CM-024. Manter até 3 issues em desenvolvimento.
Ferramentas: ChatGPT — ciência e especificação; Codex — implementação versionada; Work — auditoria, benchmarks, documentação e QA; Antigravity — programação visual e testes, sempre com Git e revisão.