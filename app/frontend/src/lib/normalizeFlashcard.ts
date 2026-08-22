/**
 * Normaliza flashcards legados (formato "A alternativa correta era...")
 * para o formato clínico de alta produtividade com cenário, cloze ativo,
 * gabarito oficial e análise de distrator.
 *
 * Aplicado tanto na leitura (Revisão Ativa) quanto no preview pós-geração
 * (Estudar, Simulado) para garantir consistência visual.
 */

export interface FlashcardLike {
  front: string;
  back: string;
  stem?: string;
}

const LOW_QUALITY_PATTERNS = [
  "A alternativa correta era",
  "alternativa correta era",
  "Neste caso clínico, em vez de",
  "Para este quadro clínico,",
];

const QUESTION_END_PATTERN =
  /(?:Diante disso|Diante do exposto|Diante desse quadro|Nesse momento|Nesse caso|Considerando o caso|Em relação ao caso|Sobre o caso descrito|Qual a conduta|Qual o diagnóstico|Qual é o diagnóstico|A melhor conduta|A conduta mais adequada|O diagnóstico mais provável).*$/i;

function stripOptionLetter(text: string): string {
  return text.replace(/^[A-Ea-e][\)\.\:\-]\s*/, "").trim();
}

export function normalizeFlashcard<T extends FlashcardLike>(card: T): T {
  let front = card.front || "";
  let back = card.back || "";

  const isLegacy = LOW_QUALITY_PATTERNS.some((pat) => front.includes(pat));

  if (isLegacy) {
    // Extract the cloze content from the legacy front
    const clozeMatch = front.match(/{{c1::(.*?)}}/);
    const term = clozeMatch ? stripOptionLetter(clozeMatch[1]) : "";

    // Extract the wrong answer from the legacy back
    const wrongMatch =
      back.match(/Você marcou\s*['"](.*?)['"]/i) ||
      back.match(/em vez de\s*["'](.*?)["']/i);
    const wrongTerm = wrongMatch ? stripOptionLetter(wrongMatch[1]) : "";

    // Build the clinical scenario from the stem
    let scenario = "";
    if (card.stem) {
      scenario = card.stem.trim();
      const endMatch = scenario.match(QUESTION_END_PATTERN);
      if (endMatch && endMatch.index && endMatch.index > 30) {
        scenario = scenario.substring(0, endMatch.index).trim();
      }
      scenario = scenario.replace(/[\s,;:]+$/, "").trim();
      if (scenario && !scenario.endsWith(".")) scenario += ".";
    }

    const tag = "[Caso Clínico / Conduta]";
    front =
      scenario && scenario.length > 20
        ? `${tag} ${scenario}\n\n👉 Diagnóstico / Conduta indicada: {{c1::${term}}}`
        : `${tag}\n\n👉 Diagnóstico / Conduta indicada: {{c1::${term}}}`;

    if (
      back.startsWith("Você marcou") ||
      back.startsWith("Alternativa correta:")
    ) {
      back = wrongTerm
        ? `💡 Gabarito Oficial:\n${term}\n\n⚠️ Atenção ao distrator:\nA opção '${wrongTerm}' é incorreta para este quadro clínico.`
        : `💡 Gabarito Oficial:\n${term}`;
    }
  } else {
    // Even for non-legacy cards, strip option letters from cloze content
    front = front.replace(/{{c1::[A-Ea-e][\)\.\:\-]\s*(.*?)}}/, "{{c1::$1}}");
  }

  return {
    ...card,
    front,
    back,
  };
}
