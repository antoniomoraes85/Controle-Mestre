# Introdução cinematográfica v0.7.1

Base: `feat/cronogramas-identidade-v07`, commit `0766831`, contendo `b4b2115` e `b0bc502`. Não incorporada à main na verificação inicial; PR direcionado à branch de origem. Checkout separado para preservar a pasta local sem Git.

## Implementação

- `web/index.html`: template inerte com tabuleiro, peão e rei SVG independentes; reaproveita o logo horizontal aprovado. Script local independente do app.
- `web/modules/intro.js`: uma apresentação por sessão via sessionStorage; botão, Escape, foco no painel e mudança de preferência encerram a abertura. Storage indisponível omite a introdução. Timeout independente de 2,6 s impede bloqueio se animationend falhar. Falha do logo encerra; falha do módulo deixa o template inerte; CSS ausente encerra.
- `web/style.css`: sequência de 2,5 s (tabuleiro, avanço, queda com rebote, brilho, marca/frase e fade). Transform/opacity; nenhum vídeo, biblioteca ou script externo. CSS também torna o overlay invisível ao final.
- `web/app.js`: apenas substitui o texto do banner pela frase oficial. As cinco camadas, requestAnimationFrame, botões e regras mobile/reduced-motion foram preservados.
- `tests/browser_intro.py`: testes reais com Playwright e Chrome instalado, servidor HTTP original e fixture sintética isolada.

## Acessibilidade e limites

A decoração tem aria-hidden; o painel permanece na árvore de acessibilidade, sem modal nem captura de foco. Focar um controle do painel encerra a abertura. Se o botão de pular estava focado, o foco segue para o conteúdo. Reduced motion abre diretamente o painel. A frase permanece no banner para leitura sem limite de tempo: a exibição na introdução é breve devido à duração solicitada.

A sessão segue a semântica do sessionStorage por aba; não sincroniza abas independentes. O watchdog depende do agendamento do navegador e pode ser adiado em aba em segundo plano. Testes no Chrome headless instalado no Windows, sem medição de FPS em hardware de baixa potência nem teste com leitor de tela físico. Nenhum dado pessoal foi utilizado ou publicado.

## Validação

- `python -m unittest discover -s tests`: 112 testes passaram. ResourceWarning preexistente sobre HTTPError, sem falha.
- `node --check web/app.js` e `node --check web/modules/intro.js`: passaram.
- `python tests/browser_intro.py`: primeira abertura, conclusão automática, reload sem repetição, navegação/retorno, botão, Escape, foco, alteração dinâmica de reduced motion, preferência inicial, falha de JS/logo/CSS, storage negado, watchdog sem animationend, cinco camadas, movimento/reset do parallax, botões e layout mobile sem overflow passaram.
- Desktop 1440×1000 e mobile 390×844. Capturas sintéticas locais para revisão visual, não incluídas no commit.
- `git diff --check`: passou.

Para repetir o navegador: instalar somente a ferramenta de teste com `python -m pip install playwright`; ter Chrome instalado; executar `python tests/browser_intro.py`. Não há nova dependência de runtime da plataforma.
