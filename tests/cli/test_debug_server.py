import sys

from starlette.testclient import TestClient


def test_debug_server_is_available_under_all_configured_paths(mocker):
    schema_import_path = "tests.fixtures.sample_package.sample_module"
    mocker.patch.object(sys, "argv", ["strawberry", "server", schema_import_path])
    from strawberry.cli.debug_server import app

    client = TestClient(app)

    for path in ["/", "/graphql"]:
        response = client.get(path)
        assert response.status_code == 200
