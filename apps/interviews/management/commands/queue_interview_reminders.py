from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.interviews.models import Interview
from apps.notifications.services import NotificationService


class Command(BaseCommand):
    help = "Queue deduplicated reminders for interviews within 24 hours."

    def handle(self, *args, **options):
        now = timezone.now()
        for item in Interview.objects.filter(
            status="SCHEDULED", starts_at__gt=now, starts_at__lte=now + timedelta(hours=24)
        ).select_related("application__candidate__user", "interviewer"):
            for user in [item.application.candidate.user, item.interviewer]:
                NotificationService.enqueue(
                    user,
                    "Upcoming interview",
                    f"Interview at {item.starts_at.isoformat()}: {item.location}",
                    f"reminder:{item.pk}:{user.pk}",
                )
