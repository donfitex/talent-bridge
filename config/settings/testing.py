import tempfile
from pathlib import Path
from .base import *  # noqa: F403

DEBUG = False

SECRET_KEY = "test-secret-key-talentbridge-testing-purposes-only"

ALLOWED_HOSTS = ["*"]

# Isolated fast in-memory database for testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Accelerated password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# In-memory email backend for inspecting outbound emails during tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Temporary directory for file uploads during test runs
TEST_TEMP_DIR = Path(tempfile.mkdtemp())
MEDIA_ROOT = TEST_TEMP_DIR / "media"
PRIVATE_MEDIA_ROOT = TEST_TEMP_DIR / "private_media"
RESUME_STORAGE_DIR = PRIVATE_MEDIA_ROOT / "resumes"

# Minimize noise in test output
LOGGING["loggers"]["apps"]["level"] = "WARNING"  # noqa: F405
LOGGING["loggers"]["django"]["level"] = "WARNING"  # noqa: F405
