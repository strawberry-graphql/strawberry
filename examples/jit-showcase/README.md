# Strawberry JIT Compiler Showcase 🚀

This example demonstrates the powerful JIT (Just-In-Time) compiler for Strawberry GraphQL, showing performance improvements of **5-6x** for complex queries!

## Features Demonstrated

- ⚡ **JIT Compilation** - 5-6x faster query execution
- 🔄 **Parallel Async Execution** - Additional speedup for async fields when combined with JIT
- 🎯 **Real-world Example** - Blog API with posts, authors, and comments

## Quick Start

```bash
# Install dependencies
pip install strawberry-graphql uvicorn

# Run the server
python server.py

# In another terminal, run the benchmark
python benchmark.py
```

## What's Inside

- `schema.py` - GraphQL schema definition with async resolvers
- `server.py` - FastAPI server with JIT compiler enabled
- `benchmark.py` - Performance comparison tool
- `example_queries.py` - Sample queries to test

## Performance Results

Run `python benchmark.py` to see real-time performance comparisons between standard GraphQL execution and JIT-compiled execution. Typical improvements range from 5-6x faster for complex queries with multiple resolvers.

## Live Demo

Visit http://localhost:8000/graphql after starting the server to try queries in GraphQL Playground.

Try this query to see the JIT in action:

```graphql
query GetBlogData {
  posts(limit: 10) {
    id
    title
    content
    viewCount
    author {
      name
      email
      bio
      postsCount
    }
    comments {
      id
      text
      likes
      author {
        name
      }
    }
  }
  featuredPost {
    id
    title
    viewCount
  }
  topAuthors {
    name
    postsCount
  }
}
```
