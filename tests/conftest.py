import pathlib
import sys

import pytest


def pytest_emoji_xfailed(config: pytest.Config) -> tuple[str, str]:
    return "🤷‍♂️ ", "XFAIL 🤷‍♂️ "


def pytest_emoji_skipped(config: pytest.Config) -> tuple[str, str]:
    return "🦘 ", "SKIPPED 🦘"


pytest_plugins = ("tests.plugins.strawberry_exceptions",)


@pytest.hookimpl  # type: ignore
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
    rootdir = pathlib.Path(config.rootdir)  # type: ignore

    for item in items:
        rel_path = pathlib.Path(item.path).relative_to(rootdir)

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
            "litestar",
        ]

        for marker in markers:
            if marker in rel_path.parts:
                item.add_marker(getattr(pytest.mark, marker))


@pytest.hookimpl
def pytest_ignore_collect(collection_path: pathlib.Path, config: pytest.Config):
    if sys.version_info < (3, 12) and "python_312" in collection_path.parts:
        return True
    return None
