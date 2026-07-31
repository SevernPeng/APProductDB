import json

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from .models import ImportJob


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "source_name",
        "product_type",
        "mode",
        "status",
        "total_rows",
        "error_rows",
        "uploaded_by",
        "uploaded_at",
        "imported_at",
    )
    list_filter = ("product_type__category", "product_type", "mode", "status", "uploaded_at", "imported_at")
    search_fields = ("uploaded_file", "uploaded_by__username")
    readonly_fields = (
        "uploaded_file_link",
        "product_type",
        "mode",
        "status",
        "total_rows",
        "valid_rows",
        "error_rows",
        "error_report_link",
        "summary_display",
        "uploaded_by",
        "uploaded_at",
        "imported_at",
    )
    fields = readonly_fields

    @admin.display(description="Source file")
    def source_name(self, obj):
        return obj.uploaded_file.name.rsplit("/", 1)[-1]

    @admin.display(description="Uploaded file")
    def uploaded_file_link(self, obj):
        if not obj.uploaded_file:
            return "-"
        url = reverse("imports:source_file", args=(obj.pk,))
        return format_html('<a href="{}">{}</a>', url, self.source_name(obj))

    @admin.display(description="Error report")
    def error_report_link(self, obj):
        if not obj.error_report:
            return "-"
        url = reverse("imports:error_report", args=(obj.pk,))
        return format_html('<a href="{}">Download CSV</a>', url)

    @admin.display(description="Summary")
    def summary_display(self, obj):
        return format_html("<pre>{}</pre>", json.dumps(obj.summary, ensure_ascii=False, indent=2))

    def add_view(self, request, form_url="", extra_context=None):
        return redirect("imports:upload")

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False
