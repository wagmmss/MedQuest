import { getLocalOwnerId } from "./db";

export type LearningSessionKind = "quiz" | "simulado";

const LEGACY_KEYS: Record<LearningSessionKind, string> = {
  quiz: "medquest_quiz_state",
  simulado: "medquest_simulado_state",
};

export const LEARNING_SESSION_VERSION = 2;

export function getLearningSessionKey(kind: LearningSessionKind): string {
  return `medquest_${kind}_state_v2:${getLocalOwnerId()}`;
}

function removeLegacyState(kind: LearningSessionKind): void {
  localStorage.removeItem(LEGACY_KEYS[kind]);
  sessionStorage.removeItem(LEGACY_KEYS[kind]);
}

export function readLearningSession<T>(
  kind: LearningSessionKind,
  isValid: (value: unknown) => value is T,
): T | null {
  removeLegacyState(kind);
  const key = getLearningSessionKey(kind);
  const raw = localStorage.getItem(key);
  if (!raw) return null;

  try {
    const parsed: unknown = JSON.parse(raw);
    if (isValid(parsed)) return parsed;
  } catch {
    // Invalid or partial writes are discarded below.
  }

  localStorage.removeItem(key);
  return null;
}

export function writeLearningSession(kind: LearningSessionKind, value: unknown): boolean {
  try {
    localStorage.setItem(getLearningSessionKey(kind), JSON.stringify(value));
    return true;
  } catch (error) {
    console.error(`Unable to persist ${kind} session`, error);
    return false;
  }
}

export function removeLearningSession(kind: LearningSessionKind): void {
  removeLegacyState(kind);
  localStorage.removeItem(getLearningSessionKey(kind));
}

export function clearLearningSessions(): void {
  removeLearningSession("quiz");
  removeLearningSession("simulado");
}
