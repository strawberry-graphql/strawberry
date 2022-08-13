import os
import re
from collections import defaultdict
from typing import Generator

import pytest

import rich
from _pytest.nodes import Item
from pluggy._result import _Result


class StrawberryExceptionsPlugin:
    def __init__(self):
        self._info = defaultdict(list)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item: Item) -> Generator[None, _Result, None]:
        __tracebackhide__ = True

        outcome = yield

        self._check_strawberry_exception(item, outcome)

    def _check_strawberry_exception(self, item: Item, outcome: _Result) -> None:
        __tracebackhide__ = True

        raises_marker = item.get_closest_marker("raises_strawberry_exception")

        if raises_marker is None:
            return

        exception = raises_marker.args[0]
        match = raises_marker.kwargs.get("match", None)

        # TODO: check if exception is a StrawberryException

        raised_exception = outcome.excinfo[1] if outcome.excinfo else None

        # This plugin needs to work around the other hooks, see:
        # https://docs.pytest.org/en/7.1.x/how-to/writing_hook_functions.html#hookwrapper-executing-around-other-hooks
        outcome.force_result(None)

        if raised_exception is None:
            failure_message = "Expected exception {}, but it did not raise".format(
                exception
            )

            pytest.fail(failure_message, pytrace=False)

        if not isinstance(raised_exception, exception):
            failure_message = "Expected exception {}, but raised {}".format(
                exception, raised_exception
            )

            pytest.fail(failure_message, pytrace=False)

        raised_message = str(raised_exception)
        failure_message = None

        if match is not None and not re.match(match, raised_message):
            failure_message = '"{}" does not match raised message "{}"'.format(
                match, raised_message
            )

            pytest.fail(failure_message, pytrace=False)

        self._info[exception.__class__.__name__].append(raised_exception)

    def pytest_sessionfinish(self):
        markdown = ""

        for test, info in self._info.items():
            markdown += f"# {test}\n"

            for exception in info:

                if exception is None:
                    markdown += "No exception raised\n"
                else:
                    console = rich.console.Console(record=True)
                    # TODO: only print to user's console when enabled via a flag
                    console.print(exception)

                    exception_text = console.export_text()

                    if "None" in str(exception_text):
                        markdown += "No exception raised\n"
                    else:
                        markdown += f"\n\n``````\n{exception_text}\n``````"

        summary_path = os.environ.get("GITHUB_STEP_SUMMARY", None)

        if summary_path:
            with open(summary_path, "w") as f:
                f.write(markdown)


def pytest_configure(config):
    # def pytest_configure(config):
    config.pluginmanager.register(StrawberryExceptionsPlugin(), "strawberry_exceptions")

    config.addinivalue_line(
        "markers",
        "raises_strawberry_exception: expect to raise a strawberry exception.",
    )
