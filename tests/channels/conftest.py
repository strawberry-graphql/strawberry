from pathlib import Path

import pytest


def pytest_collection_modifyitems(config, items):
    # automatically mark tests with 'channels' if they are in the channels subfolder

    rootdir = Path(config.rootdir)

    for item in items:
        rel_path = Path(item.fspath).relative_to(rootdir)

        if str(rel_path).startswith("tests/channels"):
            item.add_marker(pytest.mark.channels)
