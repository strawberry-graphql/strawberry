"""Example GraphQL queries to test with the JIT compiler.
Copy and paste these into GraphQL Playground at http://localhost:8000/graphql
"""

# Simple query - fast baseline
SIMPLE_QUERY = """
query GetPosts {
  posts(limit: 5) {
    id
    title
    wordCount
  }
}
"""

# Query with nested author data
AUTHOR_QUERY = """
query PostsWithAuthors {
  posts(limit: 10) {
    id
    title
    content
    author {
      name
      email
      bio
      postsCount
    }
  }
}
"""

# Complex query with multiple async fields
# This is where JIT + parallel execution shines!
COMPLEX_QUERY = """
query BlogDashboard {
  posts(limit: 10) {
    id
    title
    content
    wordCount
    viewCount
    createdAt
    author {
      id
      name
      email
      bio
      postsCount
      followers
    }
    comments(limit: 5) {
      id
      text
      likes
      isRecent
      author {
        name
        email
      }
    }
  }

  featuredPost {
    id
    title
    content
    viewCount
    author {
      name
      postsCount
    }
    comments(limit: 3) {
      text
      likes
    }
  }

  topAuthors(limit: 5) {
    id
    name
    bio
    postsCount
    followers
  }
}
"""

# Query with deep nesting to test recursive compilation
NESTED_QUERY = """
query DeeplyNestedQuery {
  posts(limit: 3) {
    id
    title
    author {
      name
      bio
      postsCount
    }
    comments(limit: 3) {
      id
      text
      author {
        name
        followers
      }
    }
    relatedPosts(limit: 2) {
      id
      title
      wordCount
      author {
        name
        email
      }
      comments(limit: 2) {
        text
        likes
        author {
          name
        }
      }
    }
  }
}
"""

# Search query with parameters
SEARCH_QUERY = """
query SearchPosts($searchTerm: String!, $limit: Int!) {
  searchPosts(query: $searchTerm, limit: $limit) {
    id
    title
    content
    author {
      name
    }
    viewCount
  }
}
"""

# Variables for search query
SEARCH_VARIABLES = {"searchTerm": "GraphQL", "limit": 10}

# Fragment example
FRAGMENT_QUERY = """
fragment PostDetails on Post {
  id
  title
  content
  wordCount
  viewCount
}

fragment AuthorInfo on Author {
  name
  email
  bio
  postsCount
}

query PostsWithFragments {
  posts(limit: 5) {
    ...PostDetails
    author {
      ...AuthorInfo
    }
  }

  featuredPost {
    ...PostDetails
    author {
      ...AuthorInfo
    }
  }
}
"""

# Query with directives
DIRECTIVE_QUERY = """
query ConditionalFields($includeComments: Boolean!, $skipAuthor: Boolean!) {
  posts(limit: 5) {
    id
    title

    comments @include(if: $includeComments) {
      text
      likes
    }

    author @skip(if: $skipAuthor) {
      name
      email
    }
  }
}
"""

# Variables for directive query
DIRECTIVE_VARIABLES = {"includeComments": True, "skipAuthor": False}


def print_example_queries():
    """Print example queries for easy copying."""
    examples = [
        ("Simple Query", SIMPLE_QUERY, None),
        ("Author Query", AUTHOR_QUERY, None),
        ("Complex Dashboard", COMPLEX_QUERY, None),
        ("Deeply Nested", NESTED_QUERY, None),
        ("Search Query", SEARCH_QUERY, SEARCH_VARIABLES),
        ("Fragment Query", FRAGMENT_QUERY, None),
        ("Directive Query", DIRECTIVE_QUERY, DIRECTIVE_VARIABLES),
    ]

    print("\n" + "=" * 60)
    print("📝 EXAMPLE GRAPHQL QUERIES")
    print("=" * 60)
    print("\nCopy these queries to test in GraphQL Playground:")
    print("http://localhost:8000/graphql\n")

    for i, (name, query, variables) in enumerate(examples, 1):
        print(f"\n{i}. {name}")
        print("-" * 40)
        print(query.strip())
        if variables:
            print("\nVariables:")
            print(variables)

    print("\n" + "=" * 60)
    print("💡 PERFORMANCE TIPS")
    print("=" * 60)
    print("""
1. The first execution of each unique query will be slower (compilation)
2. Subsequent executions use the cached compiled version (10x faster)
3. Complex queries with many async fields benefit most from parallel execution
4. Check the response headers for execution metrics:
   - X-Execution-Time: Time taken for this request
   - X-JIT-Enabled: Whether JIT is active
   - X-Cache-Hit-Rate: Percentage of cache hits

5. Visit http://localhost:8000/metrics to see overall performance stats
""")


if __name__ == "__main__":
    print_example_queries()
