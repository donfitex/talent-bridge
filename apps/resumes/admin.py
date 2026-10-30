from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.resumes.models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    readonly_fields = ["created_at", "updated_at", "download_file"]
    exclude = ["file"]
    search_fields = ["title", "candidate__user__email"]
    list_filter = []
    list_select_related = True

    @admin.display(description="Private CV")
    def download_file(self, obj):
        if not obj.pk or not obj.file:
            return "No file"
        return format_html(
            '<a href="{}">Download CV</a>', reverse("resumes-download", args=[obj.pk])
        )

    def has_add_permission(self, request):
        return False
