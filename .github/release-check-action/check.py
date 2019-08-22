import json
import pathlib
import sys

from comment_templates import (
    INVALID_RELEASE_FILE,
    MISSING_RELEASE_FILE,
    RELEASE_FILE_ADDED,
)
from config import GITHUB_EVENT_PATH, GITHUB_WORKSPACE, RELEASE_FILE_PATH
from github import add_or_edit_comment, update_labels
from release import InvalidReleaseFileError, get_release_info


with open(GITHUB_EVENT_PATH) as f:
    event_data = json.load(f)


release_file = pathlib.Path(GITHUB_WORKSPACE) / RELEASE_FILE_PATH

exit_code = 0

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


add_or_edit_comment(event_data, comment)
update_labels(event_data, exit_code == 0)

sys.exit(exit_code)
