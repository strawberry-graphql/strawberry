# Strawberry GraphQL - Deprecation Removal Tracking

This document tracks deprecated features being removed from Strawberry GraphQL.

## Removal Status

| Deprecation | Status | Commit/PR |
|-------------|--------|-----------|
| `is_unset()` function | Removed | aa8b88ed |
| `UNSET` import from `strawberry.arguments` | Removed | bb6e6b19 |
| `Extension` import alias | Removed | |
| `ExecutionContext.errors` property | Removed | |
| `channel_listen` method | Removed | |
| Test renames for channels | Removed | |
| `asserts_errors` parameter | Removed | |
| `types` parameter in `strawberry.union()` | Removed | |
| Pydantic `fields` parameter | Removed | |
| Sanic `json_encoder` parameter | Removed | |
| Sanic `json_dumps_params` parameter | Removed | |
| Sanic context dot notation | Removed | |
| `graphiql` parameter (10 files) | Already removed | |
| Type definition aliases | Pending | |
| `LazyType` class | Already removed | |
| `info.field_nodes` property | Already removed | |
| `strawberry server` CLI command | Already removed | |
| Scalar class wrapper pattern | Deferred (complex) | |
| Argument name matching | Removed | |
| Extension hooks | Deferred (complex) | |

---

## Completed Removals

### 1. `is_unset()` Function
**File:** `strawberry/types/unset.py`

**Old pattern:**
```python
from strawberry.types.unset import is_unset

if is_unset(value):
    ...
```

**New pattern:**
```python
from strawberry import UNSET

if value is UNSET:
    ...
```

---

### 2. `UNSET` Import from `strawberry.arguments`
**File:** `strawberry/types/arguments.py`

**Old pattern:**
```python
from strawberry.arguments import UNSET
```

**New pattern:**
```python
from strawberry import UNSET
```

---

### 3. `Extension` Import Alias
**File:** `strawberry/extensions/__init__.py`

**Old pattern:**
```python
from strawberry.extensions import Extension
```

**New pattern:**
```python
from strawberry.extensions import SchemaExtension
```

---

### 4. `ExecutionContext.errors` Property
**File:** `strawberry/types/execution.py`

**Old pattern:**
```python
context.errors
```

**New pattern:**
```python
context.pre_execution_errors
```

---

### 5. `channel_listen` Method
**File:** `strawberry/channels/handlers/base.py`

**Old pattern:**
```python
async for message in handler.channel_listen("channel", groups=["group"]):
    ...
```

**New pattern:**
```python
async with handler.listen_to_channel("channel", groups=["group"]) as listener:
    async for message in listener:
        ...
```

---

### 6. `asserts_errors` Parameter
**Files:** `strawberry/test/client.py`, `strawberry/aiohttp/test/client.py`

**Old pattern:**
```python
client.query(query, asserts_errors=False)
```

**New pattern:**
```python
client.query(query, assert_no_errors=False)
```

---

### 7. `types` Parameter in `strawberry.union()`
**File:** `strawberry/types/union.py`

**Old pattern:**
```python
MyUnion = strawberry.union("MyUnion", types=(TypeA, TypeB))
```

**New pattern:**
```python
from typing import Annotated

MyUnion = Annotated[TypeA | TypeB, strawberry.union("MyUnion")]
```

---

### 8. Pydantic `fields` Parameter
**Files:** `strawberry/experimental/pydantic/object_type.py`, `strawberry/experimental/pydantic/error_type.py`

**Old pattern:**
```python
@strawberry.experimental.pydantic.type(User, fields=["age", "name"])
class UserType:
    pass
```

**New pattern:**
```python
@strawberry.experimental.pydantic.type(User)
class UserType:
    age: strawberry.auto
    name: strawberry.auto
```

Or use `all_fields=True`:
```python
@strawberry.experimental.pydantic.type(User, all_fields=True)
class UserType:
    pass
```

---

### 9. Sanic Deprecated Parameters
**Files:** `strawberry/sanic/views.py`, `strawberry/sanic/context.py`

#### `json_encoder` and `json_dumps_params`
**Old pattern:**
```python
app.add_route(
    GraphQLView.as_view(
        schema=schema, json_encoder=MyEncoder, json_dumps_params={"indent": 2}
    )
)
```

**New pattern:**
```python
class MyGraphQLView(GraphQLView):
    def encode_json(self, data: object) -> str:
        return json.dumps(data, cls=MyEncoder, indent=2)
```

#### Context Dot Notation
**Old pattern:**
```python
context.request  # dot notation access
```

**New pattern:**
```python
context["request"]  # dict-style access
```

---

## Pending Removals

### 10. `graphiql` Parameter (10 files)
**Status:** Pending

**Files:**
- `strawberry/asgi/__init__.py`
- `strawberry/flask/views.py`
- `strawberry/fastapi/router.py`
- `strawberry/quart/views.py`
- `strawberry/sanic/views.py`
- `strawberry/chalice/views.py`
- `strawberry/django/views.py`
- `strawberry/aiohttp/views.py`
- `strawberry/channels/handlers/http_handler.py`
- `strawberry/litestar/controller.py`

**Old pattern:**
```python
GraphQLView(schema=schema, graphiql=True)
```

**New pattern:**
```python
GraphQLView(schema=schema, graphql_ide="graphiql")
# or
GraphQLView(schema=schema, graphql_ide=None)  # to disable
```

---

### 11. Type Definition Aliases
**Status:** Pending

**Files:**
- `strawberry/types/object_type.py` - `_type_definition`
- `strawberry/types/enum.py` - `_enum_definition`
- `strawberry/types/base.py` - `TypeDefinition` class
- `strawberry/types/enum.py` - `EnumDefinition` class

**Old pattern:**
```python
cls._type_definition
cls._enum_definition
from strawberry.types.base import TypeDefinition
```

**New pattern:**
```python
cls.__strawberry_definition__
from strawberry.types.base import StrawberryObjectDefinition
```

---

### 12. `LazyType` Class
**Status:** Pending
**File:** `strawberry/types/lazy_type.py`

**Old pattern:**
```python
from strawberry.lazy_type import LazyType

field: LazyType["MyType", "my_module"]
```

**New pattern:**
```python
from typing import Annotated
import strawberry

field: Annotated["MyType", strawberry.lazy("my_module")]
```

---

### 13. `info.field_nodes` Property
**Status:** Pending
**File:** `strawberry/types/info.py`

**Old pattern:**
```python
info.field_nodes
```

**New pattern:**
```python
info.selected_fields
```

---

### 14. `strawberry server` CLI Command
**Status:** Pending
**File:** `strawberry/cli/commands/server.py`

**Old pattern:**
```bash
strawberry server app:schema
```

**New pattern:**
```bash
strawberry dev app:schema
```

---

## Deferred Removals

### 15. Scalar Class Wrapper Pattern
**Status:** Deferred (too complex - requires extensive changes)
**File:** `strawberry/types/scalar.py`

**Why deferred:**
- `strawberry/federation/scalar.py` uses `_process_scalar` internally for federation-specific scalar handling
- `strawberry/schema_codegen/__init__.py` generates the deprecated pattern when converting GraphQL schemas to Python code
- 12+ test files use the deprecated pattern extensively
- Removing this would require updating federation scalar, codegen output, and many tests

**Old pattern:**
```python
MyScalar = strawberry.scalar(NewType("MyScalar", str), serialize=..., parse_value=...)


@strawberry.scalar(serialize=..., parse_value=...)
class MyClass: ...
```

**New pattern:**
```python
from strawberry.schema.config import StrawberryConfig

MyType = NewType("MyType", str)

schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(
        scalar_map={
            MyType: strawberry.scalar(name="MyType", serialize=..., parse_value=...)
        }
    ),
)
```

---

### 16. Argument Name Matching
**Status:** Removed
**File:** `strawberry/types/fields/resolver.py`

Reserved argument names (`self`, `root`, `info`, `value`) were previously matched by name as a fallback when type annotation wasn't found. This has been removed - arguments must now be properly annotated.

**Old pattern:**
```python
@strawberry.field
def my_field(self, info) -> str:  # 'info' matched by name only
    return info.field_name
```

**New pattern:**
```python
@strawberry.field
def my_field(self, info: strawberry.Info) -> str:  # proper type annotation required
    return info.field_name
```

---

### 17. Extension Hooks
**Status:** Deferred (complex, involves extension lifecycle)
**File:** `strawberry/extensions/context.py`

Deprecated extension hook methods.

---

## Deprecation Patterns Used in Codebase

1. **`warnings.warn()` with `DeprecationWarning`** - Runtime warnings
2. **Custom `DeprecatedDescriptor`** in `strawberry/utils/deprecations.py` - Attribute aliasing
3. **`@deprecated` decorator** from `typing_extensions` - Type-level deprecations
4. **Module-level `__getattr__`** - For deprecated imports
5. **`DEPRECATED_NAMES` dictionaries** - Centralized deprecation messages

---

## Verification Commands

```bash
# Linting
uv run ruff check <file>

# Type checking
uv run mypy <file> --ignore-missing-imports

# Run tests
uv run pytest <test_file> -v
```
