# TalentBridge — Job Discovery, Recruitment & Applicant Tracking Platform

TalentBridge is an enterprise-grade, production-ready recruitment and applicant tracking platform built with Django, Django REST Framework, and PostgreSQL. It bridges the gap between ambitious companies and skilled job seekers through high-efficiency job matching, verified credentials, role-based workflows, and automated candidate tracking.

---

## Key Features

- **Multi-Role Authentication**: Dedicated workflows and access control for Candidates, Employers, Recruiters, and Admins.
- **Company & Employer Management**: Company profiles, verified status badges, recruiter assignments, and organization membership.
- **Job Taxonomy & Categorization**: Granular skills tagging, industry categories, and search-friendly attributes.
- **Advanced Job Search & Discovery**: Flexible filtering by keywords, location, remote work options, salary range, and experience levels.
- **Secure Resume Handling**: Strict file-type validation, size restrictions, private storage outside static directories, and authorized download endpoints.
- **Applicant Tracking System (ATS)**: Complete candidate application pipeline (Submitted, Under Review, Shortlisted, Interview, Offer, Hired, Rejected).
- **Recruitment Audit Trail**: Tamper-evident status history tracking every transition and reviewer.
- **Real-Time Notifications & Alerts**: Candidate status alerts and employer application activity notifications.
- **Interview Scheduling**: Coordinated calendar invites for in-person, phone, and video interviews.
- **Analytics & Reporting**: Conversion metrics, time-to-hire statistics, application velocity, and administrative oversight.
- **Enterprise Security**: Production-grade CSRF protection, secure cookie handling, rate limiting, and object-level permissions.

---

## Architecture Overview

TalentBridge follows a modular monolithic architecture adhering strictly to SOLID principles:
- **`apps/common`**: Shared core models, base viewsets, standardized response envelopes, and custom permission classes.
- **`apps/users`**: Custom user identity, authentication, role management, and security policies.
- **`apps/companies`**: Corporate profiles, verification pipelines, and recruiter memberships.
- **`apps/jobs`**: Job catalog, categories, skills mapping, and listings.
- **`apps/candidates`**: Candidate profiles, preferences, and saved bookmarks.
- **`apps/resumes`**: Encrypted/protected resume uploads and permissioned document retrieval.
- **`apps/applications`**: Full lifecycle applicant tracking system with status state machine.
- **`apps/interviews`**: Multi-round interview coordination and outcome logging.
- **`apps/notifications`**: Multi-channel in-app and email notification dispatchers.
- **`apps/reports`**: Business intelligence, recruitment analytics, and metrics aggregation.

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or Docker)
- Git

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/donfitex/talent-bridge.git
   cd talent-bridge
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Update environment variables in .env
   ```

5. **Run migrations & start development server**:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

---

## Coding Conventions

- **PEP 8 & Formatting**: Enforced via `ruff check` and `ruff format`.
- **Typing**: Type annotations on business logic services and serializers.
- **SOLID Design**: Separation of concerns between Django models, DRF serializers, service layers, and viewsets.
- **Commit Standards**: Conventional Commits standard (`feat:`, `chore:`, `test:`, `docs:`, `perf:`).
