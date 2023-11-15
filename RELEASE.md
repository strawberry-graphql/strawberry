Release type: minor

Starting with this release, any error raised from within schema
extensions will abort the operation and is returned to the client.

This corresponds to the way we already handle field extension errors
and resolver errors.

This is particular useful for schema extensions performing checks early
in the request lifecycle, for example:

```python
class MaxQueryLengthExtension(SchemaExtension):
    MAX_QUERY_LENGTH = 8192

    async def on_operation(self):
        if len(self.execution_context.query) > self.MAX_QUERY_LENGTH:
            raise StrawberryGraphQLError(message="Query too large")
        yield
```
