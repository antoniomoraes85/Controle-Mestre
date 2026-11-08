# Banner hero — peão derrubando o rei e wordmark metálico

**Status:** implementação publicada em branch de revisão. Não há merge automático nem alteração em dados privados.
**Base:** `feat/intro-xadrez-v071` (PR #45), ainda dependente da branch v0.7 do Antigravity (PR #46).

## Resultado

- Banner inicial contém uma **segunda cena** do peão amarelo-ouro avançando contra o rei grafite/prateado; rei gira, tomba e fica no chão, com brilho de impacto.
- A cena é **SVG original animado por CSS**, não GIF, vídeo, biblioteca nem recurso remoto. O tabuleiro e a iluminação existentes permanecem como fundo e o parallax conserva **cinco camadas**.
- A animação do banner só começa **após terminar** a abertura cinematográfica de 2,5 segundos. Em visitas subsequentes sem introdução, ela começa junto com o render do painel.
- A frase oficial permanece **sempre visível no banner**:
  **O PODER NÃO ESTÁ NA PEÇA. ESTÁ NA ESTRATÉGIA DE QUEM A MOVE.**
- **CONTROLE** recebe material prateado com faixa especular; **MESTRE** recebe ouro metálico brilhante. O mesmo acabamento é aplicado aos logos horizontal, vertical e sidebar.
- Em `prefers-reduced-motion: reduce`, o peão aparece vencedor e o rei já tombado, sem animações de impacto ou cintilação.
- Nenhuma mudança nos cronogramas, sessões, banco SQLite, PDFs, TEC, Anki ou metas.

## Arquivos

- `web/modules/hero_duel.js` — SVG da cena (novo).
- `web/app.js` — markup do hero e evento `cm:intro:finished`.
- `web/modules/intro.js` — evento emitido ao encerrar a introdução.
- `web/style.css` — gradientes prateado e dourado, animação de peão, queda do rei, refinamento responsivo e movimento reduzido.
- `web/assets/branding/logo_horizontal_premium.svg`, `logo_vertical_premium.svg`, `logo_sidebar.svg` — texto vetorial com preenchimento metálico.
- `tests/test_hero_branding.py` — testes de regressão de DOM, CSS, sincronização, parallax e SVG.

## Critérios de validação

- Conferência estrutural da branch: JS analisado pelo mecanismo V8 sem imports ES, cinco camadas preservadas, frase oficial e classes metálicas presentes, CSS balanceado e os três SVG com gradientes específicos.
- **Pendente de homologação:** executar `python -m unittest discover -s tests -q`, `node --check web/app.js`, `node --check web/modules/hero_duel.js`, teste real no Chrome Windows e aprovação visual pelo titular.
- Testar especialmente a animação após a introdução, voltar ao painel, reduzir movimentos e largura de 390px/desktop 1440px.
- Não fazer merge sem revisão; não submeter dados pessoais.
