MISSING_RELEASE_FILE = """\
Hi, thanks for contributing to Strawberry 🍓!

We noticed that this PR is missing a `RELEASE.md` file. \
We use that to automatically do releases here on GitHub and, \
most importantly, to PyPI!

So as soon as this PR is merged, a release will be made 🚀.

Here's an example of `RELEASE.md`:

```markdown
Release type: patch

Description of the changes, ideally with some examples, if adding a new feature.
```

Release type can be one of patch, minor or major. We use [semver](https://semver.org/),\
so make sure to pick the appropriate type. If in doubt feel free to ask :)
"""

RELEASE_FILE_ADDED = """
Thanks for adding the `RELEASE.md` file!

![](https://media.giphy.com/media/xq1FxHkABwW7m/giphy.gif)

Here's a preview of the changelog:

```markdown
{changelog_preview}
```
"""

INVALID_RELEASE_FILE = """\
Thanks for adding the release file! Unfortunately it does seem to be \
invalid. Make sure it looks like the following example:

```markdown
Release type: patch

Description of the changes, ideally with some examples, if adding a new feature.
```
"""
