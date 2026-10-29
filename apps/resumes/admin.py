from django.contrib import admin

from apps.resumes.models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["title", "candidate__user__email"]
    list_filter = []
    list_select_related = True
