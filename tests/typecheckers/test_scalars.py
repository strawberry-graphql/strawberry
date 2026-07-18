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
                message='Revealed type is "def (year: typing.SupportsIndex, month: typing.SupportsIndex, day: typing.SupportsIndex, hour: typing.SupportsIndex =, minute: typing.SupportsIndex =, second: typing.SupportsIndex =, microsecond: typing.SupportsIndex =, tzinfo: datetime.tzinfo | None =, *, fold: int =) -> datetime.datetime"',
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
                message='Revealed type is "def (item: str) -> mypy_test.MyString"',
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


# Regression for https://github.com/strawberry-graphql/strawberry/issues/4092
# `JSON` is a NewType over object, so returning a plain dict/list/primitive
# from a resolver annotated as `JSON` is nominally rejected by type checkers
# (by design: NewType is nominal). The documented way to return ordinary
# JSON-compatible Python values while still exposing the `JSON` GraphQL scalar
# is to override the schema type with `graphql_type=strawberry.scalars.JSON`
# and annotate the resolver with the concrete Python type. This test guards
# that workaround under all three checkers so it keeps working as the scalar
# machinery evolves. See docs/types/scalars.md and the `graphql_type` note in
# docs/general/queries.md.
CODE_GRAPHQL_TYPE_WORKAROUND = """
import strawberry
from strawberry.scalars import JSON


@strawberry.type
class Query:
    @strawberry.field(graphql_type=JSON)
    def sync_dict(self) -> dict[str, int]:
        return {"a": 1}

    @strawberry.field(graphql_type=JSON)
    async def async_dict(self) -> dict[str, int]:
        return {"a": 1}

    @strawberry.field(graphql_type=JSON)
    def sync_list(self) -> list[int]:
        return [1, 2, 3]

    @strawberry.field(graphql_type=JSON)
    def sync_str(self) -> str:
        return "hello"

    @strawberry.field(graphql_type=JSON)
    def sync_int(self) -> int:
        return 42

    @strawberry.field(graphql_type=JSON)
    def sync_float(self) -> float:
        return 3.14

    @strawberry.field(graphql_type=JSON)
    def sync_bool(self) -> bool:
        return True

    @strawberry.field(graphql_type=JSON)
    def sync_none(self) -> None:
        return None


schema = strawberry.Schema(query=Query)
"""


def test_graphql_type_workaround_for_plain_json_values():
    results = typecheck(CODE_GRAPHQL_TYPE_WORKAROUND, strict=False)

    assert results.pyright == snapshot([])
    assert results.mypy == snapshot([])
    assert results.ty == snapshot([])


# `JSON(value)` must remain a supported static constructor. The scalar is a
# NewType and calling it is the documented way to produce a value typed as
# JSON (used by the core scalar test above and by user code). This guards that
# contract so a future change to the JSON declaration does not silently break
# constructor usage under any checker.
CODE_JSON_CONSTRUCTOR = """
import strawberry
from strawberry.scalars import JSON

json_val: JSON = JSON({"key": "value"})

reveal_type(json_val)
"""


def test_json_constructor_remains_valid():
    results = typecheck(CODE_JSON_CONSTRUCTOR, strict=False)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "json_val" is "JSON"',
                line=6,
                column=13,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "strawberry.scalars.JSON"',
                line=7,
                column=13,
            ),
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="information",
                message="Revealed type: `JSON`",
                line=7,
                column=13,
            ),
        ]
    )


# Negative control: an unrelated NewType stays nominal. Returning a plain str
# from a function annotated with a distinct NewType over str must still be
# rejected by every checker. This proves the JSON `graphql_type` workaround
# above is not passing by globally silencing checker diagnostics.
CODE_UNRELATED_NEWTYPE_NOMINAL = """
from typing import NewType

OtherType = NewType("OtherType", str)


def returns_plain_str() -> OtherType:
    return "not OtherType"
"""


def test_unrelated_newtype_stays_nominal():
    results = typecheck(CODE_UNRELATED_NEWTYPE_NOMINAL, strict=False)

    assert any(r.type == "error" for r in results.pyright)
    assert any(r.type == "error" for r in results.mypy)
    assert any(r.type == "error" for r in results.ty)
