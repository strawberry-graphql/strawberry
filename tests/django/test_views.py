from pathlib import Path

from django.http import HttpResponse
from django.test import Client, override_settings

BASE_DIR = Path(__file__).parent
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
    }
]


def test_render_graphiql_template():
    headers = {
        "Accept": "text/html",
    }
    client = Client(headers=headers)
    response: HttpResponse = client.get("/graphql/")
    assert 'JSON.parse("false")' in response.content.decode()


@override_settings(TEMPLATES=TEMPLATES)
def test_subscription_enabled_not_empty():
    headers = {
        "Accept": "text/html",
    }
    client = Client(headers=headers)
    response: HttpResponse = client.get("/graphql/")
    assert 'JSON.parse("false")' in response.content.decode()
