import decimal

from ..custom_scalar import scalar


Decimal = scalar(
    decimal.Decimal,
    name="Decimal",
    description="Decimal (fixed-point)",
    serialize=str,
    parse_value=decimal.Decimal,
)
