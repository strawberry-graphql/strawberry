from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Optional, Tuple, Union

from graphql import GraphQLNonNull, GraphQLResolveInfo
from graphql.pyutils.path import Path

from strawberry.apollo.schema_directives import CacheControl, CacheControlScope
from strawberry.extensions.base_extension import Extension
from strawberry.field import StrawberryField
from strawberry.utils.await_maybe import AwaitableOrValue


if TYPE_CHECKING:
    from strawberry.schema.schema import Schema


def is_cache_control_directive(directive) -> bool:
    return isinstance(directive, CacheControl)


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

    def replace(self, hint: CachePolicy):
        if hint.max_age is not None:
            self.max_age = hint.max_age

        if hint.scope is not None:
            self.scope = hint.scope

    @property
    def policy(
        self,
    ) -> Dict[str, Union[int, str]]:
        if self.max_age is None or self.max_age == 0:
            return {}

        return {
            "max_age": self.max_age if self.max_age else 0,
            "scope": self.scope.name.lower()
            if self.scope
            else CacheControlScope.PUBLIC.name.lower(),
        }


class ApolloCacheControl(Extension):
    default_max_age: int = 0

    def __init__(
        self,
        *,
        default_max_age: Optional[int] = 0,
        calculate_http_headers: Optional[bool] = True,
    ):
        self.calculate_http_headers = calculate_http_headers

        if default_max_age:
            self.default_max_age = default_max_age

    def on_request_start(self):
        self.fields_caches: Dict[str, CachePolicy] = {}
        self.overall_cache_policy = CachePolicy()

    def on_executing_end(self):
        if not self.calculate_http_headers:
            return

        self.execution_context.context["response"].headers[
            "cache-control"
        ] = f"max-age={self.overall_cache_policy.max_age}, {self.overall_cache_policy.scope}"

        for header in self.execution_context.context["response"].headers.items():
            print(header)

    def _get_directives(
        self, info: GraphQLResolveInfo, schema: Schema, field: StrawberryField
    ) -> Tuple[Optional[CacheControl], Optional[CacheControl]]:
        field_directive: Optional[CacheControl] = next(
            filter(is_cache_control_directive, field.directives), None  # type: ignore
        )

        resolver_directive = None
        return_type = info.return_type
        if isinstance(return_type, GraphQLNonNull):
            return_type = return_type.of_type
        return_type = schema.get_type_by_name(return_type.name)
        if return_type:
            resolver_directive: Optional[CacheControl] = next(
                filter(
                    is_cache_control_directive,
                    return_type.directives,
                ),
                None,
            )

        return field_directive, resolver_directive

    def resolve(
        self, _next, root, info: GraphQLResolveInfo, *args, **kwargs
    ) -> AwaitableOrValue[object]:
        def find_ancestor_cache_policy(
            path: Path,
        ) -> CachePolicy:
            if self.fields_caches.get(str(path.key)):
                return self.fields_caches[str(path.key)]

            if path.prev:
                return find_ancestor_cache_policy(path.prev)

            return CachePolicy()

        field_policy = CachePolicy()

        schema: Schema = info.schema._strawberry_schema  # type: ignore
        field: StrawberryField = schema.get_field_for_type(  # type: ignore
            field_name=info.field_name,
            type_name=info.parent_type.name,
        )
        field_directive, resolver_directive = self._get_directives(info, schema, field)

        if resolver_directive:
            field_policy.max_age = resolver_directive.max_age
            field_policy.scope = resolver_directive.scope

            if resolver_directive.inheredit_max_age:
                field_policy.replace(find_ancestor_cache_policy(info.path))

            self.fields_caches[str(info.path.key)] = field_policy

        # Cache hints on the fields take precedence over hints on the Type
        if field_directive:
            if field_directive.max_age:
                field_policy.max_age = field_directive.max_age

            if field_directive.scope:
                field_policy.scope = field_directive.scope

            if field_directive.inheredit_max_age:
                field_policy.replace(find_ancestor_cache_policy(info.path))

            self.fields_caches[str(info.path.key)] = field_policy

        # only scalars inheredit by default from their parents
        if field.type in schema.schema_converter.scalar_registry:
            field_policy.replace(find_ancestor_cache_policy(info.path))

        # TODO: dynamic cache control
        resolve_result = _next(root, info, *args, **kwargs)

        if field_policy.max_age is None:
            field_policy.max_age = self.default_max_age

        self.overall_cache_policy.restrict(field_policy)
        return resolve_result

    def get_results(self) -> Dict[str, Union[int, str]]:
        return self.overall_cache_policy.policy
