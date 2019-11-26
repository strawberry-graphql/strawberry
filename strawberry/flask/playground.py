from os.path import abspath, dirname, join


def render_playground_page():
    dir_path = abspath(join(dirname(__file__), ".."))
    playground_html_file = f"{dir_path}/static/playground.html"

    html_string = None
    with open(playground_html_file, "r") as f:
        html_string = f.read()
    return html_string
