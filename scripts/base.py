import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(
    subprocess.check_output(["git", "rev-parse", "--show-toplevel"])
    .decode("ascii")
    .strip()
)
PROJECT_NAME = "Strawberry"

# Files configuration

RELEASE_FILE_NAME = "RELEASE.md"
RELEASE_FILE = ROOT / RELEASE_FILE_NAME

PROJECT_TOML_FILE_NAME = "pyproject.toml"
PROJECT_TOML_FILE = ROOT / PROJECT_TOML_FILE_NAME

CHANGELOG_FILE_NAME = "CHANGELOG.md"
CHANGELOG_FILE = ROOT / CHANGELOG_FILE_NAME

# Git configuration

GIT_USERNAME = "Botberry"
GIT_EMAIL = "bot@strawberry.rocks"


def run_process(popenargs):
    return subprocess.check_output(popenargs).decode("ascii").strip()


def git(popenargs):
    # avoid decode ascii for the commit message
    return subprocess.check_output(["git", *popenargs])


def check_exit_code(popenargs):
    return subprocess.call(popenargs, shell=True)


def get_project_version():
    VERSION_REGEX = re.compile(r"^version\s*=\s*\"(?P<version>\d+\.\d+\.\d+)\"$")

    with open(PROJECT_TOML_FILE) as f:
        for line in f:
            match = VERSION_REGEX.match(line)

            if match:
                return match.group("version")

    return None


def get_release_info(file_path=RELEASE_FILE):
    RELEASE_TYPE_REGEX = re.compile(r"^[Rr]elease [Tt]ype: (major|minor|patch)$")

    with open(file_path, "r") as f:
        line = f.readline()
        match = RELEASE_TYPE_REGEX.match(line)

        if not match:
            print(
                "The file RELEASE.md should start with `Release type` "
                "and specify one of the following values: major, minor or patch."
            )
            sys.exit(1)

        type_ = match.group(1)
        changelog = "".join([line for line in f.readlines()]).strip()

    return type_, changelog


def configure_git():
    git(["config", "user.name", GIT_USERNAME])
    git(["config", "user.email", GIT_EMAIL])
