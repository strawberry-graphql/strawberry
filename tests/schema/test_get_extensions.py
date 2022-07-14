import strawberry
from strawberry.directive import DirectiveLocation
from strawberry.extensions import Extension
from strawberry.extensions.directives import (
    DirectivesExtension,
    DirectivesExtensionSync,
)


@strawberry.type
class Query:
    example: str


@strawberry.directive(locations=[DirectiveLocation.FIELD])
def uppercase(value: str) -> str:
    return value.upper()


class MyExtension(Extension):
    ...


def test_returns_empty_list_when_no_custom_directives():
    schema = strawberry.Schema(query=Query)

    assert schema.get_extensions() == []


def test_returns_extension_passed_by_user():
    schema = strawberry.Schema(query=Query, extensions=[MyExtension])

    assert schema.get_extensions() == [MyExtension]


def test_returns_directives_extension_when_passing_directives():
    schema = strawberry.Schema(query=Query, directives=[uppercase])

    assert schema.get_extensions() == [DirectivesExtension]


def test_returns_extension_passed_by_user_and_directives_extension():
    schema = strawberry.Schema(
        query=Query, extensions=[MyExtension], directives=[uppercase]
    )

    assert schema.get_extensions() == [MyExtension, DirectivesExtension]


def test_returns_directives_extension_when_passing_directives_sync():
    schema = strawberry.Schema(query=Query, directives=[uppercase])

    assert schema.get_extensions(sync=True) == [DirectivesExtensionSync]


def test_returns_extension_passed_by_user_and_directives_extension_sync():
    schema = strawberry.Schema(
        query=Query, extensions=[MyExtension], directives=[uppercase]
    )

    assert schema.get_extensions(sync=True) == [MyExtension, DirectivesExtensionSync]
