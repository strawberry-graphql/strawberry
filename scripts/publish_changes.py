import os
import sys

from base import (
    CHANGELOG_FILE_NAME,
    PROJECT_TOML_FILE_NAME,
    RELEASE_FILE_NAME,
    configure_git,
    get_project_version,
    git,
)


sys.path.append(os.path.dirname(__file__))  # noqa


if __name__ == "__main__":
    configure_git()

    version = get_project_version()

    git(["add", PROJECT_TOML_FILE_NAME])
    git(["add", CHANGELOG_FILE_NAME])
    git(["rm", "--cached", RELEASE_FILE_NAME])

    git(["commit", "-m", f"Release 🍓 {version}"])
    git(["push", "origin", "HEAD"])
