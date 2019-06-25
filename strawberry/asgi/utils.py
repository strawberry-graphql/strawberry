import pathlib


def get_playground_html(request_path: str) -> str:
    here = pathlib.Path(__file__).parents[1]
    path = here / "static/playground.html"

    with open(path) as f:
        template = f.read()

    return template.replace("{{REQUEST_PATH}}", request_path)
