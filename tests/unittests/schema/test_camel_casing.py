import strawberry
from strawberry.schema.config import StrawberryConfig


def test_camel_case_is_on_by_default():
    @strawberry.type
    class Query:
        example_field: str = "Example"

    schema = strawberry.Schema(query=Query)

    query = """
        {
            __type(name: "Query") {
                fields {
                    name
                }
            }
        }
    """

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["__type"]["fields"] == [{"name": "exampleField"}]


def test_can_set_camel_casing():
    @strawberry.type
    class Query:
        example_field: str = "Example"

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=True)
    )

    query = """
        {
            __type(name: "Query") {
                fields {
                    name
                }
            }
        }
    """

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["__type"]["fields"] == [{"name": "exampleField"}]


def test_can_set_camel_casing_to_false():
    @strawberry.type
    class Query:
        example_field: str = "Example"

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )

    query = """
        {
            __type(name: "Query") {
                fields {
                    name
                }
            }
        }
    """

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["__type"]["fields"] == [{"name": "example_field"}]


def test_can_set_camel_casing_to_false_uses_name():
    @strawberry.type
    class Query:
        example_field: str = strawberry.field(name="exampleField")

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )

    query = """
        {
            __type(name: "Query") {
                fields {
                    name
                }
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["__type"]["fields"] == [{"name": "exampleField"}]


def test_can_set_camel_casing_to_false_uses_name_field_decorator():
    @strawberry.type
    class Query:
        @strawberry.field(name="exampleField")
        def example_field(self) -> str:
            return "ABC"

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )

    query = """
        {
            __type(name: "Query") {
                fields {
                    name
                }
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["__type"]["fields"] == [{"name": "exampleField"}]


def test_camel_case_is_on_by_default_arguments():
    @strawberry.type
    class Query:
        @strawberry.field
        def example_field(self, example_input: str) -> str:
            return example_input

    schema = strawberry.Schema(query=Query)

    query = """
        {
            __type(name: "Query") {
                fields {
                    name
                    args { name }
                }
            }
        }
    """

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["__type"]["fields"] == [
        {"args": [{"name": "exampleInput"}], "name": "exampleField"}
    ]


def test_can_turn_camel_case_off_arguments():
    @strawberry.type
    class Query:
        @strawberry.field
        def example_field(self, example_input: str) -> str:
            return example_input

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )

    query = """
        {
            __type(name: "Query") {
                fields {
                    name
                    args { name }
                }
            }
        }
    """

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["__type"]["fields"] == [
        {"args": [{"name": "example_input"}], "name": "example_field"}
    ]


def test_can_turn_camel_case_off_arguments_conversion_works():
    @strawberry.type
    class Query:
        @strawberry.field
        def example_field(self, example_input: str) -> str:
            return example_input

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )

    query = """
        {
            example_field(example_input: "Hello world")
        }
    """

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["example_field"] == "Hello world"
