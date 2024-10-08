import strawberry


def test_default_value():
    @strawberry.type
    class Query:
        a: str = strawberry.field(default="Example")

    schema = strawberry.Schema(query=Query)

    query = "{ a }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data == {"a": "Example"}


def test_default_factory():
    @strawberry.type
    class Query:
        a: str = strawberry.field(default_factory=lambda: "Example")

    schema = strawberry.Schema(query=Query)

    query = "{ a }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data == {"a": "Example"}


def test_default_factory_multiple_fields():
    # NOTE: The default_factory is called when instantiating the schema
    # this is why the user will start from 2
    counter = 0

    def generate_name():
        nonlocal counter
        counter += 1
        return f"User {counter}"

    @strawberry.type
    class User:
        name: str = strawberry.field(default_factory=generate_name)

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User()

        @strawberry.field
        def user2(self) -> User:
            return User()

    schema = strawberry.Schema(query=Query)

    query = "{ user { name }, user2 { name } }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data == {"user": {"name": "User 2"}, "user2": {"name": "User 3"}}


def test_default_factory_input():
    counter = 0

    def generate_id():
        nonlocal counter
        counter += 1
        return counter

    @strawberry.input
    class MyInputType:
        id: int = strawberry.field(default_factory=generate_id)

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def update_1(self, input: MyInputType) -> str:
            return str(input.id)

        @strawberry.mutation
        def update_2(self, input: MyInputType) -> str:
            return str(input.id)

    @strawberry.type
    class Query:
        hello: str

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = "mutation { update1: update1(input: {}) update2: update2(input: {}) }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"update1": "1", "update2": "2"}
