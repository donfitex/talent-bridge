import os
import mimetypes
from django.conf import settings
from apps.common.exceptions import TalentBridgeAPIException
from apps.common.validators import validate_resume_file
from apps.users.models import User
from apps.candidates.models import CandidateProfile
from apps.resumes.models import Resume


class ResumeService:
    """
    Security and file handling service for candidate resumes.
    Ensures safe uploads, content validation, and authorized downloads.
    """

    @staticmethod
    def upload_resume(candidate: CandidateProfile, file_obj, title: str, is_default: bool = False) -> Resume:
        # Validate file format and magic bytes
        validate_resume_file(file_obj)

        ext = os.path.splitext(file_obj.name)[1].lower()
        content_type = mimetypes.guess_type(file_obj.name)[0] or "application/octet-stream"

        if is_default:
            Resume.objects.filter(candidate=candidate, is_default=True).update(is_default=False)
        elif not Resume.objects.filter(candidate=candidate).exists():
            is_default = True

        resume = Resume(
            candidate=candidate,
            title=title or file_obj.name,
            file=file_obj,
            original_filename=file_obj.name,
            file_type=content_type,
            file_size=file_obj.size,
            is_default=is_default,
        )
        resume.save()
        return resume

    @staticmethod
    def authorize_download(resume: Resume, user: User) -> bool:
        """
        Grants download access if:
        1. User is platform admin/staff.
        2. User is the candidate owner of this resume.
        3. User is an authorized employer whose company has an active job application from this candidate with this resume.
        """
        if not user or not user.is_authenticated:
            return False

        if user.is_staff or getattr(user, "is_admin_user", False):
            return True

        if resume.candidate.user == user:
            return True

        # Check if user is an employer member of a company where the candidate applied with this resume
        from apps.companies.models import EmployerMembership
        employer_companies = EmployerMembership.objects.filter(
            user=user, is_active=True
        ).values_list("company_id", flat=True)

        if not employer_companies:
            return False

        try:
            from apps.applications.models import JobApplication
            return JobApplication.objects.filter(
                job__company_id__in=employer_companies,
                candidate=resume.candidate,
                resume=resume,
            ).exists()
        except (ImportError, Exception):
            return False
