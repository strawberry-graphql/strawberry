import datetime
import json
from json import JSONEncoder
from typing import Any, Dict, Optional


class StrawberryJSONEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        return repr(o)


def pretty_print_graphql_operation(
    operation_name: Optional[str],
    query: str,
    variables: Optional[Dict["str", Any]],
):
    """Pretty print a GraphQL operation using pygments.

    Won't print introspection operation to prevent noise in the output.
    """
    try:
        pass
    except ImportError as e:
        raise ImportError(
            "pygments is not installed but is required for debug output, install it "
            "directly or run `pip install strawberry-graphql[debug-server]`",
        ) from e

    if operation_name == "IntrospectionQuery":
        return

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if variables:
        variables_json = json.dumps(variables, indent=4, cls=StrawberryJSONEncoder)
