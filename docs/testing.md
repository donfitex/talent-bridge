# Verification

Fast checks: `pytest` (SQLite; the PostgreSQL-only concurrency test is skipped).
`coverage run -m pytest` and `coverage report --fail-under=70` measure application
coverage. The suite covers models, business rules, ownership, pipeline transitions,
private media, CSRF, rate limits, tokens, notifications, interviews, health, HTML
journeys and admin pages. CI also applies actual migrations and builds Docker.

## PostgreSQL

Start the isolated disposable service:
`docker compose -f compose.test.yml up -d --wait`.
Set DJANGO_SETTINGS_MODULE=config.settings.testing_postgres and
TEST_DATABASE_URL=postgres://talentbridge_test:local-test-only@127.0.0.1:55432/talentbridge_test.
Then run `python manage.py migrate --noinput` and
`pytest -o addopts=--strict-markers`. Overriding addopts removes --no-migrations so
Django applies real migrations. No production connection belongs in TEST_DATABASE_URL.

The race test uses four independent connections synchronized at a barrier. Exactly
one request must submit and three must receive a duplicate conflict. Test PostgreSQL
is exposed only on loopback. Stop it with `docker compose -f compose.test.yml down`.

Review failures before repeating checks. The release audit records actual outcomes;
a generated CI workflow alone is not evidence that GitHub Actions passed.
