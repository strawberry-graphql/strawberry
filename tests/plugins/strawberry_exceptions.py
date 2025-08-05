import contextlib
import os
import re
from collections import defaultdict
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path

import pytest
import rich
import rich.console
from _pytest.nodes import Item
from pluggy._result import _Result
from rich.traceback import Traceback

from strawberry.exceptions import StrawberryException, UnableToFindExceptionSource

WORKSPACE_FOLDER = Path(__file__).parents[2]
DOCS_FOLDER = WORKSPACE_FOLDER / "docs/errors"


@dataclass
class Result:
    text: str
    raised_exception: StrawberryException


@contextlib.contextmanager
def suppress_output(verbosity_level: int = 0) -> Generator[None, None, None]:
    if verbosity_level >= 2:
        yield

        return

    with (
        Path(os.devnull).open("w", encoding="utf-8") as devnull,
        contextlib.redirect_stdout(devnull),
    ):
        yield


class StrawberryExceptionsPlugin:
    def __init__(self, verbosity_level: int) -> None:
        self._info: defaultdict[type[StrawberryException], list[Result]] = defaultdict(
            list
        )
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

        if not isinstance(raised_exception, exception):
            failure_message = (
                f"Expected exception {exception}, but raised {raised_exception}"
            )

            raise raised_exception

        raised_message = str(raised_exception)

        self._collect_exception(item.name, raised_exception)

        if match is not None and not re.match(match, raised_message):
            failure_message = (
                f'"{match}" does not match raised message "{raised_message}"'
            )

            if self.verbosity_level >= 1:
                print(f"Exception: {exception}")  # noqa: T201

            pytest.fail(failure_message, pytrace=False)

    def _collect_exception(
        self, test_name: str, raised_exception: StrawberryException
    ) -> None:
        console = rich.console.Console(record=True, width=120)

        with suppress_output(self.verbosity_level):
            try:
                console.print(raised_exception)
            except UnableToFindExceptionSource:
                traceback = Traceback(
                    Traceback.extract(
                        raised_exception.__class__,
                        raised_exception,
                        raised_exception.__traceback__,
                    ),
                    max_frames=10,
                )
                console.print(traceback)

        exception_text = console.export_text()

        text = f"## {test_name}\n"

        if exception_text.strip() == "None":
            text += "No exception raised\n"
        else:
            text += f"\n``````\n{exception_text.strip()}\n``````\n\n"

        documentation_path = DOCS_FOLDER / f"{raised_exception.documentation_path}.md"

        if not documentation_path.exists():
            pytest.fail(
                f"{documentation_path.relative_to(WORKSPACE_FOLDER)} does not exist",
                pytrace=False,
            )

        self._info[raised_exception.__class__].append(
            Result(text=text, raised_exception=raised_exception)
        )

    def pytest_sessionfinish(self):
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY", None)

        if not summary_path:
            return

        markdown = ""

        for exception_class, info in self._info.items():
            title = " ".join(re.findall("[a-zA-Z][^A-Z]*", exception_class.__name__))

            markdown += f"# {title}\n\n"
            markdown += (
                f"Documentation URL: {info[0].raised_exception.documentation_url}\n\n"
            )

            markdown += "\n".join([result.text for result in info])

        with Path(summary_path).open("w") as f:
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
