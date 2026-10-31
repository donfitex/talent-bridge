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


## Nigeria-wide coverage

Default location/country are now Nigeria. Run `python manage.py seed_categories` to seed the expanded 46-sector catalog. `python manage.py sync_external_jobs --all-categories --include-local --results 5` searches every catalog category plus additional active admin-created categories. For a preview add `--dry-run`. Categories describe search coverage, not a guarantee that every available Nigerian vacancy is discoverable.

The daily Actions workflow divides the catalog into eight non-overlapping, sequential shards (max one running). Each query returns at most five results per global site, separated by a three-second delay. Workers have a 15-minute timeout; provider failures are logged and the next category continues. No proxy, CAPTCHA bypass, spoofed browser identity or paid service is enabled. GitHub Actions included minutes are account-dependent; eight shards can consume more minutes than the original single query.

Global sources are LinkedIn and Indeed. ZipRecruiter targets US/Canada; Nigeria is not listed as a supported Glassdoor country in JobSpy. They are intentionally excluded from Nigeria runs rather than importing foreign results. Local adapters check robots.txt, wait two seconds between requests, enforce HTTP timeouts, reject redirects/off-domain links, limit pages and extract public JobPosting JSON-LD. HotNigerianJobs uses /hotjobs/ links and MyJobMag /job/ links. Pages without structured JobPosting records are skipped rather than guessed from unrelated HTML. A 403/429 or robots restriction skips that source; it does not trigger evasion. Local adapters currently sample recent listings, not a complete archive. Generic local roles use keyword mapping with Other Jobs fallback.
