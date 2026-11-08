# Manual de Identidade Visual Premium — CONTROLE MESTRE

**Versão:** v0.7.0  
**Status:** Implementado e homologado na interface web.

---

## 1. Conceito e Arquétipo da Marca

**CONTROLE MESTRE — PLATAFORMA DE ESTUDOS**

- **Símbolo:** Um peão de xadrez em posição de vitória, envolto por espiral de luz dourada, superando um rei tombado em tabuleiro reflexivo, sob um brasão com ramos de louro e livro aberto.
- **Significado Estratégico:**
  - **Inteligência estratégica:** Planejamento baseado em evidências, não em sorte.
  - **Persistência e disciplina:** Cada pequeno avanço (o peão) acumula poder ao longo do tempo.
  - **Superação e conquista:** Na jornada para aprovação em concursos de alta complexidade (SEFAZ-RS / SEFAZ-SC), o estudante dedicado supera os maiores desafios.

---

## 2. Paleta Cromática Oficial

| Aplicação | Cor Hex | Uso |
|---|---|---|
| **Amarelo Principal** | `#FFD600` | Acentos primários, botões de ação principal, status ativo, foco |
| **Amarelo Intenso** | `#FFEA00` | Realce luminoso, brilho especular, hover e partículas |
| **Dourado Nobre** | `#D4A017` | Frisos, gradientes metálicos, bordas nobres, subtítulos |
| **Dourado Escuro** | `#996515` | Sombras douradas e profundidade de relevo |
| **Grafite Base** | `#101114` | Fundo principal da aplicação (dark mode premium) |
| **Grafite Lateral** | `#0B0C0E` | Fundo do menu lateral e cabeçalhos escuros |
| **Superfícies (Cards)** | `#1D2026` | Fundo dos cards, painéis, tabelas e modais |
| **Bordas / Traço** | `#2E333C` | Divisórias e contornos de cards |
| **Borda Dourada** | `rgba(212, 160, 23, 0.38)` | Contorno de destaque do banner e cards especiais |
| **Texto Principal** | `#F5F5F5` | Tipografia de leitura com alto contraste |
| **Texto Secundário** | `#8E95A2` | Rótulos, metadados e legendas |

### Cores Semânticas de Estado
- **Sucesso / Executado / Online:** `#54AA36` (verde suave)
- **Erro / Cancelado:** `#FA7474` (vermelho contido)
- **Atenção / Revisão vencida:** `#EF8021` (laranja equilibrado)
- **Informativo / Métricas:** `#258BD4` (azul clássico)

---

## 3. Catálogo de Assets (`web/assets/branding/`)

Todos os assets foram desenvolvidos em vetores SVG verdadeiros (sem bitmaps embutidos em SVG) e renderizados em alta definição para PNG, WebP otimizado e ICO:

1. **Logo Horizontal Premium:**
   - `logo_horizontal_premium.svg` (880×200, vetor puro)
   - `logo_horizontal_premium.png` (1760×400, @2x)
   - `logo_horizontal_premium.webp`
2. **Logo Vertical / Emblema:**
   - `logo_vertical_premium.svg` (460×520)
   - `logo_vertical_premium.png` (920×1040, @2x)
   - `logo_vertical_premium.webp`
3. **Ícone Quadrado:**
   - `logo_icone_quadrado.svg` (512×512)
   - `logo_icone_quadrado.png` (1024×1024)
   - `logo_icone_quadrado.webp`
   - `apple-touch-icon.png` (180×180)
4. **Favicon Multi-resolução:**
   - `favicon.svg` (64×64 otimizado para abas do navegador)
   - `favicon-32x32.png`
   - `favicon-16x16.png`
   - `favicon.ico` (16, 32, 48, 64px embutidos)
5. **Versões Monocromáticas:**
   - `logo_monocromatico_escuro.svg` (branco/cinza para fundos escuros)
   - `logo_monocromatico_claro.svg` (grafite para fundos claros e impressão)
6. **Versão para Fundo Claro:**
   - `logo_fundo_claro.svg`
   - `logo_fundo_claro.png`
   - `logo_fundo_claro.webp`
   - `logo_fundo_claro_vertical.svg`
7. **Menu Lateral (Sidebar):**
   - `logo_sidebar.svg` (240×64)
   - `logo_sidebar.png`
   - `logo_sidebar.webp`
8. **Banner Hero Premium:**
   - `banner_hero_premium.webp` (1920×822, 196 KB, carregamento ultrarrápido)
   - `banner_hero_premium.png` (1920×822)
9. **Originais Preservados:**
   - `originals/logo_referencia_quadrada.png`
   - `originals/banner_referencia_horizontal.png`

---

## 4. Banner Superior com Parallax

O painel inicial (`#/home`) apresenta um banner cinematográfico com profundidade:
- **Camada 1 (Fundo):** Gradiente radial grafite com movimento sutil invertido.
- **Camada 2 (Iluminação):** Brilho dourado suave (`mix-blend-mode: screen`).
- **Camada 3 (Cena de Xadrez):** Peão vencedor, rei tombado, livro e escudo com máscara gradiente lateral.
- **Camada 4 (Partículas):** Partículas douradas flutuantes com animação leve.
- **Camada 5 (Conteúdo):** Tipografia em primeiro plano com botão de ação direta "▶ Estudar hoje".

### Requisitos Técnicos e Acessibilidade:
- **Desempenho:** Utiliza `requestAnimationFrame` e aceleração via GPU (`translate3d`), sem sobrecarga na CPU.
- **Acessibilidade:** Suporte nativo a `@media (prefers-reduced-motion: reduce)` — os efeitos e translações 3D são automaticamente neutralizados quando o usuário opta por movimento reduzido.
- **Dispositivos Móveis e Touch:** Em telas menores que 780px ou dispositivos sem mouse (`pointer: coarse`), o banner se adapta para um cabeçalho compacto e estático, preservando navegação e leitura.
- **Demais Telas:** Telas de execução diária, ciclo, trilha fiscal e materiais mantêm um cabeçalho compacto, sem poluição visual.
