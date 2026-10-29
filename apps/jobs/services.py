from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import TalentBridgeAPIException
from apps.companies.models import Company, EmployerMembership
from apps.jobs.models import Job, JobSkill, JobStatus
from apps.users.models import User


class JobManagementService:
    """
    Domain service governing employer job creation, lifecycle transitions, and validation.
    """

    @staticmethod
    def verify_employer_permission(user: User, company: Company) -> EmployerMembership:
        """Verifies that the user has an active membership in the given company."""
        if user.is_staff or getattr(user, "is_admin_user", False):
            membership = EmployerMembership.objects.filter(company=company, is_active=True).first()
            if not membership:
                membership = EmployerMembership.objects.create(
                    user=user, company=company, role="ADMIN", is_active=True
                )
            return membership

        try:
            return EmployerMembership.objects.get(user=user, company=company, is_active=True)
        except EmployerMembership.DoesNotExist:
            raise TalentBridgeAPIException(
                detail="You do not have authorization to manage job listings for this company.",
                code="UNAUTHORIZED_COMPANY_ACCESS",
                status_code=403,
            ) from None

    @staticmethod
    def publish_job(job: Job, user: User) -> Job:
        JobManagementService.verify_employer_permission(user, job.company)

        if not job.title or not job.description:
            raise TalentBridgeAPIException(
                detail="Job title and description are required before publishing.",
                code="INCOMPLETE_JOB_DETAILS",
            )

        if job.application_deadline and job.application_deadline <= timezone.now():
            raise TalentBridgeAPIException(
                detail="Application deadline must be set in the future before publishing.",
                code="INVALID_DEADLINE",
            )

        job.status = JobStatus.PUBLISHED
        if not job.published_at:
            job.published_at = timezone.now()
        job.save()
        return job

    @staticmethod
    def pause_job(job: Job, user: User) -> Job:
        JobManagementService.verify_employer_permission(user, job.company)
        job.status = JobStatus.PAUSED
        job.save(update_fields=["status", "updated_at"])
        return job

    @staticmethod
    def close_job(job: Job, user: User) -> Job:
        JobManagementService.verify_employer_permission(user, job.company)
        job.status = JobStatus.CLOSED
        job.save(update_fields=["status", "updated_at"])
        return job

    @staticmethod
    def reopen_job(job: Job, user: User, new_deadline: timezone.datetime | None = None) -> Job:
        JobManagementService.verify_employer_permission(user, job.company)
        if new_deadline:
            if new_deadline <= timezone.now():
                raise TalentBridgeAPIException(
                    detail="New application deadline must be in the future.",
                    code="INVALID_DEADLINE",
                )
            job.application_deadline = new_deadline

        job.status = JobStatus.PUBLISHED
        job.save()
        return job

    @staticmethod
    @transaction.atomic
    def duplicate_job(job: Job, user: User) -> Job:
        JobManagementService.verify_employer_permission(user, job.company)
        new_job = Job.objects.create(
            company=job.company,
            created_by=user,
            title=f"Copy of {job.title}",
            description=job.description,
            responsibilities=job.responsibilities,
            requirements=job.requirements,
            category=job.category,
            employment_type=job.employment_type,
            workplace_type=job.workplace_type,
            experience_level=job.experience_level,
            location=job.location,
            country=job.country,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency,
            salary_period=job.salary_period,
            status=JobStatus.DRAFT,
            published_at=None,
            application_deadline=None,
        )

        for js in job.job_skills.all():
            JobSkill.objects.create(job=new_job, skill=js.skill, is_required=js.is_required)

        return new_job
