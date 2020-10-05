import json
import pathlib
import sys

import httpx
from config import API_URL, GITHUB_EVENT_PATH, GITHUB_WORKSPACE, RELEASE_FILE_PATH
from release import InvalidReleaseFileError, get_release_info


with open(GITHUB_EVENT_PATH) as f:
    event_data = json.load(f)

sender = event_data["pull_request"]["user"]["login"]

if sender in ["dependabot-preview[bot]", "dependabot-preview", "dependabot"]:
    print("Skipping dependencies PRs for now.")
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

mutation = """mutation AddReleaseComment($input: AddReleaseFileCommentInput!) {
  addReleaseFileComment(input: $input)
}"""

mutation_input = {
    "prNumber": event_data["number"],
    "status": status,
    "releaseInfo": release_info,
}


response = httpx.post(
    API_URL,
    json={"query": mutation, "variables": {"input": mutation_input}},
    timeout=120,
)
response.raise_for_status()

print(f"Status is {status}")
sys.exit(exit_code)
