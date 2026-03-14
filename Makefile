.PHONY: dev test seed build install clean

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 3004

test:
	python -m pytest tests/ -v --tb=short

seed:
	python seed.py

build:
	pip install -r requirements.txt
	cd dashboard && npm install && npm run build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf dashboard/dist dashboard/node_modules
