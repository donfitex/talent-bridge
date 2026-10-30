import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.db import close_old_connections, connection
from django.test import override_settings


@pytest.mark.django_db(transaction=True)
def test_shared_cache_counter_is_atomic():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row locks are required.")
    backend = {
        "default": {"BACKEND": "apps.common.cache.PostgresCache", "LOCATION": "test_neon_cache"}
    }
    with override_settings(CACHES=backend):
        call_command("createcachetable", verbosity=0)
        key = "counter:" + uuid.uuid4().hex
        assert cache.add(key, 0)
        barrier = Barrier(4)

        def increment(_):
            close_old_connections()
            try:
                barrier.wait(timeout=20)
                for _ in range(5):
                    cache.incr(key)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(increment, range(4)))
        assert cache.get(key) == 20
        cache.delete(key)
