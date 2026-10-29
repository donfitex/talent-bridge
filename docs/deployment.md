# Production deployment

## Render

The validated `render.yaml` provisions new TalentBridge resources in Frankfurt:
paid web compute with a 1 GB media disk, smallest non-expiring paid PostgreSQL,
free Redis-compatible cache, and a five-minute notification/reminder cron job.
Names are unique to this project and do not modify unrelated workspace services.
The web service runs migrations before deployment, serves built static assets via
WhiteNoise, checks `/health/`, and uses the hostname Render assigns automatically.
The default onrender.com URL needs no custom domain. Billing and SMTP setup are
required before applying the Blueprint.

Set EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD and DEFAULT_FROM_EMAIL in
Render's secure Blueprint setup; SMTP uses port 587 and TLS by default. Cron obtains
these settings from the web service. Both use the same database/cache. Do not commit
any actual credentials. If your provider requires port 465, set EMAIL_USE_SSL=True and EMAIL_USE_TLS=False.

Push main, create a Blueprint from
https://dashboard.render.com/blueprint/new?repo=https://github.com/donfitex/talent-bridge,
review resources, provide secrets, apply, and wait for the specific deploy to be live.
Complete Git OAuth if Render requests it. The source commit must be on origin/main.

After live: verify HTTPS /health/, /api/v1/jobs/, /accounts/login/, candidate signup,
company/vacancy creation, resume upload/download, applying, withdrawal, employer
pipeline, interview creation, notification dispatch, and email receipt. Create the
first administrator with the Render shell and createsuperuser; never use a default
password. Recheck persistence after restart. Verify the cron's most recent run.

## Docker outside Render

Set a strong DJANGO_SECRET_KEY, explicit DJANGO_ALLOWED_HOSTS,
CSRF_TRUSTED_ORIGINS, FRONTEND_URL, SMTP configuration and POSTGRES_PASSWORD in .env.
Use a URL-safe database password or URL-encode it for DATABASE_URL.
`docker compose build`, then `docker compose up -d db redis`,
`docker compose run --rm web python manage.py migrate --noinput`, and
`docker compose up -d web`.
Place an HTTPS reverse proxy in front of loopback port 8000. Schedule
`python manage.py queue_interview_reminders` and
`python manage.py dispatch_notifications` at least every five minutes using the same
production environment. Use the readiness endpoint over HTTPS and configure alerts.

## Backups, upgrades and rollback

Before migrations, take an encrypted PostgreSQL backup and a private/public media
snapshot. Record commit and migration versions. Restore into an isolated database
and verify row counts, login and authorized downloads before relying on backups.
A code rollback does not undo database migrations or mail delivery. Use compatible
forward migrations or a reviewed restore plan. Monitor structured application logs,
5xx rates, latency, database connections/disk and pending/failed outbox counts.

A Render persistent disk restricts this initial deployment to one web instance and
interrupts deploys briefly. Move uploads to private object storage before horizontal
scaling. No backup restore drill, custom-domain DNS, mailbox deliverability or
load-capacity claim is implied by repository tests.
