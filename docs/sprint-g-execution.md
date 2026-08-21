# Sprint G — Testes e segurança

## Resultado

A matriz existente de autenticação, isolamento, concorrência e offline foi ampliada com telemetria, cache, índices e relatórios por usuário.

## Entregas

- telemetria de erro autenticada e limitada a 1 MiB por requisição;
- remoção de dados controlados pelo cliente e parâmetros sensíveis dos logs;
- testes de correlação, headers, Web Vitals e métricas;
- teste de invalidação de cache após mutação;
- testes de streak com descanso e relatório isolado por usuário;
- testes concorrentes/idempotentes pré-existentes preservados;
- workflow de CI para pytest, ESLint, TypeScript, build, `npm audit` e `pip-audit`;
- override da dependência transitiva vulnerável `serialize-javascript`.

## Validação

- npm audit: 0 vulnerabilidades;
- pip-audit: nenhuma vulnerabilidade conhecida;
- suíte backend: 83 testes aprovados;
- ESLint e TypeScript aprovados;
- build de produção aprovado sem avisos.

