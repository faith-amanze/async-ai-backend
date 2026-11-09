import asyncio
import logging
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app import ai_service as ai

logger = logging.getLogger("app")
app = FastAPI(title="Async AI Backend")


class TextIn(BaseModel):
    text: str


def friendly_http_error(exc: Exception) -> HTTPException:
    """Turn internal failures into safe, readable API errors."""
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return HTTPException(504, "The AI service took too long. Please try again.")
    if isinstance(exc, ai.AIServiceError):
        return HTTPException(503, "The AI service is temporarily unavailable. Please retry shortly.")
    logger.exception("Unexpected error")  # full details go to logs, not the user
    return HTTPException(500, "Something went wrong on our side.")


@app.post("/summarise")
async def summarise(body: TextIn):
    # async def is justified: we await an async operation.
    try:
        summary = await ai.generate_summary(body.text)  # await -> final string, not a coroutine
    except Exception as exc:
        raise friendly_http_error(exc)
    return {"summary": summary}


@app.post("/study-pack")
async def study_pack(body: TextIn):
    """CONCURRENT: three independent calls run together via asyncio.gather."""
    start = time.perf_counter()
    try:
        summary, quiz, flashcards = await asyncio.gather(
            ai.generate_summary(body.text),
            ai.generate_quiz(body.text),
            ai.generate_flashcards(body.text),
        )
    except Exception as exc:
        raise friendly_http_error(exc)
    return {"summary": summary, "quiz": quiz, "flashcards": flashcards,
            "mode": "concurrent", "seconds": round(time.perf_counter() - start, 2)}


@app.post("/study-pack-sequential")
async def study_pack_sequential(body: TextIn):
    """SEQUENTIAL baseline for comparison: each call waits for the previous one."""
    start = time.perf_counter()
    try:
        summary = await ai.generate_summary(body.text)
        quiz = await ai.generate_quiz(body.text)
        flashcards = await ai.generate_flashcards(body.text)
    except Exception as exc:
        raise friendly_http_error(exc)
    return {"summary": summary, "quiz": quiz, "flashcards": flashcards,
            "mode": "sequential", "seconds": round(time.perf_counter() - start, 2)}
