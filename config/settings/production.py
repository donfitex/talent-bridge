import hashlib

from django.core.exceptions import ImproperlyConfigured

from config.database import database_config

from .base import *  # noqa: F403
from .base import BASE_DIR, RESUME_STORAGE_BACKEND, env

DEBUG = False

SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# Database: Expects PostgreSQL in production
DATABASES = {"default": database_config(env)}

# HTTPS and Security Headers
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie Security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Additional Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Production Static Files (WhiteNoise)
STORAGES = {
    "default": {
        "BACKEND": "apps.resumes.storage.NeonMediaStorage"
        if RESUME_STORAGE_BACKEND == "neon"
        else "django.core.files.storage.FileSystemStorage",  # noqa: F405
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Production Logging
LOGGING["handlers"]["console"]["level"] = "INFO"  # noqa: F405
LOGGING["root"]["level"] = "INFO"  # noqa: F405
LOGGING["loggers"]["django"]["level"] = "INFO"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "INFO"  # noqa: F405


if len(SECRET_KEY) < 40 or "insecure" in SECRET_KEY or "change-me" in SECRET_KEY:
    raise ImproperlyConfigured(
        "Production requires a strong DJANGO_SECRET_KEY of at least 40 characters."
    )
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise ImproperlyConfigured("Production requires PostgreSQL DATABASE_URL.")
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Production requires explicit DJANGO_ALLOWED_HOSTS.")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
if env("CACHE_BACKEND", default="database") == "redis":
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": env("REDIS_URL"),
            "OPTIONS": {"socket_connect_timeout": 5, "socket_timeout": 5},
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "apps.common.cache.PostgresCache",
            "LOCATION": "talentbridge_cache",
            "TIMEOUT": 300,
        }
    }


SECURE_REDIRECT_EXEMPT = [r"^health/(?:live/)?$"]

# Expand high-entropy platform-generated keys to Django's preferred key length.
SECRET_KEY = hashlib.sha256(SECRET_KEY.encode()).hexdigest()
render_hostname = env("RENDER_EXTERNAL_HOSTNAME", default="")
if render_hostname:
    ALLOWED_HOSTS.append(render_hostname)
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_hostname}")
    FRONTEND_URL = env("RENDER_EXTERNAL_URL", default=f"https://{render_hostname}")
MEDIA_ROOT = env("PUBLIC_MEDIA_ROOT", default=str(BASE_DIR / "media"))

LOGGING["formatters"]["json"] = {"()": "apps.common.logging.JSONFormatter"}  # noqa: F405
LOGGING["handlers"]["console"]["formatter"] = "json"  # noqa: F405
