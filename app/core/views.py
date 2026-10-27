import logging
import mimetypes
from collections import OrderedDict
from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import connection, transaction
from django.db.models import Count, Prefetch, Q
from django.http import FileResponse, Http404, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from audit.models import AuditLog
from catalog.models import (
    Category,
    Product,
    ProductModel,
    ProductSpec,
    TemplateField,
    normalize_model_key,
)
from catalog.official_order import order_products
from catalog.product_types import product_type_code
from catalog.services import ensure_product_spec_placeholders
from catalog.spec_presentation import ordered_spec_groups
from changes.forms import ProductPageEditForm
from changes.models import ChangeRequest
from changes.services import apply_change, request_ip
from comparison.models import ProductMatch
from comparison.scoring import calculate_benchmark_index

from .omada_categories import switch_subcategories
from .permissions import catalog_access_required
from .product_filters import FILTER_PARAMETERS, apply_product_filters, filter_definitions

logger = logging.getLogger(__name__)


@catalog_access_required
@require_GET
def product_list(request, family_slug="", subcategory_slug=""):
    published_products = Product.objects.filter(is_published=True).select_related(
        "brand", "category", "product_type", "product_model"
    )
    own_products = published_products.filter(brand__is_own_brand=True)
    query = request.GET.get("q", "").strip()
    family_key = family_slug or request.GET.get("family", "").strip()
    subcategory_key = subcategory_slug or request.GET.get("subcategory", "").strip()
    category_slug = request.GET.get("category", "").strip()
    show_all_brands = request.GET.get("scope") == "all" or bool(query)

    family_definitions = (
        {
            "key": "wireless", "title": "Wireless", "eyebrow": "Connect every space",
            "description": "Ceiling, wall-plate, outdoor access points and wireless bridges.",
            "slugs": ("access-point", "wireless-bridge"),
            "subcategories": (
                {"key": "wifi-7", "title": "WiFi 7", "query": Q(category__slug="access-point", wifi_standard__iexact="Wi-Fi 7")},
                {"key": "ceiling-mount", "title": "Ceiling Mount", "query": Q(category__slug="access-point") & (Q(product_type__code="ceiling") | Q(ap_type="ceiling"))},
                {"key": "wall-plate", "title": "Wall Plate", "query": Q(category__slug="access-point") & (Q(product_type__code="wall_plate") | Q(ap_type__in=("wall", "wall_plate")))},
                {"key": "outdoor", "title": "Outdoor", "query": Q(category__slug="access-point") & (Q(product_type__code="outdoor") | Q(ap_type="outdoor"))},
                {"key": "wireless-bridge", "title": "Wireless Bridge", "query": Q(category__slug="wireless-bridge")},
                {"key": "gpon", "title": "GPON", "query": Q(model__icontains="gpon") | Q(product_model__product_name__icontains="gpon")},
                {"key": "desktop", "title": "Desktop", "query": Q(category__slug="access-point") & (Q(product_type__code="desktop") | Q(ap_type="desktop"))},
            ),
        },
        {
            "key": "switching", "title": "Switches", "eyebrow": "Build the backbone",
            "description": "Campus, aggregation and access switching, plus Agile, unmanaged and industrial models.",
            "slugs": ("managed-switches", "unmanaged-easy-smart-switches"),
            "subcategories": switch_subcategories(),
        },
        {
            "key": "gateways", "title": "Gateways", "eyebrow": "Secure every site",
            "description": "Wired, Wi-Fi and integrated gateways for business networks.",
            "slugs": ("gateway",),
            "subcategories": (
                {"key": "wired", "title": "Wired Gateways", "query": Q(product_type__code="wired_router")},
                {"key": "wifi", "title": "Wi-Fi Gateways", "query": Q(product_type__code="wireless_router")},
                {"key": "cellular", "title": "4G/5G Gateways", "query": Q(product_type__code__in=("cellular_router", "outdoor_cellular_router"))},
                {"key": "integrated", "title": "Integrated Gateways", "query": Q(product_type__code="integrated_gateway")},
            ),
        },
        {
            "key": "accessories", "title": "Accessories", "eyebrow": "Complete the deployment",
            "description": "Power, modules, converters and installation accessories.",
            "slugs": ("accessories",),
            "subcategories": (
                {"key": "poe-injectors", "title": "PoE Injectors", "query": Q(product_type__code="poe_injector")},
                {"key": "power-supplies", "title": "Power Supplies", "query": Q(product_type__code="power_supply")},
                {"key": "media-converters", "title": "Media Converters", "query": Q(product_type__code="media_converter")},
                {"key": "optical-modules", "title": "Optical Modules", "query": Q(product_type__code="optical_module")},
                {"key": "dac-cables", "title": "DAC Cables", "query": Q(product_type__code="dac_cable")},
                {"key": "mounting", "title": "Mounting", "query": Q(product_type__code__in=("mounting", "junction_box"))},
            ),
        },
    )
    valid_families = {family["key"]: family for family in family_definitions}
    active_family = valid_families.get(family_key)
    if family_slug and not active_family:
        raise Http404("Unknown product family")

    products = published_products if show_all_brands else own_products
    if query:
        products = products.filter(model_key__icontains=normalize_model_key(query))
    if active_family:
        products = products.filter(category__slug__in=active_family["slugs"])
    active_subcategory = None
    if active_family and subcategory_key:
        active_subcategory = next(
            (
                subcategory
                for subcategory in active_family["subcategories"]
                if subcategory["key"] == subcategory_key
            ),
            None,
        )
        if active_subcategory:
            products = products.filter(active_subcategory["query"])
        elif subcategory_slug:
            raise Http404("Unknown product subcategory")
    selected_category = None
    if category_slug:
        selected_category = Category.objects.filter(slug=category_slug).first()
        if selected_category:
            products = products.filter(category=selected_category)
    filter_values = {name: request.GET.get(name, "").strip() for name in FILTER_PARAMETERS}
    products = apply_product_filters(products, filter_values)
    products = order_products(products.distinct(), family_key if active_family else "", subcategory_key)

    counts_by_slug = {
        item["category__slug"]: item["count"]
        for item in own_products.values("category__slug").annotate(count=Count("pk"))
    }
    representative_products = {}
    for product in order_products(own_products):
        slug = product.category.slug
        current = representative_products.get(slug)
        if current is None or (not current.image and product.image):
            representative_products[slug] = product

    product_families = []
    for definition in family_definitions:
        family = dict(definition)
        family["count"] = sum(counts_by_slug.get(slug, 0) for slug in family["slugs"])
        family["featured_product"] = next(
            (representative_products.get(slug) for slug in family["slugs"] if representative_products.get(slug)),
            None,
        )
        product_families.append(family)

    category_cards = []
    if active_family:
        family_products = own_products.filter(category__slug__in=active_family["slugs"])
        for definition in active_family["subcategories"]:
            if definition.get("hidden"):
                continue
            matching_products = family_products.filter(definition["query"]).distinct()
            card = {"key": definition["key"], "title": definition["title"]}
            card["product_count"] = matching_products.count()
            card["featured_product"] = (
                order_products(matching_products.exclude(image=""), active_family["key"], definition["key"]).first()
                or order_products(matching_products, active_family["key"], definition["key"]).first()
            )
            category_cards.append(card)

    paginator = Paginator(products, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    query_parameters = {}
    if query:
        query_parameters["q"] = query
    if active_family and not family_slug:
        query_parameters["family"] = active_family["key"]
    if active_subcategory and not subcategory_slug:
        query_parameters["subcategory"] = active_subcategory["key"]
    if selected_category:
        query_parameters["category"] = selected_category.slug
    if request.GET.get("scope") == "all":
        query_parameters["scope"] = "all"
    clear_filter_querystring = urlencode(query_parameters)
    for name, value in filter_values.items():
        if value:
            query_parameters[name] = value

    product_filter_fields = filter_definitions(active_family["key"] if active_family else "")
    for field in product_filter_fields:
        field["value"] = filter_values[field["name"]]

    return render(
        request,
        "core/product_list.html",
        {
            "page_obj": page_obj,
            "filters": {
                "q": query,
                "family": active_family["key"] if active_family else "",
                "subcategory": active_subcategory["key"] if active_subcategory else "",
                "category": selected_category.slug if selected_category else "",
                "scope": "all" if request.GET.get("scope") == "all" else "",
            },
            "querystring": urlencode(query_parameters),
            "clear_filter_querystring": clear_filter_querystring,
            "product_filter_fields": product_filter_fields,
            "has_product_filters": any(filter_values.values()),
            "product_families": product_families,
            "category_cards": category_cards,
            "active_family": active_family,
            "active_subcategory": active_subcategory,
            "selected_category": selected_category,
            "tp_link_count": own_products.count(),
            "current_portfolio_count": (
                sum(counts_by_slug.get(slug, 0) for slug in active_family["slugs"])
                if active_family else own_products.count()
            ),
            "show_all_brands": show_all_brands,
        },
    )


@catalog_access_required
@require_http_methods(["GET", "POST"])
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
    edit_mode = request.GET.get("edit") == "1" or request.POST.get("edit_mode") == "1"
    action = request.POST.get("action", "") if request.method == "POST" else ""
    if request.method == "POST" and not edit_mode:
        return HttpResponseNotAllowed(["GET"])
    if edit_mode:
        ensure_product_spec_placeholders(product)
        from catalog.wireless import ensure_band_width
        ensure_band_width(product)
        if not product.brand.is_own_brand:
            from core.product_spec_layout import ensure_competitor_layout_fields
            ensure_competitor_layout_fields(product)
        product._prefetched_objects_cache.pop("specs", None)

    edit_form = ProductPageEditForm(
        request.POST if action == "save_product" else None,
        request.FILES if action == "save_product" else None,
        product=product,
    ) if edit_mode else None
    if edit_mode and request.method == "POST":
        if action == "save_product" and edit_form.is_valid():
            changed_values = edit_form.changed_values()
            image_changed = bool(
                edit_form.cleaned_data.get("product_image")
                or edit_form.cleaned_data.get("remove_image")
            )
            with transaction.atomic():
                locked_product = Product.objects.select_for_update().get(pk=product.pk)
                identity_before = {
                    "brand": locked_product.brand_id,
                    "model": locked_product.model,
                    "product_name": locked_product.product_model.product_name if locked_product.product_model_id else "",
                    "category": locked_product.category_id,
                    "product_type": locked_product.product_type_id,
                    "nom_records": locked_product.nom_records,
                }
                brand = edit_form.cleaned_data["identity_brand"]
                category = edit_form.cleaned_data["identity_category"]
                model = edit_form.cleaned_data["identity_model"].strip()
                canonical, _ = ProductModel.objects.get_or_create(
                    brand=brand,
                    model_key=normalize_model_key(model),
                    defaults={
                        "category": category, "model": model,
                        "product_name": edit_form.cleaned_data["identity_product_name"],
                        "lifecycle_status": edit_form.cleaned_data["product_lifecycle_status"],
                    },
                )
                canonical.product_name = edit_form.cleaned_data["identity_product_name"]
                canonical.model = model
                canonical.category = category
                canonical.save()
                locked_product.brand = brand
                locked_product.category = category
                locked_product.product_type = edit_form.cleaned_data["identity_product_type"]
                locked_product.product_model = canonical
                locked_product.model = model
                requested_nom = edit_form.cleaned_data["identity_nom_certified"]
                if requested_nom and not locked_product.has_nom:
                    locked_product.nom_records = [{
                        "source": "Manual product-page edit", "ready": True,
                        "certificates": [{
                            "standard": "NOM", "number": "MANUAL",
                            "permanent": True, "expires_on": None,
                        }],
                    }]
                elif not requested_nom and locked_product.has_nom:
                    locked_product.nom_records = []
                locked_product.updated_by = request.user
                locked_product.save()
                identity_after = {
                    "brand": locked_product.brand_id,
                    "model": locked_product.model,
                    "product_name": canonical.product_name,
                    "category": locked_product.category_id,
                    "product_type": locked_product.product_type_id,
                    "nom_records": locked_product.nom_records,
                }
                identity_changed = identity_before != identity_after
                if identity_changed:
                    AuditLog.objects.create(
                        actor=request.user, action="product.identity.updated",
                        object_type=locked_product._meta.label, object_id=str(locked_product.pk),
                        object_repr=str(locked_product), before_data=identity_before,
                        after_data=identity_after, ip_address=request_ip(request),
                    )
                for selection, old_value, proposed_value in changed_values:
                    attributes = {
                        "request_type": selection["request_type"],
                        "target_product": product,
                        "field_name": selection["field_name"],
                        "old_value": old_value,
                        "proposed_value": proposed_value,
                        "reason": "Edited inline on the product detail page.",
                        "submitted_by": request.user,
                    }
                    if selection["request_type"] == ChangeRequest.RequestType.SPEC:
                        attributes["target_spec"] = selection["target"]
                        attributes["source_url"] = (
                            selection["target"].source_url or product.official_url
                        )
                    elif selection["request_type"] == ChangeRequest.RequestType.MATCH:
                        attributes["target_match"] = selection["target"]
                        attributes["target_product"] = selection["target"].our_product
                    change = ChangeRequest.objects.create(**attributes)
                    apply_change(
                        change.pk,
                        request.user,
                        "Applied from inline product editing.",
                        request_ip(request),
                    )
                if image_changed:
                    image_product = Product.objects.select_for_update().get(pk=product.pk)
                    before_image = image_product.image.name if image_product.image else ""
                    replacement = edit_form.cleaned_data.get("product_image")
                    if image_product.image:
                        image_product.image.delete(save=False)
                    image_product.image = replacement or ""
                    image_product.updated_by = request.user
                    image_product.save(update_fields=("image", "updated_by", "updated_at"))
                    AuditLog.objects.create(
                        actor=request.user,
                        action="product.image.updated",
                        object_type=image_product._meta.label,
                        object_id=str(image_product.pk),
                        object_repr=str(image_product),
                        before_data={"image": before_image},
                        after_data={"image": image_product.image.name if image_product.image else ""},
                        ip_address=request_ip(request),
                    )
                price_changed = False
                if edit_form.price_snapshot:
                    snapshot = type(edit_form.price_snapshot).objects.select_for_update().get(pk=edit_form.price_snapshot.pk)
                    price_before = {
                        "unit_price": str(snapshot.unit_price), "currency": snapshot.currency,
                        "product_url": snapshot.product_url,
                    }
                    snapshot.unit_price = edit_form.cleaned_data["price_unit_price"]
                    snapshot.currency = edit_form.cleaned_data["price_currency"].strip().upper()
                    snapshot.product_url = edit_form.cleaned_data["price_product_url"]
                    price_after = {
                        "unit_price": str(snapshot.unit_price), "currency": snapshot.currency,
                        "product_url": snapshot.product_url,
                    }
                    price_changed = price_before != price_after
                    if price_changed:
                        snapshot.save(update_fields=("unit_price", "currency", "product_url"))
                        AuditLog.objects.create(
                            actor=request.user, action="product.price.updated",
                            object_type=snapshot._meta.label, object_id=str(snapshot.pk),
                            object_repr=str(snapshot), before_data=price_before,
                            after_data=price_after, ip_address=request_ip(request),
                        )
            total_changes = len(changed_values) + int(image_changed) + int(identity_changed) + int(price_changed)
            messages.success(request, f"Saved {total_changes} change(s)." if total_changes else "No changes were made.")
            return redirect("product-detail", pk=product.pk)

    from core.standard_spec_layout import standard_detail_rows
    detail_rows = standard_detail_rows(product)
    matrix_specs = any(spec.definition.active and spec.definition.code.startswith("matrix-")
                       for spec in product.specs.all())
    if not product.brand.is_own_brand:
        from core.product_spec_layout import competitor_detail_rows
        detail_rows = competitor_detail_rows(product, detail_rows)

    spec_rows = [row for row in detail_rows if row.get("definition")]
    for row in detail_rows:
        value_lines = []
        for raw_line in str(row["display_value"]).splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line[:1] in {"•", "·", "▪", "◦"}:
                line = line[1:].strip()
            value_lines.append(line)
        row["display_lines"] = value_lines
        row["use_two_columns"] = len(value_lines) >= 4

    product_edit_items = []
    identity_edit_items = []
    spec_edit_fields = {}
    match_edit_fields = {}
    if edit_form:
        identity_edit_items = [
            {**item, "field": edit_form[item["name"]]}
            for item in edit_form.identity_items
        ]
        for item in edit_form.edit_items:
            bound_item = {**item, "field": edit_form[item["name"]]}
            if item["selection"]["request_type"] == ChangeRequest.RequestType.PRODUCT:
                product_edit_items.append(bound_item)
            elif item["selection"]["request_type"] == ChangeRequest.RequestType.SPEC:
                spec_edit_fields[item["selection"]["target"].definition_id] = bound_item
            else:
                match_edit_fields.setdefault(item["selection"]["target"].pk, []).append(bound_item)
        for row in detail_rows:
            definition = row.get("definition")
            if definition:
                row["edit_item"] = spec_edit_fields.get(definition.pk)

    # The source workbook is organized as Group -> Specification -> Product value.
    # Keep that same reading order on the single-product page while preserving the
    # template order selected for this product type.
    grouped_rows = OrderedDict()
    for row in detail_rows:
        if product.category.slug == "managed-switches" and not row["collected"]:
            continue
        grouped_rows.setdefault(row["display_group"], []).append(row)
    spec_groups = [{"name": group_name, "rows": rows} for group_name, rows in grouped_rows.items()]
    if not matrix_specs and product.brand.is_own_brand:
        spec_groups = ordered_spec_groups(grouped_rows, product.category.slug)
    matches = []
    if product.brand.is_own_brand:
        match_queryset = product.competitor_matches.exclude(
            status=ProductMatch.Status.REJECTED
        ).filter(competitor_product__is_published=True).select_related(
            "competitor_product__brand", "competitor_product__category",
            "competitor_product__product_type",
        ).prefetch_related("competitor_product__specs__definition")
        for match in match_queryset:
            matches.append(
                {
                    "product": match.competitor_product,
                    "relationship": "Competitor",
                    "match": match,
                }
            )
    else:
        match_queryset = product.matched_as_competitor.exclude(
            status=ProductMatch.Status.REJECTED
        ).filter(our_product__is_published=True).select_related(
            "our_product__brand", "our_product__category", "our_product__product_type"
        ).prefetch_related("our_product__specs__definition")
        for match in match_queryset:
            matches.append(
                {
                    "product": match.our_product,
                    "relationship": "Our Product",
                    "match": match,
                }
            )

    # Legacy imports and benchmark cases can both link the same product pair.
    # This card lists products, so choose one relationship before ranking and
    # slicing the visible list (and before building Compare All).
    matches.sort(key=lambda item: (
        item["match"].status == ProductMatch.Status.CONFIRMED,
        item["match"].benchmark_case_id is not None,
        item["match"].updated_at,
        item["match"].pk,
    ), reverse=True)
    unique_matches = {}
    for item in matches:
        unique_matches.setdefault(item["product"].pk, item)
    matches = list(unique_matches.values())

    for item in matches:
        match = item["match"]
        item["benchmark_index"] = calculate_benchmark_index(
            match.our_product,
            match.competitor_product,
            manual_score=match.match_score,
        )
        item["edit_fields"] = match_edit_fields.get(match.pk, [])
    matches.sort(
        key=lambda item: (
            -item["benchmark_index"],
            item["product"].brand.name.casefold(),
            item["product"].model.casefold(),
            item["product"].pk,
        )
    )
    visible_matches = matches[:3]
    collapsed_matches = matches[3:]

    compare_matches_url = ""
    if matches:
        compare_ids = [product.pk] + [item["product"].pk for item in visible_matches]
        compare_matches_url = reverse("comparison:compare") + "?" + urlencode(
            [("products", product_id) for product_id in compare_ids]
        )

    price_history = list(
        product.price_snapshots.filter(source__code="syscom")
        .select_related("source")
        .order_by("-created_at", "-pk")[:52]
    )
    price_chart_points = [
        {
            "date": snapshot.created_at.strftime("%Y-%m-%d"),
            "price": float(snapshot.unit_price),
        }
        for snapshot in reversed(price_history)
    ]

    return render(
        request,
        "core/product_detail.html",
        {
            "product": product,
            "edit_mode": edit_mode,
            "edit_form": edit_form,
            "product_edit_items": product_edit_items,
            "identity_edit_items": identity_edit_items,
            "spec_rows": spec_rows,
            "spec_groups": spec_groups,
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
            "aggregate_verified_date": max((s.verified_date for s in product.specs.all() if s.verified_date and s.definition.code in {"rate_2g_mbps", "rate_5g_mbps", "rate_6g_mbps"}), default=None),
            "matches": matches,
            "visible_matches": visible_matches,
            "collapsed_matches": collapsed_matches,
            "compare_matches_url": compare_matches_url,
            "current_price": price_history[0] if price_history else None,
            "price_chart_points": price_chart_points,
        },
    )


@catalog_access_required
@require_GET
def product_image(request, pk):
    product = get_object_or_404(Product, pk=pk, is_published=True)
    if not product.image:
        raise Http404("Product image is unavailable.")
    try:
        image_file = product.image.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("Product image file is unavailable.")
    content_type = mimetypes.guess_type(product.image.name)[0] or "application/octet-stream"
    response = FileResponse(image_file, content_type=content_type)
    response["Cache-Control"] = "private, max-age=86400"
    return response


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.exception("Database health check failed")
        return JsonResponse({"status": "error", "database": "error"}, status=503)
    return JsonResponse({"status": "ok", "database": "ok"})
