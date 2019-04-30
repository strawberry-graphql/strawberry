import sys
import os

sys.path.append(os.path.dirname(__file__))  # noqa

from base import (
    get_project_version,
    git,
    configure_git,
    PROJECT_TOML_FILE_NAME,
    CHANGELOG_FILE_NAME,
    RELEASE_FILE_NAME,
)


if __name__ == "__main__":
    configure_git()

    version = get_project_version()

    git(["add", PROJECT_TOML_FILE_NAME])
    git(["add", CHANGELOG_FILE_NAME])
    git(["rm", RELEASE_FILE_NAME])

    git(["commit", "-m", f"Release 🍓 {version}"])
    git(["push", "origin", "HEAD"])
