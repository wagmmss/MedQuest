# Sprint F — Desempenho e observabilidade

## Resultado

A aplicação agora possui budgets de build, correlação ponta a ponta e telemetria estruturada, com cache e consultas críticas verificáveis.

## Entregas

- `X-Request-ID` gerado no proxy e propagado pela API;
- logs JSON sem query string, stack trace ou identificador fornecido pelo cliente;
- `Server-Timing`, p50, p95, máximo e contagem por status/rota;
- coleta autenticada de CLS, FCP, FID, INP, LCP e TTFB;
- headers de segurança no Next.js e Flask;
- invalidação de caches derivados após tentativas, revisões e favoritos;
- índices para última tentativa e timeline por usuário;
- imagens do banco removidas do precache inicial e cacheadas sob demanda;
- Material Symbols reduzida de 3.960.036 para 29.384 bytes;
- budgets automáticos para JavaScript, maior chunk e service worker.

## Baseline validada

- JavaScript total: 2.082.905 bytes (budget 2.250.000);
- maior chunk: 411.567 bytes (budget 450.000);
- service worker: 7.211 bytes (budget 250.000);
- `GET /api/stats/overview` local no banco real: 5,88 ms sem cache e 0,11 ms medidos pelo servidor com cache.

