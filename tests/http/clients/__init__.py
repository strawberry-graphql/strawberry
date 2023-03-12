"""
This module provides abstracted HTTP Clients which internally
use different framework integrations.  This allows us to write
unittests that can be run for different frameworks.
"""

from .aiohttp import AioHttpClient
from .asgi import AsgiHttpClient
from .async_django import AsyncDjangoHttpClient
from .async_flask import AsyncFlaskHttpClient
from .base import HttpClient, WebSocketClient
from .chalice import ChaliceHttpClient
from .channels import ChannelsHttpClient
from .django import DjangoHttpClient
from .fastapi import FastAPIHttpClient
from .flask import FlaskHttpClient
from .sanic import SanicHttpClient
