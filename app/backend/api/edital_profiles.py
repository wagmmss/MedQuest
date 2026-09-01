"""Catálogo Local e Versionado de Perfis de Editais para Residência Médica.

Define pesos de grandes áreas, versões e status de validação curricular de forma
puramente local, hermética e determinística, sem dependência de serviços externos.
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


CANONICAL_AREAS = [
    "Clínica Médica",
    "Cirurgia",
    "Ginecologia e Obstetrícia",
    "Pediatria",
    "Medicina Preventiva",
]


class EditalProfile(BaseModel):
    institution_code: str
    institution_label: str
    version: str
    validity_period: str
    curation_source: str
    status: Literal["validated", "experimental"]
    weights: Dict[str, float] = Field(description="Pesos por grande área médica normalizados para soma 1.0")


def normalize_weights(raw_weights: Dict[str, float]) -> Dict[str, float]:
    """Valida e normaliza pesos de grandes áreas para somarem exatamente 1.0."""
    cleaned: Dict[str, float] = {}
    for area in CANONICAL_AREAS:
        val = raw_weights.get(area, 0.0)
        try:
            val_f = float(val)
            cleaned[area] = max(0.0, val_f)
        except (ValueError, TypeError):
            cleaned[area] = 0.0

    total = sum(cleaned.values())
    if total <= 0:
        # Fallback equitativo (20% para cada área canônica)
        equal_w = 1.0 / len(CANONICAL_AREAS)
        return {area: equal_w for area in CANONICAL_AREAS}

    return {area: round(w / total, 4) for area, w in cleaned.items()}


# Catálogo local provisório de editais. Os pesos uniformes abaixo preservam o
# contrato e permitem testar a experiência, mas não representam uma extração
# ou validação oficial dos editais. Só um perfil com fonte verificável e
# revisão clínica pode receber o status ``validated``.
EDITAL_PROFILES_REGISTRY: Dict[str, EditalProfile] = {
    "USP-SP": EditalProfile(
        institution_code="USP-SP",
        institution_label="USP - São Paulo",
        version="2025.1",
        validity_period="2025-2026",
        curation_source="Perfil local provisório MedQuest; requer validação documental antes de uso decisório.",
        status="experimental",
        weights=normalize_weights({
            "Clínica Médica": 0.20,
            "Cirurgia": 0.20,
            "Ginecologia e Obstetrícia": 0.20,
            "Pediatria": 0.20,
            "Medicina Preventiva": 0.20,
        }),
    ),
    "UNICAMP": EditalProfile(
        institution_code="UNICAMP",
        institution_label="Unicamp",
        version="2025.1",
        validity_period="2025-2026",
        curation_source="Perfil local provisório MedQuest; requer validação documental antes de uso decisório.",
        status="experimental",
        weights=normalize_weights({
            "Clínica Médica": 0.20,
            "Cirurgia": 0.20,
            "Ginecologia e Obstetrícia": 0.20,
            "Pediatria": 0.20,
            "Medicina Preventiva": 0.20,
        }),
    ),
    "ENARE": EditalProfile(
        institution_code="ENARE",
        institution_label="ENARE / Ebserh",
        version="2025.1",
        validity_period="2025-2026",
        curation_source="Perfil local provisório MedQuest; requer validação documental antes de uso decisório.",
        status="experimental",
        weights=normalize_weights({
            "Clínica Médica": 0.20,
            "Cirurgia": 0.20,
            "Ginecologia e Obstetrícia": 0.20,
            "Pediatria": 0.20,
            "Medicina Preventiva": 0.20,
        }),
    ),
    "SUS-SP": EditalProfile(
        institution_code="SUS-SP",
        institution_label="SUS-SP",
        version="2025.1",
        validity_period="2025-2026",
        curation_source="Perfil local provisório MedQuest; requer validação documental antes de uso decisório.",
        status="experimental",
        weights=normalize_weights({
            "Clínica Médica": 0.20,
            "Cirurgia": 0.20,
            "Ginecologia e Obstetrícia": 0.20,
            "Pediatria": 0.20,
            "Medicina Preventiva": 0.20,
        }),
    ),
    "UNIFESP": EditalProfile(
        institution_code="UNIFESP",
        institution_label="Unifesp / EPM",
        version="2025.1",
        validity_period="2025-2026",
        curation_source="Perfil local provisório MedQuest; requer validação documental antes de uso decisório.",
        status="experimental",
        weights=normalize_weights({
            "Clínica Médica": 0.20,
            "Cirurgia": 0.20,
            "Ginecologia e Obstetrícia": 0.20,
            "Pediatria": 0.20,
            "Medicina Preventiva": 0.20,
        }),
    ),
}


def get_edital_profile(institution_code: Optional[str]) -> EditalProfile:
    """Recupera o perfil de edital para a instituição ou constrói fallback experimental."""
    code = (institution_code or "").strip().upper()
    if code in EDITAL_PROFILES_REGISTRY:
        return EDITAL_PROFILES_REGISTRY[code]

    equal_w = 1.0 / len(CANONICAL_AREAS)
    return EditalProfile(
        institution_code=institution_code or "GERAL",
        institution_label=institution_code or "Banco Geral",
        version="custom.1",
        validity_period="2025-2026",
        curation_source="Perfil padrão experimental (pesos equitativos pelas 5 grandes áreas)",
        status="experimental",
        weights={area: equal_w for area in CANONICAL_AREAS},
    )
