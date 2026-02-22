# AGENTS.md

Strawberry GraphQL

- Docs: https://strawberry.rocks/docs
- Repo: https://github.com/strawberry-graphql/strawberry

## Setup

```shell
$ poetry install --with integrations  # Install dependencies
$ poetry run pre-commit install       # Install git hooks (auto-runs checks on commit)
```

## Commands

- **Test:** `poetry run pytest`
- **Type check:** `poetry run mypy`
- **Lint:** `poetry run ruff check .`
- **Format:** `poetry run ruff format .`

## Code Style

- Ruff for linting/formatting (line length 88)
- mypy strict mode - all code must be fully typed
- Decorator-based schema: `@strawberry.type`, `@strawberry.field`, `@strawberry.mutation`
- Async-first design

## Structure

- `strawberry/` - Core library
  - `schema/` - Schema definition/execution
  - `types/` - GraphQL type definitions
  - `extensions/` - Built-in extensions
  - `django/`, `fastapi/`, `flask/`, etc. - Framework integrations
- `tests/` - pytest suite with integration markers (`django`, `fastapi`, `pydantic`, etc.)

## PR Requirements

- Include `RELEASE.md` file describing changes
- Release types: patch/minor/major
- Tests required for all code changes with full coverage
