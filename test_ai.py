import asyncio
from backend.utils.ai_client import call_llm, extract_json_from_response

async def test():
    prompt = 'Score this candidate for Python Developer role. Required skills: Python, FastAPI, SQL. Candidate has: Python, Django, SQL, 2 years experience. Return ONLY this JSON with no other text: {"score": 7.5, "match_percentage": 75.0, "skill_match_score": 8.0, "experience_match_score": 7.0, "keyword_match_score": 7.5, "reasoning": "Good Python match", "strengths": ["Python skills", "SQL knowledge"], "weaknesses": ["No FastAPI experience"]}'
    result = await call_llm(prompt, system='', max_tokens=400)
    print('Raw:', result[:300])
    parsed = extract_json_from_response(result)
    print('Score:', parsed.get('score'))
    print('Strengths:', parsed.get('strengths'))
    print('Weaknesses:', parsed.get('weaknesses'))

asyncio.run(test())
