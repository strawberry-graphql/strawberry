Release type: minor

Improve schema directives typing and printing after latest refactor.

- Support for printing schema directives for non-scalars (e.g. types) and null values.
- Also print the schema directive itself and any extra types defined in it
- Fix typing for apis expecting directives (e.g. `strawberry.field`, `strawberry.type`, etc)
  to expect an object instead of a `StrawberrySchemaDirective`, which is now an internal type.
