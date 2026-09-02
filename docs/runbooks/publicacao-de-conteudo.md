# Runbook: publicação de conteúdo e taxonomia

## Escopo e responsáveis

Este runbook é o único fluxo suportado para publicar taxonomia ou reparos de
metadados. Exige um operador de dados e um revisor distinto para qualquer
execução com `--apply`.

## Pré-condições

1. Rotação S0 concluída no provedor, com credenciais de escrita de curta duração.
2. Ambiente de staging apontando para cópia restaurável da base.
3. `TURSO_DATABASE_URL` e `TURSO_AUTH_TOKEN` presentes somente no ambiente do
   operador; nenhum segredo em argumentos, logs ou arquivos versionados.
4. Checklist verde: `pytest`, `pipeline.py check`, `check_no_embedded_secrets.py`
   e `taxonomy_sync.py`.

## Sequência normal

```powershell
cd app/backend
python scripts/pipeline.py check
python scripts/check_no_embedded_secrets.py
python scripts/pipeline.py run validate-content -- --strict
python scripts/pipeline.py run taxonomy-sync --
```

Para reparo, execute primeiro o dry-run e guarde a saída no ticket:

```powershell
python scripts/pipeline.py run content-repair -- --db ..\medquest.db
```

Somente após revisão humana, execute em staging com diretório de backup
explícito. O `--apply` é recusado sem `--backup-dir`.

```powershell
python scripts/pipeline.py run content-repair -- --db ..\medquest.db --apply --backup-dir ..\backups\<run-id>
```

## Publicação e observabilidade

- Aplique migrations forward-only no deploy; o runtime registra checksum em
  `schema_migrations` e cria `job_runs`.
- Ao executar por `pipeline.py`, passe `--db <copia-local>` para registrar
  `run_id`, hash, duração e resultado em `job_runs`.
- Publique somente se a validação não tiver falhas críticas. Depois de zerada a
  baseline de warnings, habilite `--fail-on-warnings` como gate de publicação.

## Rollback

1. Interrompa a publicação e preserve logs, hash de entrada e `run_id`.
2. Restaure o backup criado antes do `--apply` em staging e rode a auditoria
   read-only.
3. Em produção, prefira restauração point-in-time ou migration corretiva
   forward-only; não execute downgrade SQL ad-hoc.
4. Registre causa, itens afetados, horário e ação preventiva no ticket.

## Proibido

- Executar um arquivo não listado em `scripts/pipelines.json` contra staging ou
  produção.
- Publicar sem backup, dry-run e segunda revisão.
- Reutilizar token de operador, incluí-lo em script ou registrar conteúdo
  clínico/PII desnecessário em logs.
