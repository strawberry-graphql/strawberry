Release type: minor

This release adds support for an optional `offset: Int = null` pagination argument on Relay connections (`strawberry.relay.connection`), allowing offset-based pagination (`offset` + `first`) and cursor+offset slicing across `ListConnection` resolvers.
