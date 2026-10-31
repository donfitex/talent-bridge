from django.contrib import admin

from apps.jobs.models import Job, JobCategory, JobSkill, Skill


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
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
