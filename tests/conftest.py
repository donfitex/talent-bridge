import pytest
from rest_framework.test import APIClient

from tests.test_applications import recruitment  # noqa: F401


@pytest.fixture
def api_client():
    """Returns an unauthenticated DRF APIClient."""
    return APIClient()
