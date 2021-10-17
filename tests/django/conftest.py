import pathlib

import pytest


def pytest_collection_modifyitems(config, items):
    # automatically mark tests with 'django' if they are in the django subfolder

    rootdir = pathlib.Path(config.rootdir)

    for item in items:
        rel_path = pathlib.Path(item.fspath).relative_to(rootdir)

        if rel_path.is_relative_to("tests/django"):
            item.add_marker(pytest.mark.django)
