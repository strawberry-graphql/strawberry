from typing import Any, List, Optional

import pytest

import strawberry
from strawberry import UNSET
from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import StrawberryArgument
from strawberry.exceptions import OverrideError
from strawberry.field import StrawberryField
from strawberry.types.types import get_type_definition


def test_basic_override_get_result():
    class HelloField(StrawberryField):
        def get_result(self, *args, **kwargs):
            res = super().get_result(*args, **kwargs)
            return "hello " + res

    @strawberry.type
    class Query:
        @HelloField()
        def hello(self) -> str:
            return "world"

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        query="""
        {hello}
    """
    )
    assert not result.errors
    assert result.data["hello"] == "hello world"


def test_basic_override_type():
    class AlwaysReturnInt(StrawberryField):
        def override_type(self) -> StrawberryAnnotation:
            return StrawberryAnnotation(int)

    @strawberry.type
    class Query:
        @AlwaysReturnInt()
        def hello(self) -> str:
            return 2  # type: ignore

    hello = Query._type_definition.get_field_by_name("hello")
    assert hello.type is int
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        query="""
        {hello}
    """
    )
    assert not result.errors
    assert result.data["hello"] == 2


def test_basic_override_type_wrong():
    class AlwaysReturnInt(StrawberryField):
        def override_type(self):
            return int

    with pytest.raises(OverrideError):

        @strawberry.type
        class Query:
            @AlwaysReturnInt()
            def hello(self) -> str:
                return 2  # type: ignore


def test_basic_override_arguments():
    class Stringify(StrawberryField):
        def override_arguments(self) -> List[StrawberryArgument]:
            for arg in self.arguments:
                arg.type_annotation.annotation = str
            return self.arguments

    @strawberry.type
    class Query:
        @Stringify()
        def hello(self, arg1: Any, arg2: Any) -> str:
            return arg1.replace(arg2, "world")  # type: ignore

    hello = Query._type_definition.get_field_by_name("hello")
    assert hello.arguments[0].type is str
    assert hello.arguments[1].type is str
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        query="""
        {hello(arg1:"hello -", arg2:"-")}
    """
    )
    assert not result.errors
    assert result.data["hello"] == "hello world"


def test_basic_override_arguments_wrong():
    class Stringify(StrawberryField):
        def override_arguments(self):
            return [str, str]  # type: ignore

    with pytest.raises(OverrideError):

        @strawberry.type
        class Query:
            @Stringify()
            def hello(self, arg1: Any, arg2: Any) -> str:
                return arg1.replace(arg2, "world")  # type: ignore


def test_basic_override_graphql_name():
    class NoPythonKeyword(StrawberryField):
        def override_graphql_name(self):
            return self.python_name.strip("_")

    @strawberry.type
    class Query:
        in_: Optional[str] = NoPythonKeyword(default=UNSET)

    in_ = Query._type_definition.get_field_by_name("in_")
    assert in_.graphql_name == "in"
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        query="""
        {in}
    """,
        root_value=Query(),
    )
    assert not result.errors
    assert not result.data["in"]


def test_basic_override_graphql_name_wrong():
    class NoPythonKeyword(StrawberryField):
        def override_graphql_name(self):
            return 2

    with pytest.raises(OverrideError):

        @strawberry.type
        class Query:
            in_: Optional[str] = NoPythonKeyword(default=UNSET)


def test_batched_fields():
    class HelloField(StrawberryField):
        def get_result(self, *args, **kwargs):
            res = super().get_result(*args, **kwargs)
            return "hello " + res

    class FooField(StrawberryField):
        def get_result(self, *args, **kwargs):
            res = super().get_result(*args, **kwargs)
            return "foo " + res

    @strawberry.type
    class Query:
        @HelloField()
        @FooField()
        def hello(self) -> str:
            return "world"

    definition = get_type_definition(Query)
    assert isinstance(definition.fields[0], FooField)
    assert isinstance(definition.fields[0], HelloField)
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        query="""
        {hello}
    """
    )
    assert not result.errors
    assert result.data["hello"] == "hello world"
