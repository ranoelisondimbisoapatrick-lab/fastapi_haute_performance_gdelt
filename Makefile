.PHONY: up down logs api worker test lint

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

api:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

worker:
	poetry run python -m app.worker

test:
	poetry run pytest -q

lint:
	ruff check .
