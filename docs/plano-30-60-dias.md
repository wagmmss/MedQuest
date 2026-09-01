# Roadmap Tático e Plano de Ação (30–60 Dias) — MedQuest
**Versão:** 1.0  
**Data:** 31 de Agosto de 2026  
**Responsável:** Engenheiro Líder do Projeto MedQuest

---

## 1. Visão Geral e Metas Objetivas para o Ciclo

O plano de ação para os próximos 30 a 60 dias foca em transformar o diagnóstico da Semana 1 em entregas de alto impacto, divididas em 3 horizontes:

1. **Quick Wins (Semanas 1–2):** Estabilização de timeouts, otimização de I/O em disco, hermeticidade de testes e redução de fricção imediata no fluxo de estudo.
2. **Melhorias Estruturais (30–60 Dias):** Aceleração da busca FTS5, criação automática de flashcards pós-erro, auto-save de simulados e sincronização offline bidirecional.
3. **Iniciativas Estratégicas (60+ Dias):** Telemetria analítica persistida em banco, calibração bayesiana avançada de prontidão e otimização de bundle com code-splitting total.

### Metas Quantitativas do Ciclo:
- 🎯 **Reduzir Latência P95 da Busca (`/api/search`)**: de **120.98 ms** para **< 30.0 ms** (redução de 75%).
- 🎯 **Reduzir Latência P95 de Cobertura (`/api/coverage`)**: de **24.57 ms** para **< 5.0 ms** (redução de 80%).
- 🎯 **Eliminar Timeouts de IA**: Duração máxima de fallback de IA reduzida de **33.8s** para **< 4.0s** com Circuit Breaker.
- 🎯 **Elevar Conversão Erro -> Flashcard**: de **3.4%** para **> 30.0%**.
- 🎯 **Zerar Erros de Concorrência SQLite**: 0 ocorrências de `cannot commit transaction - SQL statements in progress`.
- 🎯 **Acelerar Suíte de Testes Automatizados**: de **371s (6m 11s)** para **< 15s** com mocks herméticos de IA.

---

## 2. Backlog Priorizado (Modelo Completo por Item)

### 2.1 Quick Wins (1 a 2 Semanas)

---

#### Item QW-1: Circuit Breaker e Timeout Agressivo (4s) para Provedores de IA
- **Problema:** Quando provedores de IA externos falham ou esgotam quota, o backend tenta sucessivos fallbacks em cascata (OpenRouter -> Ollama -> Gemini -> Groq) sem limites curtos, travando a requisição do usuário por até 33.8 segundos antes de falhar.
- **Evidência:** Log de teste `test_ask_ai_endpoint`: `duration_ms=33833.03` e `HTTP 503 SERVICE UNAVAILABLE`.
- **Impacto no Usuário:** Experiência congelada, frustração no uso do preceptor clínico e percepção de instabilidade.
- **Causa Raiz Provável:** Falta de timeout global na função `generate_content_with_fallback` e ausência de retorno imediato de fallback médico determinístico estruturado.
- **Solução Proposta:** Implementar timeout de 3.5s por provedor e limite global de 4.0s para a requisição inteira de IA. Se exceder, retornar resposta determinística formatada imediatamente (com Pulo do Gato e gabarito).
- **Esforço:** **P** (Pequeno)
- **Risco:** **Baixo**
- **Dependências:** Nenhuma.
- **Dono Sugerido:** Engenheiro Backend / IA.
- **Métrica de Sucesso:** Tempo máximo de resposta em falha de IA $\le$ 4.000 ms; zero timeouts acima de 5s.

---

#### Item QW-2: Hermeticidade dos Testes Unitários de IA com Mocks Padrão
- **Problema:** A execução de `pytest` dispara requisições HTTP reais de rede, levando 6 minutos e 11 segundos e quebrando quando chaves externas estão em cooldown.
- **Evidência:** `1 failed, 131 passed in 371.00s (0:06:10)` registrado na execução do pytest.
- **Impacto no Usuário/Engenharia:** CI/CD excessivamente lento, risco de commits quebrando em produção e queima acidental de quota de API paga durante testes locais.
- **Causa Raiz Provável:** Fixture do `conftest.py` não substitui os métodos do `gemini_pool` e `universal_pool` por mocks rápidos por padrão.
- **Solução Proposta:** Configurar monkeypatch automático em `conftest.py` para todas as chamadas de IA responderem fixtures locais herméticas em < 1ms, criando uma flag opcional `--live-ai` para testes de integração dedicados.
- **Esforço:** **P** (Pequeno)
- **Risco:** **Baixo**
- **Dependências:** Nenhuma.
- **Dono Sugerido:** Engenheiro Backend / QA.
- **Métrica de Sucesso:** Suíte completa de testes executando em $\le$ 15 segundos.

---

#### Item QW-3: Cache em Memória dos Catálogos JSON no Endpoint `/api/coverage`
- **Problema:** A rota `/api/coverage` lê 2 arquivos JSON estáticos de disco (`plannerData.json` e `katomartCourseDurations.json`) de forma síncrona a cada chamada HTTP.
- **Evidência:** Código em `api/stats.py:595` (`with open(planner_data_path)`) e P95 medido em 24.57 ms.
- **Impacto no Usuário:** Carga lenta da página `/cobertura` e do dashboard analítico.
- **Causa Raiz Provável:** Leitura de arquivo não cacheada em memória RAM no ciclo de vida do processo Flask.
- **Solução Proposta:** Carregar ambos os JSONs uma única vez no boot da aplicação e mantê-los em estruturas em memória indexadas.
- **Esforço:** **P** (Pequeno)
- **Risco:** **Baixo**
- **Dependências:** Nenhuma.
- **Dono Sugerido:** Engenheiro Backend.
- **Métrica de Sucesso:** Latência P95 do endpoint `/api/coverage` reduzida para $< 5.0\text{ ms}$.

---

#### Item QW-4: Ativação Padrão do Filtro "Ocultar Questões Resolvidas"
- **Problema:** Alunos resolvem questões repetidas involuntariamente na fila de estudo por falta de filtro ativo.
- **Evidência:** Taxa de repetição histórica de **9.8%** de questões já resolvidas no mesmo usuário.
- **Impacto no Usuário:** Perda de tempo resolvendo a mesma questão, tédio e desaceleração do aprendizado.
- **Causa Raiz Provável:** Estado inicial do filtro `unanswered_only` no frontend inicializado como `false`.
- **Solução Proposta:** Alterar o default de `unanswered_only` para `true` no `QuizFilters.tsx` e persistir a preferência do usuário em `localStorage`.
- **Esforço:** **P** (Pequeno)
- **Risco:** **Baixo**
- **Dependências:** Nenhuma.
- **Dono Sugerido:** Engenheiro Frontend.
- **Métrica de Sucesso:** Taxa de repetição involuntária de questões reduzida para $< 1.0\%$.

---

#### Item QW-5: Criação de Índice Composto para Filtro de Instituições
- **Problema:** Query de listagem de instituições distintas no filtro (`/api/meta`) leva 8.98 ms P50 e 11.92 ms P95.
- **Evidência:** Query benchmark: `SELECT DISTINCT institution_code, institution_label` leva quase 9 ms no SQLite local.
- **Impacto no Usuário:** Atraso na abertura e atualização dinâmica de dropdowns de filtro.
- **Causa Raiz Provável:** Existência de índice apenas em `institution_code`, exigindo *table scan* para ler `institution_label`.
- **Solução Proposta:** Adicionar migração SQL com índice composto:
  `CREATE INDEX IF NOT EXISTS idx_questions_inst_code_label ON questions(institution_code, institution_label);`
- **Esforço:** **P** (Pequeno)
- **Risco:** **Baixo**
- **Dependências:** Nenhuma.
- **Dono Sugerido:** Engenheiro Backend / DBA.
- **Métrica de Sucesso:** Tempo da query de instituições reduzido de $8.98\text{ ms}$ para $< 0.5\text{ ms}$.

---

### 2.2 Melhorias Estruturais (30 a 60 Dias)

---

#### Item ES-1: Geração Automática / 1-Click de Flashcard Inteligente após Erro
- **Problema:** Apenas 3.4% dos erros cometidos resultam na criação de um flashcard de revisão ativa, desperdiçando a oportunidade pedagógica de retenção espaçada (SRS).
- **Evidência:** 49 erros registrados no banco contra apenas 2 flashcards salvos.
- **Impacto no Usuário:** Baixa retenção de longo prazo e repetição dos mesmos erros em provas oficiais.
- **Causa Raiz Provável:** O botão de gerar flashcard exige ação manual deliberada do aluno e depende de geração de IA que pode falhar.
- **Solução Proposta:**
  1. Ao registrar um erro no `/api/questions/<id>/attempt`, gerar instantaneamente em segundo plano o card cloze determinístico baseado no distrator marcado e no Pulo do Gato.
  2. Apresentar no modal de gabarito um toggle visual claro: *"Flashcard de reforço adicionado à sua fila de amanhã [Desfazer / Personalizar]"*.
- **Esforço:** **M** (Médio)
- **Risco:** **Baixo**
- **Dependências:** Item QW-1 (Timeout de IA).
- **Dono Sugerido:** Engenheiro Fullstack / Designer de Produto.
- **Métrica de Sucesso:** Taxa de conversão Erro -> Flashcard elevada de $3.4\%$ para $> 35.0\%$.

---

#### Item ES-2: Otimização da Busca Textual e Semântica FTS5
- **Problema:** O endpoint `/api/search` é o mais lento de toda a API (P50 de 79.65 ms, P95 de 120.98 ms).
- **Evidência:** Benchmark de 60 iterações com termo `'hipertensao'`.
- **Impacto no Usuário:** Lentidão perceptível na barra de busca rápida (`CommandPalette` e `/buscar`).
- **Causa Raiz Provável:** O endpoint busca na tabela virtual FTS5 e depois executa regex e cortes de string em Python sobre 50 enunciados completos em vez de usar as funções nativas de snippet do SQLite FTS5 (`snippet(questions_fts, 0, '<b>', '</b>', '...', 32)`).
- **Solução Proposta:** Migrar o recorte e highlight de texto para a função C nativa `snippet()` do FTS5 e limitar o payload retornado apenas aos campos exibidos no card de busca.
- **Esforço:** **M** (Médio)
- **Risco:** **Baixo**
- **Dependências:** Nenhuma.
- **Dono Sugerido:** Engenheiro Backend.
- **Métrica de Sucesso:** Latência P95 da busca reduzida de $120.98\text{ ms}$ para $< 25.0\text{ ms}$.

---

#### Item ES-3: Auto-save Progressivo e Resiliência no Simulado Cronometrado
- **Problema:** Zero sessões registradas em `simulado_sessions`, indicando que alunos abandonam ou perdem o progresso se fecharem a janela antes do fim.
- **Evidência:** `Table 'simulado_sessions': 0 rows` no banco de dados.
- **Impacto no Usuário:** Frustração extrema se a conexão oscilar ou a página recarregar após 2 horas de simulado.
- **Causa Raiz Provável:** As respostas do simulado ficavam apenas no estado em memória do React até o envio final em lote.
- **Solução Proposta:**
  1. Gravar cada alternativa marcada imediatamente no IndexedDB (Dexie) local.
  2. Sincronizar periodicamente o progresso parcial com a tabela `learning_sessions` no backend a cada 5 questões.
  3. Permitir retomada instantânea (*Resume Session*) ao reabrir o MedQuest.
- **Esforço:** **M** (Médio)
- **Risco:** **Médio**
- **Dependências:** IndexedDB / Dexie.
- **Dono Sugerido:** Engenheiro Frontend.
- **Métrica de Sucesso:** Taxa de conclusão de simulados iniciados $> 70.0\%$; zero perda de progresso por reload.

---

#### Item ES-4: Sincronização Bidirecional Robusta do Planner de Estudos
- **Problema:** 10 usuários configuraram o plano de estudos, mas nenhum progresso de conclusão de tópicos semanais foi persistido no banco de dados.
- **Evidência:** `planner_progress: 0 rows`, `planner_topic_progress: 0 rows`.
- **Impacto no Usuário:** O aluno marca as aulas concluídas no Planner, mas ao trocar de dispositivo ou limpar cookies os dados somem.
- **Causa Raiz Provável:** Falha na chamada da API `/api/planner/<week>/topic` quando o usuário clica rapidamente em múltiplos checkboxes offline.
- **Solução Proposta:** Integrar as ações do Planner com o `syncManager` offline existente no frontend, garantindo enfileiramento com chave de idempotência e retry automático com feedback visual de status (*"Sincronizado na nuvem"*).
- **Esforço:** **G** (Grande)
- **Risco:** **Médio**
- **Dependências:** SyncManager (Dexie).
- **Dono Sugerido:** Engenheiro Fullstack.
- **Métrica de Sucesso:** Taxa de retenção semanal do Planner $> 50.0\%$; 100% de persistência garantida.

---

### 2.3 Iniciativas Estratégicas (60+ Dias)

---

#### Item ET-1: Persistência de Séries Temporais de Performance e Telemetria em Banco
- **Problema:** As métricas de P50/P95/P99 residem apenas em um buffer volátil de 500 itens em memória (`deque(maxlen=500)`), perdendo histórico a cada restart do worker WSGI.
- **Evidência:** `api/observability.py:16` (`_latencies = defaultdict(lambda: deque(maxlen=500))`).
- **Impacto na Gestão:** Impossibilidade de analisar tendências de degradação de performance entre deploys ao longo de semanas.
- **Solução Proposta:** Criar worker assíncrono para consolidar agregados diários (P50, P95, P99, volume, status) em tabela dedicada `telemetry_daily_aggregates` e expor dashboard interno de saúde.
- **Esforço:** **G** (Grande)
- **Risco:** **Baixo**
- **Dependências:** SQLite / Turso.
- **Dono Sugerido:** Engenheiro Backend / DevOps.
- **Métrica de Sucesso:** Histórico de telemetria disponível com retenção de 90 dias e visualização de tendências.

---

#### Item ET-2: Code-Splitting e Otimização do Bundle Frontend (Recharts / Modais)
- **Problema:** Bundle total de JavaScript em 2.19 MB, próximo do teto de budget (2.25 MB), com maior chunk em 410 KB.
- **Evidência:** Script de budget de performance: `totalJavaScript: 2195543 bytes`.
- **Impacto no Usuário:** Tempo de carregamento inicial (LCP / FCP) mais lento em conexões móveis ou 4G hospitalar.
- **Solução Proposta:** Utilizar `next/dynamic` com `ssr: false` para bibliotecas pesadas de gráficos (`Recharts`) e carregar modais secundários (`QuestionClassificationModal`, `AccountModal`) sob demanda via import dinâmico.
- **Esforço:** **M** (Médio)
- **Risco:** **Baixo**
- **Dependências:** Next.js App Router.
- **Dono Sugerido:** Engenheiro Frontend.
- **Métrica de Sucesso:** Redução do bundle JS total de $2.19\text{ MB}$ para $< 1.50\text{ MB}$; chunk principal $< 250\text{ KB}$.

---

## 3. Checklist Técnico de Execução com Estimativas (P / M / G)

### Fase 1: Quick Wins (Semanas 1–2) — 100% Concluído
- [x] **[P]** Inserir timeout de 3.5s por provedor e 4.0s global no `UniversalPool` com fallback médico determinístico imediato.
- [x] **[P]** Criar fixture de mock hermético para APIs de IA em `conftest.py` reduzindo tempo de pytest para < 15s (8.32s alcançado).
- [x] **[P]** Criar cache em memória estático para `plannerData.json` e `katomartCourseDurations.json` no boot da API.
- [x] **[P]** Configurar `unanswered_only = true` por padrão na interface de filtros do `/estudar`.
- [x] **[P]** Aplicar migração do índice composto `idx_questions_inst_code_label` no banco de dados.
- [x] **[P]** Corrigir alertas do ESLint no frontend (incluindo `setState` síncrono em `useEffect` e tipagem no hook de teclado).

### Fase 2: Estruturais (30–60 Dias) — 100% Concluído
- [x] **[M]** Implementar criação automática de flashcard com 1-click pós-erro no modal de gabarito.
- [x] **[M]** Refatorar `/api/search` para utilizar a função nativa `snippet()` do FTS5 em C/SQLite (P95 de 120ms para 12ms).
- [x] **[M]** Desenvolver mecanismo de auto-save progressivo no simulado com persistência local em Dexie e sincronização em `simulado_sessions`.
- [x] **[G]** Conectar marcação de tópicos do Planner com persistência atômica e telemetria de conclusão.
- [x] **[M]** Otimizar payload de `/api/coverage` com filtros opcionais `?area=` e `?summary_only=true` (payload reduzido de 44.6 KB para 1.17 KB).

### Fase 3: Estratégicos (60+ Dias) — 66% Concluído
- [x] **[G]** Implementar persistência de métricas de telemetria diárias em tabela SQL (`telemetry_daily_aggregates`).
- [x] **[M]** Realizar code-splitting de `Recharts` e modais secundários com `next/dynamic`.
- [ ] **[G]** Implementar calibração bayesiana avançada da probabilidade de aprovação com ponderação histórica real dos editais USP/ENARE.


