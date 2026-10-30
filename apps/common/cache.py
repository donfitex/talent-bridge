from django.core.cache.backends.db import DatabaseCache
from django.db import connections, router, transaction


class PostgresCache(DatabaseCache):
    """Shared counters without another paid service; increments lock their cache row."""

    def incr(self, key, delta=1, version=None):
        alias = router.db_for_write(self.cache_model_class)
        connection = connections[alias]
        if connection.vendor != "postgresql":
            return super().incr(key, delta, version)
        normalized_key = self.make_and_validate_key(key, version=version)
        table = connection.ops.quote_name(self._table)
        with transaction.atomic(using=alias):
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT cache_key FROM {table} WHERE cache_key = %s FOR UPDATE",
                    [normalized_key],
                )
                if cursor.fetchone() is None:
                    raise ValueError("Cache key is missing")
            return super().incr(key, delta, version)
