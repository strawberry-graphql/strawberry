import os
import sys

from base import RELEASE_FILE, run_process


sys.path.append(os.path.dirname(__file__))  # noqa


if __name__ == "__main__":
    if not os.path.exists(RELEASE_FILE):
        print("Not releasing a new version because there isn't a RELEASE.md file.")
        run_process(["circleci", "step", "halt"])
