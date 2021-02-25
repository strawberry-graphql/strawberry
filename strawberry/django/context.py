from dataclasses import dataclass

from django.http import HttpRequest


@dataclass
class StrawberryDjangoContext:
    request: HttpRequest

    def __getitem__(self, key):
        return super().__getattribute__(key)
