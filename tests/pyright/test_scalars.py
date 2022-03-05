from .utils import Result, requires_pyright, run_pyright, skip_on_windows


pytestmark = [skip_on_windows, requires_pyright]


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


def test_pyright():
    results = run_pyright(CODE)

    # NOTE: This is also guaranteeing that those scalars could be used to annotate
    # the attributes. Pyright 1.1.224+ doesn't allow non-types to be used there
    assert results == [
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
