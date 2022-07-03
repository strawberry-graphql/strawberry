Release type: minor

This release adds a link from generated GraphQLCore types to the Strawberry type
that generated them.

From a GraphQLCore type you can now access the Strawberry type by doing:

```python
strawberry_type: TypeDefinition = graphql_core_type.extensions[GraphQLCoreConverter.DEFINITION_BACKREF]
```
