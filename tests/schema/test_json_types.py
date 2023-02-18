from textwrap import dedent
from typing import Dict, Optional
from typing_extensions import TypedDict, assert_type

import strawberry
from strawberry.scalars import JSON


def test_json():
    @strawberry.type
    class Query:
        @strawberry.field
        def echo_json(self, data: JSON) -> JSON:
            return data

        @strawberry.field
        def echo_json_nullable(self, data: Optional[JSON]) -> Optional[JSON]:
            return data

    schema = strawberry.Schema(query=Query)

    expected_schema = dedent(
        '''
        """
        The `JSON` scalar type represents JSON values as specified by [ECMA-404](http://www.ecma-international.org/publications/files/ECMA-ST/ECMA-404.pdf).
        """
        scalar JSON @specifiedBy(url: "http://www.ecma-international.org/publications/files/ECMA-ST/ECMA-404.pdf")

        type Query {
          echoJson(data: JSON!): JSON!
          echoJsonNullable(data: JSON): JSON
        }
        '''  # noqa: E501
    ).strip()

    assert str(schema) == expected_schema

    result = schema.execute_sync(
        """
        query {
            echoJson(data: {hello: {a: 1}, someNumbers: [1, 2, 3], null: null})
            echoJsonNullable(data: {hello: {a: 1}, someNumbers: [1, 2, 3], null: null})
        }
    """
    )

    assert not result.errors
    assert result.data == {
        "echoJson": {"hello": {"a": 1}, "someNumbers": [1, 2, 3], "null": None},
        "echoJsonNullable": {"hello": {"a": 1}, "someNumbers": [1, 2, 3], "null": None},
    }

    result = schema.execute_sync(
        """
        query {
            echoJson(data: null)
        }
    """
    )
    assert result.errors  # echoJson is not-null null

    result = schema.execute_sync(
        """
        query {
            echoJsonNullable(data: null)
        }
    """
    )
    assert not result.errors
    assert result.data == {
        "echoJsonNullable": None,
    }


def test_json_with_type_hints():
    @strawberry.type
    class Query:
        @strawberry.field
        def echo_json(self, data: JSON[Dict[str, int]]) -> JSON[Dict[str, int]]:
            assert_type(data, Dict[str, int])
            return data

        @strawberry.field
        def echo_json_nullable(
            self, data: Optional[JSON[Dict[str, int]]]
        ) -> Optional[JSON[Dict[str, int]]]:
            assert_type(data, Optional[Dict[str, int]])
            return data

    schema = strawberry.Schema(query=Query)

    expected_schema = dedent(
        '''
        """
        The `JSON` scalar type represents JSON values as specified by [ECMA-404](http://www.ecma-international.org/publications/files/ECMA-ST/ECMA-404.pdf).
        """
        scalar JSON @specifiedBy(url: "http://www.ecma-international.org/publications/files/ECMA-ST/ECMA-404.pdf")

        type Query {
          echoJson(data: JSON!): JSON!
          echoJsonNullable(data: JSON): JSON
        }
        '''  # noqa: E501
    ).strip()

    assert str(schema) == expected_schema

    result = schema.execute_sync(
        """
        query {
            echoJson(data: {hello: {a: 1}, someNumbers: [1, 2, 3], null: null})
            echoJsonNullable(data: {hello: {a: 1}, someNumbers: [1, 2, 3], null: null})
        }
    """
    )

    assert not result.errors
    assert result.data == {
        "echoJson": {"hello": {"a": 1}, "someNumbers": [1, 2, 3], "null": None},
        "echoJsonNullable": {"hello": {"a": 1}, "someNumbers": [1, 2, 3], "null": None},
    }

    result = schema.execute_sync(
        """
        query {
            echoJson(data: null)
        }
    """
    )
    assert result.errors  # echoJson is not-null null

    result = schema.execute_sync(
        """
        query {
            echoJsonNullable(data: null)
        }
    """
    )
    assert not result.errors
    assert result.data == {
        "echoJsonNullable": None,
    }


def test_json_with_type_hints_on_type():
    class JSONTyped(TypedDict):
        foo: int
        bar: str

    @strawberry.type
    class SomeType:
        json: JSON[JSONTyped]

        @strawberry.field
        def json_foo(self) -> int:
            assert_type(self.json, JSONTyped)
            return self.json["foo"]

        @strawberry.field
        def json_bar(self) -> str:
            assert_type(self.json, JSONTyped)
            return self.json["bar"]

    @strawberry.type
    class Query:
        @strawberry.field
        def echo_some_type(self, json_typed: JSON[JSONTyped]) -> SomeType:
            return SomeType(json=json_typed)

    schema = strawberry.Schema(query=Query)

    expected_schema = dedent(
        '''
        """
        The `JSON` scalar type represents JSON values as specified by [ECMA-404](http://www.ecma-international.org/publications/files/ECMA-ST/ECMA-404.pdf).
        """
        scalar JSON @specifiedBy(url: "http://www.ecma-international.org/publications/files/ECMA-ST/ECMA-404.pdf")

        type Query {
          echoSomeType(jsonTyped: JSON!): SomeType!
        }

        type SomeType {
          json: JSON!
          jsonFoo: Int!
          jsonBar: String!
        }
        '''  # noqa: E501
    ).strip()

    assert str(schema) == expected_schema

    result = schema.execute_sync(
        """
        query {
            echoSomeType(jsonTyped: {foo: 123, bar: "bar var"}) {
                json
                jsonFoo
                jsonBar
            }
        }
    """
    )

    assert not result.errors
    assert result.data == {
        "echoSomeType": {
            "json": {"bar": "bar var", "foo": 123},
            "jsonBar": "bar var",
            "jsonFoo": 123,
        }
    }
