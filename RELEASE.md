Release type: patch

Fix two `NameError` issues in schema-codegen output when types are referenced before they are defined.

First, forward references in field annotations (e.g. `foo: Foo` appearing before `Foo` is defined) are now handled by emitting `from __future__ import annotations` at the top of the generated file. Per PEP 563, this stores all annotations as strings instead of evaluating them at class definition time, so the referenced names don't need to exist yet.

Second, union definitions like `FooOrBar = Annotated[Foo | Bar, strawberry.union(...)]` are runtime expressions that `from __future__ import annotations` cannot defer. These are now correctly ordered by declaring union member types as dependencies, so unions are always emitted after their members.

Changes:
- Emit `from __future__ import annotations` in generated code to handle forward references in field annotations.
- Add member-type dependencies for union definitions so unions are emitted after their member types.
- Ensure the schema assignment is emitted last by giving it dependencies on all other definitions.
