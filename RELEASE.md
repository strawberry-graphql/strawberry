Release type: minor

Add a [pre-commit](https://pre-commit.com/) hook to prevent redundant `@dataclass` decorators on Strawberry types.

Since Strawberry types (`@strawberry.type`, `@strawberry.input`, `@strawberry.interface`) already provide dataclass functionality, decorating them with `@dataclass` is redundant. This hook detects and prevents this pattern, helping maintain cleaner code.

To use the hook, add it to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/strawberry-graphql/strawberry
    rev: <version>
    hooks:
      - id: no-redundant-dataclasses
```
