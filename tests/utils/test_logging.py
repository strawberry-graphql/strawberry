import logging

from graphql.error import GraphQLError

from strawberry.utils.logging import StrawberryLogger


def test_strawberry_logger_error(caplog):
    caplog.set_level(logging.ERROR, logger="strawberry.execution")

    exc = GraphQLError("test exception")
    StrawberryLogger.error(exc)

    assert caplog.record_tuples == [
        ("strawberry.execution", logging.ERROR, "test exception")
    ]
