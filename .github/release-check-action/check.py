import json
import pathlib
import sys

from comment_templates import (
    INVALID_RELEASE_FILE,
    MISSING_RELEASE_FILE,
    RELEASE_FILE_ADDED,
)
from config import GITHUB_EVENT_PATH, GITHUB_TOKEN, GITHUB_WORKSPACE, RELEASE_FILE_PATH
from github import add_or_edit_comment, update_labels
from release import InvalidReleaseFileError, get_release_info


with open(GITHUB_EVENT_PATH) as f:
    event_data = json.load(f)


sender = event_data["sender"]["login"]

if sender in ["dependabot-preview", "dependabot"]:
    print("Skipping dependencies PRs for now.")
    sys.exit(0)

release_file = pathlib.Path(GITHUB_WORKSPACE) / RELEASE_FILE_PATH

exit_code = 0
release_info = None

if not release_file.exists():
    print("release file does not exist")

    exit_code = 1
    comment = MISSING_RELEASE_FILE
else:
    try:
        release_info = get_release_info(release_file)

        comment = RELEASE_FILE_ADDED.format(changelog_preview=release_info.changelog)
    except InvalidReleaseFileError:
        exit_code = 2
        comment = INVALID_RELEASE_FILE

if GITHUB_TOKEN != "":
    add_or_edit_comment(event_data, comment)
    update_labels(event_data, release_info)
else:
    print("No GitHub token set, skipping sending a comment")
    print(comment)

sys.exit(exit_code)
