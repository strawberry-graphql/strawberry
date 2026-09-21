import datetime
import json
from decimal import Decimal
from uuid import UUID

import pytest

from tests.views.schema import schema


@pytest.fixture(params=["GraphQLView", "AsyncGraphQLView"])
def view_class(request):
    from strawberry.django import views

    return getattr(views, request.param)


@pytest.mark.parametrize("batch", [False, True])
def test_default_json_encoding_preserves_django_types(view_class, batch):
    from django.core.serializers.json import DjangoJSONEncoder
    from django.http import HttpResponse

    payload = {
        "data": {
            "amount": Decimal("12.30"),
            "created": datetime.datetime(
                2026, 9, 6, 12, 30, tzinfo=datetime.timezone.utc
            ),
            "id": UUID("12345678-1234-5678-1234-567812345678"),
            "message": "café 🍓, :",
        },
        "errors": [{"message": "Something failed", "path": ["field", 0]}],
    }
    expected = (
        '{"data":{"amount":"12.30","created":"2026-09-06T12:30:00Z",'
        '"id":"12345678-1234-5678-1234-567812345678",'
        r'"message":"caf\u00e9 \ud83c\udf53, :"},'
        '"errors":[{"message":"Something failed","path":["field",0]}]}'
    )
    data = [payload, payload] if batch else payload
    expected = f"[{expected},{expected}]" if batch else expected

    response = view_class(schema=schema).create_response(data, HttpResponse())

    assert response.content.decode() == expected
    assert json.loads(response.content) == json.loads(
        json.dumps(data, cls=DjangoJSONEncoder)
    )


@pytest.mark.parametrize("as_bytes", [False, True])
def test_custom_json_encoder_is_authoritative(view_class, as_bytes):
    from django.http import HttpResponse

    class CustomView(view_class):
        def encode_json(self, data: object) -> str | bytes:
            encoded = json.dumps(data, ensure_ascii=False, indent=2)
            return encoded.encode() if as_bytes else encoded

    payload = {"data": {"message": "café 🍓"}}
    response = CustomView(schema=schema).create_response(payload, HttpResponse())

    assert (
        response.content == json.dumps(payload, ensure_ascii=False, indent=2).encode()
    )
