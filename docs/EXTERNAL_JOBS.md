# External job import

Run `python manage.py sync_external_jobs` after installing requirements and running migrations. Defaults: Software Engineer, Remote, Indeed USA, 15 results per site, last 72 hours. Sources can fail or return no results; JobSpy does not guarantee access or bypass restrictions.

Preview without writes:

```sh
python manage.py sync_external_jobs --dry-run
python manage.py sync_external_jobs --search-term "Python Developer" --location "Lagos" --country Nigeria --results 10 --hours-old 72
```

Imports use the validated Django ORM service, not an HTTP call to our own API. A unique source_url prevents repeated imports. Tracking parameters are removed; Indeed job keys are preserved. Imported companies have no employer memberships and remain unverified. Listings enter PENDING_REVIEW. Admins filter Jobs by source and status, review the original listing, and publish selected records. Public listings link to the original board; local applications are disabled for imported jobs. Employer approval rules remain unchanged.

The command does not install an in-process scheduler. For a free schedule, run it once daily from your existing machine with cron or Windows Task Scheduler, using this checkout's virtualenv Python, repository working directory and ignored production environment file. Example cron: `0 7 * * * cd /path/to/talent-bridge && .venv/bin/python manage.py sync_external_jobs >> /path/to/private-sync.log 2>&1`. Do not run it on every web worker or expose a public sync endpoint. Render free services lack paid cron/SSH facilities; no paid resource is provisioned. Scheduler must have access to Neon, and logs must remain private.

Dependencies: https://github.com/speedyapply/JobSpy

The repository also includes `.github/workflows/external-jobs.yml`: daily at 07:00 UTC (08:00 Africa/Lagos), with manual Run workflow support, one concurrent run and a ten-minute timeout. Set repository secret EXTERNAL_JOBS_DATABASE_URL to the pooled Neon URL. The workflow imports pending-review records only. GitHub Actions availability and included minutes depend on the repository/account plan.
