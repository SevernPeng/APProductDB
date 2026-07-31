import logging
from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from accounts.permissions import can_review
from catalog.datasheets import schedule_datasheet_ingestion
from catalog.forms import DatasheetUploadForm, DatasheetURLForm
from catalog.models import (
    DatasheetIngestion,
    Product,
    ProductSpec,
    TemplateField,
    normalize_model_key,
)
from catalog.product_types import product_type_code
from catalog.services import template_fields
from changes.models import ChangeRequest
from comparison.models import ProductMatch

from .permissions import catalog_access_required, contributor_required

logger = logging.getLogger(__name__)

@catalog_access_required
@require_GET
def home(request):
    published_products = Product.objects.filter(is_published=True)
    pending_changes = ChangeRequest.objects.filter(status=ChangeRequest.Status.PENDING)
    return render(
        request,
        "core/home.html",
        {
            "product_count": published_products.count(),
            "own_brand_count": published_products.filter(brand__is_own_brand=True).count(),
            "competitor_count": published_products.filter(brand__is_own_brand=False).count(),
            # Windows clocks can assign the same timestamp to rapid consecutive saves.
            "recent_products": published_products.select_related("brand").order_by("-updated_at", "-pk")[:5],
            "pending_change_count": pending_changes.filter(submitted_by=request.user).count(),
            "pending_review_count": pending_changes.count() if can_review(request.user) else None,
        },
    )


@catalog_access_required
@require_GET
def product_list(request):
    products = Product.objects.filter(
        is_published=True,
    ).select_related("brand", "category", "product_type")
    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(model_key__icontains=normalize_model_key(query))
    products = products.distinct().order_by("brand__name", "model", "region", "hardware_version")

    paginator = Paginator(products, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "core/product_list.html",
        {
            "page_obj": page_obj,
            "filters": {"q": query},
            "querystring": urlencode({"q": query}) if query else "",
        },
    )


@catalog_access_required
@require_GET
def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.filter(is_published=True)
        .select_related("brand", "category", "product_type")
        .prefetch_related(
            Prefetch(
                "specs",
                queryset=ProductSpec.objects.select_related("definition"),
            )
        ),
        pk=pk,
    )
    specs_by_code = {spec.definition.code: spec for spec in product.specs.all()}
    verified_dates = [
        spec.verified_date for spec in specs_by_code.values() if spec.verified_date
    ]
    latest_verified_date = max(verified_dates, default=None)
    bands_spec = specs_by_code.get("supported_bands")
    is_dual_band = bool(bands_spec and "6 GHz" not in bands_spec.value_text)

    selected_fields = template_fields(product.category, product_type_code(product))

    spec_rows = []
    for template_field in selected_fields:
        definition = template_field.spec_definition
        spec = specs_by_code.get(definition.code)
        if spec:
            display_value = spec.display_value
            source_url = spec.effective_source_url
            source_note = ""
            verified_date = spec.verified_date
        elif is_dual_band and definition.code in {"mimo_6g", "rate_6g_mbps"}:
            display_value = "Not Applicable"
            source_url = bands_spec.effective_source_url
            source_note = "The product does not support the 6 GHz service band."
            verified_date = bands_spec.verified_date
        elif definition.code == "max_channel_width_mhz":
            display_value = "Not Published"
            source_url = product.official_url
            source_note = "The official source does not publish this value."
            verified_date = latest_verified_date
        else:
            display_value = "Unknown"
            source_url = ""
            source_note = "This field has not been collected."
            verified_date = None
        spec_rows.append(
            {
                "definition": definition,
                "priority": template_field.priority,
                "display_group": template_field.display_group or definition.group,
                "display_value": display_value,
                "source_url": source_url,
                "source_note": source_note,
                "verified_date": verified_date,
                "collected": spec is not None,
            }
        )

    rate_verified_dates = [
        specs_by_code[code].verified_date
        for code in ("rate_2g_mbps", "rate_5g_mbps", "rate_6g_mbps")
        if code in specs_by_code and specs_by_code[code].verified_date
    ]
    matches = []
    if product.brand.is_own_brand:
        match_queryset = product.competitor_matches.exclude(
            status=ProductMatch.Status.REJECTED
        ).filter(competitor_product__is_published=True).select_related(
            "competitor_product__brand"
        )
        for match in match_queryset:
            matches.append(
                {
                    "product": match.competitor_product,
                    "relationship": "竞品",
                    "match": match,
                }
            )
    else:
        match_queryset = product.matched_as_competitor.exclude(
            status=ProductMatch.Status.REJECTED
        ).filter(our_product__is_published=True).select_related("our_product__brand")
        for match in match_queryset:
            matches.append(
                {
                    "product": match.our_product,
                    "relationship": "我方产品",
                    "match": match,
                }
            )

    compare_matches_url = ""
    if matches:
        compare_ids = [product.pk] + [item["product"].pk for item in matches[:3]]
        compare_matches_url = reverse("comparison:compare") + "?" + urlencode(
            [("products", product_id) for product_id in compare_ids]
        )

    return render(
        request,
        "core/product_detail.html",
        {
            "product": product,
            "spec_rows": spec_rows,
            "p0_spec_rows": [
                row
                for row in spec_rows
                if row["priority"] == TemplateField.Priority.P0
                and (
                    product.category.slug != "managed-switches"
                    or row["collected"]
                )
            ],
            "p1_spec_rows": [
                row
                for row in spec_rows
                if row["priority"] == TemplateField.Priority.P1
                and (
                    product.category.slug != "managed-switches"
                    or row["collected"]
                )
            ],
            "p2_spec_rows": [
                row
                for row in spec_rows
                if row["priority"] == TemplateField.Priority.P2
                and (
                    product.category.slug != "managed-switches"
                    or row["collected"]
                )
            ],
            "aggregate_rate": product.aggregate_rate_mbps,
            "aggregate_verified_date": max(rate_verified_dates, default=None),
            "matches": matches,
            "compare_matches_url": compare_matches_url,
        },
    )


def _datasheet_page_context(product, url_form=None):
    return {
        "product": product,
        "datasheet_upload_form": DatasheetUploadForm(),
        "datasheet_url_form": url_form
        or DatasheetURLForm(initial={"datasheet_url": product.datasheet_url}),
        "datasheet_ingestions": product.datasheet_ingestions.all()[:10],
    }


@catalog_access_required
@require_GET
def product_datasheet(request, pk):
    product = get_object_or_404(
        Product.objects.select_related("brand", "category", "product_type"),
        pk=pk,
        is_published=True,
    )
    return render(
        request,
        "core/product_datasheet.html",
        _datasheet_page_context(product),
    )


@contributor_required
@require_POST
def upload_datasheet(request, pk):
    product = get_object_or_404(Product, pk=pk, is_published=True)
    form = DatasheetUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(
            request,
            "Datasheet 上传失败：" + "；".join(
                message
                for errors in form.errors.values()
                for message in errors
            ),
        )
        return redirect("product-datasheet", pk=product.pk)
    ingestion = DatasheetIngestion.objects.create(
        product=product,
        source_type=DatasheetIngestion.SourceType.UPLOAD,
        uploaded_file=form.cleaned_data["datasheet"],
        requested_by=request.user,
    )
    schedule_datasheet_ingestion(ingestion.pk)
    messages.success(
        request,
        "Datasheet 已加入后台识别队列，可以继续处理其他产品。",
    )
    return redirect("product-datasheet", pk=product.pk)


@contributor_required
@require_POST
def submit_datasheet_url(request, pk):
    product = get_object_or_404(Product, pk=pk, is_published=True)
    form = DatasheetURLForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "core/product_datasheet.html",
            _datasheet_page_context(product, url_form=form),
            status=400,
        )
    source_url = form.cleaned_data["datasheet_url"]
    ingestion = DatasheetIngestion.objects.create(
        product=product,
        source_type=DatasheetIngestion.SourceType.URL,
        source_url=source_url,
        requested_by=request.user,
    )
    schedule_datasheet_ingestion(ingestion.pk)
    messages.success(
        request,
        "Datasheet URL 已加入后台校验队列；校验通过后才会保存到产品。",
    )
    return redirect("product-datasheet", pk=product.pk)


@contributor_required
@require_POST
def reprocess_datasheet_url(request, pk):
    product = get_object_or_404(Product, pk=pk, is_published=True)
    if not product.datasheet_url:
        messages.error(request, "该产品尚未填写 Datasheet URL。")
        return redirect("product-datasheet", pk=product.pk)
    ingestion = DatasheetIngestion.objects.create(
        product=product,
        source_type=DatasheetIngestion.SourceType.URL,
        source_url=product.datasheet_url,
        requested_by=request.user,
    )
    schedule_datasheet_ingestion(ingestion.pk)
    messages.success(request, "Datasheet URL 已加入后台重新识别队列。")
    return redirect("product-datasheet", pk=product.pk)


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.exception("Database health check failed")
        return JsonResponse({"status": "error", "database": "error"}, status=503)
    return JsonResponse({"status": "ok", "database": "ok"})
