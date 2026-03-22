"""
utils/ai_client.py - Unified AI client supporting OpenRouter and Groq.
Settings are read fresh on each call to avoid stale cached values.
"""
import json
import re
from typing import Optional
from backend.logger import logger


def get_s():
    """Always get fresh settings — avoids lru_cache stale reads."""
    from backend.config import get_settings
    get_settings.cache_clear()
    return get_settings()


async def _call_openrouter(prompt: str, system: str, max_tokens: int) -> str:
    from openai import AsyncOpenAI
    s = get_s()
    client = AsyncOpenAI(api_key=s.openrouter_api_key, base_url=s.openrouter_base_url)
    combined = f"{system}\n\n{prompt}" if system else prompt
    response = await client.chat.completions.create(
        model=s.openrouter_model,
        messages=[{"role": "user", "content": combined}],
        max_tokens=max_tokens,
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


async def _call_groq(prompt: str, system: str, max_tokens: int) -> str:
    from groq import AsyncGroq
    s = get_s()
    key = s.groq_api_key.strip()
    if not key:
        raise ValueError("GROQ_API_KEY is empty. Add it to your .env file.")
    client = AsyncGroq(api_key=key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = await client.chat.completions.create(
        model=s.groq_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


async def call_llm(
    prompt: str,
    system: str = "You are a helpful AI assistant.",
    max_tokens: int = 1500,
    provider: Optional[str] = None,
) -> str:
    s = get_s()
    active = (provider or s.ai_provider).lower()
    logger.debug(f"LLM call via provider={active}")
    try:
        if active == "groq":
            return await _call_groq(prompt, system, max_tokens)
        else:
            return await _call_openrouter(prompt, system, max_tokens)
    except Exception as e:
        logger.error(f"LLM call failed [{active}]: {e}")
        raise RuntimeError(f"AI provider error ({active}): {e}") from e


def extract_json_from_response(text: str) -> dict:
    if not text:
        return {}
    cleaned = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    logger.warning(f"Could not extract JSON: {text[:200]}")
    return {}