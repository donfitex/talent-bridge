# Managed email signup

Neon managed Better Auth is enabled on the existing production branch alongside Postgres and the private uploads bucket. The SDK page is /accounts/managed/. Its public base URL is NEON_AUTH_BASE_URL; credentials and session tokens are never rendered by the server.

Run npm run auth:bundle after changing the browser source. The generated bundle is checked in for the Python Docker build. Run npm run auth:verify to create a unique reserved-domain test identity, retrieve its current user, sign out, sign in and verify the restored session. This keeps the test identity in managed Auth; its random password is never printed.

This page is an additive managed-identity integration. It does not migrate Django passwords, establish Django sessions, or grant recruitment/admin access. Existing recruitment and admin accounts continue using Django login. Connecting the two requires a verified provider-subject mapping and secure session exchange; never link a privileged Django account by an unverified email match.

Shared Neon SMTP is available for getting started. Production requires custom SMTP per the Neon production checklist. Email delivery and browser session restoration have not been independently verified by the Node SDK smoke test.
