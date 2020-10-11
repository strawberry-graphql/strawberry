Release type: patch

Add `schema.introspect()` method to return introspection result of the schema.
This might be useful for tools like `apollo codegen` or `graphql-voyager` which
expect a full json representation of the schema
