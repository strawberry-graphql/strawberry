import os
from collections import defaultdict

import pytest

import rich


class ExceptionsCollector:
    def __init__(self):
        self._info = defaultdict(list)

    def pytest_sessionfinish(self):
        """
        Hook for printing test info at the end of the run
        """

        html = ""

        for test, info in self._info.items():
            html += f"<h1>{test}</h1>"

            for datum in info:
                console = rich.console.Console(record=True)

                console.print(datum)

                # hti = Html2Image()

                # console.print(datum)
                html += console.export_svg()

                # hti.screenshot(html_str=html, save_as="red_page.png", size=(900, 400))

        summary_path = os.environ.get("GITHUB_STEP_SUMMARY", None)

        if summary_path:
            with open(summary_path, "w") as f:
                f.write(html)

    @pytest.fixture
    def collect_strawberry_exception(self, request):
        """
        Fixture to collect test information
        """

        def add_exception(exception):
            """
            Adds information about test
            """
            self._info[get_test_name(request)].append(exception)

        return add_exception


def get_test_name(request):
    """
    Get the name of test from pytest
    """
    return request.node.name


def pytest_configure(config):
    """Add plugin to pytest"""
    config.pluginmanager.register(ExceptionsCollector(), "exceptions_collector")
