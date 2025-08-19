Release type: minor

This release changes the `strawberry.Maybe` type to provide a more consistent and intuitive API for handling optional fields in GraphQL inputs.

**Breaking Change**: The `Maybe` type definition has been changed from `Union[Some[Union[T, None]], None]` to `Union[Some[T], None]`. This means:

- `Maybe[str]` now only accepts string values or absent fields (refuses explicit null)
- `Maybe[str | None]` accepts strings, null, or absent fields (maintains previous behavior)

This provides a cleaner API where `if field is not None` consistently means "field was provided" for all Maybe fields. A codemod is available to automatically migrate your code: `strawberry upgrade maybe-optional`

See the [breaking changes documentation](https://strawberry.rocks/docs/breaking-changes/0.279.0) for migration details.
