import logging
from django.utils import timezone
from django.db import transaction
from apps.common.exceptions import TalentBridgeAPIException
from apps.users.models import User
from apps.candidates.models import CandidateProfile
from apps.jobs.models import Job, JobStatus
from apps.resumes.models import Resume
from apps.applications.models import JobApplication, ApplicationStatus

logger = logging.getLogger("apps.applications")


class ApplicationSubmissionService:
    """
    Orchestrates the job application submission pipeline, enforcing eligibility,
    deadline validation, duplicate prevention, and notification triggers.
    """

    @staticmethod
    @transaction.atomic
    def submit_application(user: User, job_id, resume_id, cover_letter: str = "") -> JobApplication:
        if not user or not user.is_authenticated:
            raise TalentBridgeAPIException(
                detail="Authentication is required to apply for a job.",
                code="AUTHENTICATION_REQUIRED",
                status_code=401,
            )

        candidate, _ = CandidateProfile.objects.get_or_create(user=user)

        try:
            job = Job.objects.select_related("company").get(id=job_id)
        except Job.DoesNotExist:
            raise TalentBridgeAPIException(detail="Job listing not found.", code="JOB_NOT_FOUND", status_code=404)

        if not job.is_accepting_applications:
            if job.status != JobStatus.PUBLISHED:
                raise TalentBridgeAPIException(
                    detail="This job is no longer accepting applications.",
                    code="APPLICATION_CLOSED",
                    status_code=400,
                )
            else:
                raise TalentBridgeAPIException(
                    detail="The application deadline for this job has expired.",
                    code="DEADLINE_EXPIRED",
                    status_code=400,
                )

        # Check for existing active application
        existing_app = JobApplication.objects.filter(
            job=job,
            candidate=candidate,
        ).exclude(status=ApplicationStatus.WITHDRAWN).first()

        if existing_app:
            raise TalentBridgeAPIException(
                detail="You have already submitted an active application for this job listing.",
                code="DUPLICATE_APPLICATION",
                status_code=400,
            )

        # Validate resume belongs to candidate
        try:
            resume = Resume.objects.get(id=resume_id, candidate=candidate)
        except Resume.DoesNotExist:
            raise TalentBridgeAPIException(
                detail="The selected resume does not exist or does not belong to your account.",
                code="INVALID_RESUME",
                status_code=400,
            )

        # Create the application
        application = JobApplication.objects.create(
            job=job,
            candidate=candidate,
            resume=resume,
            cover_letter=cover_letter,
            status=ApplicationStatus.SUBMITTED,
        )

        # Trigger notification hook asynchronously/safely
        ApplicationSubmissionService._notify_employer_on_application(application)

        return application

    @staticmethod
    def _notify_employer_on_application(application: JobApplication):
        """Notification dispatch decoupled from core application creation."""
        try:
            from apps.notifications.services import NotificationService
            NotificationService.notify_employer_new_application(application)
        except Exception as e:
            logger.warning("Notification delivery queued or deferred for application %s: %s", application.id, e)
