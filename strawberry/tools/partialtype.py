from abc import ABCMeta
from typing import Optional

import strawberry


class PartialType(ABCMeta):
    def __new__(cls, name: str, bases: tuple, namespaces: dict, **kwargs):
        mro = super().__new__(cls, name, bases, namespaces, **kwargs).mro()
        annotations = namespaces.get("__annotations__", {})
        fields: list[str] = []
        for base in mro[:-1]:  # the object class has no __annotations__ attr
            for k, v in base.__annotations__.items():
                # To prevent overriding the higher attr annotation
                if k not in annotations:
                    annotations[k] = v

            fields.extend(field.name for field in base._type_definition.fields)

        for field in annotations:
            if not field.startswith("_"):
                annotations[field] = Optional[annotations[field]]

        namespaces["__annotations__"] = annotations
        klass = super().__new__(cls, name, bases, namespaces, **kwargs)
        for field in fields:
            if not hasattr(klass, field):
                setattr(klass, field, strawberry.UNSET)

        return klass
