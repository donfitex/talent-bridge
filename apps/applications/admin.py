from django.contrib import admin

from apps.applications.models import ApplicationStatusHistory, JobApplication


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["candidate__user__email", "job__title"]
    list_filter = ["status"]
    list_select_related = True


@admin.register(ApplicationStatusHistory)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ["application", "previous_status", "status", "actor", "created_at"]
    readonly_fields = [f.name for f in ApplicationStatusHistory._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
