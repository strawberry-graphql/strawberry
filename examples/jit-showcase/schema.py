"""
GraphQL schema for a blog application.
Demonstrates async resolvers and complex nested queries.
"""

import asyncio
import random
from typing import List, Optional
from datetime import datetime

import strawberry


# Simulated database
class Database:
    """Simulated async database with realistic delays."""
    
    @staticmethod
    async def fetch_posts(limit: int = 10) -> List[dict]:
        """Simulate fetching posts from database."""
        await asyncio.sleep(0.01)  # 10ms database latency
        return [
            {
                "id": f"post-{i}",
                "title": f"Amazing Blog Post {i}",
                "content": f"This is the content of blog post {i}. It contains interesting information about various topics including technology, science, and culture. " * 3,
                "author_id": f"author-{i % 3}",
                "created_at": datetime.now().isoformat(),
                "view_count": random.randint(100, 10000),
            }
            for i in range(1, limit + 1)
        ]
    
    @staticmethod
    async def fetch_author(author_id: str) -> dict:
        """Simulate fetching author from database."""
        await asyncio.sleep(0.005)  # 5ms database latency
        return {
            "id": author_id,
            "name": ["Alice Johnson", "Bob Smith", "Charlie Brown"][int(author_id.split("-")[1]) % 3],
            "email": f"{author_id}@blog.com",
            "bio": f"Professional writer and blogger. Passionate about technology and innovation.",
            "posts_count": random.randint(10, 100),
        }
    
    @staticmethod
    async def fetch_comments(post_id: str, limit: int = 5) -> List[dict]:
        """Simulate fetching comments from database."""
        await asyncio.sleep(0.008)  # 8ms database latency
        return [
            {
                "id": f"comment-{post_id}-{i}",
                "post_id": post_id,
                "text": f"Great post! Really enjoyed reading about this topic. #{i}",
                "author_id": f"author-{(i + 5) % 10}",
                "likes": random.randint(0, 100),
                "created_at": datetime.now().isoformat(),
            }
            for i in range(1, min(limit + 1, 6))
        ]
    
    @staticmethod
    async def increment_views(post_id: str) -> int:
        """Simulate incrementing view count."""
        await asyncio.sleep(0.002)  # 2ms database latency
        return random.randint(100, 10000)


# GraphQL Types

@strawberry.type
class Author:
    id: str
    name: str
    email: str
    bio: str
    
    @strawberry.field
    async def posts_count(self) -> int:
        """Async field to get post count."""
        await asyncio.sleep(0.003)  # Simulate computation
        return random.randint(10, 100)
    
    @strawberry.field
    async def followers(self) -> int:
        """Async field to get follower count."""
        await asyncio.sleep(0.003)
        return random.randint(100, 10000)


@strawberry.type
class Comment:
    id: str
    text: str
    likes: int
    created_at: str
    
    def __init__(self, id: str, text: str, likes: int, created_at: str, author_id: str):
        self.id = id
        self.text = text
        self.likes = likes
        self.created_at = created_at
        self._author_id = author_id
    
    @strawberry.field
    async def author(self) -> Author:
        """Async resolver to fetch comment author."""
        data = await Database.fetch_author(self._author_id)
        return Author(**{k: v for k, v in data.items() if k != 'posts_count'})
    
    @strawberry.field
    async def is_recent(self) -> bool:
        """Check if comment is recent."""
        await asyncio.sleep(0.001)
        return True


@strawberry.type
class Post:
    id: str
    title: str
    content: str
    created_at: str
    
    def __init__(self, id: str, title: str, content: str, created_at: str, author_id: str, view_count: int):
        self.id = id
        self.title = title
        self.content = content
        self.created_at = created_at
        self._author_id = author_id
        self._view_count = view_count
    
    @strawberry.field
    async def author(self) -> Author:
        """Async resolver to fetch post author."""
        data = await Database.fetch_author(self._author_id)
        return Author(**{k: v for k, v in data.items() if k != 'posts_count'})
    
    @strawberry.field
    async def comments(self, limit: int = 5) -> List[Comment]:
        """Async resolver to fetch post comments."""
        comments_data = await Database.fetch_comments(self.id, limit)
        return [
            Comment(
                id=c["id"],
                text=c["text"],
                likes=c["likes"],
                created_at=c["created_at"],
                author_id=c["author_id"]
            )
            for c in comments_data
        ]
    
    @strawberry.field
    async def view_count(self) -> int:
        """Async field that increments and returns view count."""
        return await Database.increment_views(self.id)
    
    @strawberry.field
    def word_count(self) -> int:
        """Sync field to count words."""
        return len(self.content.split())
    
    @strawberry.field
    async def related_posts(self, limit: int = 3) -> List["Post"]:
        """Fetch related posts."""
        await asyncio.sleep(0.01)
        posts_data = await Database.fetch_posts(limit)
        return [
            Post(
                id=p["id"],
                title=p["title"],
                content=p["content"],
                created_at=p["created_at"],
                author_id=p["author_id"],
                view_count=p["view_count"]
            )
            for p in posts_data
        ]


@strawberry.type
class Query:
    @strawberry.field
    async def posts(self, limit: int = 10, offset: int = 0) -> List[Post]:
        """Fetch blog posts with pagination."""
        posts_data = await Database.fetch_posts(limit)
        return [
            Post(
                id=p["id"],
                title=p["title"],
                content=p["content"],
                created_at=p["created_at"],
                author_id=p["author_id"],
                view_count=p["view_count"]
            )
            for p in posts_data
        ]
    
    @strawberry.field
    async def post(self, id: str) -> Optional[Post]:
        """Fetch a single post by ID."""
        posts_data = await Database.fetch_posts(1)
        if posts_data:
            p = posts_data[0]
            p["id"] = id  # Use requested ID
            return Post(
                id=p["id"],
                title=p["title"],
                content=p["content"],
                created_at=p["created_at"],
                author_id=p["author_id"],
                view_count=p["view_count"]
            )
        return None
    
    @strawberry.field
    async def featured_post(self) -> Post:
        """Get the featured post."""
        await asyncio.sleep(0.005)
        return Post(
            id="featured",
            title="Featured: The Future of GraphQL",
            content="An in-depth look at GraphQL's evolution and what's coming next...",
            created_at=datetime.now().isoformat(),
            author_id="author-0",
            view_count=50000
        )
    
    @strawberry.field
    async def top_authors(self, limit: int = 5) -> List[Author]:
        """Get top authors by post count."""
        await asyncio.sleep(0.01)
        authors = []
        for i in range(limit):
            data = await Database.fetch_author(f"author-{i}")
            authors.append(Author(**{k: v for k, v in data.items() if k != 'posts_count'}))
        return authors
    
    @strawberry.field
    async def search_posts(self, query: str, limit: int = 10) -> List[Post]:
        """Search posts by title or content."""
        await asyncio.sleep(0.02)  # Simulate search
        posts_data = await Database.fetch_posts(limit)
        return [
            Post(
                id=p["id"],
                title=f"{query}: {p['title']}",
                content=p["content"],
                created_at=p["created_at"],
                author_id=p["author_id"],
                view_count=p["view_count"]
            )
            for p in posts_data
        ]


# Create the schema
schema = strawberry.Schema(Query)