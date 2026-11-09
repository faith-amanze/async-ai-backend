"""Async AI service layer (fake AI client using asyncio.sleep).

Swap `_call_model` for a real async client (e.g. anthropic.AsyncAnthropic)
and the rest of the app does not change.
"""
import asyncio


class AIServiceError(Exception):
    """Temporary failure from the AI provider (rate limit, 5xx, network)."""


class Settings:
    ai_delay: float = 1.0     # simulated latency of one AI call (seconds)
    ai_timeout: float = 3.0   # max time we are willing to wait (seconds)


settings = Settings()


async def _call_model(prompt: str) -> str:
    """Fake async AI call. Non-blocking: asyncio.sleep yields to the event loop."""
    await asyncio.sleep(settings.ai_delay)
    if "fail" in prompt.lower():          # deterministic fake outage for tests
        raise AIServiceError("provider returned 503")
    return f"[AI result for: {prompt[:40]}]"


async def ask_ai(prompt: str) -> str:
    """Call the model but never wait longer than settings.ai_timeout."""
    return await asyncio.wait_for(_call_model(prompt), timeout=settings.ai_timeout)


async def generate_summary(text: str) -> str:
    return await ask_ai(f"Summarise: {text}")


async def generate_quiz(text: str) -> list[str]:
    result = await ask_ai(f"Write a quiz on: {text}")
    return [f"Q1 {result}", f"Q2 {result}", f"Q3 {result}"]


async def generate_flashcards(text: str) -> list[dict]:
    result = await ask_ai(f"Make flashcards for: {text}")
    return [{"front": "Term 1", "back": result}, {"front": "Term 2", "back": result}]
