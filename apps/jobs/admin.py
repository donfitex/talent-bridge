from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from rest_framework.exceptions import APIException

from apps.jobs.models import Job, JobCategory, JobSkill, Skill
from apps.jobs.services import JobManagementService


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    actions = ["publish_selected"]

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
