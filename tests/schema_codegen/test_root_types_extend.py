import textwrap

from strawberry.schema_codegen import codegen


def test_extend_query():
    schema = """
    extend type Query {
        world: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Query:
            world: str

        schema = strawberry.Schema(query=Query)
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_extend_mutation():
    schema = """
    extend type Mutation {
        world: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Mutation:
            world: str

        schema = strawberry.Schema(mutation=Mutation)
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_extend_subscription():
    schema = """
    extend type Subscription {
        world: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Subscription:
            world: str

        schema = strawberry.Schema(subscription=Subscription)
        """
    ).strip()

    assert codegen(schema).strip() == expected
