import datetime
import decimal
import uuid
from operator import methodcaller

import dateutil.parser

from strawberry.custom_scalar import scalar


isoformat = methodcaller("isoformat")


Date = scalar(
    datetime.date,
    name="Date",
    description="Date (isoformat)",
    serialize=isoformat,
    parse_value=datetime.date.fromisoformat,
)
DateTime = scalar(
    datetime.datetime,
    name="DateTime",
    description="Date with time (isoformat)",
    serialize=isoformat,
    parse_value=dateutil.parser.isoparse,
)
Time = scalar(
    datetime.time,
    name="Time",
    description="Time (isoformat)",
    serialize=isoformat,
    parse_value=datetime.time.fromisoformat,
)

Decimal = scalar(
    decimal.Decimal,
    name="Decimal",
    description="Decimal (fixed-point)",
    serialize=str,
    parse_value=decimal.Decimal,
)

UUID = scalar(
    uuid.UUID,
    name="UUID",
    serialize=str,
    parse_value=uuid.UUID,
)
