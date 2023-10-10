Release type: patch

Update entity resolver exception handling to set the result to the original error instead of a `GraphQLError`, which obscured the original message and meta-fields.
There is no need to wrap the exception in a `GraphQLError` since the `graphql-core` library handles that for us in its
[execute code](https://github.com/graphql-python/graphql-core/blob/0c93b8452eed38d4f800c7e71cf6f3f3758cd1c6/src/graphql/execution/execute.py#L1372).
However, if the original it is a `TypeError`, it indicates improper use of resolver and may contain code-level error messages,
so it is replaced with a generic exception with a more client-friendly string: `"Unable to resolve reference for {EntityType}"`.
