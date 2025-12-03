Release type: patch

Fixed a bug in the codegen where Relay Node's `id` field was incorrectly generated as `_id` in the output code.

The codegen now correctly respects the explicit `graphql_name` set via the `@field(name="id")` decorator, ensuring that the generated code uses `id` instead of the Python method name `_id`.
