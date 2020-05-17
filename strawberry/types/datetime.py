import datetime
from operator import methodcaller

from ..custom_scalar import scalar


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
    parse_value=datetime.datetime.fromisoformat,
)
Time = scalar(
    datetime.time,
    name="Time",
    description="Time (isoformat)",
    serialize=isoformat,
    parse_value=datetime.time.fromisoformat,
)
