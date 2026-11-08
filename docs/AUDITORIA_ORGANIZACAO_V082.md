# Auditoria e organização conservadora — CONTROLE MESTRE v0.8.2

## Origem do pedido
Capturas de 08/11/2026 mostram a pasta `CONTROLE_MESTRE` do Windows com código-fonte, inicializadores, guias históricos, imagens, vídeo, manual em PDF, ZIPs de instalação, `__pycache__`, `.pytest_cache`, `dados`, `MATERIAL TEÓRICO`, `ANKI`, `docs`, `web`, `tests`, `.github` e `.streamlit`. A tela de Questões continha seções duplicadas intituladas **Meu histórico de questões** e **Histórico de questões**.

## Correção funcional
- O menu Questões passa a ter um único **Meu histórico de questões**.
- A rota `GET /api/questions/history` consulta `questions` como fonte única e associa, quando presentes, os metadados de `question_batches` via `legacy_question_id`; registros antigos permanecem listados.
- A consulta retorna apenas 200 entradas para manter a interface responsiva; **não remove nem limita os dados gravados no SQLite**.
- Indicadores de desempenho e caderno de erros continuam separados, pois cumprem objetivos diferentes.
- Nenhum dado existente é alterado por essa correção de interface.

## Política de organização local
**Nunca apagar ou alterar sem consentimento individual:** `dados/`, `*.db`, `*.sqlite*`, `MATERIAL TEÓRICO/`, `ANKI/`, `web/`, `docs/`, `tests/`, `.github/`, `.git/`, `core.py`, `web_server.py`, `launch.py`, `requirements.txt`, `*.bat` operacionais, `*.md` com documentação e guias referenciados.

**Arquivamento reversível elegível**, somente na raiz e após prévia: `__pycache__`, `.pytest_cache`, pacotes ZIP/RAR/7z; mídia de referência que começa com `Imagem do ChatGPT` ou `Estratégia Dourada`; manual histórico `Plataforma Controle Mestre 1.0*.pdf`; instalador obsoleto `INSTALAR_CONTROLE_MESTRE.ps1`. Se um item estiver rastreado no Git, o organizador o preserva. Outras mídias ficam intactas até inspeção de referências.

O organizador externo da conversa é `ORGANIZAR_CONTROLE_MESTRE.py` e `ORGANIZAR_CONTROLE_MESTRE.bat`. Ele:
1. Exige identificar uma pasta com `core.py` e `web_server.py`;
2. Exibe **prévia** por padrão, com lista de nomes e categorias;
3. Bloqueia a organização enquanto um serviço local ocupar as portas 8771–8780;
4. Requer autorização explícita digitando `APLICAR`;
5. Move os arquivos para `_ARQUIVO_LOCAL/<data>/...` e registra `manifesto.json`;
6. Oferece **desfazer** sem sobrescrever arquivos que já existam no destino original;
7. **Nunca exclui arquivos**.

## Pendências deliberadas
- Realizar inventário **no Windows do titular**; uma imagem não permite determinar se dois arquivos têm hash igual ou se são usados por outros scripts.
- Auditar links de documentação antes de mover guias históricos rastreados pelo Git.
- Revisar scripts lançadores redundantes e decidir quais manter após teste no Windows; não desativar lançadores por aparência de duplicação.
- Revisar arquivos de identidade/branding dos PRs #45/#47 antes de reorganizar mídias usadas pela UI.
- Concluir homologação em navegador Windows e verificar o histórico após reinicialização real.
- Não mesclar alterações em `main` sem revisão do PR correspondente.

## Testes
A suíte Python/HTTP do repositório inclui regressão que comprova coexistência de registros anteriores com baterias detalhadas, sem duplicação do retorno. O utilitário local de organização foi testado com fixtures sintéticas para prévia, arquivamento, restauração e bloqueio durante uso. A prova final em Windows permanece necessária.
