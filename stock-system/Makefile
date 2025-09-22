.PHONY: dev run fmt lint test seed indexes
dev: ; python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
run: ; uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --loop uvloop --http h11
fmt: ; black . && ruff check --fix .
lint: ; ruff check . && mypy app
test: ; pytest -q
seed: ; python scripts/seed_demo_data.py
indexes: ; python scripts/create_indexes.py
