import strawberry


@strawberry.type(description="A connection to a list of items.")
class FilmCharactersConnection:
    page_info: PageInfo = strawberry.field(description="Information to aid in pagination.")
    edges: list[FilmCharactersEdge | None] | None = strawberry.field(description="A list of edges.")
    total_count: int | None = strawberry.field(description="""
A count of the total number of objects in this connection, ignoring pagination.
This allows a client to fetch the first five objects by passing "5" as the
argument to "first", then fetch the total count so it could display "5 of 83",
for example.
""")
    characters: list[Person | None] | None = strawberry.field(description="""
A list of all of the objects returned in the connection. This is a convenience
field provided for quickly exploring the API; rather than querying for
"{ edges { node } }" when no edge data is needed, this field can be be used
instead. Note that when clients like Relay need to fetch the "cursor" field on
the edge to enable efficient pagination, this shortcut cannot be used, and the
full "{ edges { node } }" version should be used instead.
""")
