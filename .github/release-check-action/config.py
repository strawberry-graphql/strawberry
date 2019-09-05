import os


RELEASE_FILE_PATH = "RELEASE.md"
GITHUB_SHA = os.environ["GITHUB_SHA"]
GITHUB_EVENT_PATH = os.environ["GITHUB_EVENT_PATH"]
GITHUB_WORKSPACE = os.environ["GITHUB_WORKSPACE"]
API_URL = "https://gentle-beach-72400.herokuapp.com/graphql"
