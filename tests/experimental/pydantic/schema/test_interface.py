from typing import List

from pydantic import BaseModel

import strawberry


def test_pydantic_query_interface():
    @strawberry.interface
    class Cheese:
        name: str

    class SwissModel(BaseModel):
        canton: str

    @strawberry.experimental.pydantic.type(model=SwissModel, fields=["canton"])
    class Swiss(Cheese):
        pass

    class ItalianModel(BaseModel):
        province: str

    @strawberry.experimental.pydantic.type(model=ItalianModel, fields=["province"])
    class Italian(Cheese):
        pass

    @strawberry.type
    class Root:
        @strawberry.field
        def assortment(self) -> List[Cheese]:
            return [
                Italian(name="Asiago", province="Friuli"),
                Swiss(name="Tomme", canton="Vaud"),
            ]

    schema = strawberry.Schema(query=Root, types=[Swiss, Italian])

    query = """{
        assortment {
            name
            ... on Italian { province }
            ... on Swiss { canton }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["assortment"] == [
        {"name": "Asiago", "province": "Friuli"},
        {"canton": "Vaud", "name": "Tomme"},
    ]
