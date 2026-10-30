import environ
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from apps.resumes.storage import PrivateResumeStorage
from config.database import database_config


def test_neon_pooled_configuration(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://test:fake@ep-example-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require",
    )
    monkeypatch.setenv("CONN_MAX_AGE", "0")
    config = database_config(environ.Env())
    assert config["DISABLE_SERVER_SIDE_CURSORS"] is True
    assert config["CONN_HEALTH_CHECKS"] is True
    assert config["CONN_MAX_AGE"] == 0
    assert config["OPTIONS"]["sslmode"] == "require"


def test_direct_migrations_reject_pooler(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL_UNPOOLED", "postgres://test:fake@ep-example-pooler.neon.tech/neondb"
    )
    with pytest.raises(ImproperlyConfigured, match="direct"):
        database_config(environ.Env(), direct=True)
    monkeypatch.setenv("DATABASE_URL_UNPOOLED", "postgres://test:fake@ep-example.neon.tech/neondb")
    assert "-pooler" not in database_config(environ.Env(), direct=True)["HOST"]


def test_private_neon_storage_configuration():
    with override_settings(
        RESUME_STORAGE_BACKEND="neon",
        AWS_ENDPOINT_URL_S3="https://storage.example.test",
        AWS_ACCESS_KEY_ID="test-access",
        AWS_SECRET_ACCESS_KEY="test-secret",
        AWS_REGION="us-east-2",
        NEON_STORAGE_BUCKET="uploads",
    ):
        storage = PrivateResumeStorage()
        assert storage.backend.bucket_name == "uploads"
        assert storage.backend.addressing_style == "path"
        assert storage.backend.default_acl is None
        with pytest.raises(ValueError, match="authorized"):
            storage.url("resumes/test.pdf")


def test_missing_storage_credentials_fail_closed():
    with override_settings(
        RESUME_STORAGE_BACKEND="neon",
        AWS_ENDPOINT_URL_S3="",
        AWS_ACCESS_KEY_ID="",
        AWS_SECRET_ACCESS_KEY="",
    ):
        with pytest.raises(ImproperlyConfigured):
            PrivateResumeStorage().exists("resumes/test.pdf")
