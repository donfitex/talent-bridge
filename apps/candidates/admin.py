from django.contrib import admin

from apps.candidates.models import CandidateProfile, CandidateSkill


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["professional_title", "user__email"]
    list_filter = []
    list_select_related = True


@admin.register(CandidateSkill)
class CandidateSkillAdmin(admin.ModelAdmin):
    list_display = ["candidate", "skill", "years_of_experience"]
    search_fields = ["candidate__user__email", "skill__name"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["candidate", "skill"]
