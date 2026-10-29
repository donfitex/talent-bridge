from django.contrib import admin

from apps.companies.models import Company, EmployerMembership


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["name", "industry"]
    list_filter = ["verification_status"]
    list_select_related = True


@admin.register(EmployerMembership)
class EmployerMembershipAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["user__email", "company__name"]
    list_filter = ["role", "is_active"]
    list_select_related = True
