import textwrap
from enum import Enum
from typing import Any, NoReturn, Optional

import pytest

import strawberry
from strawberry import Info
from strawberry.directive import DirectiveLocation, DirectiveValue
from strawberry.extensions import SchemaExtension
from strawberry.schema.config import StrawberryConfig
from strawberry.types.base import get_object_definition
from strawberry.utils.await_maybe import await_maybe


def test_supports_default_directives():
    @strawberry.type
    class Person:
        name: str = "Jess"
        points: int = 2000

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    query = """query ($includePoints: Boolean!){
        person {
            name
            points @include(if: $includePoints)
        }
    }"""

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        query,
        variable_values={"includePoints": False},
        context_value={"username": "foo"},
    )

    assert not result.errors
    assert result.data
    assert result.data["person"] == {"name": "Jess"}

    query = """query ($skipPoints: Boolean!){
        person {
            name
            points @skip(if: $skipPoints)
        }
    }"""

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(query, variable_values={"skipPoints": False})

    assert not result.errors
    assert result.data
    assert result.data["person"] == {"name": "Jess", "points": 2000}


@pytest.mark.asyncio
async def test_supports_default_directives_async():
    @strawberry.type
    class Person:
        name: str = "Jess"
        points: int = 2000

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    query = """query ($includePoints: Boolean!){
        person {
            name
            points @include(if: $includePoints)
        }
    }"""

    schema = strawberry.Schema(query=Query)
    result = await schema.execute(query, variable_values={"includePoints": False})

    assert not result.errors
    assert result.data
    assert result.data["person"] == {"name": "Jess"}

    query = """query ($skipPoints: Boolean!){
        person {
            name
            points @skip(if: $skipPoints)
        }
    }"""

    schema = strawberry.Schema(query=Query)
    result = await schema.execute(query, variable_values={"skipPoints": False})

    assert not result.errors
    assert result.data
    assert result.data["person"] == {"name": "Jess", "points": 2000}


def test_can_declare_directives():
    @strawberry.type
    class Query:
        @strawberry.field
        def cake(self) -> str:
            return "made_in_switzerland"

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Make string uppercase"
    )
    def uppercase(value: DirectiveValue[str], example: str):
        return value.upper()

    schema = strawberry.Schema(query=Query, directives=[uppercase])

    expected_schema = '''
    """Make string uppercase"""
    directive @uppercase(example: String!) on FIELD

    type Query {
      cake: String!
    }
    '''

    assert schema.as_str() == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync('query { cake @uppercase(example: "foo") }')
    assert result.errors is None
    assert result.data == {"cake": "MADE_IN_SWITZERLAND"}


def test_directive_arguments_without_value_param():
    """Regression test for Strawberry Issue #1666.

    https://github.com/strawberry-graphql/strawberry/issues/1666
    """

    @strawberry.type
    class Query:
        cake: str = "victoria sponge"

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD],
        description="Don't actually like cake? try ice cream instead",
    )
    def ice_cream(flavor: str):
        return f"{flavor} ice cream"

    schema = strawberry.Schema(query=Query, directives=[ice_cream])

    expected_schema = '''
    """Don't actually like cake? try ice cream instead"""
    directive @iceCream(flavor: String!) on FIELD

    type Query {
      cake: String!
    }
    '''

    assert schema.as_str() == textwrap.dedent(expected_schema).strip()

    query = 'query { cake @iceCream(flavor: "strawberry") }'
    result = schema.execute_sync(query, root_value=Query())

    assert result.data == {"cake": "strawberry ice cream"}


def test_runs_directives():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Make string uppercase"
    )
    def turn_uppercase(value: DirectiveValue[str]):
        return value.upper()

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def replace(value: DirectiveValue[str], old: str, new: str):
        return value.replace(old, new)

    schema = strawberry.Schema(query=Query, directives=[turn_uppercase, replace])

    query = """query People($identified: Boolean!){
        person {
            name @turnUppercase
        }
        jess: person {
            name @replace(old: "Jess", new: "Jessica")
        }
        johnDoe: person {
            name @replace(old: "Jess", new: "John") @include(if: $identified)
        }
    }"""

    result = schema.execute_sync(query, variable_values={"identified": False})

    assert not result.errors
    assert result.data
    assert result.data["person"]["name"] == "JESS"
    assert result.data["jess"]["name"] == "Jessica"
    assert result.data["johnDoe"].get("name") is None


def test_runs_directives_camel_case_off():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Make string uppercase"
    )
    def turn_uppercase(value: DirectiveValue[str]):
        return value.upper()

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def replace(value: DirectiveValue[str], old: str, new: str):
        return value.replace(old, new)

    schema = strawberry.Schema(
        query=Query,
        directives=[turn_uppercase, replace],
        config=StrawberryConfig(auto_camel_case=False),
    )

    query = """query People($identified: Boolean!){
        person {
            name @turn_uppercase
        }
        jess: person {
            name @replace(old: "Jess", new: "Jessica")
        }
        johnDoe: person {
            name @replace(old: "Jess", new: "John") @include(if: $identified)
        }
    }"""

    result = schema.execute_sync(query, variable_values={"identified": False})

    assert not result.errors
    assert result.data
    assert result.data["person"]["name"] == "JESS"
    assert result.data["jess"]["name"] == "Jessica"
    assert result.data["johnDoe"].get("name") is None


@pytest.mark.asyncio
async def test_runs_directives_async():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Make string uppercase"
    )
    async def uppercase(value: DirectiveValue[str]):
        return value.upper()

    schema = strawberry.Schema(query=Query, directives=[uppercase])

    query = """{
        person {
            name @uppercase
        }
    }"""

    result = await schema.execute(query, variable_values={"identified": False})

    assert not result.errors
    assert result.data
    assert result.data["person"]["name"] == "JESS"


@pytest.mark.xfail
def test_runs_directives_with_list_params():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def replace(value: DirectiveValue[str], old_list: list[str], new: str):
        for old in old_list:
            value = value.replace(old, new)

        return value

    schema = strawberry.Schema(query=Query, directives=[replace])

    query = """query People {
        person {
            name @replace(oldList: ["J", "e", "s", "s"], new: "John")
        }
    }"""

    result = schema.execute_sync(query, variable_values={"identified": False})

    assert not result.errors
    assert result.data
    assert result.data["person"]["name"] == "JESS"


def test_runs_directives_with_extensions():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Make string uppercase"
    )
    def uppercase(value: DirectiveValue[str]):
        return value.upper()

    class ExampleExtension(SchemaExtension):
        def resolve(self, _next, root, info, *args: str, **kwargs: Any):
            return _next(root, info, *args, **kwargs)

    schema = strawberry.Schema(
        query=Query, directives=[uppercase], extensions=[ExampleExtension]
    )

    query = """query {
        person {
            name @uppercase
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data
    assert result.data["person"]["name"] == "JESS"


@pytest.mark.asyncio
async def test_runs_directives_with_extensions_async():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        async def person(self) -> Person:
            return Person()

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Make string uppercase"
    )
    def uppercase(value: DirectiveValue[str]):
        return value.upper()

    class ExampleExtension(SchemaExtension):
        async def resolve(self, _next, root, info, *args: str, **kwargs: Any):
            return await await_maybe(_next(root, info, *args, **kwargs))

    schema = strawberry.Schema(
        query=Query, directives=[uppercase], extensions=[ExampleExtension]
    )

    query = """query {
        person {
            name @uppercase
        }
    }"""

    result = await schema.execute(query)

    assert not result.errors
    assert result.data
    assert result.data["person"]["name"] == "JESS"


@pytest.fixture
def info_directive_schema() -> strawberry.Schema:
    """Returns a schema with directive that validates if info is recieved."""

    @strawberry.enum
    class Locale(Enum):
        EN: str = "EN"
        NL: str = "NL"

    greetings: dict[Locale, str] = {
        Locale.EN: "Hello {username}",
        Locale.NL: "Hallo {username}",
    }

    @strawberry.type
    class Query:
        @strawberry.field
        def greeting_template(self, locale: Locale = Locale.EN) -> str:
            return greetings[locale]

    field = get_object_definition(Query, strict=True).fields[0]

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD],
        description="Interpolate string on the server from context data",
    )
    def interpolate(value: DirectiveValue[str], info: strawberry.Info):
        try:
            assert isinstance(info, strawberry.Info)
            assert info._field is field
            return value.format(**info.context["userdata"])
        except KeyError:
            return value

    return strawberry.Schema(query=Query, directives=[interpolate])


def test_info_directive_schema(info_directive_schema: strawberry.Schema):
    expected_schema = '''
    """Interpolate string on the server from context data"""
    directive @interpolate on FIELD

    enum Locale {
      EN
      NL
    }

    type Query {
      greetingTemplate(locale: Locale! = EN): String!
    }
    '''

    assert textwrap.dedent(expected_schema).strip() == str(info_directive_schema)


def test_info_directive(info_directive_schema: strawberry.Schema):
    query = "query { greetingTemplate @interpolate }"
    result = info_directive_schema.execute_sync(
        query, context_value={"userdata": {"username": "Foo"}}
    )
    assert result.data == {"greetingTemplate": "Hello Foo"}


@pytest.mark.asyncio
async def test_info_directive_async(info_directive_schema: strawberry.Schema):
    query = "query { greetingTemplate @interpolate }"
    result = await info_directive_schema.execute(
        query, context_value={"userdata": {"username": "Foo"}}
    )
    assert result.data == {"greetingTemplate": "Hello Foo"}


def test_directive_value():
    """Tests if directive value is detected by type instead of by arg-name `value`."""

    @strawberry.type
    class Cake:
        frosting: Optional[str] = None
        flavor: str = "Chocolate"

    @strawberry.type
    class Query:
        @strawberry.field
        def cake(self) -> Cake:
            return Cake()

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD],
        description="Add frostring with ``flavor`` to a cake.",
    )
    def add_frosting(flavor: str, v: DirectiveValue[Cake], value: str):
        assert isinstance(v, Cake)
        assert value == "foo"  # Check if value can be used as an argument
        v.frosting = flavor
        return v

    schema = strawberry.Schema(query=Query, directives=[add_frosting])
    result = schema.execute_sync(
        """query {
            cake @addFrosting(flavor: "Vanilla", value: "foo") {
                frosting
                flavor
            }
        }
        """
    )
    assert result.data == {"cake": {"frosting": "Vanilla", "flavor": "Chocolate"}}


# Defined in module scope to allow the FowardRef to be resolvable with eval
@strawberry.directive(
    locations=[DirectiveLocation.FIELD],
    description="Add frostring with ``flavor`` to a cake.",
)
def add_frosting(flavor: str, v: DirectiveValue["Cake"], value: str) -> "Cake":
    assert isinstance(v, Cake)
    assert value == "foo"
    v.frosting = flavor
    return v


@strawberry.type
class Query:
    @strawberry.field
    def cake(self) -> "Cake":
        return Cake()


@strawberry.type
class Cake:
    frosting: Optional[str] = None
    flavor: str = "Chocolate"


def test_directive_value_forward_ref():
    """Tests if directive value by type works with PEP-563."""
    schema = strawberry.Schema(query=Query, directives=[add_frosting])
    result = schema.execute_sync(
        """query {
            cake @addFrosting(flavor: "Vanilla", value: "foo") {
                frosting
                flavor
            }
        }
        """
    )
    assert result.data == {"cake": {"frosting": "Vanilla", "flavor": "Chocolate"}}


def test_name_first_directive_value():
    @strawberry.type
    class Query:
        @strawberry.field
        def greeting(self) -> str:
            return "Hi"

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def personalize_greeting(value: str, v: DirectiveValue[str]):
        assert v == "Hi"
        return f"{v} {value}"

    schema = strawberry.Schema(Query, directives=[personalize_greeting])
    result = schema.execute_sync('{ greeting @personalizeGreeting(value: "Bar")}')

    assert result.data is not None
    assert not result.errors
    assert result.data["greeting"] == "Hi Bar"


def test_named_based_directive_value_is_deprecated():
    with pytest.deprecated_call(match=r"Argument name-based matching of 'value'"):

        @strawberry.type
        class Query:
            hello: str = "hello"

        @strawberry.directive(locations=[DirectiveLocation.FIELD])
        def deprecated_value(value): ...

        strawberry.Schema(query=Query, directives=[deprecated_value])


@pytest.mark.asyncio
async def test_directive_list_argument() -> NoReturn:
    @strawberry.type
    class Query:
        @strawberry.field
        def greeting(self) -> str:
            return "Hi"

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def append_names(value: DirectiveValue[str], names: list[str]):
        assert isinstance(names, list)
        return f"{value} {', '.join(names)}"

    schema = strawberry.Schema(query=Query, directives=[append_names])

    result = await schema.execute(
        'query { greeting @appendNames(names: ["foo", "bar"])}'
    )

    assert result.errors is None
    assert result.data
    assert result.data["greeting"] == "Hi foo, bar"


def test_directives_with_custom_types():
    @strawberry.input
    class DirectiveInput:
        example: str

    @strawberry.type
    class Query:
        @strawberry.field
        def cake(self) -> str:
            return "made_in_switzerland"

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Make string uppercase"
    )
    def uppercase(value: DirectiveValue[str], input: DirectiveInput):
        return value.upper()

    schema = strawberry.Schema(query=Query, directives=[uppercase])

    expected_schema = '''
    """Make string uppercase"""
    directive @uppercase(input: DirectiveInput!) on FIELD

    input DirectiveInput {
      example: String!
    }

    type Query {
      cake: String!
    }
    '''

    assert schema.as_str() == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync('query { cake @uppercase(input: { example: "foo" }) }')
    assert result.errors is None
    assert result.data == {"cake": "MADE_IN_SWITZERLAND"}


def test_directives_with_scalar():
    DirectiveInput = strawberry.scalar(str, name="DirectiveInput")

    @strawberry.type
    class Query:
        @strawberry.field
        def cake(self) -> str:
            return "made_in_switzerland"

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Make string uppercase"
    )
    def uppercase(value: DirectiveValue[str], input: DirectiveInput):
        return value.upper()

    schema = strawberry.Schema(query=Query, directives=[uppercase])

    expected_schema = '''
    """Make string uppercase"""
    directive @uppercase(input: DirectiveInput!) on FIELD

    scalar DirectiveInput

    type Query {
      cake: String!
    }
    '''

    assert schema.as_str() == textwrap.dedent(expected_schema).strip()

    result = schema.execute_sync('query { cake @uppercase(input: "foo") }')
    assert result.errors is None
    assert result.data == {"cake": "MADE_IN_SWITZERLAND"}


@pytest.mark.asyncio
async def test_directive_with_custom_info_class() -> NoReturn:
    @strawberry.type
    class Query:
        @strawberry.field
        def greeting(self) -> str:
            return "Hi"

    class CustomInfo(Info):
        test: str = "foo"

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def append_names(value: DirectiveValue[str], names: list[str], info: CustomInfo):
        assert isinstance(names, list)
        assert isinstance(info, CustomInfo)
        assert Info in type(info).__bases__  # Explicitly check it's not Info.
        assert info.test == "foo"
        return f"{value} {', '.join(names)}"

    schema = strawberry.Schema(
        query=Query,
        directives=[append_names],
        config=StrawberryConfig(info_class=CustomInfo),
    )

    result = await schema.execute(
        'query { greeting @appendNames(names: ["foo", "bar"])}'
    )

    assert result.errors is None
    assert result.data
    assert result.data["greeting"] == "Hi foo, bar"
