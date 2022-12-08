Release type: minor

This release introduces a `encode_json` method on all the HTTP integrations.
This method allows to customize the encoding of the JSON response. By default we
use `json.dumps` but you can override this method to use a different encoder.

It also deprecates `json_encoder` and `json_dumps_params` in the Django and
Sanic views, `encode_json` should be used instead.
