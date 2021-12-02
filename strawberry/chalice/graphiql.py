import functools
from pathlib import Path


@functools.lru_cache()
def render_graphiql_page() -> str:
    """
    Loads the graphiql html file into a string and returns it. Replacing subscription
    enabled as false, this is because this chalice integration does not currently support
    subscriptions. This function returns a static result, so cache it in ram, saving us
    from loading the file from disk each time.
    Returns:
        A cached string containing a static graphiql page.
    """
    graphiql_path = Path(__file__).parent.parent / "static/graphiql.html"
    html_string = graphiql_path.read_text()

    return html_string.replace("{{ SUBSCRIPTION_ENABLED }}", "false")
