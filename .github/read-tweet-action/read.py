import base64
import os
from pathlib import Path
from string import Template

import markdown
from bs4 import BeautifulSoup


changelog = os.environ["INPUT_CHANGELOG"]
version = os.environ.get("INPUT_VERSION", "(next)")
contributor = os.environ["INPUT_CONTRIBUTOR_NAME"]
release_url = f"https://github.com/strawberry-graphql/strawberry/releases/tag/{version}"

card_text = ""
tweet = """
🆕 Release $version is out! Thanks to $contributor for the PR 👏

Get it here 👉 $release_url
""".strip()

tweet_path = Path("./TWEET.md")
has_tweet_file = False

if tweet_path.exists():
    has_tweet_file = True

    with tweet_path.open(mode="r") as f:
        contents = f.read()

        tweet, _, card_text = [part.strip() for part in contents.partition("---")]

if not card_text:
    card_text = changelog
else:
    card_text = base64.b64encode(card_text.encode("utf-8")).decode("ascii")

tweet_template = Template(tweet)
tweet = tweet_template.substitute(
    contributor=contributor,
    version=version,
    release_url=release_url,
)


def convert_markdown_to_text(md: str) -> str:
    """Converts a markdown string to text to handle new lines in a nice way."""
    html = markdown.markdown(md)

    soup = BeautifulSoup(html, features="html.parser")

    for tag in soup.find_all():
        tag.replace_with(tag.text.replace("\n", " "))

    return soup.get_text(separator="\n\n", strip=True)


tweet = base64.b64encode(tweet.encode("utf-8")).decode("ascii")

print(f"::set-output name=tweet::{tweet}")
print(f"::set-output name=card-text::{card_text}")
print(f"::set-output name=has-tweet-file::{'true' if has_tweet_file else 'false'}")
