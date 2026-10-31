import time

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from jobspy import scrape_jobs

from apps.jobs.external import import_job


class Command(BaseCommand):
    help = "Import public LinkedIn/Indeed jobs for administrator review."

    def add_arguments(self, parser):
        parser.add_argument("--search-term", default="Software Engineer")
        parser.add_argument("--location", default="Nigeria")
        parser.add_argument("--country", default="Nigeria", help="JobSpy Indeed country name")
        parser.add_argument(
            "--results", type=int, default=15, help="Maximum results per site (1-50)"
        )
        parser.add_argument("--hours-old", type=int, default=72)
        parser.add_argument(
            "--sites", nargs="+", choices=["linkedin", "indeed"], default=["linkedin", "indeed"]
        )
        parser.add_argument("--category", default="Software Engineering")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--all-categories", action="store_true")
        parser.add_argument("--shard-index", type=int, default=0)
        parser.add_argument("--shard-count", type=int, default=1)
        parser.add_argument("--include-local", action="store_true")
        parser.add_argument("--local-limit", type=int, default=5)

    def handle(self, *args, **options):
        from apps.jobs.catalog import SEARCHES, classify
        from apps.jobs.local_sources import SOURCES, scrape_local

        if (
            not 1 <= options["shard_count"] <= 50
            or not 0 <= options["shard_index"] < options["shard_count"]
        ):
            raise CommandError("Invalid shard index/count.")
        if not 1 <= options["local_limit"] <= 20:
            raise CommandError("Use --local-limit 1-20.")
        if options["all_categories"]:
            from apps.jobs.models import JobCategory

            active = set(JobCategory.objects.filter(is_active=True).values_list("name", flat=True))
            searches = {**SEARCHES, **{name: name for name in active if name not in SEARCHES}}
            for index, (category, query) in enumerate(searches.items()):
                if index % options["shard_count"] != options["shard_index"]:
                    continue
                self.stdout.write(f"Category: {category}")
                try:
                    self.sync_query({**options, "search_term": query, "category": category})
                except CommandError as exc:
                    self.stderr.write(str(exc))
                time.sleep(3)
        else:
            self.sync_query(options)
        if options["include_local"] and options["shard_index"] == 0:
            for site in SOURCES:
                count = 0
                try:
                    for row in scrape_local(site, options["local_limit"]):
                        import_job(row, "Nigeria", classify(row["title"]), options["dry_run"])
                        count += 1
                except Exception as exc:
                    self.stderr.write(
                        f"{site}: source unavailable ({type(exc).__name__}); skipped."
                    )
                self.stdout.write(f"{site}: processed {count} structured job postings.")

    def sync_query(self, options):
        if not 1 <= options["results"] <= 50 or not 1 <= options["hours_old"] <= 720:
            raise CommandError("Use --results 1-50 and --hours-old 1-720.")
        if not 1 <= len(options["category"]) <= 100:
            raise CommandError("Category must contain 1-100 characters.")
        self.stdout.write("Starting job sync pipeline...")
        try:
            jobs = scrape_jobs(
                site_name=options["sites"],
                search_term=options["search_term"],
                location=options["location"],
                country_indeed=options["country"],
                results_wanted=options["results"],
                hours_old=options["hours_old"],
                description_format="markdown",
                fetch_description=True,
                verbose=1,
            )
        except Exception as exc:
            raise CommandError(f"Scraper failed ({type(exc).__name__}); retry later.") from None
        if jobs.empty:
            self.stdout.write(
                self.style.WARNING("No jobs returned. Check scraper warnings for source failures.")
            )
            return
        added = duplicates = invalid = 0
        for _, row in jobs.head(options["results"] * len(options["sites"])).iterrows():
            try:
                created = import_job(
                    row, options["country"], options["category"], options["dry_run"]
                )
            except (ValidationError, ValueError, TypeError):
                invalid += 1
                continue
            added += int(created)
            duplicates += int(not created)
        label = "Would add" if options["dry_run"] else "Added for admin review"
        self.stdout.write(
            self.style.SUCCESS(f"{label}: {added}; duplicates: {duplicates}; invalid: {invalid}.")
        )
