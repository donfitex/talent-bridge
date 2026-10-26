import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Returns an unauthenticated DRF APIClient."""
    return APIClient()
