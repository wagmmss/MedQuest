export interface OverviewStats {
  total_questions: number;
  distinct_answered: number;
  total_attempts: number;
  accuracy_all_attempts: number | null;
  accuracy_latest_attempt: number | null;
  coverage_pct: number | null;
  srs_due_count: number;
  accuracy_last7: number | null;
  accuracy_prev7: number | null;
  streak_days: number;
  flashcards_due_count?: number;
}

export interface CoverageSubtema {
  subtema: string;
  n_questions: number;
  answered: number;
  attempts: number;
  correct: number;
  accuracy: number | null;
  coverage_pct: number;
  status: "mastered" | "proficient" | "in_progress" | "not_started";
}

export interface CoverageArea {
  area: string;
  n_questions: number;
  n_subtemas: number;
  answered_questions: number;
  attempts: number;
  correct: number;
  mastered: number;
  proficient: number;
  in_progress: number;
  not_started: number;
  accuracy: number | null;
  subtemas: CoverageSubtema[];
}

export interface CoverageResponse {
  areas: CoverageArea[];
}

export interface TimelineStat {
  day: string;
  attempts: number;
  correct: number;
  accuracy: number;
}

export interface WeakTopic {
  topic: string;
  attempts: number;
  correct: number;
  accuracy: number;
}

export interface LearningProfileTopic {
  topic: string;
  area: string;
  available: number;
  attempts: number;
  correct: number;
  accuracy: number | null;
  coverage: number;
  confidence: number;
  retrievability: number | null;
  due_count: number;
  priority_score: number;
  reasons: string[];
}

export interface LearningProfile {
  generated_at: string;
  goal: {
    questions_today: number;
    configured_daily_questions: number;
    reviews_due: number;
    target_score: number | null;
    exam_date: string | null;
  };
  topics: LearningProfileTopic[];
  method: { deterministic: boolean; signals: string[] };
}

export interface Recommendation {
  type: string;
  icon: string;
  title: string;
  description: string;
  cta: string;
  filters: Record<string, string>;
}

export interface BreakdownStat {
  key: string;
  label: string;
  attempts: number;
  correct: number;
  accuracy: number;
}

export interface DistractorStat {
  subtema: string;
  total_wrong: number;
  wrong_choices: {
    letter: string;
    count: number;
  }[];
}

export interface PredictiveScore {
  projected_score: number;
  target_score: number | null;
  areas: {
    area: string;
    accuracy: number;
    attempts: number;
  }[];
}

export interface AtRiskTopic {
  subtema: string;
  items_count: number;
  stability: number | null;
  retrievability?: number;
}

export interface PlannerConfig {
  exam_date?: string;
  start_date?: string;
  days_per_week?: number;
  hours_per_day?: number;
  target_score?: number;
}

export interface PlannerTopic {
  area: string;
  subtema: string;
  questions_available: number;
  estimated_hours: number;
}

export interface PlannerWeek {
  week: number;
  date: string;
  topics: PlannerTopic[];
  recommended_hours: number;
  allocated_hours: number;
}

export interface PlannerPlanResponse {
  plan: PlannerWeek[];
  warning?: string;
  total_required_hours?: number;
  total_available_hours?: number;
}

export interface PlannerWeekProgress {
  studied: boolean;
  studied_at: string | null;
  rev24h: boolean;
  rev7d: boolean;
  rev30d: boolean;
}

export interface PlannerProgressMap {
  [weekId: string]: PlannerWeekProgress;
}

export interface QuestionMeta {
  institutions: { institution_code: string; institution_label: string; n: number }[];
  years: number[];
  sources: { source_file: string; n: number }[];
  areas: { area: string; n: number }[];
  specialties: { specialty: string; n: number }[];
  subtemas: { subtema: string; n: number }[];
  total_questions: number;
  answered_questions: number;
}

export interface SubtemaItem {
  subtema: string;
  n: number;
}

export interface QuestionListItem {
  id: number;
  source_file: string;
  source_number: number;
  year: number;
  institution_code: string;
  institution_label: string;
  topic: string;
  area: string;
  subtema: string;
  adaptive_score?: number;
  adaptive_reasons?: string[];
  retrievability?: number | null;
}

export interface QuestionAlternative {
  letter: string;
  text: string;
}

export interface ClinicalCase {
  stem: string;
  images: string[];
}

export interface QuestionDetail extends QuestionListItem {
  stem: string;
  alternatives: QuestionAlternative[];
  images: string[];
  already_answered?: {
    selected_letter: string;
    is_correct: number;
  };
  is_verified?: boolean;
  last_updated_at?: string;
  technical_note?: string;
  medical_references?: string;
  clinical_case?: ClinicalCase;
  usp_macro?: string;
  usp_micro?: string;
  is_favorite?: boolean;
  times_wrong?: number;
}

export interface AttemptResult {
  is_correct: boolean;
  correct_letter: string;
  explanation: string | null;
  next_review_date: string;
}

export interface BatchAttemptItem {
  question_id: number;
  selected_letter: string;
  time_spent_ms?: number;
  confidence?: string;
}

export interface BatchAttemptResultItem {
  question_id: number;
  is_correct: boolean;
  correct_letter: string;
  explanation: string | null;
  next_review_date: string;
}

export interface BatchAttemptResult {
  results: BatchAttemptResultItem[];
}

export interface BatchDetailResponse {
  questions: QuestionDetail[];
}

export interface SearchResult {
  id: number;
  institution_code: string;
  year: number;
  area: string;
  subtema: string;
  stem_snippet: string;
  exp_snippet: string;
}

export interface Flashcard {
  id: number;
  question_id: number;
  front: string;
  back: string;
  next_review_date: string;
  stem?: string;
  source_context?: string;
  is_ai_generated?: boolean;
}

export interface FlashcardGenerateResponse {
  id: number;
  question_id: number;
  front: string;
  back: string;
}
