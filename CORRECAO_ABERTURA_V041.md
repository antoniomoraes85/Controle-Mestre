# CONTROLE MESTRE v0.4.1 — Correção de inicialização no Windows

## O problema observado

O navegador mostrou `ERR_CONNECTION_REFUSED` em `127.0.0.1:8765`, mas `127.0.0.1:8501` abriu a **interface antiga do Streamlit**. São dois servidores independentes. Esse erro indica que não havia servidor web respondendo na porta 8765 naquele momento; **não permite concluir sozinho** se a causa era Python não instalado, inicializador errado, extração incompleta ou erro durante a inicialização.

## Correção aplicada

- `iniciar_windows.bat` passa a chamar `launch.py`, com verificação efetiva de Python 3.11+.
- `launch.py` confirma os arquivos essenciais, importações Python e acesso ao SQLite antes de abrir o navegador.
- Se a porta 8765 estiver ocupada, procura portas 8766–8770, sem interromper programas existentes.
- Se uma instância válida do CONTROLE MESTRE já estiver aberta, reutiliza a URL existente.
- Em caso de erro, imprime o motivo na janela e salva `logs/ultimo_erro_inicializacao.log` (fora do GitHub).
- `diagnosticar_windows.bat` identifica ambiente, arquivos, banco e porta sem iniciar a aplicação.
- A aplicação continua disponível somente em `127.0.0.1` (não exposta à internet).

## Instalação no Windows

1. Feche as janelas antigas do CONTROLE MESTRE.
2. Faça uma **cópia** de `dados/controle_mestre.db` da instalação anterior.
3. Extraia **todo** o ZIP para uma pasta nova (não execute dentro da visualização do ZIP).
4. Copie o banco antigo para a pasta `dados` da nova instalação, se quiser restaurar seus registros.
5. Clique duas vezes em **`iniciar_windows.bat`** dentro da pasta `CONTROLE_MESTRE`.
6. Leia a URL mostrada na janela preta (normalmente `http://127.0.0.1:8765`). Deixe essa janela aberta.
7. Se o navegador não abrir automaticamente, copie manualmente a URL indicada.

**Não use `8501` para visualizar a versão web premium.** A porta 8501 corresponde à versão antiga do Streamlit.

## Se não funcionar

Execute `diagnosticar_windows.bat` na mesma pasta e envie a mensagem da janela. Se existir, também pode enviar o arquivo `logs/ultimo_erro_inicializacao.log`. Evite enviar o banco de dados com seus estudos. Não é necessário abrir firewall nem expor portas públicas.

## Testes

Teste unitário de seleção/reuso de portas e arquivos essenciais, mais a suíte original Python. Teste HTTP da aplicação em porta local. A verificação em Windows real permanece pendente.