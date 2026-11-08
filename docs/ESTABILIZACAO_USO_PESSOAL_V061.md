# Plano de estabilização para estudo diário — v0.6.1

Atualização: 2026-11-07. Objetivo: usar o CONTROLE MESTRE sem depender de créditos de pesquisa/geração de código, preservando estudos e dados privados.

## Decisão de escopo
- Congelar novas funcionalidades e manter a v0.6.1 como candidata a versão pessoal de estudos.
- Priorização: **integridade de dados > facilidade de instalação > planejamento diário/semanal > catálogo externo > Anki read-only > melhorias visuais**.
- Não começar IA, RAG, RL, pagamentos, usuários, hospedagem nem análise completa de PDFs até passar na homologação funcional local.
- Nunca expor servidor ou AnkiConnect para fora de `127.0.0.1`.
- Repositório público não recebe históricos, banco SQLite, PDFs, macros do usuário nem catálogo particular.

## Evidência obtida no ambiente de desenvolvimento
- 70 testes `python -m unittest discover -s tests -q` passaram após a extração do ZIP v0.6.1.
- Servidor respondeu `GET /api/health` com versão `0.6.1`, modo `private-local`, porta 8771.
- Respostas HTTP 200 verificadas para `/`, `/app.js`, `/style.css`, `/modules/fiscal.js`, `/modules/anki_bridge.js`, `/api/overview`, `/api/sources`.
- ZIP contém catálogo local de 125 aulas, arquivos de software e pastas vazias, sem `.db`, `.xlsm`, `.bas` ou PDFs de terceiros.
- Nenhum teste do ambiente substitui a homologação visual no **Windows do titular** nem garante leitura dos PDFs e da coleção Anki reais.

## Preparação do computador (primeiro acesso)
1. Fechar todos os servidores antigos, Anki e planilhas Excel em uso.
2. Copiar a pasta atual `CONTROLE_MESTRE` inteira para um backup fora da instalação nova; **não apagar originais**.
3. Descompactar o ZIP v0.6.1 em uma pasta nova chamada `CONTROLE_MESTRE`, dentro de `Controle-Mestre-main/`, ao lado de `MATERIAL TEÓRICO/` e `ANKI/` (sem mexer nessas duas). Se já existir a pasta antiga, renomeá-la para `CONTROLE_MESTRE_ANTIGO` antes.
4. Copiar **apenas** `dados/controle_mestre.db` do backup antigo para a nova instalação, se houver histórico a manter; conservar a cópia original.
5. Executar `iniciar_windows.bat`. Verificar versão `0.6.1` e URL informada no terminal, normalmente `http://127.0.0.1:8771`.
6. Abrir `Materiais e Qconcursos`, verificar raiz externa `MATERIAL TEÓRICO` e acionar `Atualizar biblioteca`. Os PDFs permanecem intactos no local original.
7. Abrir `Trilha Fiscal RS + SC`, conferir nove disciplinas, catálogo de 125 aulas, capacidade semanal e prévia **antes de aplicar**.
8. Configurar disponibilidade real de plantões. Se a soma diária não atingir 25h, reduzir meta ou elevar disponibilidade real em dias livres: não inventar horas.
9. Abrir Anki e testar `Revisões e Anki → Verificar conexão`. É aceitável falhar caso o complemento ainda não esteja instalado. A sincronização inicial é **read-only** de inventário; não é importação de revlog.
10. Criar um teste sintético pequeno: uma tarefa de teoria; uma tarefa com questões; registrar minutos e acertos; confirmar que métricas refletem exatamente um registro; depois voltar a usar dados reais sem duplicações.

## Portões de aceite da v0.6.1 pessoal
| Gate | Verificação | Status inicial |
|---|---|---|
| G1 | Inicia no Windows com interface funcional e versão 0.6.1 | Pendente teste Windows |
| G2 | Faz backup e mantém base existente intacta durante a atualização | Pendente teste Windows |
| G3 | Localiza pasta externa sem mover PDFs e vincula a aula correta pelo nome de arquivo | Pendente PDFs reais |
| G4 | Exibe 125 aulas, não inventa as de Direito Civil; gera prévia com 25h e plantões | Backend testado, interface pendente |
| G5 | Aplicar semana só com confirmação, preservar registros e evitar duplicação de metas | Backend testado, validação manual pendente |
| G6 | Anki aberto + AnkiConnect responde; inventário não altera cards, FSRS, nem horas líquidas | Pendente conexão local do usuário |
| G7 | Qconcursos: cadernos por link; CSV consentido com prévia e sem duplicidade | Testes sintéticos, fluxo real pendente |

## Como usar o Antigravity sem dispersão
Executar **uma verificação por vez**, em branch `fix/homologacao-v061` e sem permissão para publicar PDFs ou dados pessoais. Trabalhar sobre a última versão do GitHub. Limitar alterações a defeitos reproduzíveis; proibir refatoração geral e instalação de SaaS.

### Prompt curto recomendado
> Atue como QA de uma aplicação Python + JS local e monousuário. Repositório: antoniomoraes85/Controle-Mestre, versão v0.6.1. Prioridade: homologar no Windows a abertura `iniciar_windows.bat`, tela Trilha Fiscal RS + SC, prévia semanal com dias de plantão, catálogo externo `MATERIAL TEÓRICO` e leitura local do AnkiConnect. Primeiro rode testes e reproduza um defeito. Não modifique a pasta `MATERIAL TEÓRICO`, `ANKI`, `.xlsm`, `.bas`, PDFs ou banco pessoal; trabalhe com fixtures sintéticas. Não altere o algoritmo pedagógico nem reescreva o frontend sem necessidade. Para cada correção, faça mudança mínima, teste automatizado de regressão, documente resultado, abra PR e forneça link. Não faça merge, delete ou force push sem minha aprovação. Termine após **uma** correção ou um relatório de homologação.

## Próximas melhorias após homologação (sem bloquear uso diário)
- Direito Civil: receber a relação oficial de aulas do curso do proprietário.
- Anki: histórico granular e reconciliação com CSV/planilha sem dupla contagem.
- Qconcursos: padronizar resultados exportáveis autorizados e classificação individual de erros.
- Pedagogia: harmonizar os dois motores, preservar IDs de pendências, retestes e revisão efetiva de erros.
- Conteúdo: revisar legislação/atualização editorial e metadados do Passo Estratégico; RAG opcional, apenas após licença e necessidade.

## Política de falha
- Se a aplicação **não iniciar**, preservar o backup e executar `diagnosticar_windows.bat`, sem alterar o acervo.
- Se algum PDF não for identificado, vincular manualmente a aula correta e registrar o nome real do arquivo; nunca atribuir uma aula aleatória.
- Se AnkiConnect falhar, estudar normalmente pelo Anki separado; não usar dado desatualizado como zero.
- Se a prévia for insatisfatória, **não aplicar**: revisar disponibilidade e hora-meta, manter o último plano confiável.

**Status geral:** versão local candidata a uso pessoal; ainda não homologada pelo proprietário. Trabalho avançado de Work/Codex deve permanecer congelado enquanto as integrações e o aprendizado não forem validados com os dados reais.