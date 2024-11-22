Release type: minor

The view classes of all integrations now have a `decode_json` method that allows
you to customize the decoding of HTTP JSON requests.

This is useful if you want to use a different JSON decoder, for example, to
optimize performance.
