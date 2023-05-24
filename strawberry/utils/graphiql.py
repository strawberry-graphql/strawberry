import json
import pathlib
from typing import Optional

DEFAULT_EXAMPLE_QUERY = """# Welcome to GraphiQL 🍓
#
# GraphiQL is an in-browser tool for writing, validating, and
# testing GraphQL queries.
#
# Type queries into this side of the screen, and you will see intelligent
# typeaheads aware of the current GraphQL type schema and live syntax and
# validation errors highlighted within the text.
#
# GraphQL queries typically start with a "{" character. Lines that starts
# with a # are ignored.
#
# An example GraphQL query might look like:
#
#     {
#       field(arg: "value") {
#         subField
#       }
#     }
#
# Keyboard shortcuts:
#
#       Run Query:  Ctrl-Enter (or press the play button above)
#
#   Auto Complete:  Ctrl-Space (or just start typing)
#
"""


def get_graphiql_html(
    subscription_enabled: bool = True,
    replace_variables: bool = True,
    example_query: Optional[str] = DEFAULT_EXAMPLE_QUERY,
) -> str:
    here = pathlib.Path(__file__).parents[1]
    path = here / "static/graphiql.html"

    template = path.read_text(encoding="utf-8")

    if replace_variables:
        template = template.replace(
            "{{ SUBSCRIPTION_ENABLED }}", json.dumps(subscription_enabled)
        )
        template = template.replace(
            "{{ EXAMPLE_QUERY }}", json.dumps(example_query)[1:-1]
        )

    return template
