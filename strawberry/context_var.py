from contextvars import ContextVar, Token
from typing import Optional


_context_var: ContextVar[Optional[object]] = ContextVar(
    "StrawberryContext", default=None
)


class StrawberryContext:
    def _set_context(self, context: object) -> Token:
        return _context_var.set(context)

    def _reset_context(self, context_token: Token):
        return _context_var.reset(context_token)

    def _get_key_value(self, key):
        context = _context_var.get()
        if context is None:
            raise Exception("Can't access current Strawberry context")

        return context[key]

    def __getattr__(self, key):
        return self._get_key_value(key)

    def __getitem__(self, key):
        return self._get_key_value(key)

    def get(self, key):
        """Enable .get notation for accessing the request"""
        return self._get_key_value(key)
