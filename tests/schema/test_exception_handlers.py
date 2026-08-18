import dataclasses
from collections.abc import AsyncGenerator
from typing import Annotated, Generic, TypeVar

import pytest

import strawberry
from strawberry.extensions.field_extension import FieldExtension
from strawberry.field_extensions import InputMutationExtension
from strawberry.permission import BasePermission
from strawberry.types import Info
from strawberry.types.execution import PreExecutionError
from strawberry.types.field import StrawberryField
from strawberry.utils.aio import aclosing

T = TypeVar("T")


class CustomValidationError(Exception):
    pass


class UnexpectedError(Exception):
    pass


@strawberry.type
class ValidationErrorPayload:
    message: str


@strawberry.type
class OtherErrorPayload:
    message: str


@strawberry.type
class Success:
    value: str


ValidationResult = Annotated[
    Success | ValidationErrorPayload,
    strawberry.union("ValidationResult"),
]


class CustomValidationHandler(
    strawberry.ExceptionHandler[CustomValidationError, ValidationErrorPayload]
):
    def handle(
        self,
        exception: CustomValidationError,
        *,
        field: StrawberryField,
        info: Info,
    ) -> ValidationErrorPayload:
        return ValidationErrorPayload(message=str(exception))


class FirstValidationHandler(
    strawberry.ExceptionHandler[CustomValidationError, ValidationErrorPayload]
):
    def handle(
        self,
        exception: CustomValidationError,
        *,
        field: StrawberryField,
        info: Info,
    ) -> ValidationErrorPayload:
        return ValidationErrorPayload(message="first")


class SecondValidationHandler(
    strawberry.ExceptionHandler[CustomValidationError, ValidationErrorPayload]
):
    def handle(
        self,
        exception: CustomValidationError,
        *,
        field: StrawberryField,
        info: Info,
    ) -> ValidationErrorPayload:
        return ValidationErrorPayload(message="second")


class OtherValidationHandler(
    strawberry.ExceptionHandler[CustomValidationError, OtherErrorPayload]
):
    def handle(
        self,
        exception: CustomValidationError,
        *,
        field: StrawberryField,
        info: Info,
    ) -> OtherErrorPayload:
        return OtherErrorPayload(message="other")


@strawberry.input
class CustomInput:
    value: str

    def __post_init__(self) -> None:
        if len(self.value) < 2:
            raise CustomValidationError("value is too short")


@strawberry.type
class Query:
    ok: bool = True


def test_exception_handler_converts_argument_conversion_error_to_union_type():
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, input: CustomInput) -> Success | ValidationErrorPayload:
            return Success(value=input.value)

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(input: { value: "a" }) {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "value is too short"}}


def test_exception_handler_does_not_handle_when_error_type_is_not_in_return_union():
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, input: CustomInput) -> Success:
            return Success(value=input.value)

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(input: { value: "a" }) {
                value
            }
        }
        """
    )

    assert result.errors is not None
    assert result.errors[0].message == "value is too short"
    assert result.data is None


def test_exception_handler_does_not_handle_unmatched_exception_type():
    processed_errors = []

    class TrackingSchema(strawberry.Schema):
        def process_errors(self, errors, execution_context=None):
            processed_errors.extend(errors)

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise UnexpectedError(f"unexpected value: {value}")

    schema = TrackingSchema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is not None
    assert result.errors[0].message == "unexpected value: abc"
    assert result.data is None
    assert len(processed_errors) == 1
    assert processed_errors[0].message == "unexpected value: abc"


def test_exception_handler_converts_resolver_error_to_union_type():
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "invalid value: abc"}}


def test_exception_handler_converted_error_is_not_processed():
    processed_errors = []

    class TrackingSchema(strawberry.Schema):
        def process_errors(self, errors, execution_context=None):
            processed_errors.extend(errors)

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = TrackingSchema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "invalid value: abc"}}
    assert processed_errors == []


def test_exception_handler_uses_first_matching_handler():
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[FirstValidationHandler(), SecondValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "first"}}


def test_exception_handler_skipped_when_error_type_not_in_field_union():
    # ``OtherValidationHandler`` handles the same exception type but its
    # ``error_type`` is not part of the field's return union, so the next
    # matching handler wins.
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[OtherValidationHandler(), SecondValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "second"}}


def test_exception_handler_converts_error_for_optional_union_type():
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, input: CustomInput) -> Success | ValidationErrorPayload | None:
            return Success(value=input.value)

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(input: { value: "a" }) {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "value is too short"}}


def test_exception_handler_returning_none_declines_on_optional_union_type():
    # Even on an optional union, returning ``None`` declines rather than
    # silently resolving the field to null: the original exception (here raised
    # during argument conversion) propagates as a normal GraphQL error.
    class NullValidationHandler(
        strawberry.ExceptionHandler[CustomValidationError, ValidationErrorPayload]
    ):
        def handle(
            self,
            exception: CustomValidationError,
            *,
            field: StrawberryField,
            info: Info,
        ) -> ValidationErrorPayload | None:
            return None

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, input: CustomInput) -> Success | ValidationErrorPayload | None:
            return Success(value=input.value)

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[NullValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(input: { value: "a" }) {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    # The field is nullable, so GraphQL nulls just the errored field and records
    # the propagated exception rather than converting it to a union result.
    assert result.data == {"create": None}
    assert result.errors is not None
    assert result.errors[0].message == "value is too short"


def test_exception_handler_accepts_multiple_exception_types():
    class MultipleValidationHandler(
        strawberry.ExceptionHandler[
            CustomValidationError | UnexpectedError, ValidationErrorPayload
        ]
    ):
        def handle(
            self,
            exception: CustomValidationError | UnexpectedError,
            *,
            field: StrawberryField,
            info: Info,
        ) -> ValidationErrorPayload:
            return ValidationErrorPayload(message=str(exception))

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise UnexpectedError(f"unexpected value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[MultipleValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "unexpected value: abc"}}


def test_exception_handler_does_not_handle_list_of_union_type():
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> list[Success | ValidationErrorPayload]:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is not None
    assert result.errors[0].message == "invalid value: abc"
    assert result.data is None


def test_exception_handler_matches_lazy_error_type_in_union():
    LazyValidationErrorPayload = Annotated[
        "ValidationErrorPayload",
        strawberry.lazy("tests.schema.test_exception_handlers"),
    ]

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | LazyValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "invalid value: abc"}}


def test_exception_handler_matches_lazy_union_return_type():
    LazyValidationResult = Annotated[
        "ValidationResult",
        strawberry.lazy("tests.schema.test_exception_handlers"),
    ]

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> LazyValidationResult:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "invalid value: abc"}}


def test_exception_handler_converts_resolver_error_inside_field_extension():
    class PassthroughExtension(FieldExtension):
        def resolve(self, next_, source, info, **kwargs):  # noqa: ANN003
            return next_(source, info, **kwargs)

    @strawberry.type
    class Mutation:
        @strawberry.mutation(extensions=[PassthroughExtension()])
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "invalid value: abc"}}


def test_field_extension_can_transform_resolver_error_before_handler():
    class TransformingExtension(FieldExtension):
        def resolve(self, next_, source, info, **kwargs):  # noqa: ANN003
            try:
                return next_(source, info, **kwargs)
            except CustomValidationError as exc:
                raise UnexpectedError(f"transformed: {exc}") from exc

    class UnexpectedErrorHandler(
        strawberry.ExceptionHandler[UnexpectedError, ValidationErrorPayload]
    ):
        def handle(
            self,
            exception: UnexpectedError,
            *,
            field: StrawberryField,
            info: Info,
        ) -> ValidationErrorPayload:
            return ValidationErrorPayload(message=str(exception))

    @strawberry.type
    class Mutation:
        @strawberry.mutation(extensions=[TransformingExtension()])
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler(), UnexpectedErrorHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "transformed: invalid value: abc"}}


def test_exception_handler_converts_field_extension_error():
    class FailingExtension(FieldExtension):
        def resolve(self, next_, source, info, **kwargs):  # noqa: ANN003
            raise CustomValidationError("extension failed")

    @strawberry.type
    class Mutation:
        @strawberry.mutation(extensions=[FailingExtension()])
        def create(self, value: str) -> Success | ValidationErrorPayload:
            return Success(value=value)

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "extension failed"}}


def test_exception_handler_does_not_convert_unmatched_field_extension_error():
    class FailingExtension(FieldExtension):
        def resolve(self, next_, source, info, **kwargs):  # noqa: ANN003
            raise UnexpectedError("extension failed")

    @strawberry.type
    class Mutation:
        @strawberry.mutation(extensions=[FailingExtension()])
        def create(self, value: str) -> Success | ValidationErrorPayload:
            return Success(value=value)

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is not None
    assert result.errors[0].message == "extension failed"
    assert result.data is None


@pytest.mark.asyncio
async def test_exception_handler_converts_async_field_extension_error():
    class FailingExtension(FieldExtension):
        async def resolve_async(self, next_, source, info, **kwargs):  # noqa: ANN003
            raise CustomValidationError("extension failed")

    @strawberry.type
    class Mutation:
        @strawberry.mutation(extensions=[FailingExtension()])
        async def create(self, value: str) -> Success | ValidationErrorPayload:
            return Success(value=value)

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = await schema.execute(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "extension failed"}}


def test_exception_handler_converts_error_transformed_by_field_extension():
    # An extension may catch the resolver's error and re-raise a mapped one;
    # the transformed exception is converted at the outermost layer.
    class TranslatingExtension(FieldExtension):
        def resolve(self, next_, source, info, **kwargs):  # noqa: ANN003
            try:
                return next_(source, info, **kwargs)
            except UnexpectedError as exc:
                raise CustomValidationError(str(exc)) from exc

    @strawberry.type
    class Mutation:
        @strawberry.mutation(extensions=[TranslatingExtension()])
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise UnexpectedError(f"unexpected value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "unexpected value: abc"}}


def test_exception_handler_converts_exception_that_blocks_attribute_assignment():
    # Some exception types (frozen dataclasses, C-extension types such as
    # pydantic's ValidationError) do not allow setting arbitrary attributes, so
    # the conversion must not depend on mutating the raised exception.
    @dataclasses.dataclass(frozen=True)
    class FrozenValidationError(Exception):
        detail: str = "frozen"

    class FrozenValidationHandler(
        strawberry.ExceptionHandler[FrozenValidationError, ValidationErrorPayload]
    ):
        def handle(
            self,
            exception: FrozenValidationError,
            *,
            field: StrawberryField,
            info: Info,
        ) -> ValidationErrorPayload:
            return ValidationErrorPayload(message=str(exception))

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise FrozenValidationError(value)

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[FrozenValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "abc"}}


def test_exception_handler_matches_reimported_error_type_definition():
    def define_reloaded_error():
        @strawberry.type
        class ReloadedError:
            message: str

        return ReloadedError

    # Two structurally identical definitions sharing a name and module, as would
    # happen if the module defining the error type were reloaded/reimported.
    OriginalReloadedError = define_reloaded_error()
    ReimportedReloadedError = define_reloaded_error()

    # ``ReimportedReloadedError`` only exists at runtime, so it cannot be a
    # type parameter — the ``error_type`` attribute covers this case.
    class ReimportedValidationHandler(
        strawberry.ExceptionHandler[CustomValidationError]
    ):
        error_type = ReimportedReloadedError

        def handle(
            self,
            exception: CustomValidationError,
            *,
            field: StrawberryField,
            info: Info,
        ):
            return OriginalReloadedError(message=str(exception))

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | OriginalReloadedError:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[ReimportedValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ReloadedError {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "invalid value: abc"}}


def test_argument_conversion_error_is_mapped_before_permissions_run():
    # Argument conversion happens before the field-extension chain, so a
    # conversion error has always bypassed field extensions such as permissions.
    # When a handler matches, the exception is mapped to a union result directly
    # and the permission never runs.
    permission_ran = False

    class Deny(BasePermission):
        message = "denied"

        def has_permission(self, source, info, **kwargs):  # noqa: ANN003
            nonlocal permission_ran
            permission_ran = True
            return False

    @strawberry.type
    class Mutation:
        @strawberry.mutation(permission_classes=[Deny])
        def create(self, input: CustomInput) -> Success | ValidationErrorPayload:
            return Success(value=input.value)

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(input: { value: "a" }) {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "value is too short"}}
    assert permission_ran is False


@pytest.mark.asyncio
async def test_exception_handler_converts_async_resolver_error_to_union_type():
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        async def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = await schema.execute(
        """
        mutation {
            create(value: "abc") {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "invalid value: abc"}}


@pytest.mark.asyncio
async def test_exception_handler_converts_awaitable_from_sync_resolver():
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | ValidationErrorPayload:
            async def resolve() -> Success | ValidationErrorPayload:
                raise CustomValidationError(f"invalid value: {value}")

            return resolve()  # type: ignore[return-value]

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = await schema.execute(
        """
        mutation {
            create(value: "abc") {
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "invalid value: abc"}}


@pytest.mark.asyncio
async def test_exception_handler_converts_async_argument_conversion_error():
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        async def create(self, input: CustomInput) -> Success | ValidationErrorPayload:
            return Success(value=input.value)

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = await schema.execute(
        """
        mutation {
            create(input: { value: "a" }) {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "value is too short"}}


@pytest.mark.asyncio
async def test_exception_handler_does_not_handle_subscription_setup_error():
    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def create(
            self, input: CustomInput
        ) -> AsyncGenerator[Success | ValidationErrorPayload, None]:
            yield Success(value=input.value)

    schema = strawberry.Schema(
        query=Query,
        subscription=Subscription,
        exception_handlers=[CustomValidationHandler()],
    )

    result_source = await schema.subscribe(
        """
        subscription {
            create(input: { value: "a" }) {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    async with aclosing(result_source) as subscription_result:
        result = await subscription_result.__anext__()

    assert isinstance(result, PreExecutionError)
    assert result.errors[0].message == "value is too short"
    assert result.data is None


def test_federation_schema_passes_exception_handlers_to_resolvers():
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, input: CustomInput) -> Success | ValidationErrorPayload:
            return Success(value=input.value)

    schema = strawberry.federation.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(input: { value: "a" }) {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "value is too short"}}


@pytest.mark.asyncio
async def test_exception_handler_converts_conversion_error_with_async_extension():
    # An async field extension `await`s the inner result, so the handled payload
    # produced on the conversion-error path must be awaitable too.
    class Allow(BasePermission):
        message = "denied"

        async def has_permission(self, source, info, **kwargs) -> bool:  # noqa: ANN003
            return True

    @strawberry.type
    class Mutation:
        @strawberry.mutation(permission_classes=[Allow])
        async def create(self, input: CustomInput) -> Success | ValidationErrorPayload:
            return Success(value=input.value)

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = await schema.execute(
        """
        mutation {
            create(input: { value: "a" }) {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "value is too short"}}


def test_exception_handler_converts_conversion_error_with_input_mutation_extension():
    # `InputMutationExtension` calls `vars(input)` on the arguments; the raw
    # values passed on the conversion-error path must not crash it before the
    # handler runs.
    @strawberry.type
    class Mutation:
        @strawberry.mutation(extensions=[InputMutationExtension()])
        def create(self, data: CustomInput) -> Success | ValidationErrorPayload:
            return Success(value=data.value)

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(input: { data: { value: "a" } }) {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "value is too short"}}


def test_exception_handler_matches_concrete_generic_error_type_in_union():
    @strawberry.type
    class GenericError(Generic[T]):
        message: str
        value: T

    class GenericHandler(
        strawberry.ExceptionHandler[CustomValidationError, GenericError[int]]
    ):
        def handle(
            self,
            exception: CustomValidationError,
            *,
            field: StrawberryField,
            info: Info,
        ) -> "GenericError[int]":
            return GenericError[int](message=str(exception), value=0)

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self) -> Success | GenericError[int]:
            raise CustomValidationError("boom")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[GenericHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create {
                ... on Success {
                    value
                }
                ... on IntGenericError {
                    message
                    intValue: value
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "boom", "intValue": 0}}


def test_exception_handler_converts_basic_field_error_to_union_type():
    # A "basic" field (a plain attribute with no resolver) whose return type is
    # a union should still have its errors converted; whether an unrelated
    # extension is attached must not change this.
    @strawberry.type
    class Query:
        ok: bool = True
        result: Success | ValidationErrorPayload

    class Root:
        ok = True

        @property
        def result(self) -> None:
            raise CustomValidationError("basic field boom")

    schema = strawberry.Schema(
        query=Query,
        exception_handlers=[CustomValidationHandler()],
    )

    result = schema.execute_sync(
        """
        {
            result {
                ... on Success {
                    value
                }
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """,
        root_value=Root(),
    )

    assert result.errors is None
    assert result.data == {"result": {"message": "basic field boom"}}


def test_exception_handler_conflicting_type_parameter_and_attribute_raises():
    # The type parameter says ``UnexpectedError`` while the attribute says
    # ``CustomValidationError``; a contradiction like this is a mistake, so it
    # should fail loudly rather than silently pick one.
    class ConflictingHandler(strawberry.ExceptionHandler[UnexpectedError]):
        exception_type = CustomValidationError
        error_type = ValidationErrorPayload

        def handle(self, exception, *, field, info) -> ValidationErrorPayload:
            return ValidationErrorPayload(message=str(exception))

    with pytest.raises(TypeError, match="conflicting exception types"):
        strawberry.Schema(query=Query, exception_handlers=[ConflictingHandler()])


def test_exception_handler_conflicting_error_type_parameter_and_attribute_raises():
    class ConflictingErrorHandler(
        strawberry.ExceptionHandler[CustomValidationError, OtherErrorPayload]
    ):
        error_type = ValidationErrorPayload

        def handle(self, exception, *, field, info) -> ValidationErrorPayload:
            return ValidationErrorPayload(message=str(exception))

    with pytest.raises(TypeError, match="conflicting GraphQL error types"):
        strawberry.Schema(query=Query, exception_handlers=[ConflictingErrorHandler()])


def test_exception_handler_attribute_fills_in_undeclared_error_type():
    # Parameterizing only the exception slot and supplying the error type via an
    # attribute is not a conflict: the slots do not overlap.
    class SplitHandler(strawberry.ExceptionHandler[CustomValidationError]):
        error_type = ValidationErrorPayload

        def handle(self, exception, *, field, info) -> ValidationErrorPayload:
            return ValidationErrorPayload(message=str(exception))

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[SplitHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "invalid value: abc"}}


def test_exception_handler_works_without_subclassing():
    class DuckHandler:
        exception_type = CustomValidationError
        error_type = ValidationErrorPayload

        def handle(self, exception, *, field, info):
            return ValidationErrorPayload(message=str(exception))

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[DuckHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "invalid value: abc"}}


def test_exception_handler_without_exception_type_raises_at_schema_creation():
    class IncompleteHandler(strawberry.ExceptionHandler):
        def handle(self, exception, *, field, info) -> None:
            return None

    with pytest.raises(TypeError, match="does not declare which exceptions it handles"):
        strawberry.Schema(query=Query, exception_handlers=[IncompleteHandler()])


def test_exception_handler_without_error_type_raises_at_schema_creation():
    class NoErrorTypeHandler(strawberry.ExceptionHandler[CustomValidationError]):
        def handle(self, exception, *, field, info) -> None:
            return None

    with pytest.raises(TypeError, match="does not declare the GraphQL error type"):
        strawberry.Schema(query=Query, exception_handlers=[NoErrorTypeHandler()])


def test_exception_handler_matches_type_widened_by_field_extension():
    # A field extension may widen the return type during ``apply`` (here from
    # ``Success`` to ``Success | ValidationErrorPayload``). Handler matching must
    # see the widened type, otherwise the SDL advertises the error member while
    # the exception silently leaks as a top-level error.
    class WidenReturnTypeExtension(FieldExtension):
        def apply(self, field: StrawberryField) -> None:
            field.type = Success | ValidationErrorPayload

        def resolve(self, next_, source, info, **kwargs):  # noqa: ANN003
            return next_(source, info, **kwargs)

    @strawberry.type
    class Mutation:
        @strawberry.mutation(extensions=[WidenReturnTypeExtension()])
        def create(self, value: str) -> Success:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CustomValidationHandler()],
    )

    # The widened type is what ends up in the SDL.
    assert "union" in schema.as_str()

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"create": {"message": "invalid value: abc"}}


def test_exception_handler_non_exception_type_raises_at_schema_creation():
    # ``int`` is a type but not an ``Exception`` subclass, so it could never
    # match a raised exception; reject it up front instead of silently never
    # matching.
    class BadHandler:
        exception_type = int
        error_type = ValidationErrorPayload

        def handle(self, exception, *, field, info):
            return ValidationErrorPayload(message=str(exception))

    with pytest.raises(TypeError, match="not a subclass of `Exception`"):
        strawberry.Schema(query=Query, exception_handlers=[BadHandler()])


def test_exception_handler_string_exception_type_raises_at_schema_creation():
    # A string is iterable, so a naive normalization would split it into
    # single-character "types"; it must be rejected whole at schema creation.
    class BadHandler:
        exception_type = "not an exception class"
        error_type = ValidationErrorPayload

        def handle(self, exception, *, field, info):
            return ValidationErrorPayload(message=str(exception))

    with pytest.raises(TypeError, match="not a subclass of `Exception`"):
        strawberry.Schema(query=Query, exception_handlers=[BadHandler()])


def test_exception_handler_protocol_is_runtime_checkable():
    assert isinstance(CustomValidationHandler(), strawberry.ExceptionHandler)


class DecliningValidationHandler(
    strawberry.ExceptionHandler[CustomValidationError, ValidationErrorPayload]
):
    """Always declines, so the original exception should propagate."""

    def handle(
        self,
        exception: CustomValidationError,
        *,
        field: StrawberryField,
        info: Info,
    ) -> ValidationErrorPayload | None:
        return None


def test_exception_handler_returning_none_reraises_original_exception():
    processed_errors = []

    class TrackingSchema(strawberry.Schema):
        def process_errors(self, errors, execution_context=None):
            processed_errors.extend(errors)

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = TrackingSchema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[DecliningValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    # Declining re-raises the original exception, so it propagates as a normal
    # GraphQL error just as if no handler had matched.
    assert result.data is None
    assert result.errors is not None
    assert result.errors[0].message == "invalid value: abc"
    assert len(processed_errors) == 1
    assert processed_errors[0].message == "invalid value: abc"


def test_exception_handler_returning_none_reraises_on_nullable_union():
    # On a nullable union the original exception must still surface as an error,
    # not silently resolve the field to null.
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | ValidationErrorPayload | None:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[DecliningValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.data == {"create": None}
    assert result.errors is not None
    assert result.errors[0].message == "invalid value: abc"


def test_exception_handler_can_decline_per_instance():
    # Match a broad exception type but only convert the instances we recognize;
    # everything else propagates untouched.
    class ConditionalHandler(
        strawberry.ExceptionHandler[CustomValidationError, ValidationErrorPayload]
    ):
        def handle(
            self,
            exception: CustomValidationError,
            *,
            field: StrawberryField,
            info: Info,
        ) -> ValidationErrorPayload | None:
            if str(exception).startswith("expose:"):
                return ValidationErrorPayload(message=str(exception))
            return None

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(value)

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[ConditionalHandler()],
    )

    query = """
        mutation ($value: String!) {
            create(value: $value) {
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
    """

    converted = schema.execute_sync(query, variable_values={"value": "expose:oops"})
    assert converted.errors is None
    assert converted.data == {"create": {"message": "expose:oops"}}

    declined = schema.execute_sync(query, variable_values={"value": "secret detail"})
    assert declined.data is None
    assert declined.errors is not None
    assert declined.errors[0].message == "secret detail"


def test_exception_handler_returning_none_reraises_argument_conversion_error():
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create(self, input: CustomInput) -> Success | ValidationErrorPayload:
            return Success(value=input.value)

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[DecliningValidationHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(input: { value: "a" }) {
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.data is None
    assert result.errors is not None
    assert result.errors[0].message == "value is too short"


@pytest.mark.asyncio
async def test_exception_handler_returning_none_reraises_on_async_field():
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        async def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[DecliningValidationHandler()],
    )

    result = await schema.execute(
        """
        mutation {
            create(value: "abc") {
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.data is None
    assert result.errors is not None
    assert result.errors[0].message == "invalid value: abc"


@pytest.mark.asyncio
async def test_async_exception_handler_resolving_to_none_reraises():
    # An async ``handle`` that awaits to ``None`` also declines.
    class AsyncDecliningHandler(
        strawberry.ExceptionHandler[CustomValidationError, ValidationErrorPayload]
    ):
        async def handle(
            self,
            exception: CustomValidationError,
            *,
            field: StrawberryField,
            info: Info,
        ) -> ValidationErrorPayload | None:
            return None

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        async def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[AsyncDecliningHandler()],
    )

    result = await schema.execute(
        """
        mutation {
            create(value: "abc") {
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.data is None
    assert result.errors is not None
    assert result.errors[0].message == "invalid value: abc"


def test_declining_handler_with_field_extension_is_called_once():
    calls = 0

    class PassthroughExtension(FieldExtension):
        def resolve(self, next_, source, info, **kwargs):  # noqa: ANN003
            return next_(source, info, **kwargs)

    class CountingDecliningHandler(
        strawberry.ExceptionHandler[CustomValidationError, ValidationErrorPayload]
    ):
        def handle(
            self,
            exception: CustomValidationError,
            *,
            field: StrawberryField,
            info: Info,
        ) -> None:
            nonlocal calls
            calls += 1

    @strawberry.type
    class Mutation:
        @strawberry.mutation(extensions=[PassthroughExtension()])
        def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CountingDecliningHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            create(value: "abc") {
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.data is None
    assert result.errors is not None
    assert result.errors[0].message == "invalid value: abc"
    assert calls == 1


@pytest.mark.asyncio
async def test_async_declining_handler_with_extension_is_called_once():
    calls = 0

    class PassthroughExtension(FieldExtension):
        async def resolve_async(self, next_, source, info, **kwargs):  # noqa: ANN003
            return await next_(source, info, **kwargs)

    class CountingDecliningHandler(
        strawberry.ExceptionHandler[CustomValidationError, ValidationErrorPayload]
    ):
        def handle(
            self,
            exception: CustomValidationError,
            *,
            field: StrawberryField,
            info: Info,
        ) -> None:
            nonlocal calls
            calls += 1

    @strawberry.type
    class Mutation:
        @strawberry.mutation(extensions=[PassthroughExtension()])
        async def create(self, value: str) -> Success | ValidationErrorPayload:
            raise CustomValidationError(f"invalid value: {value}")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[CountingDecliningHandler()],
    )

    result = await schema.execute(
        """
        mutation {
            create(value: "abc") {
                ... on ValidationErrorPayload {
                    message
                }
            }
        }
        """
    )

    assert result.data is None
    assert result.errors is not None
    assert result.errors[0].message == "invalid value: abc"
    assert calls == 1
