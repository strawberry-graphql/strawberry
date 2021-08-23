from dataclasses import dataclass

from django.http import HttpRequest, HttpResponse


@dataclass
class StrawberryDjangoContext:
    request: HttpRequest
    response: HttpResponse

    def __getitem__(self, key):
        # __getitem__ override needed to avoid issues for who's
        # using info.context["request"]
        return super().__getattribute__(key)

    def get(self, key):
        """Enable .get notation for accessing the request"""
        return super().__getattribute__(key)

    def __repr__(self):
        # Calling the built-in dataclass __repr__ will throw an
        # exception if we don't have a response instantiated,
        # so just return the __class__ property.
        return f"{self.__class__}"
