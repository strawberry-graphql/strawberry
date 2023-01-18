import base64
import pathlib

from config import GITHUB_WORKSPACE, RELEASE_FILE_PATH
from release import InvalidReleaseFileError, get_release_info

release_file = pathlib.Path(GITHUB_WORKSPACE) / RELEASE_FILE_PATH

release_info = None
status = "MISSING"

if not release_file.exists():
    status = "MISSING"
else:
    try:
        info = get_release_info(release_file)
        release_info = {
            "changeType": info.change_type.name,
            "changelog": info.changelog,
        }

        status = "OK"
    except InvalidReleaseFileError:
        status = "INVALID"


if release_info:
    changelog = release_info["changelog"]
    encoded_changelog = base64.b64encode(changelog.encode("utf-8")).decode("ascii")

else:
    pass
