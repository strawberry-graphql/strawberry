import strawberry


def test_type_add_type_definition_with_fields():
    @strawberry.type
    class Query:
        name: str
        age: int

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].name is None
    assert definition.fields[0].origin_name == "name"
    assert definition.fields[0].type == str

    assert definition.fields[1].name is None
    assert definition.fields[1].origin_name == "age"
    assert definition.fields[1].type == int


def test_passing_custom_names_to_fields():
    @strawberry.type
    class Query:
        x: str = strawberry.field(name="name")
        y: int = strawberry.field(name="age")

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str

    assert definition.fields[1].name == "age"
    assert definition.fields[1].type == int


def test_passing_nothing_to_fields():
    @strawberry.type
    class Query:
        name: str = strawberry.field()
        age: int = strawberry.field()

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].name is None
    assert definition.fields[0].origin_name == "name"
    assert definition.fields[0].type == str

    assert definition.fields[1].name is None
    assert definition.fields[0].origin_name == "age"
    assert definition.fields[1].type == int
