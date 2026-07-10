.PHONY: install lint typecheck test run migrate makemigration downgrade

install:
	uv sync

lint:
	uv run ruff check

typecheck:
	uv run mypy src

test:
	uv run pytest

run:
	uv run uvicorn app.main:app --reload

migrate:
	uv run alembic upgrade head

# Autogenerate a migration, e.g. `make makemigration name="add patients"`.
# Always review the generated file by hand — renames autogenerate as drop+add.
makemigration:
	uv run alembic revision --autogenerate -m "$(name)"

downgrade:
	uv run alembic downgrade -1
