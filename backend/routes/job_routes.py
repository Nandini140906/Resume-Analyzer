"""
routes/job_routes.py - POST /analyze_job endpoint.
Accepts job role + description, extracts requirements via AI, stores job profile.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.logger import logger
from backend.models.db_models import JobProfile
from backend.models.schemas import AnalyzeJobRequest, JobProfileResponse
from backend.services.ai_service import ai_service
from backend.utils.database import get_db

router = APIRouter(prefix="/api", tags=["Job Analysis"])


@router.post("/analyze_job", response_model=JobProfileResponse)
async def analyze_job(
    request: AnalyzeJobRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze a job description with AI, extract requirements,
    persist job profile, and return structured data.
    """
    logger.info(f"Analyzing job: {request.job_role}")

    # Run AI job analysis
    try:
        extracted = await ai_service.analyze_job(request.job_role, request.job_description)
    except Exception as e:
        logger.error(f"AI job analysis error: {e}")
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {str(e)}")

    # Persist
    job_profile = JobProfile(
        id=str(uuid.uuid4()),
        job_role=request.job_role,
        job_description=request.job_description,
        required_skills=extracted.get("required_skills") or [],
        preferred_skills=extracted.get("preferred_skills") or [],
        experience_level=extracted.get("experience_level") or "Not specified",
        keywords=extracted.get("keywords") or [],
        created_at=datetime.utcnow(),
    )
    db.add(job_profile)
    await db.flush()

    logger.info(f"Job profile created: {job_profile.id} | skills={len(job_profile.required_skills)}")

    return JobProfileResponse(
        job_profile_id=job_profile.id,
        job_role=job_profile.job_role,
        required_skills=job_profile.required_skills,
        preferred_skills=job_profile.preferred_skills,
        experience_level=job_profile.experience_level,
        keywords=job_profile.keywords,
        created_at=job_profile.created_at,
    )
