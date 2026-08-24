# Inventário de scripts do backend

Revisado em 2026-08-23. O diretório contém 192 arquivos: 188 Python, três JSON de dados e um banco auxiliar. A regra operacional é **deprecated por padrão**: qualquer script Python não incluído nas listas abaixo é um job histórico/one-time e não deve ser executado contra produção sem revisão de código, backup e dry-run.

## Produção

- `planner.py`: importado por `api/plan.py` e `api/stats.py`; faz parte do runtime.
- `plannerData.json` e `katomartCourseDurations.json`: dados consumidos pelo planejador e pelo endpoint de cobertura.

## Manutenção suportada e testada

- `validate.py`: auditoria read-only do dataset.
- `audit/`: módulos read-only de integridade, cobertura, duplicação, encoding, explicações e taxonomia.
- `content_repair.py`: reparo transacional com dry-run e backup obrigatório, coberto por testes.
- `taxonomy_sync.py`: compilador determinístico da taxonomia; check-only por padrão e escrita apenas com `--apply`.

## Manutenção manual sem garantia de estabilidade

- `backup_db.py`: backup local; confirmar origem e destino antes da execução.
- `make_deploy_zip.py`: empacotamento manual de deploy.
- `migrate*.py`, `sync*.py`, `update*.py` e `turso_rebuild_fts.py`: ferramentas operacionais antigas. Exigem validação em staging, backup e credenciais de menor privilégio.

## Deprecated / one-time

Todos os demais `.py` no nível superior de `scripts/`, inclusive famílias `add_*`, `alter_*`, `analyze_*`, `apply_*`, `calc_*`, `check_*`, `clean_*`, `compare_*`, `compile_*`, `debug.py`, `deepseek_*`, `dump_*`, `export_*`, `extract_*`, `find_*`, `finish_*`, `fix_*`, `generate_*`, `inject_*`, `inspect_*`, `list_*`, `match_*`, `merge_*`, `populate_*`, `print_*`, `reclassify_*`, `refactor*`, `refine_*`, `remap_*`, `rename_*`, `review_*`, `run_pipeline.py`, `sanitize_*`, `scan_*`, `search_*`, `test_*`, `upgrade_*`, `verify_*` e scripts de Turso não listados acima.

Esses arquivos permanecem no repositório apenas para rastreabilidade histórica. Eles podem importar `.env`, chamar serviços externos ou alterar banco remoto durante o import/execução. O `pytest` os ignora deliberadamente quando não são testes herméticos. Migrações futuras devem ser SQL versionado em `migrations/` ou uma ferramenta de migrations, não novos scripts ad hoc.

## Política para reativação

Para promover um script de deprecated a suportado, é obrigatório: CLI com `--dry-run`, caminhos explícitos, timeout de rede, transação com rollback, backup para mutações, nenhum efeito colateral no import, teste hermético e documentação nesta lista.
