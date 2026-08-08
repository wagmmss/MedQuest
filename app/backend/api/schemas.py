"""Validação de entrada com Pydantic."""
from typing import Optional, Literal

from pydantic import BaseModel, Field, ValidationError

__all__ = ["AttemptIn", "BatchAttemptItem", "BatchAttemptIn", "PlannerConfigIn", "PlannerStudyIn", "PlannerRevisionIn",
           "GeneratePlanIn", "ValidationError"]


class AttemptIn(BaseModel):
    selected_letter: str = Field(pattern=r"^[A-Ea-e]$")
    time_spent_ms: Optional[int] = Field(default=None, ge=0)
    confidence: Optional[Literal["chutei", "duvida", "certeza"]] = None


class BatchAttemptItem(BaseModel):
    question_id: int
    selected_letter: str = Field(pattern=r"^[A-Ea-e]$")
    time_spent_ms: Optional[int] = Field(default=None, ge=0)
    confidence: Optional[Literal["chutei", "duvida", "certeza"]] = None


class BatchAttemptIn(BaseModel):
    attempts: list[BatchAttemptItem]


class PlannerConfigIn(BaseModel):
    exam_date: Optional[str] = None
    start_date: Optional[str] = None
    days_per_week: int = Field(default=6, ge=1, le=7)
    hours_per_day: int = Field(default=4, ge=1, le=24)


class PlannerStudyIn(BaseModel):
    studied: bool = False


class PlannerRevisionIn(BaseModel):
    type: Literal["rev24h", "rev7d", "rev30d"]
    checked: bool = False


class GeneratePlanIn(BaseModel):
    exam_date: str
    start_date: Optional[str] = None
    hours_per_week: int = Field(default=20, ge=1, le=168)
    intensive: bool = False
