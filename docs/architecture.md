# Architecture

TalentBridge is a Django modular monolith. API views validate request shapes and
permissions; services own transactional business rules; models enforce persistent
relationships and constraints. HTML views reuse the same domain services.

- users: email identity, candidate/employer/recruiter/admin roles, sessions, password
  reset and purpose-separated email verification tokens.
- companies: company profiles and active memberships. Only owners/admins manage
  memberships. Recruiters can manage vacancies and applications for their companies.
- jobs: published discovery, skills, categories, filtering, lifecycle operations.
- candidates/resumes: professional profiles, visibility controls and private files.
- applications: submission, withdrawal, company-scoped pipeline and append-only
  history through the service layer. Candidate responses exclude internal notes.
- interviews: future appointments, duration validation, company interviewers,
  overlapping candidate/interviewer protection and status updates.
- notifications: durable in-app/email outbox, retries and deduplication keys.
- reports: company-scoped vacancy and application pipeline counts.

## Transaction boundaries

Submission locks candidate then job before testing duplicate eligibility. A partial
unique constraint is the final defense against concurrent active applications.
Withdrawal and employer transitions lock the application before checking its state.
Interview scheduling locks application, interviewer and candidate before checking
appointments. PostgreSQL is required for production and concurrency verification.
SQLite is a convenience for fast development tests, not evidence of row locking.

Outbox rows are written in the domain transaction. SMTP occurs in a separate worker
command. Delivery is at least once: a process failure after SMTP acceptance and before
recording sent_at can cause redelivery. Ten failed attempts require operator review.
Status history is append-only via services/admin; database superusers and bulk SQL
can still modify rows. This is an audit trail, not a cryptographic tamper-proof log.

## Scaling

Public lists use pagination; company and candidate relations use select_related and
prefetch_related. Indexed foreign keys and status/date indexes support discovery and
ATS queries. Redis shares API/authentication counters between Gunicorn workers.

The initial Render configuration runs one web instance with a persistent media disk.
Horizontal web scaling requires replacing local media with private object storage
and testing the replacement's signed or authorized download behavior. PostgreSQL and
the outbox remain shared across instances. Increase compute and database connection
limits based on observed traffic, not worker count alone.
