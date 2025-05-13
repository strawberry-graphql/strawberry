---
title: Integrations
---

# Integration

Strawberry can be used with a variety of web frameworks and libraries. Here is a
list of the integrations along with the features they support.

Note, this table is not up to date, and this page shouldn't be linked anywhere
(yet).

| name                        | Supports sync | Supports async       | Supports subscriptions via websockets | Supports subscriptions via multipart HTTP | Supports file uploads | Supports batch queries |
| --------------------------- | ------------- | -------------------- | ------------------------------------- | ----------------------------------------- | --------------------- | ---------------------- |
| [django](./django.md)       | ✅            | ✅ (with Async view) | ❌ (use Channels for websockets)      | ✅ (From Django 4.2)                      | ✅                    | ❌                     |
| [starlette](./starlette.md) | ✅            | ✅                   | ✅                                    | ✅                                        | ✅                    | ✅                     |
| [aiohttp](./aiohttp.md)     | ✅            | ✅                   | ✅                                    | ✅                                        | ✅                    | ✅                     |
| [flask](./flask.md)         | ✅            | ✅                   | ❌                                    | ❌                                        | ✅                    | ✅                     |
| [channels](./channels.md)   | ✅            | ✅                   | ✅                                    | ❌                                        | ✅                    | ✅                     |
| [fastapi](./fastapi.md)     | ✅            | ✅                   | ✅                                    | ✅                                        | ✅                    | ✅                     |
