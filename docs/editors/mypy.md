---
title: Mypy
---

# Mypy

Strawberry comes with support for
[Mypy](https://mypy.readthedocs.io/en/stable/), a popular static type checker
for Python.

This guide will explain how to configure Mypy to work with Strawberry.

## Install Mypy

The first thing we need to do is to install
[Mypy](https://mypy.readthedocs.io/en/stable/), this is the tool that will
perform the type checking.

Once the tool is installed, we need to configure it to enable type checking and
use the Strawberry plugin. To do so we need to create a `mypy.ini` file in the
root of our project and add the following settings:

```ini
[mypy]
plugins = strawberry.ext.mypy_plugin
```

You can also configure Mypy inside the `pyproject.toml` file, like so:

```toml
[tool.mypy]
plugins = ["strawberry.ext.mypy_plugin"]
```

Once you have configured the settings, you can run `mypy` and you should be
getting type checking errors.
