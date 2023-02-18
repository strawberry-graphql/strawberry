from .utils import Result, requires_pyright, run_pyright, skip_on_windows

pytestmark = [skip_on_windows, requires_pyright]


CODE = """
from typing import Any, Dict
from typing_extensions import TypedDict
import strawberry
from strawberry.scalars import ID, JSON, Base16, Base32, Base64


class SomeTypedDict(TypedDict):
    foo: int
    bar: str


@strawberry.type
class SomeType:
    id: ID
    json: JSON
    json_any: JSON[Any]
    json_typed_with_scalar: JSON[int]
    json_typed_with_dict: JSON[Dict[str, int]]
    json_typed_with_typeddict: JSON[SomeTypedDict]
    base16: Base16
    base32: Base32
    base64: Base64


obj = SomeType(
    id=ID("123"),
    json=JSON({"foo": "bar"}),
    json_any={"foo": "bar"},
    json_typed_with_scalar=1,
    json_typed_with_dict={"foo": 1},
    json_typed_with_typeddict={"foo": 1, "bar": "str"},
    base16=Base16(b"<bytes>"),
    base32=Base32(b"<bytes>"),
    base64=Base64(b"<bytes>"),
)

reveal_type(obj.id)
reveal_type(obj.json)
reveal_type(obj.json_any)
reveal_type(obj.json_typed_with_scalar)
reveal_type(obj.json_typed_with_dict)
reveal_type(obj.json_typed_with_typeddict)
reveal_type(obj.base16)
reveal_type(obj.base16)
reveal_type(obj.base64)
"""


def test_pyright():
    results = run_pyright(CODE)

    # NOTE: This is also guaranteeing that those scalars could be used to annotate
    # the attributes. Pyright 1.1.224+ doesn't allow non-types to be used there
    __import__("pprint").pprint(results)
    assert results == [
        Result(
            type="information", message='Type of "obj.id" is "ID"', line=38, column=13
        ),
        Result(
            type="information",
            message='Type of "obj.json" is "JSON[Any]"',
            line=39,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "obj.json_any" is "Any"',
            line=40,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "obj.json_typed_with_scalar" is "int"',
            line=41,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "obj.json_typed_with_dict" is "Dict[str, int]"',
            line=42,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "obj.json_typed_with_typeddict" is "SomeTypedDict"',
            line=43,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "obj.base16" is "Base16"',
            line=44,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "obj.base16" is "Base16"',
            line=45,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "obj.base64" is "Base64"',
            line=46,
            column=13,
        ),
    ]


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
    results = run_pyright(CODE_SCHEMA_OVERRIDES, strict=False)

    assert results == [
        Result(
            type="information",
            message='Type of "EpochDateTime" is "Type[datetime]"',
            line=17,
            column=13,
        ),
    ]
