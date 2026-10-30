# Security and operations

Production rejects weak/default keys, wildcard allowed hosts and SQLite. HTTPS,
secure cookies, HSTS, CSRF, password hashing and private object authorization are
configured. The Render proxy terminates TLS; only trust its forwarded protocol
header when the application port is reachable through that trusted proxy.

Resumes live in private storage, never under publicly served /media or /static.
Only the candidate owner, platform administrators and active company members with
an associated application can download. Responses use attachment disposition,
no-store and nosniff. PDF/DOCX extension, signature, size and DOCX structure checks
are enforced. These checks do not replace malware scanning for hostile uploads.
Files are private by application policy; application code does not itself encrypt
file bytes at rest. Apply provider encryption and backup policy separately.

Existing resumes uploaded before private storage was configured may remain under
MEDIA_ROOT/resumes. Before exposing an existing installation, move referenced files
into RESUME_STORAGE_DIR while preserving their relative names, verify authorized
downloads, then remove the old public copies. Back up before moving existing data.

Redis provides shared API/authentication throttling. These limits complement an
edge rate limiter; trusted-client-IP configuration should match the actual proxy.
Use restricted database/Redis access and keep .env out of Git and Docker images.
SMTP credentials must never be entered in chat, source files or command arguments.

Store database backups and media backups separately and encrypted. Test restoration
into an isolated environment regularly. Restrict administrator access and review
membership changes. Do not grant staff access to ordinary recruiters.


## Current Neon storage configuration

CVs now use the private Neon uploads bucket instead of local production disk or
AWS S3/KMS. Existing authorization checks still gate every CV download. The S3
protocol's AWS_* credential names identify Neon storage credentials in this setup.
General company media is also stored on Neon with signed URLs, so free-host
restarts do not discard uploaded logos. No AWS KMS encryption claim applies.
