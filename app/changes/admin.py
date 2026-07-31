from django.contrib import admin

from .models import ChangeRequest


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "target_product",
        "field_name",
        "status",
        "submitted_by",
        "submitted_at",
        "reviewed_by",
    )
    list_filter = ("status", "request_type", "submitted_at")
    search_fields = (
        "target_product__model",
        "field_name",
        "submitted_by__username",
        "reason",
    )
    readonly_fields = (
        "request_type",
        "target_product",
        "target_spec",
        "target_match",
        "field_name",
        "old_value",
        "proposed_value",
        "reason",
        "source_url",
        "attachment",
        "status",
        "submitted_by",
        "submitted_at",
        "reviewed_by",
        "reviewed_at",
        "review_comment",
    )
    date_hierarchy = "submitted_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and obj is not None

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        return {}
