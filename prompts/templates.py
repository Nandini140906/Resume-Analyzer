"""
prompts/templates.py - Simplified AI prompt templates compatible with small models like Gemma.
All prompts merged into single user message (no system prompt separation).
"""

def resume_parser_prompt(raw_text: str) -> tuple[str, str]:
    system = ""
    user = f"""Extract information from this resume and return ONLY a JSON object. No explanation, no markdown, just JSON.

Resume:
{raw_text[:3000]}

Return this exact JSON (use null for missing fields, [] for missing lists, 0 for missing numbers):
{{"name": "Full Name", "email": "email@example.com", "phone": "phone number", "skills": ["skill1", "skill2"], "experience_years": 0, "education": ["Degree at School (Year)"], "companies": ["Company Name (dates)"], "certifications": ["cert1"], "summary": "brief summary"}}

Rules:
- experience_years: ONLY count paid jobs/internships at real companies. Students with no job = 0. Do NOT count college years.
- Return only the JSON object, nothing else."""
    return system, user


def job_analyzer_prompt(job_role: str, job_description: str) -> tuple[str, str]:
    system = ""
    user = f"""Analyze this job description and return ONLY a JSON object. No explanation, no markdown, just JSON.

Job Role: {job_role}
Job Description: {job_description[:2000]}

Return this exact JSON:
{{"required_skills": ["skill1", "skill2"], "preferred_skills": ["skill1"], "experience_level": "X-Y years", "keywords": ["keyword1", "keyword2"], "responsibilities": ["resp1"], "qualifications": ["qual1"]}}

Return only the JSON object, nothing else."""
    return system, user


def scoring_prompt(candidate_data: dict, job_profile: dict) -> tuple[str, str]:
    system = ""
    user = f"""Score this candidate for the job. Return ONLY a JSON object, nothing else.

JOB: {job_profile.get('job_role', '')}
Required Skills: {', '.join(job_profile.get('required_skills', []))}
Experience Needed: {job_profile.get('experience_level', '')}
Keywords: {', '.join(job_profile.get('keywords', [])[:10])}

CANDIDATE:
Skills: {', '.join(candidate_data.get('skills', []))}
Experience: {candidate_data.get('experience_years', 0)} years
Education: {'; '.join(candidate_data.get('education', []))}

Return this exact JSON:
{{"score": 7.5, "match_percentage": 75.0, "skill_match_score": 8.0, "experience_match_score": 7.0, "keyword_match_score": 7.5, "reasoning": "Brief explanation", "strengths": ["strength1", "strength2"], "weaknesses": ["weakness1"]}}

Rules:
- score: 1-10 float (10 = perfect match)
- match_percentage: 0-100 float
- Return only the JSON object, nothing else."""
    return system, user


def ats_gap_prompt(candidate_skills: list, job_keywords: list, raw_resume_text: str) -> tuple[str, str]:
    system = ""
    user = f"""Find ATS keyword gaps. Return ONLY a JSON object, nothing else.

Job Keywords Required: {', '.join(job_keywords[:20])}
Candidate Skills: {', '.join(candidate_skills[:20])}

Return this exact JSON:
{{"missing_keywords": ["kw1", "kw2"], "present_keywords": ["kw1"], "ats_score": 65.0, "suggestions": ["Add Docker to skills section", "Mention CI/CD in experience"]}}

Return only the JSON object, nothing else."""
    return system, user


def weakness_detector_prompt(raw_resume_text: str) -> tuple[str, str]:
    system = ""
    user = f"""Find weaknesses in this resume. Return ONLY a JSON object, nothing else.

Resume (first 1500 chars):
{raw_resume_text[:1500]}

Return this exact JSON:
{{"issues": [{{"category": "Missing Metrics", "description": "No quantifiable achievements", "severity": "high"}}], "missing_sections": ["Certifications"], "formatting_hints": ["Add LinkedIn URL"], "overall_quality": "fair"}}

overall_quality options: poor, fair, good, excellent
Return only the JSON object, nothing else."""
    return system, user


def cover_letter_prompt(candidate_data: dict, job_role: str, job_description: str) -> tuple[str, str]:
    system = ""
    user = f"""Write a short professional cover letter for this candidate. Plain text only, no JSON.

Candidate: {candidate_data.get('name', 'Candidate')}
Skills: {', '.join(candidate_data.get('skills', [])[:8])}
Experience: {candidate_data.get('experience_years', 0)} years
Job Role: {job_role}
Job Description: {job_description[:500]}

Write 3 paragraphs:
1. Opening with enthusiasm for the role
2. Highlight 2 relevant skills/experiences  
3. Call to action

Keep under 250 words. Start with "Dear Hiring Manager,"."""
    return system, user


def final_report_prompt(candidate_data: dict, analysis: dict, job_role: str) -> tuple[str, str]:
    system = ""
    user = f"""Write a recruiter assessment report in markdown. 

Candidate: {candidate_data.get('name', 'Unknown')}
Job: {job_role}
Score: {analysis.get('score', 0)}/10
Match: {analysis.get('match_percentage', 0)}%
Shortlisted: {'Yes' if analysis.get('shortlisted') else 'No'}
Strengths: {', '.join(analysis.get('strengths', []))}
Weaknesses: {', '.join(analysis.get('weaknesses', []))}

Write sections: Summary, Score Breakdown, Strengths, Weaknesses, Recommendation.
Keep it under 300 words."""
    return system, user