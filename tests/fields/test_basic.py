import strawberry


def test_type_add_type_definition_with_fields():
    @strawberry.type
    class Query:
        name: str
        age: int

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type == str

    assert definition.fields[1].python_name == "age"
    assert definition.fields[1].graphql_name is None
    assert definition.fields[1].type == int


def test_passing_custom_names_to_fields():
    @strawberry.type
    class Query:
        x: str = strawberry.field(name="name")
        y: int = strawberry.field(name="age")

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].python_name == "x"
    assert definition.fields[0].graphql_name == "name"
    assert definition.fields[0].type == str

    assert definition.fields[1].python_name == "y"
    assert definition.fields[1].graphql_name == "age"
    assert definition.fields[1].type == int


def test_passing_nothing_to_fields():
    @strawberry.type
    class Query:
        name: str = strawberry.field()
        age: int = strawberry.field()

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type == str

    assert definition.fields[1].python_name == "age"
    assert definition.fields[1].graphql_name is None
    assert definition.fields[1].type == int


def test_can_use_types_directly():
    @strawberry.type
    class User:
        username: str

        @strawberry.field
        def email(self) -> str:
            return self.username + "@somesite.com"

    user = User(username="abc")
    assert user.username == "abc"
    assert user.email() == "abc@somesite.com"


def test_graphql_name_unchanged():
    @strawberry.type
    class Query:
        the_field: int = strawberry.field(name="some_name")

    definition = Query._type_definition

    assert definition.fields[0].python_name == "the_field"
    assert definition.fields[0].graphql_name == "some_name"
