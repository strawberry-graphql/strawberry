import typing

import strawberry
from strawberry.federation.schema_directives import Key


@strawberry.federation.type(directives=[Key(fields="id", resolvable=False)])
class User:
    id: strawberry.ID


async def get_user(root: "Organization", info: strawberry.Info) -> User:
    return User(id=root._owner)


@strawberry.federation.type(keys=["id"])
class Organization:
    id: strawberry.ID
    name: str
    _owner: strawberry.Private[User]
    owner: User = strawberry.field(resolver=get_user)

    @classmethod
    async def resolve_reference(
        cls, id: strawberry.ID
    ) -> typing.Optional["Organization"]:
        return await get_organization_by_id(id=id)


async def get_organizations():
    return [
        Organization(
            id=strawberry.ID("org1"),
            name="iotflow",
            _owner="abcdert1",
        ),
        Organization(
            id=strawberry.ID("org2"),
            name="ibrag",
            _owner="abdfr2",
        ),
    ]


async def get_organization_by_id(id: strawberry.ID) -> typing.Optional[Organization]:
    for organization in await get_organizations():
        if organization.id == id:
            return organization
    return None


@strawberry.type
class Query:
    organizations: typing.List[Organization] = strawberry.field(
        resolver=get_organizations
    )

    @strawberry.field
    async def organization(self, id: strawberry.ID) -> typing.Optional[Organization]:
        return await get_organization_by_id(id)


schema = strawberry.federation.Schema(
    query=Query, types=[Organization, User], enable_federation_2=True
)
