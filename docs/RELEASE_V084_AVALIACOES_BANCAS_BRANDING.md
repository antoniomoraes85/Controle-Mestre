# CONTROLE MESTRE v0.8.4 — Avaliações, bancas, biblioteca e identidade

## Funcionalidades implementadas
- Menu **Simulados e redações**: cadastro independente de provas completas de **Português**; concurso, banca, ano da prova, data de resolução, questões totais/acertos/erros/brancos, tempo e notas.
- Gráficos separados de evolução de provas de Português, simulados e redações; estatísticas por banca para cada categoria. Simulados e redações antigos continuam intactos.
- Menu **Questões**: gráfico com percentual ponderado por disciplina/banca calculado da tabela `questions`, sem somar simulados e redações. Menos de 10 questões por combinação marca amostra pequena.
- Menu **Materiais e TEC Concursos**: mostra o assunto do catálogo, o PDF associado e links de cadernos (TEC, QConcursos e `questo.es` por HTTPS) ao lado. Cadernos existentes são associados quando disciplina/assunto coincidem; é possível vincular manualmente o caderno e salvar no SQLite.
- Os assuntos das aulas vêm de `aulas_primeiro_ciclo.csv` existente no computador do usuário: o aplicativo **não inventa assuntos faltantes**. O catálogo é procurado prioritariamente em `%LOCALAPPDATA%\ControleMestre\dados\catalogo\aulas_primeiro_ciclo.csv`; se não existir, há tentativa de leitura do diretório legado no app. Para recuperar a antiga lista, copiar **somente o CSV** para a pasta persistente, sem alterar ou substituir o banco.
- Nova logo tipográfica de alta legibilidade; bloco Minha preparação simplificado para Meu Ambiente; slogan principal da plataforma em destaque.
- Peão metálico prateado avança e derruba o rei dourado em animação SVG/CSS no painel inicial. É uma ilustração vetorial tridimensional sombreada, **não vídeo filmado de peças reais nem foto fotorrealista**. A animação é desativada quando o dispositivo informa preferência por movimento reduzido.

## Regras de integridade
1. Provas de Português → tabela `portuguese_exams`, independente de `mock_exams`, `essays` e `questions`.
2. Comparações por banca usam acertos/total ponderados pelo volume real; redações usam a média das notas normalizadas.
3. Links de cadernos não são PDFs nem textos de provas. Nenhum PDF protegido é hospedado, copiado para o GitHub ou reescrito.
4. O banco de dados do usuário permanece em `%LOCALAPPDATA%\ControleMestre\dados\controle_mestre.db`.
5. Scripts de atualização devem sempre criar backup SQLite consistente **antes** de atualizar o código; não mesclar automaticamente histórico da pasta antiga com o atual.
6. Esta branch depende dos PRs anteriores. Não executar merge automático ou alegar homologação visual no Windows antes de testes no computador do proprietário.

## Verificação recomendada no Windows
1. Fechar o servidor antigo; manter cópias de segurança separadas.
2. Instalar a versão 0.8.4 com instalador de revisão fixa; verificar `/api/health`.
3. Abrir a página inicial, conferir slogan, marca e animação do peão.
4. Registrar uma prova de Português real e confirmar que aparece somente em sua categoria.
5. Registrar questões e confirmar gráfico da banca correspondente.
6. Abrir Materiais e TEC, conferir assunto do CSV e vincular URL HTTPS de caderno; reiniciar e confirmar persistência.
7. Verificar que histórico de simulados, redações, questões, horas e Anki não foi alterado.

## Pendências
- O próximo edital oficial SEFAZ-RS e os conteúdos do Passo Estratégico não são fornecidos por esta funcionalidade; incidências históricas dos Bizus têm fonte e limites próprios no guia de estudos.
- O catálogo depende de listas privadas do usuário; sem CSV, a plataforma não apresenta nome de aulas que não conhece.
- Necessária homologação visual e de comportamento da cena de xadrez no Windows do proprietário antes de encerrar ajustes estéticos.
