# Definition of Done (DoD) Técnico e Padrão de Engenharia — MedQuest
**Versão:** 1.0  
**Data de Publicação:** 01 de Setembro de 2026  
**Responsável:** Engenharia Líder MedQuest  

---

## 1. Objetivo

Definir os critérios obrigatórios de qualidade, segurança, estabilidade e performance que todo código (backend, frontend, migrações de banco e scripts) deve atender antes de ser considerado concluído e pronto para merge na branch principal (`main`).

---

## 2. Checklist Obrigatório de Pull Request (DoD)

Todo PR submetido no repositório MedQuest deve preencher e validar o seguinte checklist:

### 2.1 Backend e Banco de Dados
- [ ] **Testes Automatizados:** Suíte completa de testes (`pytest`) executando 100% verde em **< 15 segundos**.
- [ ] **Hermeticidade:** Nenhuma chamada real de rede/API externa ocorre durante os testes (mocks obrigatórios em `conftest.py`).
- [ ] **Transações Seguras:** Todas as escritas em banco utilizam o context manager `with db_transaction(db, immediate=True):`.
- [ ] **Validação de Entrada:** Schemas Pydantic (`api/schemas.py`) configurados com limites estritos (`min_length`, `max_length`, `ge`, `le`).
- [ ] **Auditoria e Observabilidade:** Eventos de domínio estruturados emitidos via `record_domain_event(...)` em todas as ações de negócio relevantes.
- [ ] **Invalidação de Cache:** Caches voláteis em memória (`overview_cache`) explicitamente invalidados ao gravar dados do usuário (`invalidate_user_caches(user_id)`).
- [ ] **Guardrails de Performance:** Validação pelo script `python scripts/check_performance_guardrails.py` sem violação dos SLAs de latência.

### 2.2 Frontend e Interface
- [ ] **Orçamento de Bundle:** Verificação de bundles (`npm run check:performance`) aprovada dentro dos limites de 2.25 MB.
- [ ] **Code-Splitting:** Componentes pesados (gráficos `Recharts`, editores ricos, modais secundários) carregados dinamicamente via `next/dynamic` com skeleton loading.
- [ ] **Resiliência Offline:** Operações críticas salvas localmente em `Dexie` (IndexedDB) antes ou em contingência à rede.
- [ ] **Zero Cascading Renders:** Ausência de `setState` síncronos redundantes em `useEffect` e ausência de avisos de ESLint.
- [ ] **Acessibilidade e UX:** Estados de loading claros (`Loader2` / `animate-pulse`), feedback visual imediato via `toast` e suporte a Optimistic UI.

### 2.3 Segurança e Isolamento
- [ ] **Isolamento Multi-Tenant:** Todas as queries filtram obrigatoriamente por `user_id = g.user_id`.
- [ ] **Higienização de Entradas:** Expressões regulares e termos de busca sanitizados contra injeção ou travamento de CPU (ex: `_fts5_escape`).
- [ ] **Autenticação de Métricas:** Endpoints administrativos/diagnósticos protegidos por verificação de hash seguro via `hmac.compare_digest`.

### 2.4 Documentação e Rastreabilidade
- [ ] **Rastreabilidade de Item:** PR vinculado a um item do Backlog Operacional ou Issue com métrica de impacto declarada.
- [ ] **Evidência Numérica:** PR inclui captura ou log com antes/depois de latência, payload ou comportamento.
- [ ] **Plano de Rollback:** Estratégia clara documentada para reversão rápida sem perda de dados caso ocorra anomalia em produção.

---

## 3. Padrão de Template para Pull Requests

```markdown
### 📌 Resumo da Mudança
[Descreva sucintamente o problema resolvido e a abordagem técnica adotada]

### 🎯 Item do Backlog Vinculado
- Item: [ex: ES-2 / OP-04]
- Métrica Impactada: [ex: Latência P95 da Busca reduzida de 120ms para < 30ms]

### 🧪 Evidências de Validação
- [x] Pytest: 133/133 passando em X.XXs
- [x] Performance Guardrails: PASS em todos os endpoints
- [x] Bundle Check: Total JS = X.XX MB (< 2.25 MB)

### 🛡️ Checklist de DoD
- [x] Sem chamadas de IA síncronas sem timeout
- [x] Invalidação de cache aplicada
- [x] Isolamento de user_id verificado
- [x] Tratamento explícito de erro com feedback ao usuário

### 🔄 Plano de Rollback
[Instruções de reversão rápida de commit/migração]
```

---

## 4. Plano de Manutenção Contínua

- A DoD deve ser revisada trimestralmente pelo time de engenharia.
- Violações recorrentes de SLAs devem gerar tickets automáticos de refatoração no backlog.
