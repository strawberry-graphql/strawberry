import pathlib


def pytest_emoji_xfailed(config):
    return "🤷‍♂️ ", "XFAIL 🤷‍♂️ "


def pytest_collection_modifyitems(config, items):
    # automatically mark tests with the appropriate subfolder marker

    rootdir = pathlib.Path(config.rootdir)

    for item in items:
        rel_path = pathlib.Path(item.fspath).relative_to(rootdir).parts

        if rel_path[0] == "tests" and len(rel_path) >= 2:
            subfolder = rel_path[1]
            if subfolder == "asgi":
                item.add_marker("asgi")
                item.add_marker("starlette")
            else:
                item.add_marker(subfolder)
