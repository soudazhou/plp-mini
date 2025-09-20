# Repository Guidelines

## Project Structure & Module Organization
The FastAPI backend lives in `backend/src` with domain modules under `models/`, `repositories/`, `services/`, and `api/`; add new features by following that layering. Tests for the backend sit in `backend/tests` and mirror the module path; fixtures go in `backend/tests/conftest.py` when added. The Angular client is in `frontend/src` with feature folders under `frontend/src/app`; component-specific specs belong beside their implementation while broader scenarios go in `frontend/tests`. Infrastructure assets (Docker, IaC templates) live in `infrastructure/`, and product briefs/specs are under `specs/` and `prompts/`.

## Build, Test, and Development Commands
- `cd backend && pip install -r requirements.txt` — set up the FastAPI service dependencies inside your virtualenv.
- `cd backend && uvicorn src.main:app --reload` — run the API locally on port 8000.
- `cd backend && pytest` — execute the backend test suite with short tracebacks.
- `cd backend && python test_runner.py` — quick smoke check the import graph and API boot.
- `cd frontend && npm install` — install Angular workspace dependencies.
- `cd frontend && npm run start` — launch the dev server on http://localhost:4200.
- `./verify_implementation.sh` — run the end-to-end validation script used by maintainers.

## Coding Style & Naming Conventions
Backend Python uses Black (line length 88), Flake8, and full typing; keep modules snake_case and classes in PascalCase. Prefer dependency-injected services and keep Pydantic schemas in `api/` packages. TypeScript/HTML/SCSS files are formatted with Prettier (2-space indent) and linted via ESLint; use PascalCase for components/services and dash-case for selectors (`legalanalytics-dashboard`).

## Testing Guidelines
Write backend tests with Pytest, naming files `test_*.py` and functions `test_*` to align with `backend.pyproject`. When validating contract behaviour, add FastAPI client tests under `backend/tests/api/`. Frontend specs use Jasmine/Karma; colocate `*.spec.ts` with the component and keep coverage high by running `npm run test:coverage`. Root-level `test_endpoints.py` provides example HTTP checks—extend it when adding public routes.

## Commit & Pull Request Guidelines
History favors brief, action-led summaries (`initial implementation:`); follow that pattern in the imperative mood and reference issues when available. Group related changes into single commits, and include schema migrations or generated assets explicitly. Pull requests should link specs, outline testing performed, and attach screenshots or API examples for UI or contract changes. Mention config updates so reviewers can refresh `.env` or Docker settings.

## Security & Configuration Tips
Backend settings come from environment variables described in `backend/src/settings.py`; never commit real secrets—use `.env.example` style snippets in docs instead. `infrastructure/docker-compose.yml` provisions local Postgres/Redis/Elasticsearch; keep versions in sync with requirements before sharing compose changes. Review `environment.ts` files before enabling new frontend features to ensure flags default safely.
