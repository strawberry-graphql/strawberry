import os
import pathlib
import typing


def get_graphiql_html(
    subscription_enabled: bool = False,
    subscription_graphql_ws: bool = False,
    graphiql_html_file_path: typing.Optional[os.PathLike] = None,
    raw: bool = False,
) -> str:
    """
    Renders graphiql template from `graphiql_html_file_path`,
    if not provided renders bundled strawberry template.

    If `subscription_enabled` is True,
    then graphiql will try to connect to ws endpoint on same url path.

    If `subscription_graphql_ws` is True,
    then graphiql will use new [graphql-ws](https://github.com/enisdenjo/graphql-ws)
    library for subscription client. Otherwise it will use depricated
    [subscriptions-transport-ws](https://github.com/apollographql/subscriptions-transport-ws).

    If `raw` is True, then all other options are ignored and template
    string returned without interpolations.
    """
    if graphiql_html_file_path is None:
        graphiql_html_file_path = (
            pathlib.Path(__file__).parent.parent / "static" / "graphiql.html"
        )
    else:
        graphiql_html_file_path = pathlib.Path(graphiql_html_file_path)

    template = graphiql_html_file_path.read_text()

    if not raw:
        template = template.replace(
            "{{ SUBSCRIPTION_ENABLED }}", str(subscription_enabled).lower()
        )
        template = template.replace(
            "{{ SUBSCRIPTION_GRAPHQL_WS }}", str(subscription_graphql_ws).lower()
        )
    return template
