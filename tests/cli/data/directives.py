from strawberry.directive import DirectiveLocation

import strawberry


@strawberry.directive(
    locations=[
        DirectiveLocation.FIELD_DEFINITION
    ],
)
def uppercase(
    example: str
):
    pass

@strawberry.type
class Query:
    a: str
