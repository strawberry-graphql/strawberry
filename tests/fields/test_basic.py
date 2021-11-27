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
    assert definition.fields[0].type == str

    assert definition.fields[1].python_name == "age"
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
    assert definition.fields[0].type == str

    assert definition.fields[1].python_name == "age"
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
