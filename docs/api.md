# API

Interactive documentation: `/api/docs/`. Machine-readable OpenAPI: `/api/schema/`.
Generate/validate with `python manage.py spectacular --file tmp/openapi.yaml --validate
--fail-on-warn --settings=config.settings.testing` (create tmp first).

All JSON success responses use `{ "data": ... }`, optionally with `message`.
Paginated lists place `count`, `next`, `previous` and `results` inside `data`.
Errors use `{ "error": { "code": "...", "message": "...", "details": {} } }`.
Common codes: 400 invalid input, 403 unauthorized/unauthenticated session, 404 missing
or inaccessible object, 409 duplicate or invalid transition, 429 rate limit,
500 unexpected internal failure. Responses do not expose exception details.

## Sessions and CSRF

GET `/api/v1/auth/csrf/`, retain the cookie, then send its value as `X-CSRFToken`
on login and every authenticated unsafe request. Use same-origin credentials.
The HTML forms include CSRF tokens automatically. Logout requires POST.
Basic authentication is disabled. Cookie sessions work in the browsable API.

## Endpoints

| Prefix | Operations |
| --- | --- |
| `/api/v1/auth/` | register/candidate, register/employer, login, logout, me, password/change, password/reset, password/reset/confirm, verify-email, deactivate |
| `/api/v1/jobs/` | Published discovery/detail; `POST {id}/apply/` with resume_id and optional cover_letter |
| `/api/v1/job-categories/`, `/api/v1/skills/` | Taxonomy discovery/creation according to role |
| `/api/v1/companies/` | Profiles and owner/admin-controlled memberships |
| `/api/v1/candidates/` | Self profile and privacy-aware discovery |
| `/api/v1/resumes/` | Upload/manage/default and authorized `{id}/download/` |
| `/api/v1/applications/` | Candidate list/detail and `{id}/withdraw/` |
| `/api/v1/employer/jobs/` | CRUD, publish, pause, close, reopen, duplicate |
| `/api/v1/employer/applications/` | Company-scoped list/detail, `{id}/transition/`, CSV export |
| `/api/v1/interviews/` | Candidate read access; employer scheduling and PATCH status/feedback |
| `/api/v1/notifications/` | Own messages and `{id}/read/` |
| `/api/v1/employer/reports/` | Company-scoped counts and pipeline |

Pipeline: SUBMITTED -> UNDER_REVIEW -> SHORTLISTED -> INTERVIEW -> OFFERED -> HIRED.
REJECTED is available from each intermediate stage. Candidate withdrawal is allowed
before HIRED/REJECTED/WITHDRAWN. Reapplication is allowed after withdrawal.
Notes and feedback are employer-only; candidates receive safe status history.
Scheduling requires INTERVIEW stage. Rescheduling cancels the old appointment and
creates another; COMPLETED and CANCELLED appointments cannot be modified.
