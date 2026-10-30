from django.contrib import admin

from apps.common.models import ContactMessage, SiteContent

admin.site.site_header = "TalentBridge Administration"
admin.site.site_title = "TalentBridge Admin"
admin.site.index_title = "Manage recruitment and website content"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["subject", "name", "email", "resolved", "created_at"]
    list_filter = ["resolved", "created_at"]
    search_fields = ["subject", "name", "email", "message"]
    readonly_fields = ["name", "email", "subject", "message", "created_at", "updated_at"]

    def has_add_permission(self, request):
        return False


@admin.register(SiteContent)
class SiteContentAdmin(admin.ModelAdmin):
    list_display = ["key", "title"]
    readonly_fields = ["key"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
