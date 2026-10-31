"""Normalize and import untrusted scraper data through validated Django models."""

import hashlib
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
    domain = "linkedin.com" if site == "linkedin" else "indeed.com"
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


@transaction.atomic
def import_job(row, country, category_name, dry_run=False):
    site = text(row.get("site")).lower()
    if site not in {"linkedin", "indeed"}:
        raise ValidationError("Unsupported source")
    url = canonical_url(row.get("job_url"), site)
    if Job.objects.filter(source_url=url).exists():
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
