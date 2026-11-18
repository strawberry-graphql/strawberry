from strawberry.http.ides import get_graphql_ide_html


def test_graphiql_uses_configured_subscription_url():
    html = get_graphql_ide_html(
        graphql_ide="graphiql",
        subscription_url="wss://example.com/ws/graphql",
    )

    assert 'const customSubscriptionUrl = "wss://example.com/ws/graphql";' in html
    assert "const customSubscriptionUrl = null;" not in html


def test_graphiql_defaults_to_deriving_the_subscription_url():
    html = get_graphql_ide_html(graphql_ide="graphiql")

    assert "const customSubscriptionUrl = null;" in html


def test_subscription_url_is_ignored_for_non_graphiql_ides():
    html = get_graphql_ide_html(
        graphql_ide="pathfinder",
        subscription_url="wss://example.com/ws/graphql",
    )

    assert "wss://example.com/ws/graphql" not in html
