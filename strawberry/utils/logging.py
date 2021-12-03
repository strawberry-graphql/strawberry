import logging
import sys
from typing import Any, Optional

from typing_extensions import Final

from graphql.error import GraphQLError

from strawberry.types import ExecutionContext


class StrawberryLogger:
    logger: Final[logging.Logger] = logging.getLogger("strawberry.execution")

    @classmethod
    def error(
        cls,
        error: GraphQLError,
        execution_context: Optional[ExecutionContext] = None,
        # https://www.python.org/dev/peps/pep-0484/#arbitrary-argument-lists-and-default-argument-values
        **logger_kwargs: Any,
    ) -> None:
        # "stack_info" is a boolean; check for None explicitly
        if logger_kwargs.get("stack_info") is None:
            logger_kwargs["stack_info"] = True

        # stacklevel was added in version 3.8
        # https://docs.python.org/3/library/logging.html#logging.Logger.debug
        if sys.version_info >= (3, 8):
            logger_kwargs["stacklevel"] = 3

        cls.logger.error(error, exc_info=error.original_error, **logger_kwargs)
