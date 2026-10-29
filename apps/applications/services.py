import logging
from django.utils import timezone
from django.db import transaction, IntegrityError
from apps.common.exceptions import TalentBridgeAPIException
from apps.users.models import User
from apps.candidates.models import CandidateProfile
from apps.jobs.models import Job, JobStatus
from apps.resumes.models import Resume
from apps.applications.models import JobApplication, ApplicationStatus, ApplicationStatusHistory

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

        if not user.is_candidate:
            raise TalentBridgeAPIException(detail="Only candidates can apply.", code="CANDIDATE_REQUIRED", status_code=403)

        candidate, _ = CandidateProfile.objects.get_or_create(user=user)
        CandidateProfile.objects.select_for_update().get(pk=candidate.pk)

        try:
            job = Job.objects.select_for_update().get(id=job_id)
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
                status_code=409,
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
        try:
            with transaction.atomic():
                application = JobApplication.objects.create(
                    job=job, candidate=candidate, resume=resume, cover_letter=cover_letter,
                    status=ApplicationStatus.SUBMITTED,
                )
        except IntegrityError:
            raise TalentBridgeAPIException(detail="You already applied for this job.", code="DUPLICATE_APPLICATION", status_code=409) from None

        ApplicationStatusHistory.objects.create(application=application, actor=user, status=application.status)

        # Trigger notification hook asynchronously/safely
        transaction.on_commit(lambda: ApplicationSubmissionService._notify_employer_on_application(application))

        return application

    @staticmethod
    def _notify_employer_on_application(application: JobApplication):
        """Notification dispatch decoupled from core application creation."""
        try:
            from apps.notifications.services import NotificationService
            NotificationService.notify_employer_new_application(application)
        except Exception as e:
            logger.warning("Notification delivery queued or deferred for application %s: %s", application.id, e)


class ApplicationWithdrawalService:
    @staticmethod
    @transaction.atomic
    def withdraw(user, application_id):
        try:
            application = JobApplication.objects.select_for_update().get(
                pk=application_id, candidate__user=user)
        except JobApplication.DoesNotExist:
            raise TalentBridgeAPIException(detail="Application not found.", code="NOT_FOUND", status_code=404) from None
        if application.status in {ApplicationStatus.WITHDRAWN, ApplicationStatus.HIRED, ApplicationStatus.REJECTED}:
            raise TalentBridgeAPIException(detail="This application cannot be withdrawn.", code="INVALID_TRANSITION", status_code=409)
        previous = application.status
        application.status = ApplicationStatus.WITHDRAWN
        application.withdrawn_at = timezone.now()
        application.save(update_fields=["status", "withdrawn_at", "updated_at"])
        ApplicationStatusHistory.objects.create(application=application, actor=user, previous_status=previous, status=application.status)
        transaction.on_commit(lambda: ApplicationSubmissionService._notify_employer_on_application(application))
        return application


class ApplicationTransitionService:
    transitions = {
        ApplicationStatus.SUBMITTED: {ApplicationStatus.UNDER_REVIEW, ApplicationStatus.REJECTED},
        ApplicationStatus.UNDER_REVIEW: {ApplicationStatus.SHORTLISTED, ApplicationStatus.REJECTED},
        ApplicationStatus.SHORTLISTED: {ApplicationStatus.INTERVIEW, ApplicationStatus.REJECTED},
        ApplicationStatus.INTERVIEW: {ApplicationStatus.OFFERED, ApplicationStatus.REJECTED},
        ApplicationStatus.OFFERED: {ApplicationStatus.HIRED, ApplicationStatus.REJECTED},
    }

    @staticmethod
    @transaction.atomic
    def transition(user, application_id, target, note=""):
        from apps.applications.access import employer_applications
        allowed = employer_applications(user).filter(pk=application_id).exists()
        if not allowed or not (user.is_employer or user.is_recruiter or user.is_admin_user):
            raise TalentBridgeAPIException(detail="Application not found.", code="NOT_FOUND", status_code=404)
        application = JobApplication.objects.select_for_update().get(pk=application_id)
        previous = application.status
        if target not in ApplicationTransitionService.transitions.get(previous, set()):
            raise TalentBridgeAPIException(detail="Invalid application status transition.", code="INVALID_TRANSITION", status_code=409)
        application.status = target
        application.save(update_fields=["status", "updated_at"])
        ApplicationStatusHistory.objects.create(application=application, actor=user,
            previous_status=previous, status=target, note=note)
        transaction.on_commit(lambda: ApplicationSubmissionService._notify_employer_on_application(application))
        return application
