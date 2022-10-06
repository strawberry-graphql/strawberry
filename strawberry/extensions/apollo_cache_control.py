from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Optional, Union

from graphql import GraphQLResolveInfo

from strawberry.apollo.schema_directives import CacheControl, CacheControlScope
from strawberry.extensions.base_extension import Extension
from strawberry.field import StrawberryField
from strawberry.types import ExecutionContext
from strawberry.utils.await_maybe import AwaitableOrValue


if TYPE_CHECKING:
    from strawberry.schema.schema import Schema


# @dataclass
# class CacheHint:
#     max_age: Optional[int] = None
#     scope: Optional[CacheControlScope] = None


@dataclass
class CachePolicy:
    max_age: Optional[int] = None
    scope: Optional[CacheControlScope] = None

    @classmethod
    def from_directive(cls, directive: Optional[CacheControl] = None):
        cache_policy = cls()
        if directive:
            if directive.max_age:
                cache_policy.max_age = directive.max_age

            if directive.scope:
                cache_policy.scope = directive.scope

        return cache_policy

    def restrict(self, hint: CachePolicy):
        if hint.max_age is not None and (
            self.max_age is None or hint.max_age < self.max_age
        ):
            self.max_age = hint.max_age

        if hint.scope is not None and self.scope != CacheControlScope.PRIVATE:
            self.scope = hint.scope

    @property
    def policy(
        self,
    ) -> Dict[str, Union[int, str]]:
        if self.max_age is None or self.max_age == 0:
            return {}

        return {
            "max_age": self.max_age,
            "scope": self.scope.name.lower()
            if self.scope
            else CacheControlScope.PUBLIC.name.lower(),
        }


class ApolloCacheControlExtension(Extension):
    max_age: int = 0
    overall_cache_policy = None

    def __init__(
        self,
        *,
        default_max_age: Optional[int] = 0,
        calculate_http_headers: Optional[bool] = True,
        execution_context: Optional[ExecutionContext] = None,
    ):
        self.calculate_http_headers = calculate_http_headers

        if default_max_age:
            self.max_age = default_max_age

        if execution_context:
            self.execution_context = execution_context

    def on_request_start(self):
        self.fields_caches: Dict[str, CachePolicy] = {}

    def on_executing_end(self):
        if not self.calculate_http_headers:
            return

        self.execution_context.context["response"].headers[
            "cache-control"
        ] = f"max-age={self.max_age}, public"

        for header in self.execution_context.context["response"].headers.items():
            print(header)

    def _get_cache_control_directive(
        self, field: StrawberryField
    ) -> Optional[CacheControl]:
        def is_cache_control_directive(directive) -> bool:
            return isinstance(directive, CacheControl)

        directive: Optional[CacheControl] = next(filter(is_cache_control_directive, field.directives), None)  # type: ignore

        return directive

    def resolve(
        self, _next, root, info: GraphQLResolveInfo, *args, **kwargs
    ) -> AwaitableOrValue[object]:
        schema: Schema = info.schema._strawberry_schema  # type: ignore
        field: StrawberryField = schema.get_field_for_type(  # type: ignore
            field_name=info.field_name,
            type_name=info.parent_type.name,
        )

        if not field:
            return _next(root, info, *args, **kwargs)

        print(field.name)

        cache_control_directive = self._get_cache_control_directive(field)
        if not cache_control_directive:
            return _next(root, info, *args, **kwargs)

        field_policy = CachePolicy.from_directive(cache_control_directive)
        self.fields_caches[field.name.lower()] = field_policy
        parent_policy = self.fields_caches.get(info.parent_type.name)

        #
        if cache_control_directive.inheredit_max_age and field_policy.max_age is None:
            inheritMaxAge = True
            if cache_control_directive.scope:
                pass

        if self.overall_cache_policy:
            self.overall_cache_policy.restrict(field_policy)
        else:
            self.overall_cache_policy = field_policy

        return _next(root, info, *args, **kwargs)

    def get_results(self) -> Dict[str, Union[int, str]]:
        if not self.overall_cache_policy:
            return {}
        return self.overall_cache_policy.policy
