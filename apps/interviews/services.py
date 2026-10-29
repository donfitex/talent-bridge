from django.db import transaction
from django.utils import timezone

from apps.applications.access import employer_applications
from apps.applications.models import JobApplication
from apps.common.exceptions import TalentBridgeAPIException
from apps.interviews.models import Interview
from apps.notifications.services import NotificationService
from apps.users.models import User


def notify_interview(item):
    NotificationService.enqueue(
        item.application.candidate.user,
        "Interview update",
        f"{item.application.job.title}: {item.status}, {item.starts_at.isoformat()}, {item.location}",
        f"interview:{item.pk}:{item.updated_at.isoformat()}",
    )

    NotificationService.enqueue(
        item.interviewer,
        "Interview update",
        f"{item.application.job.title}: {item.status}, {item.starts_at.isoformat()}, {item.location}",
        f"interview:{item.pk}:{item.updated_at.isoformat()}:interviewer",
    )


class InterviewService:
    @staticmethod
    @transaction.atomic
    def schedule(user, data):
        application = data["application"]
        if not employer_applications(user).filter(pk=application.pk).exists():
            raise TalentBridgeAPIException(detail="Application not found.", status_code=404)
        application = JobApplication.objects.select_for_update().get(pk=application.pk)
        if application.status != "INTERVIEW":
            raise TalentBridgeAPIException(
                detail="Application must be in the interview stage.", status_code=409
            )
        interviewer = data["interviewer"]
        User.objects.select_for_update().get(pk=interviewer.pk)
        # Serialize candidate schedules across applications as well as interviewer schedules.
        from apps.candidates.models import CandidateProfile

        CandidateProfile.objects.select_for_update().get(pk=application.candidate_id)
        if (
            not interviewer.is_active
            or not interviewer.employer_memberships.filter(
                company=application.job.company, is_active=True
            ).exists()
        ):
            raise TalentBridgeAPIException(detail="Interviewer must be an active company member.")
        if data["starts_at"] <= timezone.now() or data["ends_at"] <= data["starts_at"]:
            raise TalentBridgeAPIException(detail="Provide a future start and a later end.")
        from django.db.models import Q

        overlap = Interview.objects.filter(
            status="SCHEDULED", starts_at__lt=data["ends_at"], ends_at__gt=data["starts_at"]
        ).filter(Q(interviewer=interviewer) | Q(application__candidate=application.candidate))
        if overlap.exists():
            raise TalentBridgeAPIException(
                detail="Candidate or interviewer already has an overlapping interview.",
                status_code=409,
            )
        item = Interview.objects.create(**data)
        notify_interview(item)
        return item

    @staticmethod
    @transaction.atomic
    def update(user, item, data):
        item = Interview.objects.select_for_update().get(pk=item.pk)
        if not employer_applications(user).filter(pk=item.application_id).exists():
            raise TalentBridgeAPIException(detail="Interview not found.", status_code=404)
        if item.status != "SCHEDULED":
            raise TalentBridgeAPIException(detail="Interview is already final.", status_code=409)
        target = data.get("status", item.status)
        if target == "COMPLETED" and item.starts_at > timezone.now():
            raise TalentBridgeAPIException(
                detail="A future interview cannot be completed.", status_code=409
            )
        item.status = target
        item.feedback = data.get("feedback", item.feedback)
        item.save(update_fields=["status", "feedback", "updated_at"])
        notify_interview(item)
        return item
