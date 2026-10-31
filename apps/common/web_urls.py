from django.urls import path

from apps.common import web_views as v
from apps.common.web_forms import EmailLoginForm

urlpatterns = [
    path("staff/contact-messages/", v.contact_inbox, name="web-contact-inbox"),
    path(
        "jobs/<uuid:pk>/external/confirm/",
        v.confirm_external_application,
        name="web-external-confirm",
    ),
    path("companies/<slug:slug>/", v.company_detail, name="web-company-detail"),
    path("accounts/password/code/", v.password_code_reset, name="web-code-reset"),
    path("accounts/managed/", v.managed_auth, name="web-managed-auth"),
    path("contact/", v.contact, name="web-contact"),
    path("dashboard/", v.dashboard),
    path("accounts/password/reset/", v.password_request, name="web-password-request"),
    path("reset-password/", v.password_reset),
    path("verify-email/", v.verify_email),
    path("", v.jobs, name="web-home"),
    path("jobs/", v.jobs, name="web-jobs"),
    path("jobs/<uuid:pk>/", v.job_detail, name="web-job-detail"),
    path("jobs/<uuid:pk>/apply/", v.apply, name="web-apply"),
    path("companies/", v.companies, name="web-companies"),
    path(
        "accounts/login/",
        v.AccountLoginView.as_view(
            template_name="web/form.html",
            authentication_form=EmailLoginForm,
            extra_context={"title": "Welcome back"},
        ),
        name="web-login",
    ),
    path("accounts/logout/", v.signout, name="web-logout"),
    path("accounts/register/", v.register, name="web-register"),
    path("candidate/dashboard/", v.candidate_dashboard, name="web-candidate"),
    path("candidate/applications/", v.candidate_dashboard, name="web-applications"),
    path("candidate/applications/<uuid:pk>/withdraw/", v.withdraw, name="web-withdraw"),
    path("candidate/profile/", v.profile, name="web-profile"),
    path("candidate/resumes/", v.resumes, name="web-resumes"),
    path("employer/dashboard/", v.employer_dashboard, name="web-employer"),
    path("employer/jobs/", v.employer_dashboard),
    path("employer/company/", v.company_create, name="web-company-create"),
    path("employer/jobs/new/", v.job_edit, name="web-job-create"),
    path("employer/jobs/<uuid:pk>/edit/", v.job_edit, name="web-job-edit"),
    path("employer/jobs/<uuid:pk>/<str:action>/", v.job_action, name="web-job-action"),
    path("employer/applications/<uuid:pk>/", v.pipeline, name="web-pipeline"),
    path("employer/applications/<uuid:pk>/interview/", v.schedule_interview, name="web-schedule"),
]
