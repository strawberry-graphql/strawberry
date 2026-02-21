import strawberry

from .type_fruit import Fruit

# Simulate what a third-party decorator (e.g. strawberry-django's filter_type) does:
# re-process a type, creating a new StrawberryObjectDefinition for the same origin class.
strawberry.type(Fruit)


@strawberry.type
class FruitBowl:
    fruit: Fruit
