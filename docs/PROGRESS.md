# TalentBridge delivery ledger

Scope confirmed: adapt the EventHub master plan to recruitment. Preserve the existing
TalentBridge models and APIs. Event registration becomes job application submission;
event capacity and waitlists do not apply to recruitment. Use transactional duplicate
prevention, application state transitions and interview scheduling instead.

Starting point: `025dfcd`, application submission. Candidate application views and
route registration were already present as uncommitted work and are being completed.

Remaining delivery phases (each validated and committed on main):

1. Candidate application management, transactional submission and withdrawal.
2. Employer applicant tracking, immutable status history and company authorization.
3. Interview scheduling, notifications, reminders and recruitment reports.
4. Administrative management and public/candidate/employer web workflows.
5. Security, model/service/API/concurrency/journey tests and query optimization.
6. OpenAPI, linting, Docker, Gunicorn, static/private media, CI and health checks.
7. Deployment runbook and evidence-based release audit. A live deployment requires
   an actual hosting target, production credentials, domain and email configuration.

Baseline: Django system check passes; repository originally contains no tests.
