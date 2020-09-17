Release type: minor

* `UnionDefinition` has been renamed to `StrawberryUnion`
* `strawberry.union` now returns an instance of `StrawberryUnion` instead of a
dynamically generated class instance with a `_union_definition` attribute of
type `UnionDefinition`.
