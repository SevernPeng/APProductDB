from pathlib import Path

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.auth.decorators import user_passes_test
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from audit.models import AuditLog
from catalog.models import ProductType

from .forms import ImportUploadForm
from .models import ImportJob
from .services import ImportValidationError, execute_import_job, validate_import_job
from .template_profiles import get_template_profile


def _is_superuser(user):
    return user.is_authenticated and user.is_superuser


def _log_action(request, job, flag, message):
    LogEntry.objects.log_actions(
        user_id=request.user.pk,
        queryset=[job],
        action_flag=flag,
        change_message=message,
        single_object=True,
    )


@user_passes_test(_is_superuser)
def upload(request):
    if request.method == "POST":
        form = ImportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.uploaded_by = request.user
            job.summary = {"audit": []}
            job.save()
            _log_action(request, job, ADDITION, "Uploaded workbook for validation.")
            validate_import_job(job)
            if job.status == ImportJob.Status.READY:
                messages.success(request, "工作簿校验通过，请检查预览后确认导入。")
            else:
                messages.error(request, "工作簿校验未通过，请下载错误报告。")
            return redirect("imports:detail", pk=job.pk)
    else:
        form = ImportUploadForm(initial={"mode": ImportJob.Mode.PREVIEW})
    recent_jobs = ImportJob.objects.select_related(
        "uploaded_by", "product_type", "product_type__category"
    )[:10]
    product_types = ProductType.objects.filter(
        active=True,
        category__slug__in=(
            "access-point",
            "managed-switches",
            "unmanaged-easy-smart-switches",
            "gateway",
            "accessories",
        ),
    ).select_related("category").order_by(
        "category__name", "display_order", "name"
    )
    template_groups = []
    for product_type in product_types:
        if (
            not template_groups
            or template_groups[-1]["category"].pk != product_type.category_id
        ):
            template_groups.append(
                {"category": product_type.category, "product_types": []}
            )
        template_groups[-1]["product_types"].append(product_type)
    return render(
        request,
        "imports/upload.html",
        {
            "form": form,
            "recent_jobs": recent_jobs,
            "template_groups": template_groups,
        },
    )


@user_passes_test(_is_superuser)
def download_template(request, product_type_id):
    product_type = get_object_or_404(
        ProductType.objects.select_related("category"),
        pk=product_type_id,
        active=True,
    )
    profile = get_template_profile(product_type.category.slug, product_type.code)
    if profile is None or not profile.path.is_file():
        raise Http404("The selected product-type template is not available.")
    response = FileResponse(
        profile.path.open("rb"),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{profile.filename}"'
    return response


@user_passes_test(_is_superuser)
def detail(request, pk):
    job = get_object_or_404(ImportJob.objects.select_related("uploaded_by"), pk=pk)
    if request.method == "POST":
        try:
            counters = execute_import_job(job)
        except ImportValidationError as exc:
            messages.error(request, str(exc))
        except Exception:
            messages.error(request, "导入失败，所有数据库变更已回滚。请查看任务审计信息和应用日志。")
        else:
            _log_action(request, job, CHANGE, f"Confirmed Excel import: {counters}")
            AuditLog.objects.create(
                actor=request.user,
                action="excel_import.completed",
                object_type=job._meta.label,
                object_id=str(job.pk),
                object_repr=str(job),
                before_data={},
                after_data=counters,
                ip_address=request.META.get("REMOTE_ADDR") or None,
            )
            messages.success(request, "Excel 已在单一数据库事务中导入成功。")
        return redirect("imports:detail", pk=job.pk)
    return render(request, "imports/detail.html", {"job": job})


@user_passes_test(_is_superuser)
def source_file(request, pk):
    job = get_object_or_404(ImportJob, pk=pk)
    if not job.uploaded_file:
        raise Http404("This import job has no source workbook.")
    filename = Path(job.uploaded_file.name).name
    response = FileResponse(
        job.uploaded_file.open("rb"),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@user_passes_test(_is_superuser)
def error_report(request, pk):
    job = get_object_or_404(ImportJob, pk=pk)
    if not job.error_report:
        raise Http404("This import job has no error report.")
    response = FileResponse(job.error_report.open("rb"), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="import-{job.pk}-errors.csv"'
    return response
