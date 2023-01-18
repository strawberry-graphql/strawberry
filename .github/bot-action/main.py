# TODO: improve this to support multiple commands
import base64
import os

import httpx

API_URL = os.environ["BOT_API_URL"]
API_TOKEN = os.environ["API_SECRET"]


mutation = """mutation AddReleaseComment($input: AddReleaseFileCommentInput!) {
  addReleaseFileComment(input: $input)
}"""


release_info = None

if os.environ["INPUT_STATUS"] == "OK":
    changelog = base64.b64decode(os.environ["INPUT_CHANGELOG_BASE64"]).decode("utf-8")

    release_info = {
        "changeType": os.environ["INPUT_CHANGE_TYPE"],
        "changelog": changelog,
    }

if tweet := os.environ.get("INPUT_TWEET"):
    tweet = base64.b64decode(tweet).decode("utf-8")


mutation_input = {
    "prNumber": int(os.environ["INPUT_PR_NUMBER"]),
    "status": os.environ["INPUT_STATUS"],
    "releaseCardUrl": os.environ["INPUT_RELEASE_CARD_URL"],
    "tweet": tweet,
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
