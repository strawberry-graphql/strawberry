import os
import pathlib
import typing


def get_graphiql_html(
    subscription_enabled: bool,
    subscription_graphql_ws: bool = False,
    graphiql_html_file_path: typing.Optional[os.PathLike] = None,
) -> str:
    if graphiql_html_file_path is None:
        graphiql_html_file_path = (
            pathlib.Path(__file__).parent.parent / "static" / "graphiql.html"
        )
    else:
        graphiql_html_file_path = pathlib.Path(graphiql_html_file_path)

    template = graphiql_html_file_path.read_text()
    template = template.replace(
        "{{ SUBSCRIPTION_ENABLED }}", str(subscription_enabled).lower()
    )
    template = template.replace(
        "{{ SUBSCRIPTION_GRAPHQL_WS }}", str(subscription_graphql_ws).lower()
    )
    return template
