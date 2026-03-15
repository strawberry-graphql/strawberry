Release type: patch

Fix `TypeError: unhashable type: 'EnumAnnotation'` when using `Annotated` enums as resolver parameter types (e.g., `Annotated[Color, strawberry.enum()]`).
