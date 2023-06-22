Release type: minor

This release gives codegen clients the ability to inquire about the `__typename`
of a `GraphQLObjectType`.  This information can be used to automatically select
the proper type to hydrate when working with a union type in the response.
