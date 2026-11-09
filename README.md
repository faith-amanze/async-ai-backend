# Async AI Backend (FastAPI)

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload     # docs at http://127.0.0.1:8000/docs
pytest -q
```

Endpoints: `POST /summarise`, `POST /study-pack` (concurrent), `POST /study-pack-sequential`.
Body: `{"text": "your text"}`. See `docs/async-upgrade-report.md`.
