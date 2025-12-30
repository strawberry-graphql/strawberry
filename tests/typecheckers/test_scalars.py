from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, requires_ty, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy, requires_ty]


CODE = """
import strawberry
from strawberry.scalars import ID, JSON, Base16, Base32, Base64


@strawberry.type
class SomeType:
    id: ID
    json: JSON
    base16: Base16
    base32: Base32
    base64: Base64


obj = SomeType(
    id=ID("123"),
    json=JSON({"foo": "bar"}),
    base16=Base16(b"<bytes>"),
    base32=Base32(b"<bytes>"),
    base64=Base64(b"<bytes>"),
)

reveal_type(obj.id)
reveal_type(obj.json)
reveal_type(obj.base16)
reveal_type(obj.base16)
reveal_type(obj.base64)
"""


def test():
    results = typecheck(CODE)

    # NOTE: This is also guaranteeing that those scalars could be used to annotate
    # the attributes. Pyright 1.1.224+ doesn't allow non-types to be used there
    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "obj.id" is "ID"',
                line=23,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "obj.json" is "JSON"',
                line=24,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "obj.base16" is "Base16"',
                line=25,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "obj.base16" is "Base16"',
                line=26,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "obj.base64" is "Base64"',
                line=27,
                column=13,
            ),
        ]
    )
    # Now that scalars are proper NewTypes, mypy correctly identifies them
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "strawberry.scalars.ID"',
                line=23,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.scalars.JSON"',
                line=24,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.scalars.Base16"',
                line=25,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.scalars.Base16"',
                line=26,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.scalars.Base64"',
                line=27,
                column=13,
            ),
        ]
    )
    # Now that scalars are proper NewTypes, ty no longer reports errors
    assert results.ty == snapshot(
        [
            Result(
                type="information",
                message="Revealed type: `ID`",
                line=23,
                column=13,
            ),
            Result(
                type="information",
                message="Revealed type: `JSON`",
                line=24,
                column=13,
            ),
            Result(
                type="information",
                message="Revealed type: `Base16`",
                line=25,
                column=13,
            ),
            Result(
                type="information",
                message="Revealed type: `Base16`",
                line=26,
                column=13,
            ),
            Result(
                type="information",
                message="Revealed type: `Base64`",
                line=27,
                column=13,
            ),
        ]
    )


CODE_SCHEMA_OVERRIDES = """
import strawberry
from datetime import datetime, timezone

EpochDateTime = strawberry.scalar(
    datetime,
)

@strawberry.type
class Query:
    a: datetime

schema = strawberry.Schema(query=Query, scalar_overrides={
    datetime: EpochDateTime,
})

reveal_type(EpochDateTime)
"""


def test_schema_overrides():
    # TODO: change strict to true when we improve type hints for scalar
    results = typecheck(CODE_SCHEMA_OVERRIDES, strict=False)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "EpochDateTime" is "type[datetime]"',
                line=16,
                column=13,
            )
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "def (year: typing.SupportsIndex, month: typing.SupportsIndex, day: typing.SupportsIndex, hour: typing.SupportsIndex =, minute: typing.SupportsIndex =, second: typing.SupportsIndex =, microsecond: typing.SupportsIndex =, tzinfo: datetime.tzinfo | None =, *, fold: builtins.int =) -> datetime.datetime"',
                line=17,
                column=13,
            )
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="information",
                message="Revealed type: `<class 'datetime'>`",
                line=17,
                column=13,
            ),
        ]
    )


CODE_SCALAR_MAP = """
import strawberry
from typing import NewType
from strawberry.schema.config import StrawberryConfig

MyString = NewType("MyString", str)

@strawberry.type
class Query:
    value: MyString

schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(
        scalar_map={
            MyString: strawberry.scalar(
                name="MyString",
                serialize=lambda v: v.upper(),
            )
        }
    ),
)

reveal_type(MyString)
reveal_type(MyString("test"))
"""


def test_scalar_map():
    results = typecheck(CODE_SCALAR_MAP, strict=False)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "MyString" is "type[MyString]"',
                line=23,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "MyString("test")" is "MyString"',
                line=24,
                column=13,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "def (item: builtins.str) -> mypy_test.MyString"',
                line=24,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "mypy_test.MyString"',
                line=25,
                column=13,
            ),
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="information",
                message="Revealed type: `<NewType pseudo-class 'MyString'>`",
                line=24,
                column=13,
            ),
            Result(
                type="information",
                message="Revealed type: `MyString`",
                line=25,
                column=13,
            ),
        ]
    )


CODE_NEWTYPE_SCALAR_USAGE = """
import strawberry
from strawberry.scalars import JSON, Base64

@strawberry.type
class Query:
    # Test using NewType scalars in various positions
    json_field: JSON
    base64_field: Base64

    @strawberry.field
    def process_json(self, data: JSON) -> JSON:
        return data

    @strawberry.field
    def encode_data(self, data: str) -> Base64:
        return Base64(data.encode())

# Test that NewType scalars can be instantiated correctly
json_val: JSON = JSON({"key": "value"})
base64_val: Base64 = Base64(b"hello")

reveal_type(json_val)
reveal_type(base64_val)
"""


def test_newtype_scalar_usage():
    results = typecheck(CODE_NEWTYPE_SCALAR_USAGE, strict=False)

    # Verify pyright sees the correct types
    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "json_val" is "JSON"',
                line=22,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "base64_val" is "Base64"',
                line=23,
                column=13,
            ),
        ]
    )
    # Verify mypy sees the correct types
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "strawberry.scalars.JSON"',
                line=23,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.scalars.Base64"',
                line=24,
                column=13,
            ),
        ]
    )
    # Verify ty sees the correct types (no errors about invalid type expressions)
    assert results.ty == snapshot(
        [
            Result(
                type="information",
                message="Revealed type: `JSON`",
                line=23,
                column=13,
            ),
            Result(
                type="information",
                message="Revealed type: `Base64`",
                line=24,
                column=13,
            ),
        ]
    )
