import textwrap

from strawberry.schema_codegen import codegen


def test_adds_schema_if_schema_is_defined():
    schema = """
    type Root {
        hello: String!
    }

    type RootMutation {
        hello: String!
    }

    type RootSubscription {
        hello: String!
    }

    schema {
        query: Root
        mutation: RootMutation
        subscription: RootSubscription
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Root:
            hello: str

        @strawberry.type
        class RootMutation:
            hello: str

        @strawberry.type
        class RootSubscription:
            hello: str

        schema = strawberry.Schema(query=Root, mutation=RootMutation, subscription=RootSubscription)
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_adds_schema_if_has_query():
    schema = """
    type Query {
        hello: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Query:
            hello: str

        schema = strawberry.Schema(query=Query)
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_adds_schema_if_has_mutation():
    schema = """
    type Mutation {
        hello: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Mutation:
            hello: str

        schema = strawberry.Schema(mutation=Mutation)
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_adds_schema_if_has_subscription():
    schema = """
    type Subscription {
        hello: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Subscription:
            hello: str

        schema = strawberry.Schema(subscription=Subscription)
        """
    ).strip()

    assert codegen(schema).strip() == expected
