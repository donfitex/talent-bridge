from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from jobspy import scrape_jobs

from apps.jobs.external import import_job


class Command(BaseCommand):
    help = "Import public LinkedIn/Indeed jobs for administrator review."

    def add_arguments(self, parser):
        parser.add_argument("--search-term", default="Software Engineer")
        parser.add_argument("--location", default="Remote")
        parser.add_argument("--country", default="USA", help="JobSpy Indeed country name")
        parser.add_argument(
            "--results", type=int, default=15, help="Maximum results per site (1-50)"
        )
        parser.add_argument("--hours-old", type=int, default=72)
        parser.add_argument(
            "--sites", nargs="+", choices=["linkedin", "indeed"], default=["linkedin", "indeed"]
        )
        parser.add_argument("--category", default="Software Engineering")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
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
