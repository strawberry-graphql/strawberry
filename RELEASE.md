Release type: patch

Fix `UnallowedReturnTypeForUnion` when using a generic type with a union
TypeVar (e.g. `Collection[A | B]`) inside an outer union
(`Collection[A | B] | Error`).
