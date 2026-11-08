"""Data models for CV Optimizer."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CriterionScore(BaseModel):
    criterion_id: str
    name: str
    weight: float
    score: float
    max_score: float
    percentage: float
    status: str  # "Crítico", "Atenção", "Bom", "Excelente"
    details: List[str] = Field(default_factory=list)


class DiagnosisResult(BaseModel):
    overall_score: int
    criteria: List[CriterionScore]
    key_issues: List[str]
    positive_points: List[str]
    initial_recommendations: List[str]
    char_count: int
    word_count: int
    has_extractable_text: bool
    detected_sections: List[str] = Field(default_factory=list)


class ResumeContact(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""


class ResumeExperience(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    period: str = ""
    bullets: List[str] = Field(default_factory=list)


class ResumeEducation(BaseModel):
    degree: str = ""
    institution: str = ""
    period: str = ""
    details: str = ""


class ResumeStructured(BaseModel):
    contact: ResumeContact = Field(default_factory=ResumeContact)
    summary: str = ""
    experiences: List[ResumeExperience] = Field(default_factory=list)
    education: List[ResumeEducation] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    additional: List[str] = Field(default_factory=list)


class PendingRecommendation(BaseModel):
    id: str
    priority: str  # "alta", "media", "baixa"
    title: str
    problem: str
    why_matters: str
    what_to_do: str
    example: Optional[str] = None


class IssueResolutionStatus(BaseModel):
    issue: str
    status: str  # "resolvido", "parcialmente_resolvido", "nao_resolvido"
    explanation: str


class ComparisonResult(BaseModel):
    original_score: int
    optimized_score: int
    absolute_delta: int
    criteria_comparison: List[Dict[str, Any]]
    resolved_issues: List[IssueResolutionStatus]
    partially_resolved_issues: List[IssueResolutionStatus]
    unresolved_issues: List[IssueResolutionStatus]
    human_recommendations: List[PendingRecommendation]


class OptimizationStep(BaseModel):
    step_number: int
    title: str
    description: str
    status: str = "completed"  # "completed", "in_progress", "pending"


class PreservationCheck(BaseModel):
    is_valid: bool
    preserved_companies: List[str]
    preserved_dates: List[str]
    preserved_degrees: List[str]
    preserved_skills: List[str]
    hallucination_warnings: List[str]
    details: List[str]
