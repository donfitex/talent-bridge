from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect
from django.urls import path
from django.views.decorators.http import require_POST
from rest_framework.exceptions import APIException

from apps.jobs.models import Job, JobCategory, JobSkill, JobStatus, Skill
from apps.jobs.services import JobManagementService


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    change_list_template = "admin/jobs/job/change_list.html"
    filter_horizontal = ["additional_categories"]
    actions = ["publish_selected"]

    def get_urls(self):
        return [
            path(
                "publish-all/",
                self.admin_site.admin_view(require_POST(self.publish_all)),
                name="jobs_job_publish_all",
            ),
        ] + super().get_urls()

    def publish_all(self, request):
        if not self.has_change_permission(request):
            raise PermissionDenied
        jobs = self.get_queryset(request).filter(
            status__in=[JobStatus.DRAFT, JobStatus.PENDING_REVIEW]
        )
        if jobs.exists():
            self.publish_selected(request, jobs.iterator(chunk_size=100))
        else:
            self.message_user(request, "No draft or pending-review jobs to publish.")
        return redirect("admin:jobs_job_changelist")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in {"description", "responsibilities", "requirements", "how_to_apply"}:
            from apps.common.widgets import RichTextWidget

            kwargs["widget"] = RichTextWidget()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    @admin.action(description="Publish selected jobs", permissions=["change"])
    def publish_selected(self, request, queryset):
        count = 0
        for job in queryset:
            try:
                JobManagementService.publish_job(job, request.user)
            except (ValidationError, APIException):
                self.message_user(
                    request,
                    f"Could not publish {job.title}. Check its details and deadline.",
                    level=messages.ERROR,
                )
            else:
                count += 1
        if count:
            self.message_user(
                request,
                f"{count} job(s) published successfully. Their status is now Published.",
                level=messages.SUCCESS,
            )

    list_display = ["__str__", "status", "source_site", "created_at"]
    readonly_fields = ["created_at", "updated_at", "source_url", "source_site"]
    search_fields = ["title", "description"]
    list_filter = ["status", "source_site", "workplace_type"]
    list_select_related = True


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["name"]
    list_filter = []
    list_select_related = True


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["name"]
    list_filter = []
    list_select_related = True


@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    list_display = ["job", "skill", "is_required"]
    search_fields = ["job__title", "skill__name"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["job", "skill"]
