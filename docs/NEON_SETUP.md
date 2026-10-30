# Neon integration

Project: calm-cell-51299624. Organization: org-steep-field-51623490.
Branch: production (br-dark-smoke-b52wnp22). Region: us-east-2.
The private uploads bucket stores CVs under resumes/ and general media under media/.
Neon supplies both PostgreSQL and Object Storage. No AWS account, S3 bucket or KMS
key is used. The AWS_* names are Neon's standard S3-protocol connection variables.

## Local setup

Install the Neon CLI and sign in with neon login if needed. Then:

```sh
neon init -y --project-id calm-cell-51299624 --branch production --services postgres,object-storage
neon config add bucket uploads
neon config plan
neon deploy
```

The deployment writes credentials to the ignored .env (or .env.local when no .env
exists). It does not host Django or deploy Render. Do not commit either env file or
.neon. The CLI also installs agent tooling; initial setup reported a missing Copilot
CLI and installed skills/MCP as its fallback. No browser login was needed because
the CLI already had valid OAuth credentials.

Set RESUME_STORAGE_BACKEND=neon, NEON_STORAGE_BUCKET=uploads and
CACHE_BACKEND=database. Preserve all DATABASE_URL, DATABASE_URL_UNPOOLED,
AWS_ENDPOINT_URL_S3, AWS_REGION, AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY values
pulled by Neon. The deployment leaves authentication in Django.

Django continues using psycopg. DATABASE_URL is pooled for requests; migration.py
requires DATABASE_URL_UNPOOLED and rejects a pooler hostname. Health checks,
server-side cursor disabling, a connection timeout and zero persistent connection
age accommodate the hosted database. Run:

```sh
python manage.py migrate --settings=config.settings.migration --noinput
python manage.py createcachetable --settings=config.settings.migration
python manage.py seed_categories
npm ci
npm run build
npm run storage:verify
python manage.py verify_neon
python manage.py runserver
```

The build type-checks neon.ts, checks Django, detects migration drift and collects
production static assets. The Files SDK verification uploads a real local text file,
lists its unique verification prefix and compares downloaded contents. Its text
object is retained for inspection. verify_neon tests actual PostgreSQL writes and
CV upload/download/ownership checks through Django's API; synthetic database rows
are rolled back and its CV object is removed. Neither command prints credentials.

CV bytes are uploaded server-side after validation. The bucket is private and CV
storage refuses public URLs: existing authorized download endpoints stream files.
General media gets signed URLs. Unit tests force local storage and an isolated
cache; they never use production credentials or delete production records.

## Verification evidence

- npm run build: TalentBridge Django build passed.
- Files SDK: uploaded/listed/downloaded verification/c3d2dc9e-4b14-446d-a28d-e30213b3073c/hello.txt.
- File contents:
  TalentBridge Neon Object Storage verification.
  Private upload and read-back succeeded.
- CV API: upload 201; authorized download 200; 49 bytes match; other candidate 403.
- Local running app: /health/, /api/v1/jobs/, / and /accounts/login/ returned 200.
- Initial verification harness incorrectly closed its transaction on a duplicate
  response.close call; corrected to use Django's streaming wrapper cleanup.
- One local startup attempt failed DNS resolution; a retry connected successfully.
- npm initially explored unrelated SDK peers; install was restarted with the
  required adapter peers explicitly declared. npm audit reported zero vulnerabilities.

References:
https://neon.com/docs/guides/django
https://neon.com/docs/storage/get-started
