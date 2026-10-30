from pathlib import Path

import environ

from config.database import database_config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_SECRET_KEY=(str, "django-insecure-talentbridge-secret-key-change-in-production"),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    DATABASE_URL=(str, f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
    FRONTEND_URL=(str, "http://localhost:3000"),
    PRODUCTION_DOMAIN=(str, "talentbridge.example.com"),
    RESUME_STORAGE_DIR=(str, str(BASE_DIR / "private_media" / "resumes")),
    MAX_RESUME_SIZE_MB=(int, 5),
    EMAIL_BACKEND=(str, "django.core.mail.backends.console.EmailBackend"),
    EMAIL_HOST=(str, "localhost"),
    EMAIL_PORT=(int, 1025),
    EMAIL_HOST_USER=(str, ""),
    EMAIL_HOST_PASSWORD=(str, ""),
    EMAIL_USE_TLS=(bool, False),
    DEFAULT_FROM_EMAIL=(str, "TalentBridge <noreply@talentbridge.com>"),
)

# Read .env file if it exists
env_file = BASE_DIR / ".env"
if not env_file.exists():
    env_file = BASE_DIR / ".env.local"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.common.apps.CommonConfig",
    "apps.users.apps.UsersConfig",
    "apps.companies.apps.CompaniesConfig",
    "apps.jobs.apps.JobsConfig",
    "apps.candidates.apps.CandidatesConfig",
    "apps.resumes.apps.ResumesConfig",
    "apps.applications.apps.ApplicationsConfig",
    "apps.interviews.apps.InterviewsConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.reports.apps.ReportsConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {"default": database_config(env)}

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
PRIVATE_MEDIA_ROOT = BASE_DIR / "private_media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email Configuration
EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

# Front-end and business variables
FRONTEND_URL = env("FRONTEND_URL")
PRODUCTION_DOMAIN = env("PRODUCTION_DOMAIN")
RESUME_STORAGE_DIR = Path(env("RESUME_STORAGE_DIR"))
MAX_RESUME_SIZE_MB = env("MAX_RESUME_SIZE_MB")

# REST Framework Configuration
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler",
}

# DRF Spectacular OpenAPI documentation
SPECTACULAR_SETTINGS = {
    "TITLE": "TalentBridge API",
    "DESCRIPTION": "Production-ready REST API for Job Discovery, Recruitment & Applicant Tracking Platform",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Base Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}:{lineno} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"

AUTH_RATE_LIMIT = env.int("AUTH_RATE_LIMIT", default=30)
MIDDLEWARE.insert(3, "apps.common.security.AuthenticationRateLimitMiddleware")
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "rest_framework.authentication.SessionAuthentication"
]
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [
    "rest_framework.throttling.AnonRateThrottle",
    "rest_framework.throttling.UserRateThrottle",
]
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {"anon": "120/min", "user": "600/min"}
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "apps.common.renderers.EnvelopeJSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

SPECTACULAR_SETTINGS["ENUM_NAME_OVERRIDES"] = {
    "UserRoleEnum": "apps.users.models.UserRole.choices",
    "MembershipRoleEnum": "apps.companies.models.EmployerRole.choices",
    "ApplicationStatusEnum": "apps.applications.models.ApplicationStatus.choices",
    "JobStatusEnum": "apps.jobs.models.JobStatus.choices",
}

SPECTACULAR_SETTINGS["POSTPROCESSING_HOOKS"] = [
    "drf_spectacular.hooks.postprocess_schema_enums",
    "apps.common.schema.envelope_responses",
]

EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=10)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)

# Neon Object Storage uses S3 protocol variables injected by neon deploy.
RESUME_STORAGE_BACKEND = env("RESUME_STORAGE_BACKEND", default="local")
NEON_STORAGE_BUCKET = env("NEON_STORAGE_BUCKET", default="uploads")
AWS_ENDPOINT_URL_S3 = env("AWS_ENDPOINT_URL_S3", default="")
AWS_REGION = env("AWS_REGION", default="us-east-2")
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
AWS_SESSION_TOKEN = env("AWS_SESSION_TOKEN", default="")

CACHE_BACKEND = env("CACHE_BACKEND", default="local")
if CACHE_BACKEND == "database":
    CACHES = {
        "default": {
            "BACKEND": "apps.common.cache.PostgresCache",
            "LOCATION": "talentbridge_cache",
            "TIMEOUT": 300,
        }
    }

if RESUME_STORAGE_BACKEND == "neon":
    STORAGES = {
        "default": {"BACKEND": "apps.resumes.storage.NeonMediaStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
