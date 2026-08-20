# Prompt para o Antigravity — Fase 4 (migração do frontend)

Cole o texto abaixo no Antigravity, com o projeto MedQuest aberto.

---

Você vai continuar a migração do frontend do **MedQuest** (app de estudo para residência médica USP) do app vanilla (`app/static/`) para **Next.js** (`app/frontend/`), por **estrangulamento** (uma view por vez; o vanilla continua servindo o resto). O backend Flask já está pronto.

## ⚠️ REGRA CRÍTICA — leia antes de escrever qualquer código Next
Este projeto usa **Next.js 16.3**, que tem **breaking changes** em relação ao seu conhecimento de treino. **LEIA** `app/frontend/node_modules/next/dist/docs/` e o `app/frontend/AGENTS.md` **antes** de escrever código Next. Não use padrões de Next 14/15 de memória — não vão compilar. Confirme App Router, Server/Client Components, `params`, etc. na versão instalada.

## Stack (já configurada)
- Next 16.3, React 19, TypeScript, **Tailwind v4** (config via `@theme` em `src/app/globals.css` — **JÁ FEITO**, não recrie).
- Rode: backend `python app/backend/app.py` (porta 5050); frontend `npm run dev --prefix app/frontend` (porta 3000).

## Design tokens JÁ prontos (use estes utilitários, NÃO invente cores)
- **Cores:** `bg-background`, `text-foreground`, `bg-card`, `bg-card-2`, `border-border`, `text-muted-foreground`, `bg-primary`/`text-primary` (índigo, acento único), `bg-secondary`, `bg-success`/`bg-warning`/`bg-destructive`. Áreas: `text-area-preventiva`, `-pediatria`, `-go`, `-cirurgia`, `-clinica`.
- **Tipografia:** `text-caption/small/body/body-l/h2/h1/display` (o `body-l` = 18px, line-height 1.7, para o **enunciado da questão**).
- **Raio:** `rounded-sm/md/lg/pill`. **Sombra:** `shadow-1` (cartões), `shadow-2` (modais).
- **Tema claro E escuro:** dark mode por classe `.dark` no `<html>`. Faça um toggle (e respeite `prefers-color-scheme` no primeiro load).

## Princípios visuais
Ferramenta de trabalho (referência: **Linear, Notion**), NÃO landing page. **Sidebar colapsável** (não topbar), **Command palette (Cmd+K)**, densidade alta, sem glassmorphism/orbs. Enunciado em coluna única ~70 caracteres. Estados obrigatórios: **loading (skeleton), empty (com ação), error (boundary)**.

## API (Flask, http://localhost:5050 — CORS liberado; use `NEXT_PUBLIC_API_URL`)
Mesmos endpoints em `/api` e `/api/v1`:
- `GET /api/meta` · `GET /api/questions` (filtros: area, subtema, year, institution, status, favorite) · `GET /api/questions/:id` · `POST /api/questions/:id/attempt` body `{selected_letter, confidence?, time_spent_ms?}` · `POST /api/questions/:id/favorite`
- `GET /api/stats/overview` · `/api/stats/breakdown?by=area|institution|year|subtema` · `/api/stats/timeline` · `/api/stats/weak-topics` · `/api/stats/recommendations` · `/api/stats/distractors`
- `GET /api/coverage`
- `GET|POST /api/planner/config` · `GET /api/planner` · `POST /api/planner/:week/study` · `POST /api/planner/:week/revision` · `POST /api/generate_plan`

## Tarefas (ordem por risco crescente — NÃO inverta)
0. Crie `src/types/api.ts` (tipos das respostas) e `src/lib/api.ts` (cliente fetch usando `NEXT_PUBLIC_API_URL`, fallback `http://localhost:5050`).
1. **Dashboard PRIMEIRO** — em `src/app/page.tsx`, **remova os números falsos hardcoded** (1245, 78.4%, 34) e busque dados **reais** de `/api/stats/overview`. Layout: **1 número herói** (ex.: `srs_due_count` → "X questões pra revisar hoje") + **1 ação primária** + grid secundário (streak, acurácia últimas, cobertura). Nada de 3 números iguais.
2. Depois, nesta ordem: **Cobertura** (`/api/coverage`, chips de subtema por status) → **Análise** (`/api/stats/*`, gráficos + distratores) → **Planner** → **Estudar/Quiz por último** (mais complexo: timer, atalhos, rasura, notas, confiança, SRS).
3. Use **Server Components** para leitura (dashboard/cobertura) e **Client Components** para interação (quiz).

Entregue **uma view por vez**, com screenshot, para revisão antes de seguir.
