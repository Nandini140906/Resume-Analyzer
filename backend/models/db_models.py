"""
models/db_models.py - SQLAlchemy ORM models for persistence.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, JSON, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class JobProfile(Base):
    """Stores extracted job requirements for a session."""
    __tablename__ = "job_profiles"

    id = Column(String(36), primary_key=True)          # UUID
    job_role = Column(String(256), nullable=False)
    job_description = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list)        # ["Python", "SQL"]
    preferred_skills = Column(JSON, default=list)
    experience_level = Column(String(64))               # "3-5 years"
    keywords = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    candidates = relationship("Candidate", back_populates="job_profile", cascade="all, delete-orphan")


class Candidate(Base):
    """Stores uploaded resume metadata and parsed data."""
    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True)           # UUID
    job_profile_id = Column(String(36), ForeignKey("job_profiles.id"), nullable=True)
    file_name = Column(String(256), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(16))                      # pdf | docx
    raw_text = Column(Text)
    name = Column(String(256))
    email = Column(String(256))
    phone = Column(String(64))
    skills = Column(JSON, default=list)
    experience_years = Column(Float)
    education = Column(JSON, default=list)
    companies = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    parsed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    job_profile = relationship("JobProfile", back_populates="candidates")
    analysis = relationship("CandidateAnalysis", back_populates="candidate", uselist=False, cascade="all, delete-orphan")


class CandidateAnalysis(Base):
    """Stores AI scoring and insights for a candidate against a job."""
    __tablename__ = "candidate_analyses"

    id = Column(String(36), primary_key=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id"), nullable=False)
    score = Column(Float)                               # 1-10
    match_percentage = Column(Float)
    skill_match_score = Column(Float)
    experience_match_score = Column(Float)
    keyword_match_score = Column(Float)
    rank = Column(Integer)
    shortlisted = Column(Boolean, default=False)
    reasoning = Column(Text)
    strengths = Column(JSON, default=list)
    weaknesses = Column(JSON, default=list)
    ats_missing_keywords = Column(JSON, default=list)
    ats_suggestions = Column(JSON, default=list)
    cover_letter = Column(Text)
    report = Column(Text)                               # Full markdown report
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="analysis")
