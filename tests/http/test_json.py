import json

import pytest

from strawberry.http.base import BaseView


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            {"data": {"message": "café 🍓, :", "values": [1, True, None]}},
            r'{"data":{"message":"caf\u00e9 \ud83c\udf53, :","values":[1,true,null]}}',
        ),
        (
            {
                "data": None,
                "errors": [{"message": "Something failed", "path": ["x", 0]}],
            },
            '{"data":null,"errors":[{"message":"Something failed","path":["x",0]}]}',
        ),
        (
            [{"data": {"ok": True}}, {"errors": [{"message": "Failed"}]}],
            '[{"data":{"ok":true}},{"errors":[{"message":"Failed"}]}]',
        ),
    ],
)
def test_default_json_encoding(payload: object, expected: str) -> None:
    encoded = BaseView().encode_json(payload)

    assert encoded == expected
    assert json.loads(encoded) == json.loads(json.dumps(payload)) == payload
