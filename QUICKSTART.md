# LegalAnalytics Mini Quickstart

Quick reference for verifying the backend with the standalone endpoint script.

## 1. Activate the virtual environment

```bash
cd /Users/wenxuan.zhou/PLP/plpmin/plp-mini
source .venv/bin/activate
```

> Tip: if you prefer not to activate the venv globally, prefix commands with
> `./.venv/bin/python` instead of `python`.

## 2. Start Postgres

```bash
docker compose -f infrastructure/docker-compose.yml up -d postgres
docker compose -f infrastructure/docker-compose.yml ps   # wait for "Up ... (healthy)"
```

## 3. Seed the database (testing profile)

```bash
cd backend
export DATABASE_URL=postgresql+psycopg2://dev:dev123@127.0.0.1:5432/legalanalytics
python scripts/seed_data.py --env testing --clear
```

## 4. Launch the API

```bash
export PYTHONPATH=$(pwd)/src
uvicorn src.main:app --host 127.0.0.1 --port 8000 --log-level info
```

Leave this process running while you test.

## 5. Run endpoint smoke tests (new terminal)

```bash
cd /Users/wenxuan.zhou/PLP/plpmin/plp-mini
source .venv/bin/activate
export PYTHONPATH=$(pwd)/backend/src
python test_endpoints.py
```

## 6. Cleanup

- Stop the API server (`Ctrl+C` in its terminal)
- `docker compose -f infrastructure/docker-compose.yml stop postgres`

## Troubleshooting

- **Port 8000 in use**: `lsof -ti tcp:8000 | xargs kill -9`
- **`python` command not found**: ensure the virtual environment is active or use
  `./.venv/bin/python`.
- **Seeder cannot connect to Postgres**: confirm the container is running
  (`docker compose ... ps`) before executing the seed script.

