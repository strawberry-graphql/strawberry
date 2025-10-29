"""Count how many times each type of async resolver is called."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "examples" / "jit-showcase"))

from schema import Query  # type: ignore

# Analyze the data
root = Query()
posts = root.posts(limit=10)
print(f"Number of posts: {len(posts)}")

total_authors = 0
total_comments = 0
total_comment_authors = 0

for post in posts:
    # Each post has 1 author
    total_authors += 1

    # Each post has some comments
    comments = post.comments(limit=5)
    total_comments += len(comments)

    # Each comment has 1 author
    total_comment_authors += len(comments)

print("\nAsync resolver calls per query:")
print("  posts(): 1")
print(f"  post.author(): {total_authors}")
print(f"  post.comments(): {total_authors}")
print(f"  comment.author(): {total_comment_authors}")
print("  featuredPost(): 1")
print(f"  TOTAL: {1 + total_authors + total_authors + total_comment_authors + 1}")

# Plus viewCount and postsCount
print("\nAdditional async calls:")
print(f"  author.postsCount(): {total_authors}")
print("  featuredPost.viewCount(): 1")
print(
    f"  GRAND TOTAL: {1 + total_authors + total_authors + total_comment_authors + 1 + total_authors + 1}"
)
