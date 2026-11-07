# CONTROLE MESTRE v0.5.1 — PDFs do Estratégia e Qconcursos (local)

**Status:** versão de teste local e monousuário. Não existe autenticação, SaaS, busca de provas por API nem sincronização automática de login com Estratégia/Qconcursos. Esta versão preserva a heurística v0.5 e o banco do usuário.

## Atualização no Windows sem perda de dados
1. Encerre o CONTROLE MESTRE e o Streamlit anterior.
2. Faça cópia externa de `dados/controle_mestre.db` antes da atualização, com o aplicativo fechado.
3. Extraia todo o ZIP v0.5.1 em pasta **nova** e coloque o banco antigo na pasta `CONTROLE_MESTRE/dados/`, se desejar preservar registros.
4. Execute `iniciar_windows.bat` e mantenha o terminal aberto. O novo painel usa **127.0.0.1:8771** ou outra porta livre de 8771 a 8780. **A porta 8765 foi reservada para o AnkiConnect.**
5. No menu, abra **Materiais e Qconcursos**.
6. A aplicação cria automaticamente um backup SQLite verificado em `dados/backups/`, no primeiro início de cada dia em que o banco existe. É complemento, não substituto de backup externo periódico.

## Indexar PDFs já obtidos legitimamente do Estratégia
1. Copie seus PDFs completos para `CONTROLE_MESTRE/dados/materiais/estrategia/`. Pode criar subpastas por disciplina ou curso.
2. Na tela **Materiais e Qconcursos**, clique em **Atualizar biblioteca**.
3. O aplicativo cataloga nome, tamanho, SHA-256, identificador de aula quando presente no filename e, se PyMuPDF estiver instalado, número de páginas e título do PDF.
4. Clique em **Vincular** e escolha disciplina, assunto do edital, curso e número da aula. Associação é manual para evitar mapeamentos falsos.
5. O catálogo **não guarda no SQLite o PDF completo**, questões ou textos das aulas, tampouco faz upload para GitHub ou IA. Os PDFs continuam na pasta privada.

**Observações:** nenhum PDF foi entregue com esta atualização; o usuário ainda fornecerá o acervo. Arquivos protegidos por senha e PDFs digitalizados não são automaticamente desbloqueados/OCRizados. Não há busca RAG ou geração de resumos nesta versão. Essas capacidades exigem uma etapa própria, verificação de licenças e acesso autorizado aos arquivos. Por precaução, não expor os PDFs a usuários do futuro produto SaaS.

## Qconcursos (assinatura pessoal)
**1. Salvar atalhos**: abra seu caderno/filtro no site oficial Qconcursos, copie a URL e use **+ Salvar link**. O clique abre o navegador no site Qconcursos, em que você continua usando sua conta normalmente. A plataforma não coleta login/senha.

**2. Importar seus resultados por CSV**: salve um CSV UTF-8 na pasta `CONTROLE_MESTRE/dados/importacoes/qconcursos/`, com uma linha por bateria de questões e os cabeçalhos:

`data;disciplina;assunto;total;acertos;banca;link;id`

Exemplo **totalmente sintético**, para salvar em `meus_resultados.csv`:

```csv
data;disciplina;assunto;total;acertos;banca;link;id
07/11/2026;Direito Tributário;Obrigação tributária;20;15;FCC;https://www.qconcursos.com/questoes-de-concursos/questoes;minha-bateria-001
06/11/2026;Contabilidade Geral;Patrimônio;10;8;FCC;;minha-bateria-002
```

Na tela, selecione o CSV e escolha **Pré-visualizar resultados**. Confirme os números antes de aplicar. O importador verifica formato, contabiliza resultados e usa identificadores para evitar duplicação. Reimportar o mesmo arquivo não duplica resultados; blocos com IDs iguais também não.

**Restrição:** a consulta de suporte público do Qconcursos não confirmou uma API oficial de integração nem uma exportação CSV padronizada de desempenho. O arquivo acima é preparado pelo usuário (manual ou a partir de dados que ele tenha autorização para exportar). Não realizar scraping, automação de login, extração em massa de enunciados ou redistribuição de conteúdo licenciado.

**Prevenção de duplicidade:** não inclua no CSV as mesmas baterias já cadastradas manualmente no CONTROLE MESTRE. A ferramenta deduplica importações por hash/ID, mas não consegue detectar automaticamente que um registro manual representa a mesma atividade.

## Estado técnico e limites
- Implementados: catálogo local com vínculo manual; atalhos de cadernos; importação de resultados CSV com prévia e anti-duplicação; backup pré-inicialização; reserva da porta 8765.
- Pendente: extração semântica de PDFs, indexação RAG local, classificação automática de aulas conforme edital, importação oficial Qconcursos por API, AnkiConnect read-only e homologação visual Windows.
- Testes Python/HTTP e sintaxe JS verificados no desenvolvimento. Teste visual via navegador automatizado **bloqueado pelo ambiente**; valide a interface no Windows.

## Referências e tarefas
- [Termos de uso do Estratégia](https://www.estrategiaconcursos.com.br/pagina/termos-de-uso-20260731/)
- [Termos de uso Qconcursos](https://www.qconcursos.com/termos-de-uso)
- [Suporte: cadernos Qconcursos](https://suporte.qconcursos.com/pt-BR/articles/11655308-como-criar-um-caderno-de-questoes)
- [AnkiConnect](https://github.com/amikey/anki-connect)
- GitHub: CM-002 (porta), CM-003 (backup), CM-010/024/025 (PDFs), CM-026/027 (resultados Qconcursos), CM-004 (homologação).