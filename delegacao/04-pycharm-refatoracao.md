# Delegação → PyCharm Pro (Fase 2: Backend sério)

**Objetivo:** transformar `app/backend/app.py` (768 linhas, monolito) numa API organizada, validada e testada — sem quebrar o frontend vanilla que já consome os endpoints.

> Trabalhe numa branch: `git switch -c fase2-backend`.

## 1. Quebrar em blueprints
`app.py` → cria `app/backend/api/` com:
- `questions.py` — listagem, detalhe, filtros, contagem
- `attempts.py` — registrar tentativa + SRS
- `stats.py` — overview, breakdown, timeline, weak-topics, recommendations
- `planner.py` — config + progresso
- `coverage.py` — mapa de cobertura
- `__init__.py` — `create_app()` (application factory) registra os blueprints sob **`/api/v1`**.
Use o refactor **Extract Method / Move** do PyCharm. **Mantenha as rotas antigas `/api/*` como alias** temporário pro vanilla não quebrar.

## 2. Validação com Pydantic
Hoje é `request.get_json(force=True)` sem validação. Crie modelos (ex.: `AttemptIn{selected_letter: Literal['A'..'E']}`, `PlannerConfigIn`, filtros de questões) e valide toda entrada.

## 3. Trocar SM-2 → FSRS
O SRS atual (`app.py` ~234-260) ignora tempo de resposta e dificuldade. Use a lib **`fsrs`** (Python). Migre `spaced_repetition` para os campos do FSRS (stability, difficulty, etc.), preservando o histórico de `attempts`.

## 4. Schema evolutivo (fazer agora, custa ~2h)
Migrations em `migrations/` (versionadas):
- `002_user_id.sql` — adicionar `user_id` (default 1) em `attempts`, `spaced_repetition`, `favorites`, `planner_progress`, `planner_config`. Lançar só pra você, mas pronto pra multiusuário.
- `003_attempts_extra.sql` — adicionar **`time_spent_ms`** e **`confidence`** (chutei/dúvida/certeza) em `attempts`. *Coletar já, mesmo antes de usar na UI — dado não coletado é perdido pra sempre.*

## 5. Testes (pytest) — meta 70% na lógica
Foco: cálculos de stats (acurácia, breakdown), lógica do SRS/FSRS, filtros de questões, planner. `conftest.py` com um banco de teste em memória.

## 6. Config por ambiente
`config.py` lendo variáveis de ambiente; `debug=False` fora de dev; nada de segredo hardcoded.

## Entregar
Branch com blueprints + testes passando + as migrations. Eu reviso a arquitetura e o schema antes de mesclar.
