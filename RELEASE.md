Release type: patch

Restore minimal mypy plugin for pydantic integration types (`__init__`, `to_pydantic()`, `from_pydantic()`). Add support for `Annotated` pattern with enums (e.g. `Annotated[MyEnum, strawberry.enum(description="...")]`) as a type-safe alternative to variable assignment.
