# CONTROLE MESTRE — v0.2 visual (05/11/2026)

## Correções realizadas

- Tema Streamlit **dark** configurado no arquivo `.streamlit/config.toml` para evitar textos escuros sobre menu escuro.
- Cabeçalho e sidebar alinhados à identidade visual da plataforma, com contraste e estados de navegação.
- Cartões de KPIs com rótulos, valores e descrições legíveis, sem deltas invisíveis.
- Progresso semanal em barra contextualizada (realizado/meta).
- Em vez de gráfico de 28 datas com zero, quatro semanas agregadas **apenas quando há dados**.
- Substituição da tabela branca de prioridades por classificação responsiva com barras e aviso de insuficiência de dados.
- Próximas atividades organizadas em cartões de leitura rápida.
- Atualização estética aplicada também a controles, formulários, botões e tabelas restantes via tema global.
- Componentes HTML de dados variáveis sanitizados (`html.escape`).

## Instalação

1. Faça backup de `dados/controle_mestre.db` da sua instalação anterior.
2. Extraia esta versão **em uma pasta separada**. Se desejar continuar com seus dados anteriores, copie somente o arquivo do banco anterior para `dados/controle_mestre.db` na nova pasta, com o aplicativo parado.
3. Execute `iniciar_windows.bat` ou `python -m streamlit run app.py`.
4. No navegador, use `Ctrl+F5` para remover o cache visual da sessão, caso ainda apareça a formatação antiga.
5. No menu **Planejamento semanal**, defina seus plantões e gere metas; depois registre estudo em **Estudar hoje**.

## Validação e limites

- Compilação de `app.py` e `ui_theme.py`: validada.
- Testes unitários automatizados: executados localmente.
- A instalação de Streamlit não está disponível no ambiente de validação; a interface **não foi verificada em navegador rodando a aplicação**. Conferir no PC do usuário.
- Sem alterações de esquema ou registros no SQLite; código compatível com o banco v0.1.
- Nenhum dado pessoal deve ser incluído no repositório público.