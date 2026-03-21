"""
models/schemas.py - Pydantic v2 schemas for API request/response validation.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─── Shared / Base ────────────────────────────────────────────────────────────

class SuccessResponse(BaseModel):
    success: bool = True
    message: str = "OK"


# ─── Upload Resume ─────────────────────────────────────────────────────────────

class UploadedFile(BaseModel):
    file_id: str
    file_name: str
    file_type: str


class UploadResumeResponse(BaseModel):
    uploaded: list[UploadedFile]
    total: int


# ─── Job Profile ───────────────────────────────────────────────────────────────

class AnalyzeJobRequest(BaseModel):
    job_role: str = Field(..., min_length=2, max_length=256)
    job_description: str = Field(..., min_length=20)


class JobProfileResponse(BaseModel):
    job_profile_id: str
    job_role: str
    required_skills: list[str]
    preferred_skills: list[str]
    experience_level: str
    keywords: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Rank Candidates ───────────────────────────────────────────────────────────

class RankCandidatesRequest(BaseModel):
    file_ids: list[str]
    job_profile_id: str


class CandidateSummary(BaseModel):
    candidate_id: str
    file_name: str
    name: Optional[str] = None
    email: Optional[str] = None
    skills: list[str] = []
    experience_years: Optional[float] = None
    score: float
    match_percentage: float
    rank: int
    shortlisted: bool
    reasoning: str
    strengths: list[str] = []
    weaknesses: list[str] = []
    ats_missing_keywords: list[str] = []

    model_config = {"from_attributes": True}


class RankCandidatesResponse(BaseModel):
    job_profile_id: str
    total_candidates: int
    shortlisted_count: int
    candidates: list[CandidateSummary]


# ─── Export ────────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    job_profile_id: str
    format: str = Field(default="csv")


# ─── Candidate Detail ──────────────────────────────────────────────────────────

class CandidateDetailResponse(BaseModel):
    candidate_id: str
    file_name: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: list[str] = []
    experience_years: Optional[float] = None
    education: list[str] = []
    companies: list[str] = []
    certifications: list[str] = []
    score: Optional[float] = None
    match_percentage: Optional[float] = None
    rank: Optional[int] = None
    shortlisted: Optional[bool] = None
    reasoning: Optional[str] = None
    strengths: Optional[list[str]] = None
    weaknesses: Optional[list[str]] = None
    ats_missing_keywords: Optional[list[str]] = None
    ats_suggestions: Optional[list[str]] = None
    cover_letter: Optional[str] = None
    report: Optional[str] = None

    model_config = {"from_attributes": True}
