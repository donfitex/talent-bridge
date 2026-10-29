from .base import env
from .testing import *  # noqa: F403

DATABASES = {"default": env.db("TEST_DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = 0
