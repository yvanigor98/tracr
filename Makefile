.PHONY: help install dev-install up down logs test lint typecheck format migrate shell

help:
	@echo "Tracr — available commands:"
	@echo "  make install       Install production dependencies"
	@echo "  make dev-install   Install all dependencies including dev"
	@echo "  make up            Start all services via Docker Compose"
	@echo "  make down          Stop all services"
	@echo "  make logs          Tail logs from all services"
	@echo "  make test          Run test suite"
	@echo "  make lint          Run ruff linter"
	@echo "  make typecheck     Run mypy type checker"
	@echo "  make format        Auto-format code with ruff"
	@echo "  make migrate       Run Alembic migrations"
	@echo "  make shell         Open Python shell with app context"

install:
	uv sync

dev-install:
	uv sync --all-groups

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

test:
	uv run pytest --cov=tracr --cov-report=term-missing

lint:
	uv run ruff check .

typecheck:
	uv run mypy tracr/

format:
	uv run ruff format .
	uv run ruff check --fix .

migrate:
	uv run alembic upgrade head

shell:
	uv run python -c "import tracr; import IPython; IPython.embed()"
