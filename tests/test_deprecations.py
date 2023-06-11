import strawberry


def test_type_definition_is_aliased():
    @strawberry.type
    class A:
        a: int

    assert A.__strawberry_object__ is A._type_definition
