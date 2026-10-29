# TalentBridge

A Django recruitment platform with job discovery, company hiring workspaces,
private resumes, applicant tracking, interviews and email/in-app notifications.

## Run locally

Python 3.12+ is required. In a virtual environment:

```sh
pip install -r requirements-dev.txt
# Copy .env.example to .env and set local values.
python manage.py migrate
python manage.py seed_categories
python manage.py runserver
```

Open http://localhost:8000/. Register a candidate to upload a resume and apply, or
an employer to create a company and publish vacancies. Set FRONTEND_URL to the
same origin for verification and reset links. Development email appears in the
server console. Create administration access with `python manage.py createsuperuser`.
No default administrator credentials are included.

## Implemented workflows

- Search, filter and paginate published jobs; responsive job/detail pages.
- Candidate signup, session login, profile, password recovery and email verification.
- Private PDF/DOCX uploads with validation and permission-checked downloads.
- Transactional submission, duplicate prevention, withdrawal and reapplication.
- Company-scoped employer/recruiter pipeline, safe CSV exports and status history.
- Interview scheduling with candidate/interviewer overlap checks and private feedback.
- Durable notification outbox, retryable delivery, in-app inbox and reminder commands.
- Employer reports and searchable Django administration.
- CSRF, tenant permissions, shared-cache rate limits and production settings checks.
- Health endpoints, OpenAPI, Docker/Gunicorn, GitHub Actions and Render Blueprint.

## Verify

```sh
ruff check .
ruff format --check .
pytest
coverage run -m pytest
coverage report --fail-under=70
```

SQLite is used by the fast test configuration. Real PostgreSQL concurrency and
migration instructions are in [testing](docs/testing.md). CI uses PostgreSQL and
builds the Docker image. Runtime readiness is at `/health/`; liveness is at
`/health/live/`. Interactive API docs are at `/api/docs/`.

## Documentation

- [Architecture and scaling](docs/architecture.md)
- [API and authentication](docs/api.md)
- [Development](docs/development.md)
- [Tests and concurrency](docs/testing.md)
- [Security and private media](docs/security.md)
- [Render/Docker deployment and recovery](docs/deployment.md)
- [Delivery progress](docs/PROGRESS.md)

The repository adapts the supplied engineering plan to recruitment. Event seat
capacity and waitlists are replaced with application duplicate protection and
interview scheduling. Production deployment and external email delivery require
hosting secrets and verification; see the release audit for actual evidence.
