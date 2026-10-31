"""Normalize and import untrusted scraper data through validated Django models."""

import hashlib
import re
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.companies.models import Company
from apps.jobs.models import Job, JobCategory


def text(value, default=""):
    if value is None or str(value).strip().lower() in {"", "nan", "none", "nat", "<na>"}:
        return default
    return str(value).strip()


def canonical_url(value, site):
    parts = urlsplit(text(value))
    host = (parts.hostname or "").lower()
    domain = {
        "linkedin": "linkedin.com",
        "indeed": "indeed.com",
        "hotnigerianjobs": "hotnigerianjobs.com",
        "myjobmag": "myjobmag.com",
    }[site]
    if (
        parts.scheme != "https"
        or not (host == domain or host.endswith("." + domain))
        or parts.username
        or parts.password
    ):
        raise ValidationError("Invalid source URL")
    query = parse_qs(parts.query)
    if site == "indeed":
        key = query.get("jk", query.get("vjk", []))
        if key:
            return "https://www.indeed.com/viewjob?" + urlencode({"jk": key[0]})
    return urlunsplit(("https", host, parts.path.rstrip("/"), "", ""))


def content_fields(row):
    description = text(row.get("description"))
    sections = {
        "responsibilities": text(row.get("responsibilities")),
        "requirements": text(row.get("requirements")),
    }
    aliases = {
        "responsibilities": "responsibilities",
        "key responsibilities": "responsibilities",
        "what you will do": "responsibilities",
        "what you'll do": "responsibilities",
        "requirements": "requirements",
        "qualifications": "requirements",
        "required qualifications": "requirements",
        "what you bring": "requirements",
        "skills and experience": "requirements",
    }
    current = None
    extracted = {key: [] for key in sections}
    for line in description.splitlines():
        heading = line.strip().strip("#*_: ").lower()
        if heading in aliases:
            current = aliases[heading]
        elif re.match(r"^\s*#{1,6}\s+", line) or (
            line.strip().startswith("**") and line.strip().endswith("**")
        ):
            current = None
        elif current:
            extracted[current].append(line)
    for key in sections:
        if not sections[key]:
            sections[key] = "\n".join(extracted[key]).strip()
    return {
        "description": description[:100000],
        **{key: value[:50000] for key, value in sections.items()},
    }


def safe_company_url(value):
    value = text(value)
    parts = urlsplit(value)
    if parts.scheme == "https" and parts.hostname and not parts.username and not parts.password:
        return value[:1000]
    return ""


def enrich_company(company, row):
    values = {
        "description": text(row.get("company_description"))[:50000],
        "industry": text(row.get("company_industry"))[:100],
        "source_logo_url": safe_company_url(row.get("company_logo")),
        "website": safe_company_url(row.get("company_url_direct"))[:255],
    }
    changed = []
    for field, value in values.items():
        if value and not getattr(company, field):
            setattr(company, field, value)
            changed.append(field)
    if changed:
        company.save(update_fields=[*changed, "updated_at"])


@transaction.atomic
def import_job(row, country, category_name, dry_run=False):
    site = text(row.get("site")).lower()
    if site not in {"linkedin", "indeed", "hotnigerianjobs", "myjobmag"}:
        raise ValidationError("Unsupported source")
    url = canonical_url(row.get("job_url"), site)
    content = content_fields(row)
    existing = Job.objects.select_for_update().filter(source_url=url).first()
    if existing:
        enrich_company(existing.company, row)
        changed = []
        for field, value in content.items():
            old = getattr(existing, field)
            if value and (
                not old
                or (
                    field == "description"
                    and old.startswith("See the original listing for the full job description.")
                )
            ):
                setattr(existing, field, value)
                changed.append(field)
        if changed:
            existing.save(update_fields=[*changed, "updated_at"])
        if dry_run:
            transaction.set_rollback(True)
        return False
    title = text(row.get("title"))
    if not title:
        raise ValidationError("Missing job title")
    name = text(row.get("company"), "Unknown Company")[:255]
    digest = hashlib.sha256(url.encode()).hexdigest()
    company_key = hashlib.sha256((site + ":" + name.casefold()).encode()).hexdigest()[:24]
    company, _ = Company.objects.get_or_create(
        slug="external-" + company_key, defaults={"name": name}
    )
    enrich_company(company, row)
    category, _ = JobCategory.objects.get_or_create(
        name=category_name,
        defaults={"slug": "external-" + hashlib.sha256(category_name.encode()).hexdigest()[:20]},
    )
    description = text(
        row.get("description"), "See the original listing for the full job description."
    )
    description = (
        description[:100000]
        + f"\n\nOriginally posted on {site.capitalize()}. Apply on the original site: {url}"
    )
    job, created = Job.objects.get_or_create(
        source_url=url,
        defaults={
            "source_site": site,
            "title": title[:255],
            "slug": "external-" + digest,
            "company": company,
            "category": category,
            "description": description,
            "responsibilities": content["responsibilities"],
            "requirements": content["requirements"],
            "location": text(row.get("location"), "Remote")[:255],
            "country": country[:100],
            "workplace_type": "REMOTE"
            if text(row.get("is_remote")).lower() == "true"
            else "ONSITE",
            "status": "PENDING_REVIEW",
        },
    )
    if dry_run:
        transaction.set_rollback(True)
    return created
