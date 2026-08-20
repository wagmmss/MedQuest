# Delegação → Antigravity (Fase 4: Frontend Next.js)

## ⚠️ REGRA CRÍTICA — LEIA ANTES DE ESCREVER QUALQUER CÓDIGO NEXT
Este projeto usa **Next.js 16.3**, que tem **breaking changes** em relação ao conhecimento de qualquer LLM (inclusive você). **Antes de gerar código Next, leia** `app/frontend/node_modules/next/dist/` (docs/tipos) e o `app/frontend/AGENTS.md`. Não escreva código de Next 14/15 de memória — não vai compilar. Confirme APIs (App Router, `use client`, server actions, params) na versão instalada.

## Contexto
- Migração por **estrangulamento**: o Next.js assume o shell; cada view migra uma a uma; o app vanilla (`app/static/`) continua servindo o que ainda não migrou.
- **Não** invente dados. Hoje `app/frontend/src/app/page.tsx` tem números hardcoded (1.245, 78.4%, 34) — isso deve ser **removido** e substituído por dados reais da API.

## API (Flask)
- Base: `http://localhost:5050` em dev (produção: variável `NEXT_PUBLIC_API_URL`).
- Endpoints atuais em `app/backend/app.py` (serão versionados em `/api/v1/*` na Fase 2): `/api/meta`, `/api/questions`, `/api/questions/:id`, `/api/questions/:id/attempt` (POST), `/api/stats/*`, `/api/coverage`, `/api/planner*`.
- CORS já habilitado (Flask-Cors).
- Padrão de fetch: Server Components para leitura (dashboard/cobertura), Client Components para interação (quiz).

## Ordem de migração (risco crescente — NÃO inverter)
1. **Dashboard** (só leitura) → 2. **Cobertura USP** → 3. **Análise** → 4. **Planner** → 5. **Estudar/Quiz por último** (view mais complexa: timer, atalhos, rasura, notas, SRS — não pode quebrar).

## Componentes a gerar (a partir do Figma; ~40)
Primitivos: Button, Input, Select, Chip, Toggle, Card, Badge, StatTile, ProgressRing, Table, SidebarItem, Toast, Modal/Lightbox, Skeleton, EmptyState.
Compostos por view: `AreaCard`, `CoverageChip`, `WeekCard`, `QuestionCard`, `AlternativeButton`, `ExplanationPanel`, `StatsChart`, `WeakTopicsList`, `RecommendationCard`, `CommandPalette` (Cmd+K).

## Regras
- TypeScript estrito, tipos derivados das respostas da API (crie `types/api.ts`).
- Tailwind v4 com os tokens do Figma.
- Acessibilidade: foco visível, labels, contraste AA.
- Estados obrigatórios: loading (skeleton), empty (com ação), error (boundary).
- Nada de dado mockado em produção.

## Entregar por PR/branch
Uma view por vez, com screenshots. Eu reviso arquitetura e integração antes de mesclar.
