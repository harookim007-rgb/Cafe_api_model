.PHONY: setup model run test lint up gpu down onnx

setup:
	pip install -r requirements-dev.txt

model:
	python scripts/train_sentiment.py

run:
	SEED_DEMO=1 uvicorn app.main:app --reload --port 8080

test:
	pytest -q

lint:
	ruff check .

up:
	cp -n .env.example .env || true
	docker compose up -d --build

onnx:
	python scripts/export_resnet18.py

gpu: onnx
	cp -n .env.example .env || true
	docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build

down:
	docker compose -f docker-compose.yml -f docker-compose.gpu.yml down
