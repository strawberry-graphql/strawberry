import pathlib
from typing import List, Tuple

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

        if "pydantic" in rel_path.parts:
            item.add_marker(pytest.mark.pydantic)
