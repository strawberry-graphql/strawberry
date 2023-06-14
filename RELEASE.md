Release type: minor

This release removes our custom `__dataclass_transform__` decorator and replaces
it with typing-extension's one. It also removes parts of the mypy plugin, since
most of it is not needed anymore 🙌

This update requires typing_extensions>=4.1.0
