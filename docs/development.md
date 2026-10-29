# Development

Use Python 3.12+ and install `requirements-dev.txt` into a virtual environment.
Copy `.env.example` to `.env`; keep local development settings and SQLite initially.
Run `python manage.py migrate`, `python manage.py seed_categories`, then
`python manage.py runserver`. Open `/`, register a candidate or employer and log in.
Employers create a company before creating vacancies. Candidates upload a PDF or
DOCX before applying. Django administration is at `/admin/`; create access using
`python manage.py createsuperuser`, never a checked-in default password.

Set FRONTEND_URL to the origin serving the HTML UI for working verification/reset
links. Development uses console mail: verification URLs appear in local output.
Production SMTP credentials belong in the hosting secret configuration.

Use `ruff check .`, `ruff format --check .` and `pytest` before committing. Install
hooks with `pre-commit install`. Work is committed directly on main as requested.
The project uses same-origin sessions; a separate-origin frontend requires explicit
CSRF origin/CORS configuration before it can access authenticated APIs.
