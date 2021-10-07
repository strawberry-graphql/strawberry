import logging

from graphql.error import GraphQLError

from strawberry.utils.logging import error_logger


def test_error_logger(caplog):
    caplog.set_level(logging.ERROR, logger="strawberry.execution")

    exc = GraphQLError("test exception")
    error_logger([exc])

    assert caplog.record_tuples == [
        ("strawberry.execution", logging.ERROR, "test exception")
    ]
