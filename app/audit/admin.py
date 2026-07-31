from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "actor",
        "action",
        "object_type",
        "object_repr",
        "ip_address",
    )
    list_filter = ("action", "object_type", "created_at")
    search_fields = ("object_repr", "object_id", "actor__username")
    readonly_fields = (
        "actor",
        "action",
        "object_type",
        "object_id",
        "object_repr",
        "before_data",
        "after_data",
        "created_at",
        "ip_address",
    )
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and obj is not None

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        return {}
