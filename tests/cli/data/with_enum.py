from enum import Enum

import strawberry


@strawberry.type
class Query:
    options: "Options"


@strawberry.enum
class Options(Enum):
    TRUE = "true"
    FALSE = "false"
    MAYBE = "maybe"
    NO_IDEA = "no_idea"
