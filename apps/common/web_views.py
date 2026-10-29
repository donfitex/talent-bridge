from functools import wraps

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from rest_framework.exceptions import APIException

from apps.applications.access import employer_applications
from apps.applications.models import JobApplication
from apps.applications.services import (
    ApplicationSubmissionService,
    ApplicationTransitionService,
    ApplicationWithdrawalService,
)
from apps.candidates.models import CandidateProfile
from apps.common.web_forms import (
    ApplicationForm,
    CandidateForm,
    CompanyForm,
    InterviewForm,
    JobForm,
    PipelineForm,
    RegistrationForm,
    ResumeForm,
)
from apps.companies.models import Company, EmployerMembership
from apps.jobs.models import Job, JobCategory, JobStatus
from apps.jobs.services import JobManagementService
from apps.resumes.models import Resume
from apps.resumes.services import ResumeService


def employer_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not (
            request.user.is_employer or request.user.is_recruiter or request.user.is_admin_user
        ):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapped


def candidate_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_candidate:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapped


def form_page(request, title, form, save, destination):
    if request.method == "POST" and form.is_valid():
        try:
            save(form)
        except (APIException, ValidationError) as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, "Saved successfully.")
            return redirect(destination)
    return render(request, "web/form.html", {"title": title, "form": form})


def jobs(request):
    qs = Job.objects.filter(status=JobStatus.PUBLISHED).select_related("company", "category")
    query = request.GET.get("q", "").strip()
    if query:
        qs = qs.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(company__name__icontains=query)
        )
    if request.GET.get("location"):
        qs = qs.filter(location__icontains=request.GET["location"])
    if request.GET.get("category"):
        qs = qs.filter(category__slug=request.GET["category"])
    return render(
        request,
        "web/jobs.html",
        {
            "page_obj": Paginator(qs, 12).get_page(request.GET.get("page")),
            "categories": JobCategory.objects.filter(is_active=True),
            "query": query,
        },
    )


def job_detail(request, pk):
    job = get_object_or_404(
        Job.objects.select_related("company", "category"), pk=pk, status=JobStatus.PUBLISHED
    )
    existing = (
        JobApplication.objects.filter(job=job, candidate__user=request.user)
        .exclude(status="WITHDRAWN")
        .first()
        if request.user.is_authenticated
        else None
    )
    return render(request, "web/job_detail.html", {"job": job, "application": existing})


def register(request):
    form = RegistrationForm(request.POST or None)
    return form_page(request, "Create your account", form, lambda f: f.save(), "web-login")


@require_POST
@login_required
def signout(request):
    logout(request)
    return redirect("web-jobs")


@candidate_required
def apply(request, pk):
    job = get_object_or_404(Job, pk=pk, status="PUBLISHED")
    form = ApplicationForm(request.POST or None, user=request.user)
    return form_page(
        request,
        f"Apply for {job.title}",
        form,
        lambda f: ApplicationSubmissionService.submit_application(
            request.user, job.pk, f.cleaned_data["resume"].pk, f.cleaned_data["cover_letter"]
        ),
        "web-applications",
    )


@candidate_required
def candidate_dashboard(request):
    applications = (
        JobApplication.objects.filter(candidate__user=request.user)
        .select_related("job__company", "resume")
        .prefetch_related("interviews")
    )
    return render(
        request,
        "web/applications.html",
        {
            "applications": applications,
            "interviews": request.user.candidate_profile.applications.filter(
                interviews__status="SCHEDULED"
            ).distinct()
            if hasattr(request.user, "candidate_profile")
            else [],
        },
    )


@candidate_required
@require_POST
def withdraw(request, pk):
    try:
        ApplicationWithdrawalService.withdraw(request.user, pk)
    except APIException as exc:
        messages.error(request, str(exc))
    return redirect("web-applications")


@candidate_required
def profile(request):
    instance, _ = CandidateProfile.objects.get_or_create(user=request.user)
    form = CandidateForm(request.POST or None, instance=instance)
    return form_page(request, "Professional profile", form, lambda f: f.save(), "web-profile")


@candidate_required
def resumes(request):
    form = ResumeForm(request.POST or None, request.FILES or None)
    candidate, _ = CandidateProfile.objects.get_or_create(user=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            ResumeService.upload_resume(
                candidate,
                form.cleaned_data["file"],
                form.cleaned_data["title"],
                form.cleaned_data["is_default"],
            )
        except (APIException, ValidationError) as exc:
            form.add_error(None, str(exc))
        else:
            return redirect("web-resumes")
    return render(
        request,
        "web/resumes.html",
        {"form": form, "resumes": Resume.objects.filter(candidate=candidate)},
    )


def companies(request):
    return render(request, "web/companies.html", {"companies": Company.objects.all()})


@employer_required
def company_create(request):
    form = CompanyForm(request.POST or None)

    def save(form):
        with transaction.atomic():
            company = form.save()
            EmployerMembership.objects.create(user=request.user, company=company, role="OWNER")

    return form_page(request, "Create company profile", form, save, "web-employer")


@employer_required
def employer_dashboard(request):
    qs = Job.objects.select_related("company", "category")
    if not request.user.is_admin_user:
        qs = qs.filter(
            company__memberships__user=request.user, company__memberships__is_active=True
        )
    return render(
        request,
        "web/employer.html",
        {
            "jobs": qs,
            "applications": employer_applications(request.user)[:100],
            "statuses": ApplicationTransitionService.transitions,
        },
    )


@employer_required
def job_edit(request, pk=None):
    instance = None
    if pk:
        instance = get_object_or_404(Job, pk=pk)
        try:
            JobManagementService.verify_employer_permission(request.user, instance.company)
        except APIException:
            raise PermissionDenied from None
    form = JobForm(request.POST or None, instance=instance, user=request.user)

    def save(form):
        job = form.save(commit=False)
        if not job.pk or not job.created_by_id:
            job.created_by = request.user
        JobManagementService.verify_employer_permission(request.user, job.company)
        job.save()

    return form_page(
        request, "Edit vacancy" if instance else "Create vacancy", form, save, "web-employer"
    )


@employer_required
@require_POST
def job_action(request, pk, action):
    job = get_object_or_404(Job, pk=pk)
    actions = {
        "publish": JobManagementService.publish_job,
        "pause": JobManagementService.pause_job,
        "close": JobManagementService.close_job,
    }
    if action not in actions:
        raise PermissionDenied
    try:
        actions[action](job, request.user)
    except (APIException, ValidationError) as exc:
        messages.error(request, str(exc))
    return redirect("web-employer")


@employer_required
def pipeline(request, pk):
    application = get_object_or_404(employer_applications(request.user), pk=pk)
    form = PipelineForm(request.POST or None)
    return form_page(
        request,
        f"Review {application.candidate.user.get_full_name()}",
        form,
        lambda f: ApplicationTransitionService.transition(
            request.user, pk, f.cleaned_data["status"], f.cleaned_data["note"]
        ),
        "web-employer",
    )


@employer_required
def schedule_interview(request, pk):
    from apps.interviews.services import InterviewService

    application = get_object_or_404(employer_applications(request.user), pk=pk)
    form = InterviewForm(request.POST or None, application=application)
    return form_page(
        request,
        "Schedule interview",
        form,
        lambda f: InterviewService.schedule(
            request.user, {**f.cleaned_data, "application": application}
        ),
        "web-employer",
    )


def password_request(request):
    from apps.common.web_forms import PasswordRequestForm
    from apps.users.services import UserService

    form = PasswordRequestForm(request.POST or None)
    return form_page(
        request,
        "Reset your password",
        form,
        lambda f: UserService.request_password_reset(f.cleaned_data["email"]),
        "web-login",
    )


def password_reset(request):
    from apps.common.web_forms import PasswordResetForm
    from apps.users.services import UserService

    form = PasswordResetForm(request.POST or None)

    def save(form):
        if not UserService.confirm_password_reset(
            request.GET.get("uid", ""),
            request.GET.get("token", ""),
            form.cleaned_data["new_password"],
        ):
            raise ValidationError("This password reset link is invalid or expired.")

    return form_page(request, "Choose a new password", form, save, "web-login")


def verify_email(request):
    from apps.users.services import UserService

    if request.method == "POST":
        if UserService.verify_email(request.GET.get("uid", ""), request.GET.get("token", "")):
            messages.success(request, "Your email address is verified.")
            return redirect("web-login")
        messages.error(request, "This verification link is invalid or expired.")
    return render(request, "web/form.html", {"title": "Verify your email address", "form": None})


@login_required
def dashboard(request):
    return redirect("web-candidate" if request.user.is_candidate else "web-employer")
