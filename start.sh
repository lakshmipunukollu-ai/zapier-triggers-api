#!/bin/bash
pip install -r requirements.txt --quiet
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
