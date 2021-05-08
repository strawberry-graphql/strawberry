import functools
from os.path import abspath, dirname, join


@functools.lru_cache
def render_graphiql_page() -> str:
    """
    Loads the graphiql html file into a string and returns it. Replacing subscription enabled as false, this is because
    this chalice integration does not currently support subscriptions.
    This function returns a static result, so cache it in ram, saving us from loading the file from disk each time.
    Returns:
        A cached string containing a static graphiql page.
    """
    dir_path = abspath(join(dirname(__file__), ".."))
    graphiql_html_file = f"{dir_path}/static/graphiql.html"

    html_string = None

    with open(graphiql_html_file, "r") as f:
        html_string = f.read()

    return html_string.replace("{{ SUBSCRIPTION_ENABLED }}", "false")
