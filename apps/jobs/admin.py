from django.contrib import admin
from apps.jobs.models import Job, JobCategory, Skill

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ['title', 'description']
    list_filter = ['status', 'workplace_type']
    list_select_related = True

@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ['name']
    list_filter = []
    list_select_related = True

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ['name']
    list_filter = []
    list_select_related = True

