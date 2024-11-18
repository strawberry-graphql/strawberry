Release type: minor

In this release, we migrated the `graphql-transport-ws` types from data classes to typed dicts.
Using typed dicts enabled us to precisely model `null` versus `undefined` values, which are common in that protocol.
As a result, we could remove custom conversion methods handling these cases and simplify the codebase.
