from typing import Any, Optional

import strawberry
from strawberry.schema_directive import Location

# ------- data -------

dimension = {
    "size": "small",
    "weight": 1,
    "unit": "kg",
}

user = {
    "email": "support@apollographql.com",
    "name": "Jane Smith",
    "total_products_created": 1337,
    "years_of_employment": 10,
}


deprecated_product = {
    "sku": "apollo-federation-v1",
    "package": "@apollo/federation-v1",
    "reason": "Migrate to Federation V2",
    "created_by": user["email"],
}

products_research = [
    {
        "study": {
            "case_number": "1234",
            "description": "Federation Study",
        },
        "outcome": None,
    },
    {
        "study": {
            "case_number": "1235",
            "description": "Studio Study",
        },
        "outcome": None,
    },
]


products = [
    {
        "id": "apollo-federation",
        "sku": "federation",
        "package": "@apollo/federation",
        "variation": {"id": "OSS"},
        "dimensions": dimension,
        "research": [products_research[0]],
        "created_by": user["email"],
        "notes": None,
    },
    {
        "id": "apollo-studio",
        "sku": "studio",
        "package": "",
        "variation": {"id": "platform"},
        "dimensions": dimension,
        "research": [products_research[1]],
        "created_by": user["email"],
        "notes": None,
    },
]


# ------- resolvers -------


def get_product_by_id(id: strawberry.ID) -> Optional["Product"]:
    data = next((product for product in products if product["id"] == id), None)

    if not data:
        return None

    return Product.from_data(data)


def get_product_by_sku_and_package(sku: str, package: str) -> Optional["Product"]:
    data = next(
        (
            product
            for product in products
            if product["sku"] == sku and product["package"] == package
        ),
        None,
    )

    return Product.from_data(data) if data else None


def get_product_by_sku_and_variation(sku: str, variation: dict) -> Optional["Product"]:
    data = next(
        (
            product
            for product in products
            if product["sku"] == sku and product["variation"]["id"] == variation["id"]
        ),
        None,
    )

    return Product.from_data(data) if data else None


# ------- types -------


@strawberry.federation.schema_directive(
    locations=[Location.OBJECT],
    name="custom",
    compose=True,
    import_url="https://myspecs.dev/myCustomDirective/v1.0",
)
class Custom: ...


@strawberry.federation.type(extend=True, keys=["email"])
class User:
    email: strawberry.ID = strawberry.federation.field(external=True)
    name: Optional[str] = strawberry.federation.field(override="users")
    total_products_created: Optional[int] = strawberry.federation.field(external=True)
    years_of_employment: int = strawberry.federation.field(external=True)

    # TODO: the camel casing will be fixed in a future release of Strawberry
    @strawberry.federation.field(requires=["totalProductsCreated", "yearsOfEmployment"])
    def average_products_created_per_year(self) -> Optional[int]:
        if self.total_products_created is not None:
            return round(self.total_products_created / self.years_of_employment)

        return None

    @classmethod
    def resolve_reference(cls, **data: Any) -> Optional["User"]:
        if email := data.get("email"):
            years_of_employment = data.get("yearsOfEmployment")

            return User(
                email=email,
                name="Jane Smith",
                total_products_created=1337,
                years_of_employment=years_of_employment,
            )

        return None


@strawberry.federation.type(shareable=True)
class ProductDimension:
    size: Optional[str]
    weight: Optional[float]
    unit: Optional[str] = strawberry.federation.field(inaccessible=True)


@strawberry.type
class ProductVariation:
    id: strawberry.ID


@strawberry.type
class CaseStudy:
    case_number: strawberry.ID
    description: Optional[str]


@strawberry.federation.type(keys=["study { caseNumber }"])
class ProductResearch:
    study: CaseStudy
    outcome: Optional[str]

    @classmethod
    def from_data(cls, data: dict) -> "ProductResearch":
        return ProductResearch(
            study=CaseStudy(
                case_number=data["study"]["case_number"],
                description=data["study"]["description"],
            ),
            outcome=data["outcome"],
        )

    @classmethod
    def resolve_reference(cls, **data: Any) -> Optional["ProductResearch"]:
        study = data.get("study")

        if not study:
            return None

        case_number = study["caseNumber"]

        research = next(
            (
                product_research
                for product_research in products_research
                if product_research["study"]["case_number"] == case_number
            ),
            None,
        )

        return ProductResearch.from_data(research) if research else None


@strawberry.federation.type(keys=["sku package"])
class DeprecatedProduct:
    sku: str
    package: str
    reason: Optional[str]
    created_by: Optional[User]

    @classmethod
    def resolve_reference(cls, **data: Any) -> Optional["DeprecatedProduct"]:
        if deprecated_product["sku"] == data.get("sku") and deprecated_product[
            "package"
        ] == data.get("package"):
            return DeprecatedProduct(
                sku=deprecated_product["sku"],
                package=deprecated_product["package"],
                reason=deprecated_product["reason"],
                created_by=User.resolve_reference(
                    email=deprecated_product["created_by"]
                ),
            )

        return None


@strawberry.federation.type(
    keys=["id", "sku package", "sku variation { id }"], directives=[Custom()]
)
class Product:
    id: strawberry.ID
    sku: Optional[str]
    package: Optional[str]
    variation_id: strawberry.Private[str]

    @strawberry.field
    def variation(self) -> Optional[ProductVariation]:
        return (
            ProductVariation(strawberry.ID(self.variation_id))
            if self.variation_id
            else None
        )

    @strawberry.field
    def dimensions(self) -> Optional[ProductDimension]:
        return ProductDimension(**dimension)

    @strawberry.federation.field(provides=["totalProductsCreated"])
    def created_by(self) -> Optional[User]:
        return User(**user)

    notes: Optional[str] = strawberry.federation.field(tags=["internal"])
    research: list[ProductResearch]

    @classmethod
    def from_data(cls, data: dict) -> "Product":
        research = [
            ProductResearch.from_data(research) for research in data.get("research", [])
        ]

        return cls(
            id=data["id"],
            sku=data["sku"],
            package=data["package"],
            variation_id=data["variation"],
            notes="hello",
            research=research,
        )

    @classmethod
    def resolve_reference(cls, **data: Any) -> Optional["Product"]:
        if "id" in data:
            return get_product_by_id(id=data["id"])

        if "sku" in data:
            if "variation" in data:
                return get_product_by_sku_and_variation(
                    sku=data["sku"], variation=data["variation"]
                )
            if "package" in data:
                return get_product_by_sku_and_package(
                    sku=data["sku"], package=data["package"]
                )

        return None


@strawberry.federation.interface_object(keys=["id"])
class Inventory:
    id: strawberry.ID
    deprecated_products: list[DeprecatedProduct]

    @classmethod
    def resolve_reference(cls, id: strawberry.ID) -> "Inventory":
        return Inventory(
            id=id, deprecated_products=[DeprecatedProduct(**deprecated_product)]
        )


@strawberry.federation.type(extend=True)
class Query:
    product: Optional[Product] = strawberry.field(resolver=get_product_by_id)

    @strawberry.field(deprecation_reason="Use product query instead")
    def deprecated_product(self, sku: str, package: str) -> Optional[DeprecatedProduct]:
        return None


schema = strawberry.federation.Schema(
    query=Query, enable_federation_2=True, types=[Inventory]
)
