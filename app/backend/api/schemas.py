"""Validação de entrada com Pydantic."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

__all__ = [
    "AttemptIn",
    "BatchAttemptIn",
    "BatchAttemptItem",
    "CronDispatchIn",
    "FavoriteIn",
    "FlashcardBatchIn",
    "FlashcardGenerateIn",
    "FlashcardPreviewIn",
    "FlashcardReportIn",
    "FlashcardReviewIn",
    "FlashcardSaveIn",
    "GeneratePlanIn",
    "NotificationConfigIn",
    "PlannerConfigIn",
    "PlannerRevisionIn",
    "PlannerStudyIn",
    "PrescribeStudyIn",
    "PushSubscriptionIn",
    "PushSubscriptionKeys",
    "PushUnsubscribeIn",
    "QuestionBatchIn",
    "ReviewIn",
    "SimuladoCustomIn",
    "SimuladoSessionIn",
    "SynthesizeExplanationIn",
    "ValidationError",
    "validation_errors",
]


class APIInput(BaseModel):
    """Base for request bodies: reject unknown fields instead of ignoring them."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def validation_errors(error: ValidationError) -> list[dict]:
    """Return Pydantic diagnostics that Flask can safely JSON-encode."""

    return error.errors(include_url=False, include_context=False)


class AttemptIn(APIInput):
    selected_letter: str = Field(default="A", pattern=r"^(?:[A-Ea-e]|DISCURSIVA|D)?$")
    time_spent_ms: int | None = Field(default=None, ge=0)
    confidence: Literal["chutei", "duvida", "certeza", "defer"] | None = None
    is_correct: bool | None = None
    user_answer_text: str | None = Field(default=None, max_length=10000)


class BatchAttemptItem(APIInput):
    question_id: int = Field(gt=0)
    selected_letter: str = Field(default="A", pattern=r"^(?:[A-Ea-e]|DISCURSIVA|D)?$")
    time_spent_ms: int | None = Field(default=None, ge=0)
    confidence: Literal["chutei", "duvida", "certeza", "defer"] | None = None
    is_correct: bool | None = None
    user_answer_text: str | None = Field(default=None, max_length=10000)


class BatchAttemptIn(APIInput):
    attempts: list[BatchAttemptItem] = Field(max_length=500)


class ReviewIn(APIInput):
    confidence: Literal["chutei", "duvida", "certeza"]
    is_correct: bool | None = None


class PlannerConfigIn(APIInput):
    exam_date: str | None = None
    start_date: str | None = None
    days_per_week: int = Field(default=6, ge=1, le=7)
    hours_per_day: int = Field(default=4, ge=1, le=24)
    target_score: float | None = Field(default=None, ge=0, le=100)
    target_institution: str | None = Field(default=None, max_length=500)
    target_institutions: list[str] | None = Field(default=None, max_length=50)
    target_specialty: str | None = Field(default=None, max_length=100)



class PlannerStudyIn(APIInput):
    studied: bool = False


class PlannerTopicProgressIn(APIInput):
    subtema: str = Field(min_length=1, max_length=500)
    completed: bool = False


class PlannerRevisionIn(APIInput):
    type: Literal["rev24h", "rev7d", "rev30d"]
    checked: bool = False


class GeneratePlanIn(APIInput):
    exam_date: str
    start_date: str | None = None
    hours_per_week: int = Field(default=20, ge=1, le=168)
    intensive: bool = False


class SimuladoCustomIn(APIInput):
    institutions: list[str] = Field(default_factory=list, max_length=20)
    years: list[str] = Field(default_factory=list, max_length=20)
    questions_per_area: int = Field(default=20, ge=1, le=100)
    # These options are consumed by the frontend after the question IDs are selected.
    duration_minutes: int | None = Field(default=None, ge=1, le=24 * 60)
    force_4_options: bool = False


class SimuladoSessionIn(APIInput):
    client_session_id: str = Field(min_length=8, max_length=100)
    planned_duration_seconds: int = Field(ge=1, le=24 * 60 * 60)
    elapsed_seconds: int = Field(ge=0, le=24 * 60 * 60)
    total_questions: int = Field(ge=1, le=500)
    answered_count: int = Field(ge=0, le=500)
    correct_count: int = Field(ge=0, le=500)
    filters: dict = Field(default_factory=dict)
    area_results: list[dict] = Field(default_factory=list, max_length=20)


class QuestionBatchIn(APIInput):
    ids: list[int] = Field(min_length=1, max_length=200)
    force_4_options: bool = False

    @model_validator(mode="after")
    def validate_ids(self):
        if any(question_id <= 0 for question_id in self.ids):
            raise ValueError("ids must contain positive integers")
        # Preserve caller order while avoiding repeated database and response work.
        self.ids = list(dict.fromkeys(self.ids))
        return self


class FavoriteIn(APIInput):
    is_favorite: bool | None = None


class FlashcardGenerateIn(APIInput):
    question_id: int = Field(gt=0)
    wrong_letter: str = Field(default="", pattern=r"^(?:[A-Ea-e])?$")


class FlashcardPreviewIn(APIInput):
    question_id: int = Field(gt=0)
    wrong_letter: str = Field(default="", pattern=r"^(?:[A-Ea-e])?$")


class FlashcardSaveIn(APIInput):
    question_id: int = Field(gt=0)
    front: str = Field(min_length=1, max_length=10_000)
    back: str = Field(default="", max_length=20_000)
    context: str = Field(default="", max_length=2_000)


class FlashcardBatchIn(APIInput):
    items: list[FlashcardGenerateIn] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def unique_questions(self):
        question_ids = [item.question_id for item in self.items]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("items must contain unique question_id values")
        return self


class FlashcardReviewIn(APIInput):
    confidence: Literal["errei", "duvida", "certeza"]


class FlashcardReportIn(APIInput):
    reason: str = Field(min_length=1, max_length=1_000)


class PrescribeStudyIn(APIInput):
    target_institution: str | None = Field(default=None, max_length=100)
    weak_topics: list[dict] | None = Field(default=None, max_length=20)
    distractors: list[dict] | None = Field(default=None, max_length=20)
    at_risk_topics: list[dict] | None = Field(default=None, max_length=20)


class SynthesizeExplanationIn(APIInput):
    force_regenerate: bool = False


class NotificationConfigIn(APIInput):
    enabled: bool = False
    preferred_hour: int = Field(default=8, ge=0, le=23)
    days_of_week: list[int] = Field(default=[0, 1, 2, 3, 4, 5, 6], max_length=7)
    max_daily_reminders: Literal[1] = 1


    @model_validator(mode="after")
    def validate_days(self):
        for day in self.days_of_week:
            if not isinstance(day, int) or day < 0 or day > 6:
                raise ValueError("days_of_week must contain integers from 0 to 6")
        return self


class PushSubscriptionKeys(APIInput):
    p256dh: str = Field(min_length=1, max_length=500)
    auth: str = Field(min_length=1, max_length=500)


class PushSubscriptionIn(APIInput):
    endpoint: str = Field(min_length=10, max_length=2000, pattern=r"^https://.*")
    keys: PushSubscriptionKeys
    expiration_time: int | None = None


class PushUnsubscribeIn(APIInput):
    endpoint: str | None = Field(default=None, max_length=2000)


class CronDispatchIn(APIInput):
    force_user_id: str | None = Field(default=None, max_length=100)
    ignore_hour: bool = False
