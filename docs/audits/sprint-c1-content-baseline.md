# MedQuest Content & Taxonomy Audit (Sprint C1.1)
**Generated At:** 2026-08-21T00:58:12.475425+00:00
**Database Size:** 45359104 bytes

## 1. Summary
- **Total Questions:** 7852
- **Usable (missing_alts=0):** 7798
- **No Area:** 0
- **No Subtema:** 0

## 2. Critical Failures (Integrity)
> [!WARNING]
> These issues will cause `--strict` mode to fail.
- **Empty Statements:** 7
- **Empty Alternatives:** 206
- **Invalid Correct Letters:** 0
- **Answers w/o Alternative:** 3
- **Questions with Duplicated Alt Letters:** 0
- **Orphan Alternatives:** 0
- **Orphan Images:** 0
- **missing_alts=0 but Incomplete:** 0
- **Duplicated Source File+Number:** 0

## 3. Warnings
- **missing_alts=1 but Complete:** 51 (Possible pedagogical deactivation)

## 4. Human Review Queue (Explanations)
- **High Priority (Empty/Placeholder):** 203
- **Medium Priority (Too short):** 7
- **Low Priority (Heuristic):** 1253

## 5. Duplication
- **Literal Exact Groups:** 1952 (Affects 3904 Qs)
- **Normalized Exact Groups:** 0 (Affects 0 Qs)

## 6. Taxonomy Divergence
**DB State:** 5 Areas, 187 Subtemas

| Catalog | Status | Missing Areas | Missing Subtemas | Affected Qs |
|---|---|---|---|---|
| taxonomy_json | unverified | - | - | - |
| canonical_subtemas_py | verified | 5 | 187 | 7798 |
| plannerData_json | verified | 2 | 73 | 2785 |
| plannerData_ts | verified | 0 | 0 | 0 |

### Source Consumers
- **taxonomy_json**: Unknown (No verified direct importer in backend currently scripts).
- **canonical_subtemas_py**: Backend maintenance scripts (e.g. tests or legacy sync).
- **plannerData_json**: Backend dynamic planners or seeders.
- **plannerData_ts**: Frontend application code (e.g., app/simulado/page.tsx, components).

## 7. Sprint C2 Proposals
- **Technical Corrections (Automated)**: Address critical integrity failures systematically (e.g. purging actual orphans, fixing broken structure flags).
- **Taxonomy Standardization**: Decide on a single source of truth and normalize the database strings, migrating affected questions.
- **Medical Review**: Have humans or assisted workflows review the explanation queue. (Do not rely blindly on LLMs for final clinical truth).