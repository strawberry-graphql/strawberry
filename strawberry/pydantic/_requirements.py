"""Check that a supported version of pydantic is installed.

This module is imported first by `strawberry.pydantic`, so users get a clear
error instead of failures deeper in the integration.
"""

import re

try:
    import pydantic
except ModuleNotFoundError as exc:
    if exc.name != "pydantic":
        raise

    raise ModuleNotFoundError(
        "strawberry.pydantic requires pydantic. "
        "Install it with `pip install 'strawberry-graphql[pydantic]'`.",
        name="pydantic",
    ) from exc


def _check_pydantic_version() -> None:
    match = re.match(r"(\d+)\.(\d+)", pydantic.VERSION)
    version = (int(match[1]), int(match[2])) if match else (0, 0)

    # pydantic inputs are validated with `model_validate(by_name=True)`, which
    # was added in pydantic 2.11
    if version < (2, 11):
        raise ImportError(
            "strawberry.pydantic requires pydantic>=2.11, but pydantic "
            f"{pydantic.VERSION} is installed. "
            "Upgrade it with `pip install -U 'pydantic>=2.11'`."
        )


_check_pydantic_version()
