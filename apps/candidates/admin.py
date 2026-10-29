from django.contrib import admin

from apps.candidates.models import CandidateProfile


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["professional_title", "user__email"]
    list_filter = []
    list_select_related = True
