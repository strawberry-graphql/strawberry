import contextlib
import os
import re
from collections import defaultdict
from typing import DefaultDict, Generator, Tuple

import pytest

import rich
import rich.console
from _pytest.nodes import Item
from pluggy._result import _Result

from strawberry.exceptions import StrawberryException


@contextlib.contextmanager
def suppress_output(verbosity_level: int = 0) -> Generator[None, None, None]:
    if verbosity_level >= 2:
        yield

        return

    with open(os.devnull, "w") as devnull:
        with contextlib.redirect_stdout(devnull):
            yield


class StrawberryExceptionsPlugin:
    def __init__(self, verbosity_level: int) -> None:
        self._info: DefaultDict[Tuple[str, str], list] = defaultdict(list)
        self.verbosity_level = verbosity_level

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

        if not issubclass(exception, StrawberryException):
            pytest.fail(f"{exception} is not a StrawberryException")

        raised_exception = outcome.excinfo[1] if outcome.excinfo else None

        # This plugin needs to work around the other hooks, see:
        # https://docs.pytest.org/en/7.1.x/how-to/writing_hook_functions.html#hookwrapper-executing-around-other-hooks
        outcome.force_result(None)

        if raised_exception is None:
            failure_message = f"Expected exception {exception}, but it did not raise"

            pytest.fail(failure_message, pytrace=False)

        self._collect_exception(raised_exception)

        if not isinstance(raised_exception, exception):
            failure_message = (
                f"Expected exception {exception}, but raised {raised_exception}"
            )

            pytest.fail(failure_message, pytrace=False)

        raised_message = str(raised_exception)

        if match is not None and not re.match(match, raised_message):
            failure_message = (
                f'"{match}" does not match raised message "{raised_message}"'
            )

            if self.verbosity_level >= 1:
                print("Exception", exception)

            pytest.fail(failure_message, pytrace=False)

    def _collect_exception(self, raised_exception: StrawberryException) -> None:
        console = rich.console.Console(record=True)

        with suppress_output(self.verbosity_level):
            console.print(raised_exception, soft_wrap=True)

        exception_text = console.export_text()

        if exception_text.strip() == "None":
            text = "No exception raised\n"
        else:
            text = f"\n\n``````\n{exception_text}\n``````\n\n"

        self._info[
            raised_exception.__class__.__name__, raised_exception.documentation_url
        ].append(text)

    def pytest_sessionfinish(self):
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY", None)

        if not summary_path:
            return

        markdown = ""

        for test, info in self._info.items():
            test_name, documentation_url = test
            test_name = " ".join(re.findall("[a-zA-Z][^A-Z]*", test_name))

            markdown += f"# {test_name}\n\n"
            markdown += f"Documentation URL: {documentation_url}\n"

            markdown += "\n".join(info)

        with open(summary_path, "w") as f:
            f.write(markdown)


def pytest_configure(config):
    config.pluginmanager.register(
        StrawberryExceptionsPlugin(verbosity_level=config.getoption("verbose")),
        "strawberry_exceptions",
    )

    config.addinivalue_line(
        "markers",
        "raises_strawberry_exception: expect to raise a strawberry exception.",
    )
