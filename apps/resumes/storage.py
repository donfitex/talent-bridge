from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.deconstruct import deconstructible
from django.utils.functional import cached_property
from storages.backends.s3 import S3Storage


@deconstructible
class PrivateResumeStorage(Storage):
    """Private storage with stable migration identity and an environment-selected backend."""

    @cached_property
    def backend(self):
        if settings.RESUME_STORAGE_BACKEND == "local":
            return FileSystemStorage(location=settings.RESUME_STORAGE_DIR, base_url=None)
        if settings.RESUME_STORAGE_BACKEND != "neon":
            raise ImproperlyConfigured("RESUME_STORAGE_BACKEND must be local or neon.")
        if not all(
            [
                settings.AWS_ENDPOINT_URL_S3,
                settings.AWS_ACCESS_KEY_ID,
                settings.AWS_SECRET_ACCESS_KEY,
            ]
        ):
            raise ImproperlyConfigured("Neon Object Storage credentials and endpoint are required.")
        return NeonObjectStorage()

    def _open(self, name, mode="rb"):
        return self.backend.open(name, mode)

    def _save(self, name, content):
        return self.backend.save(name, content)

    def exists(self, name):
        return self.backend.exists(name)

    def delete(self, name):
        return self.backend.delete(name)

    def size(self, name):
        return self.backend.size(name)

    def path(self, name):
        return self.backend.path(name)

    def url(self, name):
        raise ValueError("Private resumes require an authorized download endpoint.")


class NeonObjectStorage(S3Storage):
    def __init__(self, **kwargs):
        from botocore.config import Config

        options = {
            "bucket_name": settings.NEON_STORAGE_BUCKET,
            "endpoint_url": settings.AWS_ENDPOINT_URL_S3,
            "region_name": settings.AWS_REGION,
            "access_key": settings.AWS_ACCESS_KEY_ID,
            "secret_key": settings.AWS_SECRET_ACCESS_KEY,
            "security_token": settings.AWS_SESSION_TOKEN or None,
            "addressing_style": "path",
            "signature_version": "s3v4",
            "default_acl": None,
            "file_overwrite": False,
            "querystring_auth": True,
            "object_parameters": {"CacheControl": "private, no-store"},
            "client_config": Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                connect_timeout=10,
                read_timeout=30,
                retries={"mode": "standard", "max_attempts": 3},
            ),
        }
        options.update(kwargs)
        super().__init__(**options)


class NeonMediaStorage(NeonObjectStorage):
    def __init__(self):
        super().__init__(location="media")
