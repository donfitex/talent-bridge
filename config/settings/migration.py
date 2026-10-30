"""Run migrations with Neon's direct connection, without starting HTTP workers."""

from config.database import database_config

from .base import *  # noqa: F403
from .base import env

DATABASES = {"default": database_config(env, direct=True)}
