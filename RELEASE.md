Release type: patch

Update type annotations for `Response.data` and `Response.extensions` in the test client to `Any`, instead of `JsonValue`, to allow nested subscript access in test assertions without type failures.
