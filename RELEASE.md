Release type: patch

Fixed a bug where `strawberry.Maybe[T]` was incorrectly accepting `null` values when passed through variables

Previously, `Maybe[T]` returned a validation error for literal `null` values in GraphQL queries, but allowed `null` when passed via variables, resulting in `Some(None)` reaching the resolver instead of raising a validation error.

This fix ensures consistent validation behavior for `Maybe[T]` regardless of how the input is provided:

- `Maybe[T]` now returns a validation error for `null` in both literal queries and variables
- `Maybe[T | None]` continues to accept `null` values as expected
- Error message indicates to use `Maybe[T | None]` if null values are needed
