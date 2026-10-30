"""Database configuration shared by HTTP workers and migration commands."""

from django.core.exceptions import ImproperlyConfigured


def database_config(env, *, direct=False):
    url = env("DATABASE_URL_UNPOOLED", default="") if direct else ""
    if direct and not url:
        raise ImproperlyConfigured("DATABASE_URL_UNPOOLED is required for direct migrations.")
    config = env.db_url_config(url) if direct else env.db("DATABASE_URL")
    if config["ENGINE"] == "django.db.backends.postgresql":
        config["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=0)
        config["CONN_HEALTH_CHECKS"] = True
        config["DISABLE_SERVER_SIDE_CURSORS"] = True
        config.setdefault("OPTIONS", {})["connect_timeout"] = 10
        if ".neon.tech" in config.get("HOST", ""):
            config["OPTIONS"]["sslmode"] = "require"
        if direct and "-pooler" in config.get("HOST", ""):
            raise ImproperlyConfigured("Migration connections must use the direct Neon hostname.")
    return config
