import dataclasses
import typing

import strawberry
from strawberry.arguments import UNSET, is_unset


def test_mutation():
    @strawberry.type
    class Query:
        hello: str = "Hello"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def say(self, info) -> str:
            return "Hello!"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = "mutation { say }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["say"] == "Hello!"


def test_mutation_with_input_type():
    @strawberry.input
    class SayInput:
        name: str
        age: int

    @strawberry.type
    class Query:
        hello: str = "Hello"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def say(self, info, input: SayInput) -> str:
            return f"Hello {input.name} of {input.age} years old!"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = 'mutation { say(input: { name: "Patrick", age: 10 }) }'

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["say"] == "Hello Patrick of 10 years old!"


def test_unset_types():
    @strawberry.type
    class Query:
        hello: str = "Hello"

    @strawberry.input
    class InputExample:
        name: str
        age: typing.Optional[int] = UNSET

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def say(self, info, name: typing.Optional[str] = UNSET) -> str:  # type: ignore
            if is_unset(name):
                return "Name is unset"

            return f"Hello {name}!"

        @strawberry.mutation
        def say_age(self, info, input: InputExample) -> str:
            age = "unset" if is_unset(input.age) else input.age

            return f"Hello {input.name} of age {age}!"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = 'mutation { say sayAge(input: { name: "P"}) }'

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["say"] == "Name is unset"
    assert result.data["sayAge"] == "Hello P of age unset!"


def test_unset_types_name_with_underscore():
    @strawberry.type
    class Query:
        hello: str = "Hello"

    @strawberry.input
    class InputExample:
        first_name: str
        age: typing.Optional[str] = UNSET

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def say(
            self, info, first_name: typing.Optional[str] = UNSET  # type: ignore
        ) -> str:
            if is_unset(first_name):
                return "Name is unset"

            if first_name == "":
                return "Hello Empty!"

            return f"Hello {first_name}!"

        @strawberry.mutation
        def say_age(self, info, input: InputExample) -> str:
            age = "unset" if is_unset(input.age) else input.age
            age = "empty" if age == "" else age

            return f"Hello {input.first_name} of age {age}!"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """mutation {
        one: say
        two: say(firstName: "Patrick")
        three: say(firstName: "")
        empty: sayAge(input: { firstName: "Patrick", age: "" })
        null: sayAge(input: { firstName: "Patrick", age: null })
        sayAge(input: { firstName: "Patrick" })
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["one"] == "Name is unset"
    assert result.data["two"] == "Hello Patrick!"
    assert result.data["three"] == "Hello Empty!"
    assert result.data["empty"] == "Hello Patrick of age empty!"
    assert result.data["null"] == "Hello Patrick of age None!"
    assert result.data["sayAge"] == "Hello Patrick of age unset!"


def test_unset_types_stringify_empty():
    @strawberry.type
    class Query:
        hello: str = "Hello"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def say(
            self, info, first_name: typing.Optional[str] = UNSET  # type: ignore
        ) -> str:
            return f"Hello {first_name}!"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """mutation {
        say
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["say"] == "Hello !"

    query = """mutation {
        say(firstName: null)
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["say"] == "Hello None!"


def test_converting_to_dict_with_unset():
    @strawberry.type
    class Query:
        hello: str = "Hello"

    @strawberry.input
    class Input:
        name: typing.Optional[str] = UNSET

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def say(self, info, input: Input) -> str:
            data = dataclasses.asdict(input)

            if is_unset(data["name"]):
                return "Hello 🤨"

            return f"Hello {data['name']}!"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """mutation {
        say(input: {})
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["say"] == "Hello 🤨"
