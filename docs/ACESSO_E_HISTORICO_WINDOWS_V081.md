# CONTROLE MESTRE v0.8.1 — acesso local com histórico persistente (Windows)

**Status:** implementação em branch de integração/PR #49; não é SaaS nem hospedagem pública. Código revisado por testes Python/HTTP e sintaxe JavaScript; homologação visual no Windows do titular pendente.

## Acesso

O programa usa `launch.py` e o painel HTTP privado em `127.0.0.1`, portas `8771–8780`; 8765 permanece reservada ao AnkiConnect. Não compartilhe a porta na Internet.

Para abrir sem clonar manualmente o código, o proprietário recebeu um instalador local ZIP em sua conversa. Ele baixa o conteúdo desta branch e instala em:

- Código: `%LOCALAPPDATA%\ControleMestre\app\`
- Histórico: `%LOCALAPPDATA%\ControleMestre\dados\controle_mestre.db`
- Backups verificados: `%LOCALAPPDATA%\ControleMestre\dados\backups\`
- Atalho desktop: `CONTROLE MESTRE`

O inicializador lê `CONTROLE_MESTRE_DB` quando definido e faz backup SQLite consistente antes de aplicar migrações de esquema; o histórico é independente do diretório de instalação.

**Importante:** se já existir histórico em outro `dados/controle_mestre.db`, indicar sua localização no primeiro uso do instalador; não sobrescrever o histórico permanente com banco vazio. Não executar dois servidores sobre o mesmo banco durante atualização. Não apagar o diretório `dados`.

## Como usar

1. Abrir o atalho CONTROLE MESTRE no mesmo Windows onde os dados serão guardados.
2. No menu **Questões**, selecionar **POR BATERIA** ou **POR QUESTÃO**.
3. No modo por bateria, informar totais e acertos; a API registra e finaliza de uma vez, contabilizando o resultado uma única vez.
4. No modo por questão, criar cabeçalho, cadastrar todas as respostas (inclusive as não resolvidas), conferir totais, concluir; **antes da finalização, a bateria permanece como rascunho** e não altera os indicadores.
5. Rascunhos podem ser retomados pelo menu Questões após fechar e reabrir o navegador.
6. O histórico de baterias finalizadas e o caderno de erros aparecem no mesmo menu; questões, sessões, revisões, metas e planos são mantidos no SQLite local.
7. O menu Inteligência de estudos mostra as orientações iniciais de reforços sem modificar o planejamento automaticamente.
8. Fechar a janela do servidor encerra o programa, não exclui os registros; reabrir o atalho utiliza o mesmo banco.

## Proteção e limites

- A persistência é **local ao dispositivo**. Não existe sincronização automática entre computadores.
- Os backups automáticos protegem contra alterações, mas **não** contra perda total do disco. Copiar regularmente um backup verificado para mídia externa ou armazenamento pessoal protegido.
- Os resultados de reforço e suas orientações são heurísticos; o ciclo completo de reteste e intervenções persistentes permanece em desenvolvimento.
- A `main` ainda não inclui os PRs dependentes; instalação deve usar explicitamente a branch de integração, até homologação.
- A interface exige testes manuais no Windows real do titular. Não afirmar homologação sem essa verificação.
- Nunca publicar dados pessoais, arquivos .db, PDFs protegidos ou backups no GitHub público.

## Validação de engenharia

CI na branch `feat/integra-erros-reforcos-v081`, executado em 08/11/2026: **191 testes Python aprovados**, em 3.11 e 3.13, mais verificação sintática Node dos módulos atualizados. Inclui testes HTTP sintéticos para salvar, recuperar rascunhos, finalizar de forma idempotente e consultar histórico após novas conexões SQLite. O resultado não substitui homologação em Windows.
