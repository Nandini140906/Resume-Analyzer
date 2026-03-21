"""
routes/ranking_routes.py - POST /rank_candidates endpoint.
Triggers the full AI analysis + ranking pipeline for a set of candidates.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.config import get_settings
from backend.logger import logger
from backend.models.db_models import JobProfile, Candidate, CandidateAnalysis
from backend.models.schemas import (
    RankCandidatesRequest, RankCandidatesResponse, CandidateSummary,
    CandidateDetailResponse,
)
from backend.services.ranking_service import ranking_service
from backend.utils.database import get_db

router = APIRouter(prefix="/api", tags=["Ranking"])
settings = get_settings()


@router.post("/rank_candidates", response_model=RankCandidatesResponse)
async def rank_candidates(
    request: RankCandidatesRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Run the full AI pipeline (parse → score → ATS → report) for all
    submitted file IDs against the given job profile. Returns ranked results.
    """
    # Validate job profile exists
    job_result = await db.execute(
        select(JobProfile).where(JobProfile.id == request.job_profile_id)
    )
    job_profile = job_result.scalar_one_or_none()
    if not job_profile:
        raise HTTPException(status_code=404, detail="Job profile not found.")

    if not request.file_ids:
        raise HTTPException(status_code=400, detail="No file IDs provided.")

    # Run ranking pipeline
    try:
        analyses = await ranking_service.rank_candidates(
            file_ids=request.file_ids,
            job_profile=job_profile,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ranking pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Fetch candidates for response assembly
    cand_result = await db.execute(
        select(Candidate).where(Candidate.id.in_(request.file_ids))
    )
    candidates = {c.id: c for c in cand_result.scalars().all()}

    summaries: list[CandidateSummary] = []
    for analysis in analyses:
        cand = candidates.get(analysis.candidate_id)
        if not cand:
            continue
        summaries.append(CandidateSummary(
            candidate_id=cand.id,
            file_name=cand.file_name,
            name=cand.name,
            email=cand.email,
            skills=cand.skills or [],
            experience_years=cand.experience_years,
            score=analysis.score,
            match_percentage=analysis.match_percentage,
            rank=analysis.rank,
            shortlisted=analysis.shortlisted,
            reasoning=analysis.reasoning or "",
            strengths=analysis.strengths or [],
            weaknesses=analysis.weaknesses or [],
            ats_missing_keywords=analysis.ats_missing_keywords or [],
        ))

    summaries.sort(key=lambda s: s.rank)

    return RankCandidatesResponse(
        job_profile_id=request.job_profile_id,
        total_candidates=len(summaries),
        shortlisted_count=sum(1 for s in summaries if s.shortlisted),
        candidates=summaries,
    )


@router.get("/candidate/{candidate_id}", response_model=CandidateDetailResponse)
async def get_candidate_detail(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full details for a single analyzed candidate."""
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    analysis_result = await db.execute(
        select(CandidateAnalysis).where(CandidateAnalysis.candidate_id == candidate_id)
    )
    analysis = analysis_result.scalars().first()

    return CandidateDetailResponse(
        candidate_id=candidate.id,
        file_name=candidate.file_name,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        skills=candidate.skills or [],
        experience_years=candidate.experience_years,
        education=candidate.education or [],
        companies=candidate.companies or [],
        certifications=candidate.certifications or [],
        score=analysis.score if analysis else None,
        match_percentage=analysis.match_percentage if analysis else None,
        rank=analysis.rank if analysis else None,
        shortlisted=analysis.shortlisted if analysis else None,
        reasoning=analysis.reasoning if analysis else None,
        strengths=analysis.strengths if analysis else None,
        weaknesses=analysis.weaknesses if analysis else None,
        ats_missing_keywords=analysis.ats_missing_keywords if analysis else None,
        ats_suggestions=analysis.ats_suggestions if analysis else None,
        cover_letter=analysis.cover_letter if analysis else None,
        report=analysis.report if analysis else None,
    )


@router.get("/candidate/{candidate_id}/report_pdf")
async def download_report_pdf(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Generate and download a professional PDF report for a candidate."""
    from fastapi.responses import Response
    from backend.utils.pdf_generator import generate_report_pdf

    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    analysis_result = await db.execute(
        select(CandidateAnalysis).where(CandidateAnalysis.candidate_id == candidate_id)
    )
    analysis = analysis_result.scalars().first()

    candidate_data = {
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "skills": candidate.skills or [],
        "experience_years": candidate.experience_years,
        "education": candidate.education or [],
        "companies": candidate.companies or [],
    }

    analysis_data = {
        "score": analysis.score if analysis else 0,
        "match_percentage": analysis.match_percentage if analysis else 0,
        "skill_match_score": analysis.skill_match_score if analysis else 0,
        "experience_match_score": analysis.experience_match_score if analysis else 0,
        "keyword_match_score": analysis.keyword_match_score if analysis else 0,
        "shortlisted": analysis.shortlisted if analysis else False,
        "reasoning": analysis.reasoning if analysis else "",
        "strengths": analysis.strengths if analysis else [],
        "weaknesses": analysis.weaknesses if analysis else [],
        "ats_missing_keywords": analysis.ats_missing_keywords if analysis else [],
        "ats_suggestions": analysis.ats_suggestions if analysis else [],
        "rank": analysis.rank if analysis else None,
    }

    # Get job role
    job_role = "Unknown Role"
    if candidate.job_profile_id:
        from backend.models.db_models import JobProfile
        jp_result = await db.execute(
            select(JobProfile).where(JobProfile.id == candidate.job_profile_id)
        )
        jp = jp_result.scalar_one_or_none()
        if jp:
            job_role = jp.job_role

    pdf_bytes = generate_report_pdf(candidate_data, analysis_data, job_role)
    safe_name = (candidate.name or "candidate").replace(" ", "_")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="report_{safe_name}.pdf"'
        },
    )