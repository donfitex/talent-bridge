# Job publishing and editing

Jobs default to Unspecified experience and NGN currency. Existing values are preserved. Closing dates are optional; missing dates display Not Specified. Expired listings retain their red notice and disable external Apply actions.

Approved employers and staff can edit published jobs using their existing job edit links or admin. Primary category remains required for compatibility; select additional categories for cross-sector roles. Public category filters match both.

External application link is independent of source attribution. How to Apply has its own rich-text field. External applications retain candidate confirmation and dashboard tracking. Rich text supports headings, lists, emphasis, quotes and links; it does not duplicate every Word/Google Docs page-layout feature. Browser clipboard formatting is converted into these supported formats. Server output is sanitized with an allowlist; arbitrary scripts, event handlers and unsafe URL schemes are removed.

The editor is self-hosted Quill 2.0.2, pinned after auditing the HTML-export advisory affecting 2.0.3. Run npm run editor:bundle after modifying its source. Vendored CSS omits the development sourcemap reference. npm audit passed with zero findings at implementation time. Light/dark editor toolbar and surface colors follow the site theme. Visual browser verification remains necessary for unusual pasted layouts.

Sharing provides Facebook, X/Twitter, LinkedIn, WhatsApp, email and print controls. Clicking a share link opens the chosen provider; the app does not publish on a user's behalf.
