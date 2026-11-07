# Histórico de versões — CONTROLE MESTRE

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