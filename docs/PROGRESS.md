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


## Completed commits

| Commit | Phase | Evidence |
| --- | --- | --- |
| 432cf81 | Candidate application management | 3 passing tests |
| 3c126f1 | Employer ATS and status audit | 4 passing tests |
| dc8a47a | Interviews, outbox, reports | 6 passing tests |
| 4430ad2 | Public, candidate, employer and admin interfaces | 8 passing tests |
| e76571c | Private files, tenant boundaries and auth security | 13 passing tests |
| dbd68e9 | Testing, quality, API/health and production configuration | 19 PostgreSQL tests passed, fresh migrations passed |

The PostgreSQL run includes four concurrent submissions: one success and three
409 duplicate responses. Coverage at that checkpoint: 81%. OpenAPI generated and
validated with zero warnings/errors. Ruff and Django checks passed. Browser review
confirmed the responsive discovery page and empty state.

Deployment target confirmed: Render, My Workspace (tea-d5o00a6r433s73bf2fug).
No existing TalentBridge services were found. render.yaml defines separate resources.
SMTP values, infrastructure billing review and live smoke checks remain external
release requirements; they are not marked complete by local test results.


Latest verification: 22 tests passed against PostgreSQL, 82% coverage. Production
Docker build succeeded locally and in GitHub Actions. CI run 40933236244 passed
for 46999b9. The deployment review reached a Render payment-method requirement;
SMTP credentials and live verification are also pending. See RELEASE_AUDIT.md.
Additional commits: ceeadaf (token/privacy fixes), 1d5db04 (containers/CI), f32302d
(interview cancellation consistency), 46999b9 (Render Blueprint/runbooks).


Final user direction: keep Render deployment prepared without activating paid
resources. Brevo selected for transactional email; host/port/TLS are configured,
with SMTP login/key/verified sender intentionally left for secure deployment setup.
No paid infrastructure or live deployment was activated.


## 30 October: Neon and free Render

User selected Neon instead of AWS for both PostgreSQL and file storage. Linked
calm-cell-51299624 / production, deployed private uploads bucket, pulled credentials
into the ignored .env, applied existing migrations and seeded categories.

Real Files SDK upload/list/download passed for an 89-byte text file; its contents
matched. Real Django CV API checks passed (201 upload, 200 matching download,
403 cross-candidate access). Synthetic database rows were rolled back and the CV
verification object removed. The text verification object remains for inspection.
Local HTTP checks for health, jobs, home and login all returned 200. npm run build
passed. Django tests force local storage and never use the production database.

Render configuration now uses a free web service, no paid disk/database/cron and
no additional Redis service. Shared cache counters are stored on Neon and updates
lock rows. Prepared Brevo SMTP uses port 2525 for Render free compatibility. A
remote Render web deployment and SMTP delivery remain unclaimed; no AWS resources
or paid Render resources were activated.
