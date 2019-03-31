import pathlib


def get_playground_template(request_path: str) -> str:
    here = pathlib.Path(__file__).parents[1]
    templates_path = here / "templates"

    with open(templates_path / "playground.html") as f:
        template = f.read()

    return template.replace("{{REQUEST_PATH}}", request_path)
