# TODO: improve this to support multiple commands
import os

import httpx


API_URL = "https://strawberry-bot-r3o3etjz6a-ew.a.run.app/graphql"


mutation = """mutation AddReleaseComment($input: AddReleaseFileCommentInput!) {
  addReleaseFileComment(input: $input)
}"""


mutation_input = {
    "prNumber": int(os.environ["INPUT_PR_NUMBER"]),
    "status": os.environ["INPUT_STATUS"],
    "releaseInfo": {
        "changeType": os.environ["INPUT_CHANGE_TYPE"],
        "changelog": os.environ["INPUT_CHANGELOG"],
    },
}

response = httpx.post(
    API_URL,
    json={"query": mutation, "variables": {"input": mutation_input}},
    timeout=120,
)
response.raise_for_status()

response_data = response.json()

if "errors" in response_data:
    raise RuntimeError(f"Response contained errors: {response_data['errors']}")
