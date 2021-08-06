# TODO: improve this to support multiple commands
import os

import httpx


API_URL = os.environ["BOT_API_URL"]
API_TOKEN = os.environ["API_SECRET"]


mutation = """mutation AddReleaseComment($input: AddReleaseFileCommentInput!) {
  addReleaseFileComment(input: $input)
}"""


release_info = None

if os.environ["INPUT_STATUS"] == "OK":
    release_info = {
        "changeType": os.environ["INPUT_CHANGE_TYPE"],
        "changelog": os.environ["INPUT_CHANGELOG"].replace(r"\`", "`"),
    }

mutation_input = {
    "prNumber": int(os.environ["INPUT_PR_NUMBER"]),
    "status": os.environ["INPUT_STATUS"],
    "releaseCardUrl": os.environ["INPUT_RELEASE_CARD_URL"],
    "releaseInfo": release_info,
}

response = httpx.post(
    API_URL,
    json={"query": mutation, "variables": {"input": mutation_input}},
    headers={"Authorization": f"Bearer {API_TOKEN}"},
    timeout=120,
)
response.raise_for_status()

response_data = response.json()

if "errors" in response_data:
    raise RuntimeError(f"Response contained errors: {response_data['errors']}")

print(response_data)
