---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! This release adds support for Django 6.0
    and 6.1, and drops Django older than 5.2, which reached end of life. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release adds support for Django 6.0
    and 6.1, and drops Django older than 5.2, which reached end of life. Django
    5.2 LTS is now the minimum supported version.
---

This release adds support for Django 6.0 and 6.1, and drops support for Django
older than 5.2.

Django 4.2, 5.0 and 5.1 have all reached end of life. Django 5.2 LTS is now the
minimum supported version, and the test suite runs against Django 5.2, 6.0 and
6.1.

If you are still on one of the dropped versions, we strongly recommend
upgrading to Django 5.2 or newer: unmaintained releases no longer get security
fixes.
