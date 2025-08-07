# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Testing
- `poetry run nox -s tests`: Run full test suite
- `poetry run nox -s "tests-3.12"`: Run tests with specific Python version
- `poetry run pytest tests/`: Run tests with pytest directly
- `poetry run pytest tests/path/to/test.py::test_function`: Run specific test

### Code Quality
- `poetry run ruff check`: Run linting (configured in pyproject.toml)
- `poetry run ruff format`: Format code
- `poetry run mypy strawberry/`: Type checking
- `poetry run pyright`: Alternative type checker

### Development
- `poetry install --with integrations`: Install dependencies
- `poetry run strawberry server app`: Run development server
- `poetry run strawberry export-schema`: Export GraphQL schema
- `poetry run strawberry codegen`: Generate TypeScript types

## Common Development Practices
- Always use poetry to run python tasks and tests
- Use `poetry run` prefix for all Python commands to ensure correct virtual environment

## Architecture Overview

Strawberry is a Python GraphQL library that uses a **decorator-based, code-first approach** built on Python's type system and dataclasses.

### Core Components

**Schema Layer** (`strawberry/schema/`):
- `schema.py`: Main Schema class for execution and validation
- `schema_converter.py`: Converts Strawberry types to GraphQL-core types
- `config.py`: Configuration management

**Type System** (`strawberry/types/`):
- `object_type.py`: Core decorators (`@type`, `@input`, `@interface`)
- `field.py`: Field definitions and `@field` decorator
- `enum.py`, `scalar.py`, `union.py`: GraphQL type implementations

**Extensions System** (`strawberry/extensions/`):
- `base_extension.py`: Base SchemaExtension class with lifecycle hooks
- `tracing/`: Built-in tracing (Apollo, DataDog, OpenTelemetry)
- Plugin ecosystem for caching, security, performance

**HTTP Layer** (`strawberry/http/`):
- Framework-agnostic HTTP handling
- Base classes for framework integrations
- GraphQL IDE integration

### Framework Integrations

Each framework integration (FastAPI, Django, Flask, etc.) inherits from base HTTP classes and implements:
- Request/response adaptation
- Context management
- WebSocket handling for subscriptions
- Framework-specific middleware

### Key Patterns

1. **Decorator-First Design**: Uses `@type`, `@field`, `@mutation` decorators
2. **Dataclass Foundation**: All GraphQL types are Python dataclasses
3. **Type Annotation Integration**: Automatic GraphQL type inference from Python types
4. **Lazy Type Resolution**: Handles forward references and circular dependencies
5. **Schema Converter Pattern**: Clean separation between Strawberry and GraphQL-core types

### Federation Support

Built-in Apollo Federation support via `strawberry.federation` with automatic `_service` and `_entities` field generation.

## Development Guidelines

### Type System
- Use Python type annotations for GraphQL type inference
- Leverage `@strawberry.type` for object types
- Use `@strawberry.field` for custom resolvers
- Support for generics and complex type relationships

### Extension Development
- Extend `SchemaExtension` for schema-level extensions
- Use `FieldExtension` for field-level middleware
- Hook into execution lifecycle: `on_operation`, `on_parse`, `on_validate`, `on_execute`

### Testing Patterns
- Tests are organized by module in `tests/`
- Use `strawberry.test.client` for GraphQL testing
- Integration tests for each framework in respective directories
- Snapshot testing for schema output

### Code Organization
- Main API surface in `strawberry/__init__.py`
- Experimental features in `strawberry/experimental/`
- Framework integrations in separate packages
- CLI commands in `strawberry/cli/`

## Important Files

- `strawberry/__init__.py`: Main API exports
- `strawberry/schema/schema.py`: Core schema execution
- `strawberry/types/object_type.py`: Core decorators
- `noxfile.py`: Test configuration
- `pyproject.toml`: Project configuration and dependencies
