from dataclasses import dataclass

from django.http import HttpRequest


@dataclass
class StrawberryDjangoContext:
    request: HttpRequest

    def __getitem__(self, key):
        # __getitem__ override needed to avoid issues for who's
        # using info.context["request"]
        return super().__getattribute__(key)

    def get(self, key):
        """Enable .get notation for accessing the request"""
        return super().__getattribute__(key)
