"""
services/ranking_service.py - End-to-end resume analysis and ranking pipeline.
"""
import uuid
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.config import get_settings
from backend.logger import logger
from backend.models.db_models import Candidate, CandidateAnalysis, JobProfile
from backend.utils.file_parser import extract_text
from backend.services.ai_service import ai_service

settings = get_settings()


def build_local_report(candidate, analysis, job_role):
    """Build a complete markdown report from existing data — no AI needed."""
    name = candidate.name or candidate.file_name
    score = analysis.score or 0
    match = analysis.match_percentage or 0
    status = "SHORTLISTED" if analysis.shortlisted else "Not Shortlisted"
    strengths = "\n".join(f"- {s}" for s in (analysis.strengths or []) if s) or "- No data available"
    weaknesses = "\n".join(f"- {w}" for w in (analysis.weaknesses or []) if w) or "- No data available"
    missing_kw = ", ".join(analysis.ats_missing_keywords or []) or "None identified"
    suggestions = "\n".join(f"- {s}" for s in (analysis.ats_suggestions or []) if s) or "- No suggestions"
    skills = ", ".join(candidate.skills or []) or "Not extracted"
    education = "\n".join(f"- {e}" for e in (candidate.education or [])) or "- Not found"
    companies = "\n".join(f"- {c}" for c in (candidate.companies or [])) or "- No work experience listed"
    experience = candidate.experience_years or 0
    skill_score = analysis.skill_match_score or 0
    exp_score = analysis.experience_match_score or 0
    kw_score = analysis.keyword_match_score or 0
    reasoning = analysis.reasoning or "Analysis unavailable."

    return f"""# Candidate Assessment Report

## Candidate Summary
- **Name:** {name}
- **Email:** {candidate.email or "N/A"}
- **Phone:** {candidate.phone or "N/A"}
- **Experience:** {experience} years
- **Status:** {status}

## Role Applied For
{job_role}

## Score Breakdown
| Metric | Score |
|--------|-------|
| Overall Score | {score:.1f} / 10 |
| Match Percentage | {match:.1f}% |
| Skill Match | {skill_score:.1f} / 10 |
| Experience Match | {exp_score:.1f} / 10 |
| Keyword Match | {kw_score:.1f} / 10 |

## Skills
{skills}

## Education
{education}

## Work History
{companies}

## Strengths
{strengths}

## Areas for Improvement
{weaknesses}

## ATS Keyword Analysis
**Missing Keywords:** {missing_kw}

**Improvement Suggestions:**
{suggestions}

## AI Reasoning
{reasoning}

## Final Recommendation
{"This candidate meets the shortlist threshold and is recommended for further review." if analysis.shortlisted else "This candidate does not currently meet the minimum threshold for this role."}
"""


class RankingService:

    async def process_candidate(self, candidate, job_profile, db):
        logger.info(f"Processing candidate: {candidate.file_name}")

        if not candidate.raw_text:
            raw_text = extract_text(candidate.file_path, candidate.file_type)
            candidate.raw_text = raw_text
        else:
            raw_text = candidate.raw_text

        parsed = await ai_service.parse_resume(raw_text)
        candidate.name = parsed.get("name")
        candidate.email = parsed.get("email")
        candidate.phone = parsed.get("phone")
        candidate.skills = parsed.get("skills") or []
        candidate.experience_years = parsed.get("experience_years") or 0
        candidate.education = parsed.get("education") or []
        candidate.companies = parsed.get("companies") or []
        candidate.certifications = parsed.get("certifications") or []
        candidate.parsed_at = datetime.utcnow()

        job_profile_dict = {
            "job_role": job_profile.job_role,
            "required_skills": job_profile.required_skills or [],
            "preferred_skills": job_profile.preferred_skills or [],
            "experience_level": job_profile.experience_level or "",
            "keywords": job_profile.keywords or [],
        }

        scoring_task = ai_service.score_candidate(parsed, job_profile_dict)
        ats_task = ai_service.analyze_ats_gaps(
            candidate_skills=candidate.skills,
            job_keywords=job_profile.keywords or [],
            raw_resume_text=raw_text,
        )
        weakness_task = ai_service.detect_weaknesses(raw_text)

        scoring_result, ats_result, weakness_result = await asyncio.gather(
            scoring_task, ats_task, weakness_task
        )

        cover_letter = await ai_service.generate_cover_letter(
            candidate_data=parsed,
            job_role=job_profile.job_role,
            job_description=job_profile.job_description,
        )

        shortlisted = scoring_result["score"] >= settings.shortlist_score_threshold

        weakness_list = [
            issue.get("description", "") for issue in (weakness_result.get("issues") or [])
        ] + (scoring_result.get("weaknesses") or [])
        weakness_list = [w for w in weakness_list if w]

        analysis = CandidateAnalysis(
            id=str(uuid.uuid4()),
            candidate_id=candidate.id,
            score=scoring_result["score"],
            match_percentage=scoring_result["match_percentage"],
            skill_match_score=scoring_result.get("skill_match_score"),
            experience_match_score=scoring_result.get("experience_match_score"),
            keyword_match_score=scoring_result.get("keyword_match_score"),
            shortlisted=shortlisted,
            reasoning=scoring_result.get("reasoning", ""),
            strengths=scoring_result.get("strengths") or [],
            weaknesses=weakness_list,
            ats_missing_keywords=ats_result.get("missing_keywords") or [],
            ats_suggestions=ats_result.get("suggestions") or [],
            cover_letter=cover_letter,
        )

        db.add(analysis)
        logger.info(f"Candidate {candidate.name or candidate.file_name} scored {analysis.score}/10")
        return analysis

    async def rank_candidates(self, file_ids, job_profile, db):
        result = await db.execute(select(Candidate).where(Candidate.id.in_(file_ids)))
        candidates = result.scalars().all()

        if not candidates:
            raise ValueError("No candidates found for provided file IDs.")

        for c in candidates:
            c.job_profile_id = job_profile.id

        sem = asyncio.Semaphore(3)

        async def process_with_sem(c):
            async with sem:
                return await self.process_candidate(c, job_profile, db)

        analyses = await asyncio.gather(*[process_with_sem(c) for c in candidates])
        sorted_analyses = sorted(analyses, key=lambda a: a.score, reverse=True)
        for rank, analysis in enumerate(sorted_analyses, start=1):
            analysis.rank = rank

        candidate_map = {c.id: c for c in candidates}
        for analysis in sorted_analyses:
            candidate = candidate_map.get(analysis.candidate_id)
            if candidate:
                parsed_data = {
                    "name": candidate.name,
                    "email": candidate.email,
                    "skills": candidate.skills or [],
                    "experience_years": candidate.experience_years,
                    "education": candidate.education or [],
                }
                analysis_data = {
                    "score": analysis.score,
                    "match_percentage": analysis.match_percentage,
                    "shortlisted": analysis.shortlisted,
                    "strengths": analysis.strengths or [],
                    "weaknesses": analysis.weaknesses or [],
                    "ats_missing_keywords": analysis.ats_missing_keywords or [],
                }
                # Try AI report, fall back to local structured report
                ai_report = await ai_service.generate_report(
                    parsed_data, analysis_data, job_profile.job_role
                )
                if ai_report and "unavailable" not in ai_report.lower():
                    analysis.report = ai_report
                else:
                    analysis.report = build_local_report(candidate, analysis, job_profile.job_role)
                    logger.info(f"Used local report for {candidate.name or candidate.file_name}")

        await db.flush()
        logger.info(f"Ranked {len(sorted_analyses)} candidates. Shortlisted: {sum(1 for a in sorted_analyses if a.shortlisted)}")
        return sorted_analyses


ranking_service = RankingService()