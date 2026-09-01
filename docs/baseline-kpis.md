# Baseline de Indicadores-Chave de Desempenho (KPIs) — MedQuest
**Versão:** 1.0 (Semana 1 de Diagnóstico)  
**Data:** 31 de Agosto de 2026  
**Ambiente:** Baseline consolidado sobre banco de produção local (`medquest.db` / WAL Mode / 7.674 questões).

---

## 1. Resumo dos KPIs de Baseline

| Indicador (KPI) | Fonte de Dados | Fórmula / Método de Cálculo | Valor Atual (Baseline) | Meta Próximo Ciclo (30 dias) | Meta Longo Prazo (60 dias) |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Latência P95 — Busca (`/api/search`)** | Telemetria / Benchmark | Quantil 95% do tempo de resposta | **120.98 ms** | **< 30.0 ms** | **< 15.0 ms** |
| **Latência P95 — Cobertura (`/api/coverage`)** | Telemetria / Benchmark | Quantil 95% do tempo de resposta | **24.57 ms** | **< 5.0 ms** | **< 2.0 ms** |
| **Latência P95 — Prontidão (`/api/stats/exam-readiness`)** | Telemetria / Benchmark | Quantil 95% do tempo de resposta | **21.95 ms** | **< 8.0 ms** | **< 5.0 ms** |
| **Latência P95 — Questões (`/api/questions`)** | Telemetria / Benchmark | Quantil 95% do tempo de resposta | **5.51 ms** | **< 5.0 ms** | **< 3.0 ms** |
| **Latência P95 — Overview (`/api/stats/overview`)** | Telemetria / Benchmark | Quantil 95% do tempo de resposta | **0.74 ms** | **< 1.0 ms** | **< 0.5 ms** |
| **Tamanho do Payload (`/api/coverage`)** | Medição HTTP | Bytes transferidos no corpo da resposta | **44.65 KB** | **< 15.0 KB** | **< 8.0 KB** (compactado) |
| **Tempo Máximo em Falha de IA** | Logs / Traces de Erro | Duração total até fallback em falha externa | **33.833 ms** (33.8s) | **< 4.000 ms** (4.0s) | **< 2.000 ms** (2.0s) |
| **Taxa de Erro de Sistema (HTTP 5xx)** | Logs de Servidor | $\frac{\text{Erros 5xx}}{\text{Total de Requisições}} \times 100$ | **< 0.5%** | **< 0.05%** | **< 0.01%** |
| **Taxa de Conversão Erro -> Flashcard** | Tabela `attempts` vs `flashcards` | $\frac{\text{Flashcards Criados}}{\text{Total de Erros}} \times 100$ | **3.4%** (2 / 49) | **> 25.0%** | **> 45.0%** |
| **Taxa de Conclusão de Simulado** | Tabela `simulado_sessions` | $\frac{\text{Sessões Concluídas}}{\text{Simulados Iniciados}} \times 100$ | **0.0%** (0 / N) | **> 60.0%** | **> 80.0%** |
| **Taxa de Adesão ao Planner Semanal** | Tabela `planner_progress` | $\frac{\text{Semanas com Check}}{\text{Planos Gerados}} \times 100$ | **0.0%** (0 / 10) | **> 40.0%** | **> 70.0%** |
| **Taxa de Retrabalho / Repetição de Ação** | Tabela `attempts` por usuário | $\frac{\text{Tentativas Repetidas}}{\text{Total de Tentativas}} \times 100$ | **9.8%** | **< 2.0%** | **< 1.0%** |
| **Tempo Médio por Questão (Estudo)** | Campo `time_spent_ms` em `attempts` | Média ponderada do tempo em tela | **10.3 s** (novos) | **8.0 s - 15.0 s** | **Equilibrado** |
| **Tempo de Execução da Suíte de Testes** | `pytest` | Duração do comando em ambiente local/CI | **371 s** (6m 11s) | **< 15 s** (hermético) | **< 8 s** |
| **Tamanho Total de JavaScript (Frontend)** | Script de budget de performance | Soma dos bytes de scripts `.next/static` | **2.19 MB** | **< 1.80 MB** | **< 1.40 MB** |

---

## 2. Detalhamento dos Endpoints Críticos (Tabela de Baseline de Latência)

Medição realizada com **60 amostras por endpoint** em regime estável de warmup:

```
+---------------------------------------------+---------+---------+---------+----------+-------------+
| Endpoint                                    | P50(ms) | P95(ms) | P99(ms) | Max (ms) | Payload(KB) |
+---------------------------------------------+---------+---------+---------+----------+-------------+
| GET /api/search?q=hipertensao&limit=20      |   79.65 |  120.98 |  122.90 |   134.12 |        1.26 |
| GET /api/coverage                           |   21.23 |   24.57 |   26.53 |    35.60 |       44.65 |
| GET /api/stats/domain-summary               |   19.80 |   23.77 |   27.04 |    31.10 |        1.08 |
| GET /api/stats/exam-readiness               |   18.38 |   21.95 |   22.60 |    25.40 |        1.09 |
| GET /api/questions?area=Clinica+Medica&l=50 |    9.10 |   10.72 |   12.40 |    15.20 |        0.00 |
| GET /api/subtemas                           |    5.63 |    8.08 |   10.48 |    12.10 |        4.56 |
| GET /api/stats/weak-topics                  |    4.47 |    6.21 |    6.44 |     7.10 |        0.00 |
| GET /api/stats/timeline?days=14             |    4.30 |    6.11 |    6.68 |     7.50 |        0.00 |
| GET /api/flashcards/review                  |    4.05 |    5.83 |    6.19 |     8.40 |        0.00 |
| GET /api/questions?limit=20                 |    3.54 |    5.51 |    5.86 |     6.80 |        7.86 |
| GET /api/planner/topics                     |    3.47 |    5.24 |    6.71 |     7.90 |        0.00 |
| GET /api/stats/breakdown                    |    3.39 |    4.66 |    5.61 |     6.20 |        0.00 |
| GET /api/planner/config                     |    3.37 |    5.87 |    6.14 |     7.50 |        0.18 |
| GET /api/planner                            |    3.36 |    5.37 |    5.95 |     6.80 |        0.00 |
| GET /api/stats/predictive-score             |    3.09 |    5.22 |    5.84 |     6.50 |        0.05 |
| GET /api/questions/1000                     |    2.98 |    4.58 |    5.25 |     6.00 |        0.02 |
| GET /api/meta                               |    0.67 |    1.03 |    1.22 |     1.82 |       41.54 |
| GET /api/stats/overview                     |    0.42 |    0.74 |    0.77 |     1.00 |        0.54 |
+---------------------------------------------+---------+---------+---------+----------+-------------+
```

---

## 3. Decomposição das Queries do Banco de Dados (`medquest.db`)

| Operação SQL | P50 (ms) | P95 (ms) | Max (ms) | Observações de Diagnóstico |
| :--- | :---: | :---: | :---: | :--- |
| `COUNT(*) FROM questions` | **0.01** | **0.01** | 1.34 | Leitura do B-Tree de contagem indexado. |
| `SELECT DISTINCT area FROM questions` | **0.31** | **0.32** | 0.69 | Utiliza índice `idx_questions_area`. |
| `SELECT DISTINCT institution_code, institution_label` | **8.98** | **11.92** | 12.85 | ⚠️ **Lento:** Falta índice cobrindo `institution_code, institution_label`. |
| `SELECT q.* WHERE area = ? AND subtema = ?` | **0.00** | **0.00** | 0.09 | Utiliza `idx_questions_area_subtema`. |
| `SELECT question + alternatives LEFT JOIN` | **0.01** | **0.01** | 0.06 | Utiliza `idx_alt_qid`. |
| `FTS5 MATCH 'hipertensao'` | **0.07** | **0.10** | 0.58 | O índice virtual FTS5 é rápido; overhead está no Python. |
| `Attempts aggregate por user_id` | **0.01** | **0.01** | 0.06 | Utiliza `idx_attempts_user_question`. |
| `Spaced repetition due cards` | **0.01** | **0.01** | 0.02 | Utiliza `idx_spaced_repetition_review`. |

---

## 4. Distribuição de Comportamento e Fricção de Usuários

Dados consolidados a partir da base histórica de tentativas:

### 4.1 Nível de Confiança Informado pelo Aluno
- **Não Informado (`none`):** 35 tentativas (**59.3%**)
- **Adiado (`defer` / padrão):** 16 tentativas (**27.1%**)
- **Certeza Absoluta (`certeza`):** 7 tentativas (**11.9%**)
- **Dúvida (`duvida`):** 1 tentativa (**1.7%**)

*Diagnóstico de Produto:* Quase 60% dos alunos não utilizam o seletor de confiança porque a submissão rápida não exige a marcação. Isso empobrece o algoritmo adaptativo FSRS, que depende da autoavaliação para calibrar a curva de esquecimento.

### 4.2 Retrabalho e Repetição Involuntária
- **Tentativas repetidas no mesmo usuário:** 9.8% (4 repetições em 41 tentativas).
- *Ação:* Tornar o filtro `?unanswered_only=true` o padrão na inicialização do componente `QuizFilters.tsx`.

---

## 5. Como Fechar as Lacunas na Semana 2

1. **Adicionar Índice Composto de Instituição**:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_questions_inst_code_label ON questions(institution_code, institution_label);
   ```
2. **Implementar Cache TTL em Memória para `/api/coverage`**:
   - Manter as estruturas de `plannerData.json` e `katomartCourseDurations.json` carregadas no boot da aplicação em vez de executar `open()` a cada requisição.
3. **Ativar Fallback com Timeout de 4s em Chamadas de IA**:
   - Interromper cadeias de fallback antes de exceder o limite de tolerância do usuário.
4. **Mockar I/O de Rede nos Testes Unitários**:
   - Configurar fixture padrão de pytest para simular respostas de IA instantaneamente em modo offline/CI.
