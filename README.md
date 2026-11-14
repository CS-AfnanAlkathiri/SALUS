# SALUS
Astronaut Health & Self-Assessment Assistant · NASA Space Apps Challenge prototype

SALUS is a local, full-stack workstation. Select a body region, complete a guided assessment, log measurements, compare supported readings with a personal mission baseline, and read cited NASA research and crew follow-up guidance.

## Quick start

Requirements are Python 3.11+ and a terminal. The release archive includes the built frontend and the synthetic dataset.

```bash
cd salus/backend
python -m venv .venv
```

Activate with `source .venv/bin/activate` on macOS or Linux, or `.venv\Scripts\Activate.ps1` in Windows PowerShell. Then run:

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). First startup imports the included CSVs, trains and saves the synthetic model, and builds the local evidence index. Subsequent starts retain user-entered measurements and assessment sessions in `backend/state/`. Set `SALUS_STATE_DIR` to use a separate database and model cache. After dependency installation, core features work without internet access. Following citations opens the original web sources.

### Frontend development
Use Node.js 20.19+ or 22.12+. Run the backend from the preceding section. In a second terminal:
```bash
cd salus/frontend
npm ci
npm run dev
```
Vite forwards `/api` to the local backend. To rebuild the release frontend, run `npm run build` from that directory and restart the backend. `VITE_API_BASE_URL` overrides the API base when deploying the frontend separately. `SALUS_CORS` is a comma-separated list of allowed dev origins.

### Verify and maintain
From `salus/backend`:
```bash
python -m pytest -q
python -m app.ml
python -m app.evidence
```
Retraining is an explicit command over the supplied synthetic corpus. Restart the app to load regenerated artifacts. To regenerate frontend types, export the API schema with `python -c "from app.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > ../docs/openapi.json` from the backend, then run `npm run types` in the frontend. Interactive API docs are at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

For the optional browser smoke script, install Playwright with `python -m pip install playwright` and `python -m playwright install chromium`. Start a local SALUS instance with a throwaway state directory, then run `python tests/browser_demo.py`. The script creates test assessments.

## Documentation

- [Demo script](docs/DEMO_SCRIPT.md)
- [Engineering report](docs/ENGINEERING_REPORT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API contract](docs/API_CONTRACT.md)
- [Data dictionary](docs/DATA_DICTIONARY.md)
- [Model card](docs/ML_MODEL_CARD.md)
- [NASA source register](docs/NASA_SOURCE_REGISTER.md)
- [Guidance source register](docs/GUIDANCE_SOURCE_REGISTER.md)
- [Safety limitations](docs/SAFETY_LIMITATIONS.md)
