import pydantic

import strawberry


@strawberry.pydantic.type
class Account(pydantic.BaseModel):
    iban: str
