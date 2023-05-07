from typing import Tuple


def pytest_emoji_xfailed(config) -> Tuple[str, str]:
    return "🤷‍♂️ ", "XFAIL 🤷‍♂️ "


def pytest_emoji_skipped(config) -> Tuple[str, str]:
    return "🦘 ", "SKIPPED 🦘"


pytest_plugins = ("tests.plugins.strawberry_exceptions",)
