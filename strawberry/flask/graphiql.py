from os.path import abspath, dirname, join


def render_graphiql_page():
    dir_path = abspath(join(dirname(__file__), ".."))
    graphiql_html_file = f"{dir_path}/static/graphiql.html"

    html_string = None

    with open(graphiql_html_file, "r") as f:
        html_string = f.read()

    return html_string.replace("{{ SUBSCRIPTION_ENABLED }}", "false")
