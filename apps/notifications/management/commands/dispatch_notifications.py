from django.core.management.base import BaseCommand

from apps.notifications.services import NotificationService


class Command(BaseCommand):
    help = (
        "Deliver pending email notifications; failures remain retryable (at-least-once delivery)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        self.stdout.write(
            f"Delivered {NotificationService.dispatch(max(1, options['limit']))} notifications"
        )
