# Strawberry JIT Compiler Showcase 🚀

This directory demonstrates the powerful JIT (Just-In-Time) compiler for Strawberry GraphQL, showing performance improvements of **5-6x** for complex queries!

## 🎯 Quick Start Guide

**New to JIT?** Run the examples in this order:

### 1. Start Here: `quickstart.py` (5 min)
```bash
python quickstart.py
```
Your first JIT query - see immediate 5-6x performance gains!

### 2. Simple Demo: `simple_demo.py` (10 min)
```bash
python simple_demo.py
```
Product catalog example with caching and performance comparisons.

### 3. Real-World: `large_dataset_demo.py` (15 min)
```bash
python large_dataset_demo.py
```
E-commerce application with 1000+ records, complex nested queries.

### 4. Specialized Demos
```bash
python overhead_demo.py          # Overhead elimination for wide queries
python error_handling_demo.py    # Error handling and propagation
python benchmark.py              # Full benchmark suite (20+ min)
```

### 5. Production Server: `server.py`
```bash
python server.py
# Visit http://localhost:8000/graphql
```

## 📚 What's Inside

### Core Examples
- **quickstart.py** - Essential 5-minute intro
- **simple_demo.py** - Product catalog with caching
- **large_dataset_demo.py** - E-commerce with realistic data
- **overhead_demo.py** - Overhead elimination demo
- **error_handling_demo.py** - Error scenarios

### Benchmarking
- **benchmark.py** - Comprehensive performance tests
- **benchmark_summary.py** - Aggregated results (removed - use benchmark.py)

### Infrastructure
- **schema.py** - Shared blog API schema
- **server.py** - FastAPI server with JIT
- **example_queries.py** - Sample queries

## ⚡ Features Demonstrated

- ✅ **5-6x faster execution** for complex queries
- ✅ **Parallel async execution** with asyncio.gather()
- ✅ **Query caching** strategies
- ✅ Fragments, directives, variables
- ✅ Error handling and propagation
- ✅ Custom scalars and enums
- ✅ Introspection support

## 📊 Performance Results

Typical improvements across examples:
- **Simple queries**: 2-4x faster
- **Nested queries**: 5-6x faster
- **Large datasets**: 6-8x faster
- **Async parallel**: Additional 2-3x with gather()

Run any example to see real-time benchmarks!

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
