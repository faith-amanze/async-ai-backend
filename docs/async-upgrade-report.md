\# Async Upgrade Report



\## 1. Updated endpoint

I upgraded `POST /summarise` (`app/main.py`). It is `async def` because it awaits an async operation:



```python

@app.post("/summarise")

async def summarise(body: TextIn):

&#x20;   try:

&#x20;       summary = await ai.generate\_summary(body.text)

&#x20;   except Exception as exc:

&#x20;       raise friendly\_http\_error(exc)

&#x20;   return {"summary": summary}

```



`generate\_summary` is an async service function in `app/ai\_service.py`. It uses a fake AI call

(`asyncio.sleep`) because no API key is needed; `\_call\_model` can be replaced by a real async client.

Because I use `await`, the endpoint returns the final string, not a coroutine object

(checked by `test\_summarise\_returns\_result\_not\_coroutine`).



\## 2. Async flow

1\. Request arrives -> FastAPI runs `summarise` on the event loop.

2\. `await ai.generate\_summary(...)` -> `ask\_ai` -> `asyncio.wait\_for(\_call\_model(...), timeout)`.

3\. While the AI call waits (`asyncio.sleep` / network), the event loop is free to serve other requests.

4\. Result returns, or an exception is mapped by `friendly\_http\_error`:



| Failure | Exception | Response |

|---|---|---|

| AI too slow | `asyncio.TimeoutError` | 504 "The AI service took too long. Please try again." |

| Temporary provider failure | `AIServiceError` | 503 "temporarily unavailable. Please retry shortly." |

| Anything else | `Exception` | 500 "Something went wrong on our side." (details logged only) |



\## 3. Sequential vs concurrent

New endpoints generate three independent outputs (summary, quiz, flashcards):



\- `POST /study-pack-sequential`: awaits each call one after another -> total ≈ A + B + C.

\- `POST /study-pack`: `await asyncio.gather(summary, quiz, flashcards)` -> total ≈ max(A, B, C).



Measured by calling both endpoints in the FastAPI `/docs` page, with a simulated 1 s AI call per task:



| Version | Time |

|---|---|

| Sequential (`/study-pack-sequential`) | 3.0 s |

| Concurrent (`/study-pack`, `asyncio.gather`) | 1.0 s |



This is a \~3x speed-up, because the three calls are independent and spend their time waiting.



\## 4. Timeout test

`tests/test\_async.py::test\_timeout\_returns\_504` sets the fake AI delay to 1.0 s and the timeout to 0.2 s.

Expected result: HTTP 504 with the friendly message, returned after \~0.2 s instead of hanging.

Run with `pytest -q`.



I also tested temporary failure: `POST /summarise` with `{"text": "please fail"}` returned 503 with the

message "The AI service is temporarily unavailable. Please retry shortly."



\## 5. When async helps

Async helps when a request spends most of its time \*\*waiting on I/O\*\* (AI APIs, databases, HTTP calls):

the server can handle other requests meanwhile, and independent waits can overlap with `gather`.

It does \*\*not\*\* speed up CPU-heavy work (e.g. local model inference, big loops); that blocks the event loop

and needs threads/processes. Also, `async def` is only useful if the body actually awaits something async.

