Release type: patch

This update relaxes type annotations for `Response.data` and `Response.extensions` from `dict[str, JsonValue]` to `dict[str, JsonValue]` in the test client, making assertions in tests easier to write.
