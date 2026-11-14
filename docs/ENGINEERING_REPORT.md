# SALUS engineering report

## Delivered

- React and TypeScript workstation with responsive anatomy exploration, guided assessment, results, Recharts history, NASA Knowledge, and emergency access.
- FastAPI versioned endpoints, OpenAPI-generated frontend types, and SQLAlchemy/SQLite persistence.
- Eight imported profiles, 480 daily records, and 45 assessment records. CSV seeding is repeatable.
- Three guided pathway groups with optional readings and save/resume. Abdomen and musculoskeletal are research-only entry points.
- Pooled Isolation Forest with personal normalization and one-feature fallbacks. The 240-row holdout scored precision 0.783, recall 0.900, and F1 0.837 against synthetic scenario labels. See [model metrics](model-metrics.json).
- Offline TF-IDF retrieval over six cited NASA source sections. The sources are listed in the [NASA register](NASA_SOURCE_REGISTER.md).
- Deterministic crew follow-up and immediate urgent-warning escalation with source-linked prototype content.

## Verification

| Check | Result |
| --- | --- |
| TypeScript and Vite production build | Passed |
| Backend and API test suite | 8 passed |
| Browser: AST-02, Day 45 fatigue and save/resume | Passed. The model flagged the pattern and SALUS retrieved the NASA sleep section. |
| Browser: AST-03, Day 49 cardiovascular assessment | Passed. The result preserved entered pressures and retrieved the NASA cardiovascular section. |
| Browser: emergency warning-sign interruption | Passed. The next screen was Emergency Assistance. |
| API: emergency with both ML and retrieval disabled | Passed |
| Mobile touch and viewport regression test | The included Playwright script could not launch local Chromium in the execution environment. Mobile device QA remains open. |

## Remaining work

Clinical review and mission-approved procedures are unavailable. This local prototype neither contacts crew automatically nor issues treatments. It includes a curated retrieval corpus instead of automated ingestion, an SVG anatomy instead of 3D, and a training design rationale instead of a comparative model benchmark. The desktop browser confirmed keyboard activation of anatomy markers. Accessibility testing and physical mobile-device QA remain open.

## Repository

`frontend/src/` contains the workstation, anatomy SVG, and API client. `frontend/dist/` is prebuilt. `backend/app/` contains the API, data models, guided pathways, evidence, and ML. `backend/data/` holds the synthetic CSVs and NASA corpus. `backend/tests/` holds the API tests and optional browser smoke script. `docs/` contains the source registers, model card, OpenAPI schema, and demo instructions.

From `salus/backend`, install with `python -m pip install -r requirements.txt` and start with `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Full setup is in [README](../README.md).
