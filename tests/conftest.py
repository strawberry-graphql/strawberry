import pathlib
import sys
from typing import Any, List, Tuple

import graphql
import pytest


def pytest_emoji_xfailed(config: pytest.Config) -> Tuple[str, str]:
    return "🤷‍♂️ ", "XFAIL 🤷‍♂️ "


def pytest_emoji_skipped(config: pytest.Config) -> Tuple[str, str]:
    return "🦘 ", "SKIPPED 🦘"


pytest_plugins = ("tests.plugins.strawberry_exceptions",)


@pytest.hookimpl  # type: ignore
def pytest_collection_modifyitems(config: pytest.Config, items: List[pytest.Item]):
    rootdir = pathlib.Path(config.rootdir)  # type: ignore

    for item in items:
        rel_path = pathlib.Path(item.fspath).relative_to(rootdir)

        markers = [
            "aiohttp",
            "asgi",
            "chalice",
            "channels",
            "django",
            "fastapi",
            "flask",
            "quart",
            "pydantic",
            "sanic",
            "starlite",
            "litestar",
        ]

        for marker in markers:
            if marker in rel_path.parts:
                item.add_marker(getattr(pytest.mark, marker))


@pytest.hookimpl
def pytest_ignore_collect(
    collection_path: pathlib.Path, path: Any, config: pytest.Config
):
    if sys.version_info < (3, 12) and "python_312" in collection_path.parts:
        return True

    markers = config.getoption("-m")

    # starlite has some issues with pydantic 2, which we
    # use in our dev deps, so we skip starlite unless
    # we're running the tests for it
    if "starlite" not in markers and "starlite" in collection_path.parts:
        return True


IS_GQL_32 = "3.3" not in graphql.__version__


def skip_if_gql_32(reason: str) -> pytest.MarkDecorator:
    return pytest.mark.skipif(
        IS_GQL_32,
        reason=reason,
    )
