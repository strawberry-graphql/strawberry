Release type: patch

Fix crash in Django's `HttpResponse.__repr__` by handling `status_code=None` in `TemporalHttpResponse.__repr__`.
