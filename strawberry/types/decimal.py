import decimal

from ..custom_scalar import scalar


Decimal = scalar(
    decimal.Decimal,
    name="Decimal",
    description="Date (isoformat)",
    serialize=str,
    parse_value=decimal.Decimal,
)
