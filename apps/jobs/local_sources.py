"""Bounded public structured-data adapters; no proxy or anti-bot bypass."""

import json
import time
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

SOURCES = {
    "hotnigerianjobs": ("https://www.hotnigerianjobs.com/", "/hotjobs/"),
    "myjobmag": ("https://www.myjobmag.com/", "/job/"),
}
AGENT = "TalentBridgeJobSync/1.0"


def structured_jobs(value):
    if isinstance(value, list):
        for item in value:
            yield from structured_jobs(item)
    elif isinstance(value, dict):
        types = value.get("@type", [])
        if "JobPosting" in ([types] if isinstance(types, str) else types):
            yield value
        for key in ("@graph", "itemListElement", "item"):
            if key in value:
                yield from structured_jobs(value[key])


def scrape_local(site, limit=5):
    base, pattern = SOURCES[site]
    session = requests.Session()
    session.headers["User-Agent"] = AGENT

    def get(url):
        if urlsplit(url).netloc != urlsplit(base).netloc:
            raise ValueError("Off-domain URL")
        time.sleep(2)
        response = session.get(url, timeout=(5, 15), allow_redirects=False)
        response.raise_for_status()
        if response.status_code != 200 or len(response.content) > 2_000_000:
            raise ValueError("Unexpected response")
        return response.text

    robots_text = get(urljoin(base, "robots.txt"))
    robots = RobotFileParser()
    robots.parse(robots_text.splitlines())
    if not robots.can_fetch(AGENT, base):
        raise ValueError("Source disallows automated access")
    soup = BeautifulSoup(get(base), "lxml")
    links = []
    for anchor in soup.select("a[href]"):
        url = urljoin(base, anchor["href"])
        if (
            pattern in urlsplit(url).path
            and urlsplit(url).netloc == urlsplit(base).netloc
            and url not in links
        ):
            links.append(url)
    for url in links[:limit]:
        if not robots.can_fetch(AGENT, url):
            continue
        page = BeautifulSoup(get(url), "lxml")
        for script in page.select('script[type="application/ld+json"]'):
            try:
                items = list(structured_jobs(json.loads(script.string or script.get_text())))
            except (ValueError, TypeError):
                continue
            for job in items:
                company = job.get("hiringOrganization") or {}
                if not isinstance(company, dict):
                    company = {}
                title = job.get("title")
                if not title:
                    continue
                description = BeautifulSoup(job.get("description") or "", "lxml").get_text(
                    "\n", strip=True
                )
                yield {
                    "site": site,
                    "job_url": url,
                    "title": title,
                    "company": company.get("name"),
                    "company_logo": company.get("logo")
                    if isinstance(company.get("logo"), str)
                    else "",
                    "company_url_direct": company.get("sameAs"),
                    "description": description,
                    "location": "Nigeria",
                }
