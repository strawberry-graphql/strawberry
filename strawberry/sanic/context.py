from dataclasses import dataclass

from sanic.request import Request


@dataclass
class StrawberrySanicContext:
    request: Request

    def __getitem__(self, key):
        return super().__getattribute__(key)
