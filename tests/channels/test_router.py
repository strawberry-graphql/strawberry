from unittest import mock

import pytest

from tests.views.schema import schema


def _fake_asgi():
    return lambda: None


@mock.patch("strawberry.channels.router.GraphQLHTTPConsumer.as_asgi")
@mock.patch("strawberry.channels.router.GraphQLWSConsumer.as_asgi")
@pytest.mark.parametrize("pattern", ["^graphql", "^foo"])
def test_included_paths(ws_asgi: mock.Mock, http_asgi: mock.Mock, pattern: str):
    from strawberry.channels.router import GraphQLProtocolTypeRouter

    http_ret = _fake_asgi()
    http_asgi.return_value = http_ret

    ws_ret = _fake_asgi()
    ws_asgi.return_value = ws_ret

    router = GraphQLProtocolTypeRouter(schema, url_pattern=pattern)
    assert set(router.application_mapping) == {"http", "websocket"}

    assert len(router.application_mapping["http"].routes) == 1
    http_route = router.application_mapping["http"].routes[0]
    assert http_route.pattern._regex == pattern
    assert http_route.callback is http_ret

    assert len(router.application_mapping["websocket"].routes) == 1
    http_route = router.application_mapping["websocket"].routes[0]
    assert http_route.pattern._regex == pattern
    assert http_route.callback is ws_ret


@mock.patch("strawberry.channels.router.GraphQLHTTPConsumer.as_asgi")
@mock.patch("strawberry.channels.router.GraphQLWSConsumer.as_asgi")
@pytest.mark.parametrize("pattern", ["^graphql", "^foo"])
def test_included_paths_with_django_app(
    ws_asgi: mock.Mock,
    http_asgi: mock.Mock,
    pattern: str,
):
    from strawberry.channels.router import GraphQLProtocolTypeRouter

    http_ret = _fake_asgi()
    http_asgi.return_value = http_ret

    ws_ret = _fake_asgi()
    ws_asgi.return_value = ws_ret

    django_app = _fake_asgi()
    router = GraphQLProtocolTypeRouter(
        schema,
        django_application=django_app,
        url_pattern=pattern,
    )
    assert set(router.application_mapping) == {"http", "websocket"}

    assert len(router.application_mapping["http"].routes) == 2
    http_route = router.application_mapping["http"].routes[0]
    assert http_route.pattern._regex == pattern
    assert http_route.callback is http_ret

    django_route = router.application_mapping["http"].routes[1]
    assert django_route.pattern._regex == "^"
    assert django_route.callback is django_app

    assert len(router.application_mapping["websocket"].routes) == 1
    http_route = router.application_mapping["websocket"].routes[0]
    assert http_route.pattern._regex == pattern
    assert http_route.callback is ws_ret
