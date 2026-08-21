# Sprint C2 — Taxonomia e remediação técnica de conteúdo

## Resultado

A implementação da C2 foi concluída com separação explícita entre correções técnicas determinísticas e decisões médicas/editoriais humanas.

- `taxonomy.json` é a fonte pedagógica de verdade.
- `plannerData.json`, `plannerData.ts` e `subtema_map.json` são compilados e verificados deterministicamente.
- Os 202 IDs de subtema existentes foram preservados.
- Foram adicionados 73 IDs, totalizando 275 IDs únicos.
- Os quatro catálogos passaram a cobrir todos os 187 subtemas encontrados no banco.
- O reparo do banco é dry-run por padrão e exige `--apply` com backup.
- Nenhum texto médico é criado, reescrito ou removido automaticamente.

## Plano calculado sobre o banco real

- 2.785 questões receberiam o `subtema_id` canônico que ainda falta.
- 61 questões possuem ao menos uma falha técnica crítica.
- 7 questões ainda precisam ser desabilitadas e colocadas em quarentena.
- 54 questões críticas já estavam desabilitadas/quarentenadas.
- 1.463 questões seriam marcadas como `needs_human_review` pelas heurísticas de explicação.
- Nenhum subtema real permanece fora do mapa canônico.
- Nenhuma flag `alternatives.is_correct` pôde ser corrigida automaticamente com segurança no banco real; as divergências restantes pertencem a questões sem alternativa correspondente.

## Validação da aplicação

O plano completo foi aplicado ao banco local original em 21/08/2026, depois que o processo que mantinha o SQLite aberto foi encerrado manualmente pelo usuário:

- backup consistente criado antes da transação;
- transação única concluída;
- `PRAGMA integrity_check = ok` após a aplicação;
- 2.785 IDs canônicos de subtema atribuídos;
- zero questões com subtema preenchido e `subtema_id` vazio;
- 61 questões em quarentena;
- 1.463 questões marcadas para revisão humana;
- contagens preservadas: 7.852 questões, 34.379 alternativas, 7.718 explicações e 1.580 imagens;
- plano residual sem mutações pendentes.

Rastreabilidade dos arquivos:

- banco: `C:\dev\MedQuest\app\backend\medquest.db`;
- SHA-256 anterior: `6a95ba19e321998550d8a25bd805a0b24e844b5bd32655b9a04cd05eab5cc602`;
- SHA-256 posterior: `b20c81e3aa198dfbf0a47910f96386c70ba1465e076e2b265dd2c26c9df5e839`;
- backup: `C:\dev\MedQuest\backups\sprint-c2\medquest-pre-c2-20260821T013505Z.db`;
- SHA-256 do backup SQLite consistente: `0151fd183daafe438d7714985da808be78ac559f8603c85e8f111da358805661`.

O hash do backup lógico pode diferir do arquivo principal anterior porque a API de backup do SQLite incorpora de forma consistente o estado confirmado do WAL. Nenhum WAL/SHM foi removido ou manipulado manualmente.

## Protocolo de revisão humana

As marcações automáticas são triagem, não veredito médico.

1. Prioridade alta: explicação vazia, placeholder inequívoco ou truncamento claro.
2. Prioridade média: explicação abaixo do limite configurado.
3. Prioridade baixa: heurística textual que exige avaliação editorial antes de qualquer mudança.
4. O revisor deve preservar enunciado e gabarito oficial, registrar fonte médica, data da revisão e decisão editorial.
5. Nenhuma correção clínica deve ser aplicada apenas por sugestão de LLM.

## Validações

- Testes específicos C1.1/C2: `20 passed`.
- Suíte completa backend: `68 passed`.
- Compilação Python: aprovada.
- Compilador taxonômico em modo check: `in_sync=true`.
- Plano executado duas vezes: objetos JSON idênticos.
- Auditoria normal: exit `0`.
- Auditoria strict: exit `1` pelas falhas reais, sem traceback.
- Plano residual pós-aplicação: zero alterações automáticas pendentes.
- `PRAGMA integrity_check`: `ok` no banco original aplicado.
- `git diff --check`: aprovado.

## Recuperação operacional

O backup e seu manifesto devem ser preservados. Em caso de recuperação, a aplicação deve ser fechada antes da restauração, e o hash do arquivo restaurado deve ser validado contra o manifesto antes de reabrir o sistema.
