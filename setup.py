#!/usr/bin/env python

# we use poetry for our build, but this file seems to be required
# in order to get GitHub dependencies graph to work

import setuptools

if __name__ == "__main__":
    setuptools.setup(name="strawberry-graphql")
