from typing import AsyncIterator, List

import strawberry
from strawberry.directive import DirectiveLocation


@strawberry.type
class Item:
    name: str
    index: int


@strawberry.type
class Person:
    name: str
    age: int
    description: str
    address: str

    prop_a: str
    prop_b: str
    prop_c: str
    prop_d: str
    prop_e: str
    prop_f: str
    prop_g: str
    prop_h: str
    prop_i: str
    prop_j: str


def create_people(n: int):
    for i in range(n):
        yield Person(
            name=f"Person {i}",
            age=i,
            description=f"Description {i}",
            address=f"Address {i}",
            prop_a=f"Prop A {i}",
            prop_b=f"Prop B {i}",
            prop_c=f"Prop C {i}",
            prop_d=f"Prop D {i}",
            prop_e=f"Prop E {i}",
            prop_f=f"Prop F {i}",
            prop_g=f"Prop G {i}",
            prop_h=f"Prop H {i}",
            prop_i=f"Prop I {i}",
            prop_j=f"Prop J {i}",
        )


people = list(create_people(n=1_000))


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World!"

    @strawberry.field
    def people(self, limit: int = 100) -> List[Person]:
        return people[:limit] if limit else people

    @strawberry.field
    def items(self, count: int) -> List[Item]:
        return [Item(name="Item", index=i) for i in range(count)]


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def something(self) -> AsyncIterator[str]:
        yield "Hello World!"


@strawberry.directive(locations=[DirectiveLocation.FIELD])
def uppercase(value: str) -> str:
    return value.upper()


schema = strawberry.Schema(query=Query, subscription=Subscription)
schema_with_directives = strawberry.Schema(
    query=Query, directives=[uppercase], subscription=Subscription
)
