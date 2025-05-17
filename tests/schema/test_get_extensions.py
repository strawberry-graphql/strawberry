import strawberry
from strawberry.directive import DirectiveLocation, DirectiveValue
from strawberry.extensions import SchemaExtension
from strawberry.extensions.directives import (
    DirectivesExtension,
    DirectivesExtensionSync,
)


@strawberry.type
class Query:
    example: str


@strawberry.directive(locations=[DirectiveLocation.FIELD])
def uppercase(value: DirectiveValue[str]) -> str:
    return value.upper()


class MyExtension(SchemaExtension): ...


def test_returns_empty_list_when_no_custom_directives():
    schema = strawberry.Schema(query=Query)

    assert schema.get_extensions() == []


def test_returns_extension_passed_by_user():
    schema = strawberry.Schema(query=Query, extensions=[MyExtension])

    assert len(schema.get_extensions()) == 1
    assert isinstance(schema.get_extensions()[0], MyExtension)


def test_returns_directives_extension_when_passing_directives():
    schema = strawberry.Schema(query=Query, directives=[uppercase])

    assert len(schema.get_extensions()) == 1
    assert isinstance(schema.get_extensions()[0], DirectivesExtension)


def test_returns_extension_passed_by_user_and_directives_extension():
    schema = strawberry.Schema(
        query=Query, extensions=[MyExtension], directives=[uppercase]
    )
    for ext, ext_cls in zip(
        schema.get_extensions(), [MyExtension, DirectivesExtension]
    ):
        assert isinstance(ext, ext_cls)


def test_returns_directives_extension_when_passing_directives_sync():
    schema = strawberry.Schema(query=Query, directives=[uppercase])

    assert len(schema.get_extensions(sync=True)) == 1
    assert isinstance(schema.get_extensions(sync=True)[0], DirectivesExtensionSync)


def test_returns_extension_passed_by_user_and_directives_extension_sync():
    schema = strawberry.Schema(
        query=Query, extensions=[MyExtension], directives=[uppercase]
    )
    for ext, ext_cls in zip(
        schema.get_extensions(sync=True), [MyExtension, DirectivesExtensionSync]
    ):
        assert isinstance(ext, ext_cls)


def test_no_duplicate_extensions_with_directives():
    """Test to verify that extensions are not duplicated when directives are present.

    This test initially fails with the current implementation but passes
    after fixing the get_extensions method.
    """

    schema = strawberry.Schema(
        query=Query, extensions=[MyExtension], directives=[uppercase]
    )

    extensions = schema.get_extensions()

    # Count how many times our extension appears
    ext_count = sum(1 for e in extensions if isinstance(e, MyExtension))

    # With current implementation this fails as ext_count is 2
    assert ext_count == 1, f"Extension appears {ext_count} times instead of once"


def test_extension_order_preserved():
    """Test to verify that extension order is preserved while removing duplicates."""

    class Extension1(SchemaExtension):
        pass

    class Extension2(SchemaExtension):
        pass

    schema = strawberry.Schema(
        query=Query, extensions=[Extension1, Extension2], directives=[uppercase]
    )

    extensions = schema.get_extensions()
    extension_types = [
        type(ext)
        for ext in extensions
        if not isinstance(ext, (DirectivesExtension, DirectivesExtensionSync))
    ]

    assert extension_types == [Extension1, Extension2], "Extension order not preserved"
