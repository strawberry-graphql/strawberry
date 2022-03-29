Release type: minor

Add link from GraphQL types to Strawberry types

It is now straightforward to retrieve the strawberry definition that originated any GraphQL definition in the schema:

```python
strawberry_type: TypeDefinition = graphql_type.extensions[GraphQLCoreConverter.DEFINITION_BACKREF]
```
