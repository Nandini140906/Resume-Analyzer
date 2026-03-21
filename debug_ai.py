import asyncio
from backend.utils.ai_client import call_llm, extract_json_from_response

async def test():
    prompt = 'Score this candidate. Return ONLY JSON. Job: Python Developer. Required: Python, FastAPI, SQL. Candidate skills: Python, Django, SQL. Experience: 2 years. Return: {"score": 7.5, "match_percentage": 75.0, "skill_match_score": 8.0, "experience_match_score": 7.0, "keyword_match_score": 7.5, "reasoning": "Good Python match", "strengths": ["Strong Python", "Good SQL"], "weaknesses": ["Missing FastAPI"]}'
    result = await call_llm(prompt, system='', max_tokens=400)
    print('RAW:', result)
    parsed = extract_json_from_response(result)
    print('Score:', parsed.get('score'))
    print('Strengths:', parsed.get('strengths'))
    print('Weaknesses:', parsed.get('weaknesses'))

asyncio.run(test())
