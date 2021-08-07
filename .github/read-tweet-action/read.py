import base64
import os
from pathlib import Path


changelog = os.environ["INPUT_CHANGELOG"]
card_text = ""
tweet = ""

tweet_path = Path("./TWEET.md")

if tweet_path.exists():
    with tweet_path.open(mode="r") as f:
        contents = f.read()

        tweet, _, card_text = [part.strip() for part in contents.partition("---")]

if not card_text:
    card_text = changelog
else:
    card_text = base64.b64encode(card_text.encode("utf-8")).decode("ascii")

tweet = base64.b64encode(tweet.encode("utf-8")).decode("ascii")

print(f"::set-output name=tweet::{tweet}")
print(f"::set-output name=card_text::{card_text}")
