# CONTROLE MESTRE v0.5 — Motor de planejamento inteligente

## Status
Versão **pessoal/local de teste**, compatível com o banco SQLite da v0.4.1. Não constitui alternativa pedagógica validada ao acompanhamento de um orientador. Não oferece autenticação, integração ao vivo com o Anki, usuários adicionais ou cobrança.

## Como instalar com segurança no Windows
1. Encerre os servidores das versões anteriores (ou feche as janelas pretas).
2. Faça uma cópia de segurança de `dados/controle_mestre.db` da sua versão anterior.
3. Extraia o ZIP v0.5 **inteiro** numa pasta nova.
4. Copie seu banco antigo para `CONTROLE_MESTRE/dados/controle_mestre.db`, se deseja preservar seu histórico.
5. Execute `iniciar_windows.bat` na pasta extraída.
6. Use o endereço **exibido no terminal**, pois uma versão antiga pode ocupar a porta 8765.
7. No menu lateral, abra **Inteligência de estudos**. Revise diagnósticos e a prévia semanal. Só depois clique em **Aplicar plano inteligente** para substituir as atividades pendentes.
8. Em **Planejamento**, defina a disponibilidade real para cada dia, inclusive plantões. Se a soma for menor que a meta de 25h semanais, a interface exibe a diferença.

## O que a v0.5 calcula
- Questões **avulsas** por assunto nos últimos **90 dias**; percentual ponderado por quantidade de questões.
- Desempenho não informado permanece `não aferido`, nunca `0%`.
- Até 14 questões em um assunto = **amostra insuficiente**, sem atribuição de baixa competência com base nesse percentual.
- Considera pesos de disciplinas e incidência **já cadastrada**, sem inventar dados de edital ou frequência da FCC.
- Considera revisões vencidas/para hoje, pendências do caderno de erros, última sessão e progresso cadastrado.
- Sugere uma modalidade por assunto: teoria, questões, revisão ou caderno de erros.
- Apresenta explicações para cada recomendação e um indicador heurístico relativo, **não uma chance de aprovação**.
- Calcula orçamento semanal, dias disponíveis, tarefas concluídas preservadas e minutos não distribuídos.
- A prévia é somente leitura; a aplicação pede confirmação explícita, preserva atividades concluídas e substitui exclusivamente as pendentes naquela semana, em uma transação SQLite.

## Limitações da primeira implementação
- `error_type` descreve o **erro predominante de uma bateria**, não um motivo individual verificado por questão.
- Ainda não estima esquecimento individual nem implementa integração AnkiConnect/FSRS.
- Os pesos de edital e incidência precisam de validação manual contra o edital oficial; valores existentes são **configurações**, não jurisprudência nem edital atual.
- Ausência de registro não significa ausência de estudo, nem 0% de domínio.
- A aplicação local não deve ser exposta à internet; não há login nem isolamento entre usuários.

## Validação
Execute `python -m unittest discover -s tests -v`. O backend e as novas rotas HTTP foram verificados com SQLite temporário. A navegação no navegador automatizado do ambiente de desenvolvimento foi bloqueada por política administrativa; **valide visualmente a interface no Windows**.

## Próximas etapas técnicas
1. Confirmar funcionamento no seu Windows e importar sua base real (mantida somente localmente).
2. Vincular planejamento à matriz verticalizada do edital e filtrar assuntos da FCC com fontes auditáveis.
3. Registrar motivos de erros por questão, sem duplicação de desempenho.
4. Conectar Anki por API local e estabelecer regras anti-dupla contagem.
5. Medir desempenho por simulados equivalentes antes de afirmar ganho de eficiência.
6. Migrar para backend com autenticação e banco segregado somente quando a v0.5 pessoal estiver homologada.