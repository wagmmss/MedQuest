# Delegação → Figma (Fase 3: Design System)

**Objetivo:** um design system enxuto para uma **ferramenta de trabalho** (uso 4h/dia, texto denso), não uma landing page. Referências: **Linear, Notion, ferramentas clínicas**. Nada de mesh gradient, orbs ou glassmorphism.

## Princípios
- Fundo neutro sólido; superfícies elevadas por **borda + sombra sutil** (não blur).
- **Uma** cor de acento. Texto sempre com alto contraste (AA+).
- **Modo claro E escuro** (ninguém estuda 4h no escuro de dia).
- Densidade informacional alta, mas com hierarquia clara.

## 1. Tokens (crie como Variables no Figma → exportar pra Tailwind)
- **Cor:** neutros 50–950 (base da UI); 1 acento (ex.: índigo) em 400/500/600; semânticos success/warning/danger; superfícies (bg, surface, surface-2, border).
- **Tipografia:** família (Inter ou similar); escala 12/14/16/**17-18 (corpo de questão)**/20/24/30; line-height 1.5 geral, **1.7 no corpo de questão**.
- **Espaçamento:** escala 4/8/12/16/24/32/48.
- **Raio:** 6/10/16. **Sombra:** 2 níveis (sutil / elevado).

## 2. Biblioteca de componentes (~15)
Button (primary/ghost/danger), Input, Select, Chip/Tag, Checkbox/Toggle, Card/Surface, Badge de área (5 cores), StatTile (número herói + secundários), ProgressBar/Ring, Table row, Tab/SidebarItem, Toast, Modal/Lightbox (pra imagens de ECG/RX), Skeleton, EmptyState.

## 3. As 8 telas
1. **Dashboard** — 1 número herói ("142 questões pra revisar hoje") + ação primária óbvia + grid secundário (streak, acurácia 7d, cobertura). NÃO 3 números iguais.
2. **Estudar/Quiz** — coluna única ~70 caracteres, corpo 17-18px, alternativas com estados (selecionada/certa/errada/rasurada), explicação, notas, imagem com lightbox.
3. **Cobertura USP** — cartões por área + subtemas canônicos por status (🔴🟡🟢).
4. **Planner** — card "Esta semana" + contagem regressiva + lista de temas.
5. **Análise de Desempenho** — gráficos por área/instituição/tempo + tópicos fracos + **análise de distratores**.
6. **Simulado** — configuração + tela cronometrada + resultado com nota de corte.
7. **Caderno de erros** — lista de erradas + notas (exportável PDF).
8. **Config** — perfil, tema, dados da prova.

## 4. Navegação
**Sidebar colapsável** (não topbar — vai ter 8-10 seções) + **command palette (Cmd+K)**.

## Entregar
Variables exportadas (JSON/tokens) + os frames das 8 telas em light e dark. Eu transformo os tokens no `tailwind.config` e o Antigravity implementa os componentes.
