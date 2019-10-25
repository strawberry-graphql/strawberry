import datetime

import aniso8601

from ..custom_scalar import scalar


def _serialize_isoformatted(value):
    return value.isoformat()


Date = scalar(
    datetime.date,
    name="Date",
    description="Date (isoformat)",
    serialize=_serialize_isoformatted,
    parse_value=aniso8601.parse_date,
)
DateTime = scalar(
    datetime.datetime,
    name="DateTime",
    description="Date with time (isoformat)",
    serialize=_serialize_isoformatted,
    parse_value=aniso8601.parse_datetime,
)
Time = scalar(
    datetime.time,
    name="Time",
    description="Time (isoformat)",
    serialize=_serialize_isoformatted,
    parse_value=aniso8601.parse_time,
)
