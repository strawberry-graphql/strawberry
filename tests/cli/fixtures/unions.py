import strawberry

# create a few types and then a union type


@strawberry.type
class Foo:
    a: str


@strawberry.type
class Bar:
    b: str


@strawberry.type
class Baz:
    c: str


@strawberry.type
class Qux:
    d: str


# this is the union type

Union1 = strawberry.union(name="Union1", types=(Foo, Bar, Baz, Qux))
Union2 = strawberry.union(name="Union2", types=(Baz, Qux))
