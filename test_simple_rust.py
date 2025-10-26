import strawberry_core_rs

schema_sdl = """
type Query {
  stadium: Stadium
}

type Stadium {
  name: String!
  city: String!
}
"""

query = "{ stadium { name city } }"

root_data = {"stadium": {"name": "Test", "city": "London"}}

result = strawberry_core_rs.execute_query(schema_sdl, query, root_data)
print(result)
