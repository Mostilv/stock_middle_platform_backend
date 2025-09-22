#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/create_indexes.py
python scripts/seed_demo_data.py
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --loop uvloop --http h11
