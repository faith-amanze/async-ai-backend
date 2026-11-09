# Async AI Backend (FastAPI)

A small FastAPI backend upgraded so slow AI calls are handled asynchronously, with timeouts, friendly
error handling, and concurrent execution using `asyncio.gather`.

The AI call is simulated with `asyncio.sleep`, so no API key is needed. Replace `_call_model` in
`app/ai_service.py` with a real async client to use a live model.

## What it demonstrates
- `async def` endpoint that awaits an async AI service function
- Timeout with `asyncio.wait_for` so requests never wait forever
- Friendly errors: 504 (timeout), 503 (temporary AI failure), 500 (unexpected)
- Three independent outputs (summary, quiz, flashcards) run concurrently with `asyncio.gather`
- A sequential version of the same endpoint to compare timings

## Endpoints
| Method | Path | Description |
|---|---|---|
| POST | `/summarise` | Async summary with timeout and error handling |
| POST | `/study-pack` | Summary + quiz + flashcards, **concurrent** (`asyncio.gather`) |
| POST | `/study-pack-sequential` | Same three outputs, **sequential**, for comparison |

Request body for all endpoints:

```json
{"text": "photosynthesis"}
```

`/study-pack` and `/study-pack-sequential` also return `mode` and `seconds` so you can compare speed.
Sending `{"text": "please fail"}` to `/summarise` triggers a simulated provider failure (503).

## Run it (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs to try the endpoints.

## Run the tests
```powershell
python -m pytest -q
```

## Project structure
```
app/ai_service.py   async AI service, timeout, custom error
app/main.py         endpoints and friendly error handling
tests/test_async.py tests for result, timeout, failure, concurrency
docs/async-upgrade-report.md   report: endpoint, async flow, timeout test, when async helps
```

## Report
See [docs/async-upgrade-report.md](docs/async-upgrade-report.md).
