import strawberry


class SampleClass:
    def __init__(self, schema):
        self.schema = schema


@strawberry.type
class User:
    name: str
    age: int


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(name="Patrick", age=100)


schema = strawberry.Schema(query=Query)
sample_instance = SampleClass(schema)
not_a_schema = 42
