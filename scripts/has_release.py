import sys
import os

sys.path.append(os.path.dirname(__file__))  # noqa

from base import run_process, RELEASE_FILE


if __name__ == "__main__":
    if not os.path.exists(RELEASE_FILE):
        print("Not releasing a new version because there isn't a RELEASE.md file.")
        run_process(["circleci", "step", "halt"])
