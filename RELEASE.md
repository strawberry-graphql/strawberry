Release type: patch

Strawberry will now inject `strawberry.Info` instances to `resolve_reference` classmethods instead of `GraphQLResolveInfo` instances.

This allows for the use of the additional functionality provided by `strawberry.Info`, such as filtering what's resolved based on the selected fields:

```py
@strawberry.federation.type(keys=["id"])
class User:
    id: strawberry.ID
    email: str
    orders: list[Order] = strawberry.field(default_factory=list)

    @classmethod
    def resolve_reference(cls, id: strawberry.ID, info: strawberry.Info) -> Self:
        user = db.session.query(User).filter(User.id == id).first()
        kwargs = {"id": user.id, "email": user.email}

        for field in info.selected_fields:
            for selection in field.selections:
                if selection.name == "orders":
                    orders = (
                        db.session.query(Order)
                        .filter(Order.customer_id == User.id)
                        .all()
                    )
                    kwargs["orders"] = orders

        return cls(**kwargs)
```

Note that field-related attributes will always return `None`.
