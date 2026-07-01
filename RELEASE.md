release type: minor
social_messages:
  x: >-
    {project_name} {version} removes the long-deprecated `info.field_nodes` property. Migrate to `info.selected_fields` before upgrading.
  linkedin: >-
    {project_name} {version} removes the `info.field_nodes` property that was deprecated since v0.73.1. Update your resolvers to use `info.selected_fields` instead.

This release removes the deprecated `info.field_nodes` property from `strawberry.Info` (deprecated since [0.73.1](https://github.com/strawberry-graphql/strawberry/releases/tag/0.73.1)).

### Migration guide

**Before (deprecated):**
```python
@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: strawberry.Info) -> str:
        field_nodes = info.field_nodes
        ...
```

**After:**
```python
@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: strawberry.Info) -> str:
        selected_fields = info.selected_fields
        ...
```
