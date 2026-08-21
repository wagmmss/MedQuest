# Sprint C2 — Plano de remediação de conteúdo

**Modo:** `dry_run`
**Banco analisado:** C:\dev\MedQuest\app\backend\medquest.db

## Escopo automatizado

A C2 automatiza somente metadados técnicos determinísticos. Enunciados, alternativas, explicações, referências médicas e rótulos taxonômicos não são reescritos.

- Questões críticas únicas: 61
- Questões a desabilitar por falha estrutural: 7
- Questões a colocar em quarentena: 7
- IDs canônicos de subtema a atribuir: 2785
- Flags redundantes `is_correct` a sincronizar: 0
- Questões a marcar para revisão humana: 1463
- Subtemas do banco sem ID no catálogo: 0

## Política de segurança editorial

- A execução padrão é dry-run.
- `--apply` exige diretório de backup e uma transação SQLite única.
- Conteúdo médico nunca é gerado ou corrigido automaticamente.
- Explicações sinalizadas recebem apenas `needs_human_review`.
- Falhas estruturais são desabilitadas/quarentenadas; os textos originais são preservados.

## Campos que nunca são automatizados

- `questions.stem`
- `alternatives.text`
- `explanations.explanation_text`
- `questions.medical_references`
- `questions.area`
- `questions.subtema`

## Warnings

- Empty or medically questionable content is quarantined/queued, never generated or rewritten automatically.
- Applying this plan changes operational metadata only and requires a verified backup.
