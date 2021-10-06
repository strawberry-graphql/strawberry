import logging
import sys
from typing import Any, Dict, List, Optional

from graphql.error import GraphQLError

from strawberry.types import ExecutionContext


logger = logging.getLogger("strawberry.execution")


def error_logger(
    errors: List[GraphQLError],
    execution_context: Optional[ExecutionContext] = None,
) -> None:
    kwargs: Dict[str, Any] = {
        "stack_info": True,
    }

    # stacklevel was added in version 3.8
    # https://docs.python.org/3/library/logging.html#logging.Logger.debug

    if sys.version_info >= (3, 8):
        kwargs["stacklevel"] = 3

    for error in errors:
        logger.error(error, exc_info=error.original_error, **kwargs)
