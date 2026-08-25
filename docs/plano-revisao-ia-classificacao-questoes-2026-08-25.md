# Plano de revisão assistida por IA da classificação de questões

## Objetivo

Reclassificar e validar o banco inteiro sem permitir que uma regra genérica ou
uma resposta incerta da IA modifique a base publicada. O resultado desejado é
uma classificação por **área** e **subtema canônico** que seja explicável,
auditável, reversível e calibrada contra revisão humana.

Este plano começa pelos três grupos já detectados como inflados:

1. Atenção Primária à Saúde e Estratégia Saúde da Família (ESF);
2. Sangramento Uterino Anormal (SUA) e Classificação PALM-COEIN / Miomatose;
3. Geriatria: Avaliação Ampla do Idoso, Síndromes Demenciais e Quedas.

Nenhuma alteração deve ser aplicada diretamente em `questions.subtema` durante
a fase de análise.

## Princípios obrigatórios

- A taxonomia em `app/backend/data/taxonomy.json` é a única lista válida de
  destinos. A IA não cria temas, não renomeia temas e não usa texto livre.
- A IA pode responder `ABSTENÇÃO`; ausência de evidência nunca vira um tema
  padrão.
- Cada decisão precisa citar evidência curta do enunciado, alternativas,
  comentário ou tema-fonte. Um rótulo sem evidência é inválido.
- A proposta da IA e a decisão editorial humana são registros distintos.
- Aplicação no banco só ocorre por lote aprovado, com backup, relatório de
  diferenças e possibilidade de reversão por `run_id`.
- O desempenho deve ser medido por área e por subtema, não apenas pela média
  global.

## Modelo de dados para auditoria

Criar tabelas novas; não sobrescrever dados históricos.

### `classification_runs`

Uma linha por execução: `id`, versão da taxonomia, modelo, prompt/versionamento,
data, hash do conjunto de entrada e configuração.

### `classification_proposals`

Uma linha por questão e por avaliador:

| Campo | Uso |
|---|---|
| `run_id`, `question_id`, `reviewer_role` | Rastreabilidade da execução e do avaliador (`classifier`, `critic`, `adjudicator`) |
| `proposed_area`, `proposed_subtema` | Destino obrigatório da taxonomia ou `ABSTENÇÃO` |
| `confidence` | Número de 0 a 1, com escala documentada |
| `evidence` | Trecho e justificativa clínica curta |
| `alternatives_json` | Até três destinos plausíveis, ordenados |
| `status` | `proposed`, `accepted`, `rejected`, `needs_human_review` |

### `classification_reviews`

Registra revisão humana: decisão final, revisor, data, motivo e, se houve
correção, o tema anterior. A classificação publicada é derivada somente da
última revisão aceita.

## Pipeline confiável

### 1. Congelamento e linha de base

1. Fazer backup versionado do banco e registrar hash da tabela `questions`.
2. Exportar `id`, área/subtema atuais, tema-fonte, enunciado, alternativas e
   explicação para um snapshot imutável.
3. Executar verificações estruturais: pares área/subtema válidos, duplicatas
   exatas, questões sem enunciado e temas sem questões.
4. Não alterar nada nessa fase.

### 2. Conjunto-ouro humano

Antes de processar o banco, médicos revisam uma amostra estratificada:

- pelo menos 20 questões de cada subtema com material suficiente;
- todas as questões dos subtemas muito pequenos (menos de 20);
- 100 questões extras de temas de alto volume e de fronteira clínica;
- as 638 questões inicialmente suspeitas nos três grupos inflados.

Cada questão do conjunto-ouro recebe área, subtema, evidência e justificativa.
Discordâncias entre dois revisores passam por um terceiro revisor. Esse conjunto
é a referência para calibrar prompts e limiares; não é usado para “forçar” a
resposta da IA em outras questões.

### 3. Classificação em microblocos

Processar blocos de **10 a 20 questões do mesmo contexto clínico**, nunca o
banco inteiro de uma vez. Cada bloco contém a definição curta dos subtemas
permitidos daquela área e exemplos validados do conjunto-ouro.

Para cada questão, enviar:

- enunciado integral;
- alternativas e gabarito, quando disponíveis;
- explicação existente;
- área e subtema atuais apenas como hipótese, não como verdade;
- tema-fonte como evidência secundária.

O resultado deve ser JSON validável, sem texto fora do schema:

```json
{
  "question_id": 123,
  "decision": "classify | abstain",
  "area": "Medicina Preventiva",
  "subtema": "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)",
  "confidence": 0.94,
  "evidence": "Discute longitudinalidade e adscrição territorial na ESF.",
  "alternatives": [
    {"area": "Medicina Preventiva", "subtema": "...", "confidence": 0.94}
  ]
}
```

O validador rejeita qualquer área/subtema fora da taxonomia, confiança ausente,
evidência vazia ou decisão diferente de `classify`/`abstain`.

### 4. Dupla análise independente

Cada questão recebe duas análises independentes:

1. **Classificador clínico:** determina o tema principal com base no conteúdo.
2. **Crítico de classificação:** recebe a mesma questão sem ver a primeira
   resposta e procura especificamente confusão com temas vizinhos.

Um terceiro passo de adjudicação só recebe as duas respostas estruturadas e a
questão. Ele não pode inventar uma terceira categoria sem justificar com a
taxonomia. Não reutilizar o mesmo retorno-padrão entre os papéis.

## Política de decisão

| Situação | Destino |
|---|---|
| Dois avaliadores concordam, confiança >= 0,90, evidências coerentes e desempenho validado no conjunto-ouro | Proposta de alteração em lote de alta confiança |
| Concordam entre 0,75 e 0,89 | Fila de revisão humana por amostragem estratificada; só publicar após taxa de acerto aceitável |
| Discordam, qualquer um se abstém ou confiança < 0,75 | Revisão humana obrigatória |
| Há mudança de área | Revisão humana obrigatória, independentemente da confiança |
| Destino atual é um tema que funcionou como fallback | Revisão humana obrigatória até que o fallback seja eliminado |

Mesmo os lotes de alta confiança devem ter amostra aleatória de pelo menos 10%
revisada por humano, com mínimo de 20 questões por subtema. Se a precisão dessa
amostra ficar abaixo de 98%, suspender a aplicação daquele subtema e retornar à
calibração.

## Ordem de execução

### Fase A — corrigir as filas contaminadas

1. Revisar as 317 questões sem evidência direta de APS/ESF.
2. Revisar as 91 questões sem evidência direta de SUA/miomatose.
3. Revisar as 230 questões sem evidência direta de geriatria/demência/quedas.
4. Para cada tema, conferir também uma amostra aleatória das questões que
   permaneceriam nele, evitando falso negativo do filtro inicial.

Essas 638 questões são prioridade porque os classificadores existentes usam
esses temas como retorno incondicional.

### Fase B — temas de alto volume e fronteiras conhecidas

Revisar, na sequência, todos os subtemas que receberam retorno padrão ou que
têm grande sobreposição clínica: pré-natal versus condições intercorrentes,
parto versus hemorragia, APS versus SUS/vigilância, pneumonia versus derrame
pleural, e geriatria versus neurologia/psiquiatria.

### Fase C — cobertura total estratificada

Executar o pipeline em todas as áreas, ordenando por:

1. temas sem nenhuma questão;
2. temas com menos de 20 questões;
3. temas com maior volume;
4. temas com maior taxa de desacordo da IA;
5. restantes, em blocos homogêneos.

## Interface de revisão humana

A tela de revisão deve mostrar uma questão por vez, mantendo visíveis:

- classificação atual e proposta;
- evidência das duas análises;
- até três alternativas plausíveis;
- enunciado, alternativas, gabarito e explicação;
- botões `aceitar`, `escolher outro subtema`, `manter atual`, `marcar como
  ambígua`;
- motivo obrigatório para divergência da IA.

O revisor nunca deve editar o nome do subtema livremente. A busca usa apenas a
taxonomia canônica.

## Aplicação segura e reversão

1. Gerar um CSV/JSON de alterações propostas, com `question_id`, antes/depois,
   evidência, confiança, revisor e `run_id`.
2. Rodar validação em cópia do banco.
3. Publicar apenas um lote aprovado em transação única.
4. Gerar relatório pós-aplicação: contagem por tema, mudanças por área,
   questões não classificadas e amostra das mudanças.
5. Guardar tabela de histórico. Reverter um lote significa reaplicar os valores
   anteriores registrados no mesmo `run_id`, nunca restaurar um banco inteiro.

## Critérios de encerramento

O banco só é considerado revisado quando todos os itens abaixo forem verdadeiros:

- 100% dos pares área/subtema pertencem à taxonomia atual;
- 100% das questões possuem proposta auditável ou decisão humana;
- não existe classificador com retorno-padrão de subtema;
- precisão humana amostral >= 98% para cada subtema publicado;
- 100% das mudanças de área foram revisadas por humano;
- nenhum subtema possui aumento artificial explicado por fallback;
- relatórios de execução, decisões e possibilidade de reversão estão presentes.

## Primeiro entregável prático

Implementar primeiro uma execução somente de leitura para os três temas
inflados. Ela deve gerar três filas de 10–20 questões, duas propostas
independentes por questão e um arquivo de revisão. Após validar manualmente um
piloto de 50 questões de cada fila, ajustar os prompts/limiares antes de tocar
no banco.
