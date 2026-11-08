## v0.6.1 — compatibilidade com acervo externo e catálogo privado (07/11/2026)

- Reconhece MATERIAL TEÓRICO como pasta irmã de CONTROLE_MESTRE, com opção de configurar caminho absoluto válido pelo painel.
- Scanner local de PDFs por disciplinas numeradas e subpastas Teoria Principal, Teoria Simplificada/Simplificado, PASSO ESTRATÉGICO e QUESTÕES. Não altera arquivos.
- Catálogo privado de 125 aulas, conforme listas fornecidas (8 disciplinas; Direito Civil ainda sem sumário). Não publica os sumários nem PDFs no GitHub.
- Novas metas da trilha baseadas nas aulas do catálogo, evitando criar apenas tópicos genéricos; mantém IDs e tarefas da versão anterior.
- Vínculo de materiais pela aula correta (Aula 00, Aula 01 - Parte II etc.), sem sugerir PDF de aula diferente por engano.
- Testes adicionais com pastas numeradas, quatro tipos de arquivo, preservação e falta de catálogo.
- Sem sincronização dos CSVs/Macros antigos do Anki, sem acesso ao desktop remoto, sem conclusão automática de estudo.

# Histórico de versões — CONTROLE MESTRE

## v0.6.0 — 2026-11-07 — Trilha fiscal de nove disciplinas + AnkiConnect local

- Currículo inicial de nove disciplinas determinado pelo usuário, com 50 assuntos preliminares e migração aditiva.
- Planejamento independente com prévia/confirmar, execução real e sequência teoria–questões–Passo Estratégico–revisões–erros.
- Leitura local do AnkiConnect (versão, baralhos, contagens) com retratos idempotentes e sem escrita no FSRS, notas ou cartões.
- Varredura de PDFs com classificação automática por pastas, preservando associações manuais anteriores.
- 64 testes automatizados (incluindo Anki e migração) concluídos; JS validado. Homologação Windows pendente.
- Guia: `GUIA_CONTROLE_MESTRE_V06.md`. Requisitos que exigem arquivos pessoais permanecem bloqueados.


## v0.5.1 — 2026-11-07 — Conectores locais iniciais e estabilidade

**Implementado:**
- Biblioteca local dos PDFs do Estratégia com metadados, SHA-256, identificador de aula e mapeamento manual disciplina/assunto, sem armazenar PDF/texto no SQLite.
- Gestão de atalhos de cadernos Qconcursos e importação de resultados **fornecidos pelo estudante** em CSV (não há API oficial integrada), com validação, prévia, transação e deduplicação por ID/hash.
- Diretórios fixos com validações anti-traversal para PDF/CSV.
- Backup local SQLite via API de backup, verificação de integridade e retenção limitada, disparado antes da migração ao iniciar.
- Porta 8765 reservada para AnkiConnect; aplicação inicia em 8771–8780.
- Interface "Materiais e Qconcursos" na web local.
- Guia de instalação e limites jurídicos/técnicos.

**Validação:** 48 testes Python, sintaxe JS (`node --check`), compilação Python. Navegação Playwright bloqueada por política do ambiente, portanto teste de navegação em Windows ainda pendente.

**Pendente:** adicionar PDFs reais e vincular aulas, validar importação com dados autorizados do Qconcursos, completar conexão read-only com AnkiConnect, mapear edital, OCR/indexação semântica opcional e homologação visual.

**Não é SaaS:** serviço estritamente local, sem login, autenticação, faturamento ou sincronização oficial.