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


def run_sync_view():
    client = Client()
    response: HttpResponse = client.get("/graphql/", HTTP_ACCEPT="text/html")
    assert 'JSON.parse("false")' in response.content.decode()


def test_render_graphiql_template():
    run_sync_view()


@override_settings(TEMPLATES=TEMPLATES)
def test_subscription_enabled_not_empty():
    run_sync_view()
