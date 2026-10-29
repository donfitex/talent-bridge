import logging
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from apps.notifications.models import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def enqueue(user, subject, message, key):
        return Notification.objects.get_or_create(deduplication_key=key,
            defaults={"user": user, "subject": subject, "message": message})[0]

    @staticmethod
    def notify_employer_new_application(application):
        NotificationService.enqueue(application.candidate.user, "Application update",
            f"Your application for {application.job.title} is {application.status}.",
            f"application:{application.pk}:{application.status}:candidate")
        for membership in application.job.company.memberships.filter(is_active=True).select_related("user"):
            NotificationService.enqueue(membership.user, "Recruitment update",
                f"Application {application.pk} for {application.job.title}: {application.status}.",
                f"application:{application.pk}:{application.status}:{membership.user_id}")

    notify_employer_application_withdrawn = notify_employer_new_application

    @staticmethod
    def dispatch(limit=100):
        sent = 0
        ids = list(Notification.objects.filter(sent_at__isnull=True, attempts__lt=10)
            .order_by("created_at").values_list("pk", flat=True)[:limit])
        for notification_id in ids:
            with transaction.atomic():
                item = Notification.objects.select_for_update().select_related("user").get(pk=notification_id)
                if item.sent_at or item.attempts >= 10:
                    continue
                item.attempts += 1
                try:
                    send_mail(item.subject, item.message, settings.DEFAULT_FROM_EMAIL,
                        [item.user.email], fail_silently=False)
                except Exception:
                    item.last_error = "Delivery failed; inspect mail provider logs."
                    logger.exception("Notification delivery failed: %s", item.pk)
                else:
                    item.sent_at = timezone.now()
                    item.last_error = ""
                    sent += 1
                item.save(update_fields=["sent_at", "attempts", "last_error", "updated_at"])
        return sent
