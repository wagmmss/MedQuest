# Auditoria do frontend — 23/08/2026

## Escopo revisado

Revisados os fluxos assíncronos de busca, análise e sincronização offline, além da configuração de PWA, erros globais, orçamento de bundle e a suíte E2E existente.

## Correções aplicadas

| Severidade | Local | Problema | Correção |
| --- | --- | --- | --- |
| Alta | `src/lib/api.ts` | Um cancelamento de `fetch` pode ser reportado como `TypeError` por alguns navegadores e entrar indevidamente na fila offline de mutações. | Requisições cujo `AbortSignal` foi cancelado agora são propagadas, sem enfileiramento. |
| Média | `src/app/buscar/BuscarClient.tsx` | Pesquisas digitadas em sequência mantinham chamadas já obsoletas em andamento; falhas apareciam apenas no console. | Adicionado `AbortController` no debounce, limpeza da requisição anterior e estado de erro recuperável na interface. |
| Média | `src/app/analise/AnalysisClient.tsx` | Alternar o período do gráfico mantinha chamadas antigas consumindo rede. | A chamada anterior passa a ser cancelada ao mudar o período ou desmontar o componente. |
| Baixa | `src/components/SyncProvider.tsx` | A leitura inicial da fila poderia atualizar estado após o provider ser desmontado. | O resultado assíncrono agora é ignorado depois do cleanup. |
| Média | `src/components/CommandPalette.tsx` | A busca rápida mantinha pesquisas obsoletas em voo e podia exibir resultados fora de contexto. | Adicionado cancelamento com `AbortController`, com limpeza correta do estado de erro. |
| Média | `src/app/revisao-ativa/FlashcardClient.tsx` | A carga inicial de flashcards podia terminar após a tela ser desmontada. | A consulta agora recebe um sinal de cancelamento e não atualiza estado após o cleanup. |
| Baixa | `src/app/planner/PlannerClient.tsx` | Ao falhar o salvamento de um estudo marcado, o rollback mantinha a data de estudo criada pelo estado otimista. | O rollback agora restaura também `studied_at`, removendo a data quando a semana não está concluída. |

## Performance

O build de produção mediu:

| Métrica | Atual | Limite |
| --- | ---: | ---: |
| JavaScript total | 1.885.241 bytes | 2.250.000 bytes |
| Maior chunk | 292.237 bytes | 450.000 bytes |
| Service worker | 7.438 bytes | 250.000 bytes |

Não há baseline versionado para calcular uma redução percentual de bundle. O service worker foi validado para não armazenar respostas de API ou páginas de usuário; imagens são cacheadas sob demanda e APIs usam `NetworkOnly`.

## Validação

- `npm run lint` — aprovado.
- `npm run build` — aprovado, incluindo TypeScript, validação do service worker e orçamento de performance.
- `npm run test:e2e:list` — 12 cenários E2E encontrados.
- A execução E2E de sincronização precisa de um ambiente que permita iniciar o Chromium; no sandbox padrão, o processo é bloqueado com `spawn EPERM` antes de executar os testes.

## Pendências recomendadas

1. Executar Lighthouse em ambiente de staging autenticado para registrar LCP, INP e CLS reais; esses dados não podem ser inferidos de um build local.
2. Criar uma medição de bundle versionada (por exemplo, artefato de CI) antes de definir a meta de redução de 20%.
3. Adicionar um teste E2E de busca que confirme que respostas atrasadas não sobrescrevem a consulta mais recente.
4. Se o produto exigir garantia de sincronização entre várias abas, coordenar a fila com Web Locks ou uma trava transacional no IndexedDB; a idempotência atual protege o servidor, mas não elimina trabalho duplicado entre contextos de navegador.
