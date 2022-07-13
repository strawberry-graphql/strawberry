from pydantic import BaseModel

import strawberry


class MyModel(BaseModel):
    email: str
    password: str


@strawberry.experimental.pydantic.input(model=MyModel)
class MyModelStrawberry:
    email: strawberry.auto


MyModelStrawberry(email="").to_pydantic()
