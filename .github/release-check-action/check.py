import base64
import json
import os
import pathlib
import sys

from config import GITHUB_EVENT_PATH, GITHUB_WORKSPACE, RELEASE_FILE_PATH
from github import get_changed_files
from release import InvalidReleaseFileError, get_release_info


with open(GITHUB_EVENT_PATH) as f:
    event_data = json.load(f)

sender = event_data["pull_request"]["user"]["login"]

if sender in [
    "dependabot-preview[bot]",
    "dependabot-preview",
    "dependabot",
    "dependabot[bot]",
]:
    print("Skipping dependencies PRs for now.")
    print("::set-output name=skip::true")
    sys.exit(0)


# Check the file that have changed
changed_files = get_changed_files(
    base=os.environ["GITHUB_BASE_REF"], head=os.environ["GITHUB_SHA"]
)
lib_has_changed = False

for filename in changed_files:
    if filename.startswith("strawberry"):
        lib_has_changed = True
        break

if not lib_has_changed:
    print("No library files have changed so skipping...")
    print("::set-output name=skip::true")
    sys.exit(0)

release_file = pathlib.Path(GITHUB_WORKSPACE) / RELEASE_FILE_PATH

exit_code = 0
release_info = None
status = "MISSING"

if not release_file.exists():
    status = "MISSING"

    exit_code = 1
else:
    try:
        info = get_release_info(release_file)
        release_info = {
            "changeType": info.change_type.name,
            "changelog": info.changelog,
        }

        status = "OK"
    except InvalidReleaseFileError:
        exit_code = 2
        status = "INVALID"


print(f"Status is {status}")
print(f"::set-output name=release_status::{status}")

if release_info:
    changelog = release_info["changelog"]
    encoded_changelog = base64.b64encode(changelog.encode("utf-8")).decode("ascii")

    print(f"::set-output name=changelog::{encoded_changelog}")
    print(f"::set-output name=change_type::{info.change_type.name}")
else:
    print('::set-output name=changelog::""')


sys.exit(exit_code)
