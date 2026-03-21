"""
services/ai_service.py - Orchestrates all AI-powered analysis tasks.
"""
from backend.utils.ai_client import call_llm, extract_json_from_response
from backend.logger import logger
from prompts.templates import (
    resume_parser_prompt,
    job_analyzer_prompt,
    scoring_prompt,
    ats_gap_prompt,
    weakness_detector_prompt,
    cover_letter_prompt,
    final_report_prompt,
)


class AIService:

    async def parse_resume(self, raw_text: str) -> dict:
        system, user = resume_parser_prompt(raw_text)
        try:
            response = await call_llm(user, system=system, max_tokens=800)
            result = extract_json_from_response(response)
            logger.info(f"Resume parsed -> name={result.get('name')}")
            return result
        except Exception as e:
            logger.error(f"Resume parsing failed: {e}")
            return {
                "name": None, "email": None, "phone": None,
                "skills": [], "experience_years": 0,
                "education": [], "companies": [],
                "certifications": [], "summary": ""
            }

    async def analyze_job(self, job_role: str, job_description: str) -> dict:
        system, user = job_analyzer_prompt(job_role, job_description)
        try:
            response = await call_llm(user, system=system, max_tokens=600)
            result = extract_json_from_response(response)
            logger.info(f"Job analyzed -> role={job_role}")
            return result
        except Exception as e:
            logger.error(f"Job analysis failed: {e}")
            return {
                "required_skills": [], "preferred_skills": [],
                "experience_level": "Not specified", "keywords": [],
                "responsibilities": [], "qualifications": []
            }

    async def score_candidate(self, candidate_data: dict, job_profile: dict) -> dict:
        system, user = scoring_prompt(candidate_data, job_profile)
        try:
            response = await call_llm(user, system=system, max_tokens=600)
            result = extract_json_from_response(response)
            result["score"] = max(1.0, min(10.0, float(result.get("score", 1.0))))
            result["match_percentage"] = max(0.0, min(100.0, float(result.get("match_percentage", 0.0))))
            logger.info(f"Scored {candidate_data.get('name')} = {result['score']}/10")
            return result
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            return {
                "score": 1.0, "match_percentage": 0.0,
                "skill_match_score": 1.0, "experience_match_score": 1.0,
                "keyword_match_score": 1.0,
                "reasoning": "Analysis unavailable.",
                "strengths": [], "weaknesses": ["Could not complete analysis."]
            }

    async def analyze_ats_gaps(self, candidate_skills, job_keywords, raw_resume_text) -> dict:
        system, user = ats_gap_prompt(candidate_skills, job_keywords, raw_resume_text)
        try:
            response = await call_llm(user, system=system, max_tokens=500)
            return extract_json_from_response(response)
        except Exception as e:
            logger.error(f"ATS analysis failed: {e}")
            return {"missing_keywords": [], "present_keywords": [], "ats_score": 0.0, "suggestions": []}

    async def detect_weaknesses(self, raw_resume_text: str) -> dict:
        system, user = weakness_detector_prompt(raw_resume_text)
        try:
            response = await call_llm(user, system=system, max_tokens=500)
            return extract_json_from_response(response)
        except Exception as e:
            logger.error(f"Weakness detection failed: {e}")
            return {"issues": [], "missing_sections": [], "formatting_hints": [], "overall_quality": "unknown"}

    async def generate_cover_letter(self, candidate_data, job_role, job_description) -> str:
        system, user = cover_letter_prompt(candidate_data, job_role, job_description)
        try:
            return await call_llm(user, system=system, max_tokens=600)
        except Exception as e:
            logger.error(f"Cover letter failed: {e}")
            return "Cover letter generation unavailable."

    async def generate_report(self, candidate_data, analysis, job_role) -> str:
        system, user = final_report_prompt(candidate_data, analysis, job_role)
        try:
            return await call_llm(user, system=system, max_tokens=800)
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return "Report generation unavailable."


ai_service = AIService()