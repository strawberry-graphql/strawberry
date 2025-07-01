from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing import Final

    from graphql.error import GraphQLError

    from strawberry.types import ExecutionContext


class StrawberryLogger:
    logger: Final[logging.Logger] = logging.getLogger("strawberry.execution")

    @classmethod
    def error(
        cls,
        error: GraphQLError,
        execution_context: ExecutionContext | None = None,
        # https://www.python.org/dev/peps/pep-0484/#arbitrary-argument-lists-and-default-argument-values
        **logger_kwargs: Any,
    ) -> None:
        cls.logger.error(error, exc_info=error.original_error, **logger_kwargs)


__all__ = ["StrawberryLogger"]
