from django.contrib import admin
from apps.interviews.models import Interview

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ['application__job__title']
    list_filter = ['status']
    list_select_related = True

