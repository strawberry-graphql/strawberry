# Contributing to Strawberry

First off, thanks for taking the time to contribute!

The following is a set of guidelines for contributing to Strawberry on GitHub.
These are mostly guidelines, not rules. Use your best judgment, and feel free
to propose changes to this document in a pull request.

#### Table of contents

[How to contribute](#how-to-contribute)

- [Reporting bugs](#reporting-bugs)
- [Suggesting enhancements](#suggesting-enhancements)
- [Contributing to code](#contributing-to-code)

## How to contribute

### Reporting bugs

This section guides you through submitting a bug report for Strawberry.
Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

Before creating bug reports, please check
[this list](#before-submitting-a-bug-report) to be sure that you need to create
one. When you are creating a bug report, please include as many details as
possible. Make sure you include the Python and Strawberry versions.

> **Note:** If you find a **Closed** issue that seems like it is the same thing
> that you're experiencing, open a new issue and include a link to the original
> issue in the body of your new one.

#### Before submitting a bug report

- Check that your issue does not already exist in the issue tracker on GitHub.

#### How do I submit a bug report?

Bugs are tracked on the issue tracker on GitHub where you can create a new one.

Explain the problem and include additional details to help maintainers reproduce
the problem:

- **Use a clear and descriptive title** for the issue to identify the problem.
- **Describe the exact steps which reproduce the problem** in as many details as
  possible.
- **Provide specific examples to demonstrate the steps to reproduce the issue**.
  Include links to files or GitHub projects, or copy-paste-able snippets, which you use in those examples.
- **Describe the behavior you observed after following the steps** and point out
  what exactly is the problem with that behavior.
- **Explain which behavior you expected to see instead and why.**

Provide more context by answering these questions:

- **Did the problem start happening recently** (e.g. after updating to a new version of Strawberry) or was this always a problem?
- If the problem started happening recently, **can you reproduce the problem in
  an older version of Strawberry?** What's the most recent version in which the problem doesn't happen?
- **Can you reliably reproduce the issue?** If not, provide details about how
  often the problem happens and under which conditions it normally happens.

Include details about your configuration and environment:

- **Which version of Strawberry are you using?**
- **Which Python version Strawberry has been installed for?**
- **What's the name and version of the OS you're using?**

### Suggesting enhancements

This section guides you through submitting an enhancement suggestion for
Strawberry, including completely new features and minor improvements to existing
functionality. Following these guidelines helps maintainers and the community
understand your suggestion and find related suggestions.

Before creating enhancement suggestions, please check
[this list](#before-submitting-an-enhancement-suggestion) as you might find out
that you don't need to create one. When you are creating an enhancement
suggestion, please
[include as many details as possible](#how-do-i-submit-an-enhancement-suggestion).

#### Before submitting an enhancement suggestion

- Check that your issue does not already exist in the issue tracker on GitHub.

#### How do I submit an enhancement suggestion?

Enhancement suggestions are tracked on the project's issue tracker on GitHub
where you can create a new one and provide the following information:

- **Use a clear and descriptive title** for the issue to identify the
  suggestion.
- **Provide a step-by-step description of the suggested enhancement** in as many
  details as possible.
- **Provide specific examples to demonstrate the steps**.
- **Describe the current behavior** and **explain which behavior you expected to
  see instead** and why.

### Contributing to code

> This section is about contributing to
[Strawberry Python library](https://github.com/strawberry-graphql/strawberry).

#### Local development

You will need Poetry to start contributing to Strawberry. Refer to the
[documentation](https://poetry.eustace.io/docs/#introduction) to start using
Poetry.

You will first need to clone the repository using `git` and place yourself in
its directory:

```shell
$ git clone git@github.com:strawberry-graphql/strawberry.git
$ cd strawberry
```

Now, you will need to install the required dependencies for Strawberry and be sure
that the current tests are passing on your machine:

```shell
$ poetry install --with integrations
$ poetry run pytest
$ poetry run mypy
```

Some tests are known to be inconsistent. (The fix is in progress.) These tests are marked with the `pytest.mark.flaky` marker.

Strawberry uses the [black](https://github.com/ambv/black) coding style and you
must ensure that your code follows it. If not, the CI will fail and your Pull Request will not be merged.

To make sure that you don't accidentally commit code that does not follow the
coding style, you can install a pre-commit hook that will check that everything
is in order:

```shell
$ poetry run pre-commit install
```

Your code must always be accompanied by corresponding tests. If tests are not
present, your code will not be merged.

#### Pull requests

- Be sure that your pull request contains tests that cover the changed or added
  code.
- If your changes warrant a documentation change, the pull request must also
  update the documentation.

##### RELEASE.md files

When you submit a PR, make sure to include a RELEASE.md file. We use that to automatically do releases here on GitHub and, most importantly, to PyPI!

So as soon as your PR is merged, a release will be made.

Here's an example of RELEASE.md:

```text
Release type: patch

Description of the changes, ideally with some examples, if adding a new feature.
```

Release type can be one of patch, minor or major. We use [semver](https://semver.org/), so make sure to pick the appropriate type. If in doubt feel free to ask :)
