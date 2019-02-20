# Introducing Strawberry, a new Python library for GraphQL

Hello everyone, this is something I’ve been working on over the past few months in my spare time, aided with the help of some coworkers and friends.

I’ve been interested in GraphQL since I discovered it a few years ago. I’ve been using Python for about 10 years at this point, so I’ve started playing with Graphene, but I found it quite limiting and being honest I’m quite disappointed at the way it is being developed (hopefully this will change soon, link to GitHub discussion here).

So, I had this idea of making my own Python library for GraphQL, mainly because I wanted to experiment with different concepts and features.

## How it started — dataclasses

In October 2018 I was at DjangoCon US and Tray Hunner was giving this amazing talk about dataclasses: [Easier Classes: Python Classes Without All The Cruft | DjangoCon US](https://2018.djangocon.us/talk/easier-classes-python-classes-without/)

If you’re unfamiliar with dataclasses, here’s a simple of example from the Python docs.

```python
@dataclass
class InventoryItem:
    '''Class for keeping track of an item in inventory.'''
    name: str
    unit_price: float
    quantity_on_hand: int = 0

    def total_cost(self) -> float:
        return self.unit_price * self.quantity_on_hand
```

They use the power of typings to allow developers to define a (data)class with just a few lines, the `@dataclass` decorator will then create all sort of useful methods on the class itself, for example the constructor and magic methods for sorting and comparison. [dataclasses — Data Classes — Python 3.7.2 documentation](https://docs.python.org/3/library/dataclasses.html)

## dataclasses and GraphQL

GraphQL’s type system to me sounds kinda like a dataclass, here’s an example type that could map to the class defined above:

```graphql
type InventoryItem {
  name: String!
  unitPrice: Float!
  quantityOnHand: Float!
  totalCost: Float!
}
```

As you can see there’s not a huge difference in terms of declaring the type and the class.

## Entering strawberry

With that in mind I thought it would be cool to use a dataclass inspired approach for defining GraphQL types and schemas, so here’s how it would look like for a simple schema:

```python
import strawberry

@strawberry.type
class Query:
     hello: str = "Hello"

schema = strawberry.Schema(query=Query)
```
