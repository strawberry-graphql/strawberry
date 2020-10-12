Release type: patch

Extend support for parsing isoformat datetimes,
adding a dependency on the `dateutil` library.
For example: "2020-10-12T22:00:00.000Z"
can now be parsed as a datetime with a UTC timezone.
