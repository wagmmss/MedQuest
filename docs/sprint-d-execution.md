# Sprint D — Aprendizado adaptativo

## Resultado

A Sprint D substitui a seleção aleatória opcional por uma fila adaptativa determinística e explicável, sem remover os filtros e modos de estudo existentes.

## Entregas

- retenção calculada pela API real do FSRS, com tolerância a cartões legados ou inválidos;
- diagnóstico por subtema combinando acurácia, confiança estatística, retenção e cobertura;
- fila `mode=adaptive` ordenada por revisões vencidas, risco de esquecimento, último erro e lacunas de cobertura;
- isolamento integral por `user_id` nas tentativas e cartões FSRS usados pelo ranking;
- meta diária personalizada a partir do planner, nunca menor que as revisões vencidas;
- recomendação direta para iniciar uma sessão adaptativa;
- painel de análise com meta do dia, prioridade atual e retenção estimada;
- desempate estável por ID para que a mesma entrada produza a mesma fila.

## Contratos

- `GET /api/stats/learning-profile`: meta, diagnóstico priorizado e sinais utilizados.
- `GET /api/questions?mode=adaptive&limit=N`: fila personalizada compatível com o fluxo de estudo atual.
- `GET /api/stats/at-risk`: risco baseado em retrievability do FSRS, e não em um corte arbitrário de estabilidade.

## Política do algoritmo

O score é uma heurística transparente de priorização, não uma previsão clínica nem uma avaliação do estudante. Ele usa somente o histórico do próprio usuário. A confiança cresce com o número de tentativas para evitar conclusões fortes a partir de amostras pequenas.

## Validação

- suíte backend: `72 passed`;
- TypeScript: aprovado (`tsc --noEmit`);
- ESLint dos arquivos alterados: aprovado;
- `git diff --check`: aprovado;
- testes específicos cobrem cartão FSRS válido/inválido, confiança, meta, determinismo e prioridade após erro recente.
