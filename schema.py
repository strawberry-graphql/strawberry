from pydantic import BaseModel, conlist

import strawberry
from strawberry.printer import print_schema


class Example(BaseModel):
    friends: conlist(str, min_items=1)


@strawberry.experimental.pydantic.type(model=Example, all_fields=True, is_input=True)
class ExampleGQL:
    ...


@strawberry.type
class Query:
    @strawberry.field()
    def test(self, example: ExampleGQL) -> None:
        # if to_pydantic() is not called, there will be no validation that
        # friends has at least one item
        print(example.to_pydantic())


schema = strawberry.Schema(query=Query)


def test():
    printed = print_schema(schema)
    print(printed)
