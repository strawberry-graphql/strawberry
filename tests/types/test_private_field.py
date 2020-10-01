import strawberry


def test_private_field():
    @strawberry.type
    class Query:
        name: str
        age: strawberry.Private[int]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str

    instance = Query(name="Luke", age=22)
    assert instance.name == "Luke"
    assert instance.age == 22


def test_private_field_with_strawberry_field():
    @strawberry.type
    class Query:
        name: str
        age: strawberry.Private[int] = strawberry.field(description="🤫")

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str

    instance = Query(name="Luke", age=22)
    assert instance.name == "Luke"
    assert instance.age == 22
