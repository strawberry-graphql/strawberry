from typing import Tuple


def pytest_emoji_xfailed(config) -> Tuple[str, str]:
    return "🤷‍♂️ ", "XFAIL 🤷‍♂️ "


pytest_plugins = ("tests.plugins.strawberry_exceptions",)
