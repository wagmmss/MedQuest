"""Validação de entrada com Pydantic."""
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

__all__ = [
    "AttemptIn",
    "BatchAttemptIn",
    "BatchAttemptItem",
    "GeneratePlanIn",
    "PlannerConfigIn",
    "PlannerRevisionIn",
    "PlannerStudyIn",
    "ReviewIn",
    "ValidationError",
]


class AttemptIn(BaseModel):
    selected_letter: str = Field(pattern=r"^[A-Ea-e]$")
    time_spent_ms: int | None = Field(default=None, ge=0)
    confidence: Literal["chutei", "duvida", "certeza", "defer"] | None = None


class BatchAttemptItem(BaseModel):
    question_id: int
    selected_letter: str = Field(pattern=r"^[A-Ea-e]$")
    time_spent_ms: int | None = Field(default=None, ge=0)
    confidence: Literal["chutei", "duvida", "certeza", "defer"] | None = None


class BatchAttemptIn(BaseModel):
    attempts: list[BatchAttemptItem] = Field(max_length=500)


class ReviewIn(BaseModel):
    confidence: Literal["chutei", "duvida", "certeza"]


class PlannerConfigIn(BaseModel):
    exam_date: str | None = None
    start_date: str | None = None
    days_per_week: int = Field(default=6, ge=1, le=7)
    hours_per_day: int = Field(default=4, ge=1, le=24)
    target_score: float | None = Field(default=None, ge=0, le=100)


class PlannerStudyIn(BaseModel):
    studied: bool = False


class PlannerRevisionIn(BaseModel):
    type: Literal["rev24h", "rev7d", "rev30d"]
    checked: bool = False


class GeneratePlanIn(BaseModel):
    exam_date: str
    start_date: str | None = None
    hours_per_week: int = Field(default=20, ge=1, le=168)
    intensive: bool = False
