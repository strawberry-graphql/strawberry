Release type: minor

Add first-class support for Pydantic v2+ models in Strawberry GraphQL.

This release introduces a new `strawberry.pydantic` module that allows you to directly
decorate Pydantic `BaseModel` classes to create GraphQL types, inputs, and interfaces
without requiring separate wrapper classes.

## Basic Usage

```python
import strawberry
from pydantic import BaseModel


@strawberry.pydantic.type
class User(BaseModel):
    name: str
    age: int


@strawberry.pydantic.input
class CreateUserInput(BaseModel):
    name: str
    age: int
```

## Features

- `@strawberry.pydantic.type` - Convert Pydantic models to GraphQL types
- `@strawberry.pydantic.input` - Convert Pydantic models to GraphQL input types
- `@strawberry.pydantic.interface` - Convert Pydantic models to GraphQL interfaces
- Automatic field extraction from Pydantic models
- Pydantic field descriptions preserved in GraphQL schema
- Pydantic field aliases used as GraphQL field names
- Support for `strawberry.Private` to exclude fields from schema
- Support for `strawberry.field()` with `Annotated` for directives, permissions, deprecation
- Generic Pydantic model support
- `strawberry.pydantic.Error` type for validation error handling in union return types

## Migration from Experimental

The experimental `strawberry.experimental.pydantic` integration is now deprecated.
See the documentation for migration guide.

---

## TODO: Improvements Needed Before/After Release

### Documentation Fixes
- [x] Remove or implement `from_pydantic()`/`to_pydantic()` methods mentioned in docs
- [x] Update test snapshots for Pydantic version (2.11 → 2.12) - made assertions version-agnostic

### Code Quality
- [x] Replace `typing._GenericAlias` private API usage - now uses `is_generic_alias` utility
- [x] Narrow exception handling in `schema_converter.py` - refactored to `_maybe_convert_validation_error`
- [x] Add computed field tests to verify `include_computed` works with `@computed_field`

### Future Pydantic v2 Features to Implement

#### High Priority
- [ ] Validation context - Pass `strawberry.Info` to Pydantic validators
- [ ] Honor `model_config` settings (`strict`, `extra='forbid'`, etc.)
- [ ] Expose `@field_validator` errors in a structured way

#### Medium Priority
- [ ] Discriminated unions - Use `__typename` as discriminator
- [ ] `@model_validator` support for cross-field validation
- [ ] Separate input/output aliases (`validation_alias` vs `serialization_alias`)
- [ ] Strict mode configuration per field/type

#### Low Priority
- [ ] `TypeAdapter` support for non-model types
- [ ] `RootModel` support for custom scalar-like types
- [ ] Custom serializers via `@model_serializer`
- [ ] JSON schema generation integration
- [ ] Functional validators (`BeforeValidator`, `AfterValidator`, etc.)
