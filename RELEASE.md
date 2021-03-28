Release type: minor

* `FieldDefinition` has been absorbed into `StrawberryField` and now no longer exists.

* `FieldDefinition.origin_name` and `FieldDefinition.name`  have been replaced with
  `StrawberryField.python_name` and `StrawberryField.graphql_name`. This should help
  alleviate some backend confusion about which should be used for certain situations.

* `strawberry.types.type_resolver.resolve_type` has been split into
  `resolve_type_argument` and `_resolve_type` (for arguments) until `StrawberryType` is
  implemented to combine them back together. This was done to reduce the scope of this
  PR and defer changing `ArgumentDefinition` (future `StrawberryArgument`) until a
  different PR.

> Note: The constructor signature for `StrawberryField` has `type_` as an argument
> instead of `type` as was the case for `FieldDefinition`. This is done to prevent
> shadowing of builtins.

> Note: `StrawberryField.name` still exists because of the way dataclass `Field`s
work, but is an alias for `StrawberryField.python_name`.
