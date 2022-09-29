Release type: minor

This release adds support for the following options in all our HTTP integrations:

- `json_encoder`: optional JSON encoder, defaults to `json.JSONEncoder`, will
  be used to serialize the data.
- `json_dumps_params`: optional dictionary of keyword arguments to pass to the
  `json.dumps` call used to generate the response. To get the most compact JSON
  representation, you should specify `{"separators": (",", ":")}`, defaults to
  `None`.
