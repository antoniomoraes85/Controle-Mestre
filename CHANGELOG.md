## v0.7.0 — Motor de cronogramas, identidade premium e testes herméticos (2026-11-08)

- **Identidade visual premium:** Substituição da identidade verde-limão por paleta nobre em amarelo principal (#FFD600), amarelo intenso (#FFEA00), dourado (#D4A017) e grafite profundo (#101114).
- **Símbolo e marca:** Peão de xadrez em posição de vitória superando o rei tombado, com brasão heráldico, livro aberto e ramos de louro em vetor SVG puro de alta precisão.
- **Catálogo de assets:** Versões horizontal, vertical, ícone quadrado, favicon multi-resolução (.ico, .svg, .png), versões monocromáticas e adaptadas para fundo claro e menu lateral em web/assets/branding/. Originais do ChatGPT preservados em originals/.
- **Banner hero com parallax:** Efeito parallax com 5 camadas independentes (fundo, iluminação, cena de xadrez, partículas e conteúdo), movimento suave via 
equestAnimationFrame e aceleração por GPU, adaptável a dispositivos móveis e com suporte estrito a prefers-reduced-motion.
- **Harmonização da interface:** Interface dark mode premium, com cronômetro, métricas, cartões, tabelas, modais e barra de navegação ajustados à nova paleta.
- **Testes herméticos:** Suíte de 112 testes automatizados 100% aprovada através de isolamento sintético (	ests/_isolation.py), sem dependência de PDFs externos ou catálogo privado.
- **Entrega 1 do motor de cronogramas:** Novo schedule.py aditivo com escala 24×72 configurável, ocorrências de indisponibilidade, ciclo contínuo por execução real, cronograma fixo e prévia/aplicação com backup verificado e controle de versão. Detalhes em docs/CRONOGRAMAS_V07_ENTREGA1.md.

## v0.6.2 — Correção do catálogo visível e integração inicial TEC Avançado (2026-11-07)

- Corrigido bug de renderização: 125 aulas previamente cadastradas no CSV agora aparecem no painel **Materiais e TEC Concursos**, independentemente da descoberta de PDFs.
- Separadas as contagens de **aulas descritas** e **PDFs reais encontrados**. A tela informa caminho esperado da pasta externa, com configuração manual segura.
- Criadas rotas de cadernos TEC (validação HTTPS do domínio oficial) e importador CSV de resultados elaborados pelo usuário em `dados/importacoes/tec/`; banco legado Qconcursos mantido sem migração destrutiva.
- Cadastro manual de questões com `TEC Concursos` como plataforma-padrão; tipos de material Teoria, Simplificado, Questões, Passo Estratégico.
- Conector TEC limitado a links e resultados autorizados; sem login, scraping, APIs não documentadas ou coleta automática de dados de conta.
- Guia de atualização sem mover PDFs/Anki; suíte Python e smoke JS executados. Homologação visual Windows pendente.

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
