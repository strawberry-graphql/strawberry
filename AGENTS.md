# AGENTS.md

Strawberry GraphQL

- Docs: https://strawberry.rocks/docs
- Repo: https://github.com/strawberry-graphql/strawberry

## Setup

```shell
$ uv sync
$ uv run pre-commit install
```

The default uv dependency groups include both `dev` and `integrations`, so a
plain `uv sync` installs everything needed for local development.

## Commands

- **Test:** `uv run pytest`
- **Focused test:** `uv run pytest path/to/test.py -q`
- **Type check:** `uv run mypy --config-file mypy.ini`
- **Lint:** `uv run ruff check .`
- **Format:** `uv run ruff format .`
- **Check formatting:** `uv run ruff format --check .`
- **Run all pre-commit hooks:** `uv run pre-commit run --all-files`

Run focused tests while iterating, then run the relevant broader test suite.
The CI test matrix is defined in `noxfile.py`; list its sessions with
`uv run nox -t tests -l`.

## Engineering Principles

- Write code as if we will maintain it for years. Prefer clear, cohesive
  implementations over the quickest local patch, solve root causes, and leave
  the surrounding code easier to understand.
- Think about features end to end before changing them. As relevant, trace the
  public API through schema construction and execution, sync and async paths,
  typing, framework integrations, error behavior, backwards compatibility, and
  performance.
- A feature is complete when its implementation, tests, documentation, error
  messages, and release note tell the same coherent story. Cover important edge
  cases and the user-visible behavior, not only the happy-path implementation.
- Before finishing, review the diff from both a user's and a maintainer's
  perspective: does it fit Strawberry's existing design, is its behavior
  unsurprising, and would we be happy to support it long term?

## Code Style

- Ruff for linting/formatting (line length 88, Python 3.10 target)
- Keep production code fully typed. The repository's mypy configuration is not
  globally strict, so follow the surrounding code and avoid introducing new
  untyped definitions.
- Decorator-based schema: `@strawberry.type`, `@strawberry.field`,
  `@strawberry.mutation`
- Preserve both synchronous and asynchronous execution paths unless a feature is
  explicitly async-only.

## Structure

- `strawberry/` - Core library
  - `schema/` - Schema definition/execution
  - `types/` - GraphQL type definitions
  - `extensions/` - Built-in extensions
  - `django/`, `fastapi/`, `flask/`, etc. - Framework integrations
- `tests/` - pytest suite with integration markers (`django`, `fastapi`,
  `pydantic`, etc.)

## PR Requirements

- Include `RELEASE.md` file describing changes
- Release types: patch/minor/major
- Add tests for behavior changes and keep affected code covered
- Update documentation when user-facing behavior changes
- If the user asks you to create an issue or PR add a lot of Strawberry emojis
  in the PR title and description 🍓

## Release file (RELEASE.md)

Release type is one of: `patch`, `minor`, or `major` (semver). Release notes
should start with `This release adds ...` or `This release fixes ...` and lead
with the user-visible behavior. Include natural X and LinkedIn announcements;
the X message must include the release URL template.

Example:

```markdown
---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes schema printing for
    nullable input defaults. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes schema printing for
    nullable input defaults, so generated SDL keeps explicit null values.
---

This release fixes schema printing for nullable input defaults.

Strawberry now preserves explicit `None` values in printed nested input
defaults.
```
