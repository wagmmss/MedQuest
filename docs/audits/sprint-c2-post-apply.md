# Relatório Baseline de Conteúdo e Taxonomia (Sprint C1.1)

**Data de geração:** 2026-08-21T01:41:32.331275Z
**Banco:** C:\dev\MedQuest\app\backend\medquest.db
**Schema do relatório:** 1.1.0

## Resumo executivo

- Questões: 7852
- Questões utilizáveis (`missing_alts=0`): 7791
- Registros em falhas críticas: 216
- Questões na fila humana: 1461
- Fontes taxonômicas não verificadas: 0
- SQLite: `query_only=1`, `integrity_check=ok`

## Integridade

- Enunciados vazios: 7
- Alternativas vazias: 206
- Gabaritos ausentes/inválidos: 0
- Gabaritos sem alternativa correspondente: 3
- Questões com letras duplicadas: 0
- `missing_alts=0` estruturalmente incompletas: 0
- `missing_alts=1` completas (warning): 7
- Orphans: alternatives=0, explanations=0, images=0
- Origens duplicadas: 0

## Duplicação

- Literal exact: 1952 grupos / 3904 questões
- Normalized exact: 6 grupos / 12 questões
- Probable duplicate: not_executed — Fuzzy/embedding matching was not executed because it is unsafe for automatic classification.

## Taxonomia

- Subtemas no banco: 187
- `taxonomy_json`: verified; DB não mapeados=0; catálogo sem questões=88
- `canonical_subtemas_py`: verified; DB não mapeados=0; catálogo sem questões=0
- `plannerData_json`: verified; DB não mapeados=0; catálogo sem questões=88
- `plannerData_ts`: verified; DB não mapeados=0; catálogo sem questões=88

## Cobertura

As oito distribuições incluem metadados explícitos de truncamento:
- `area`: total=6, retornados=6, truncated=false
- `institution`: total=7, retornados=7, truncated=false
- `year`: total=7, retornados=7, truncated=false
- `area_institution`: total=40, retornados=40, truncated=false
- `area_year`: total=42, retornados=42, truncated=false
- `subtema`: total=188, retornados=188, truncated=false
- `subtema_institution`: total=1131, retornados=1131, truncated=false
- `subtema_year`: total=1209, retornados=1209, truncated=false

- Subtemas com <5 questões: 9
- Subtemas com <10 questões: 12
- Subtemas com <20 questões: 35

## Warnings

- Fuzzy/embedding matching was not executed because it is unsafe for automatic classification.
- Some alternatives.is_correct flags disagree with questions.correct_letter.
- Some missing_alts=1 questions are structurally complete; this is a warning only.
