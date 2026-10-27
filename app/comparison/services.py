from collections import OrderedDict

from django.db.models import Prefetch

from catalog.models import Product, ProductSpec, TemplateField
from catalog.product_types import product_type_code
from catalog.services import template_fields
from catalog.spec_applicability import (
    POE_OUTPUT_SPEC_CODES,
)
from catalog.spec_presentation import ordered_spec_groups, workbook_spec_group
from comparison.spec_values import SpecResolver

POE_SPEC_CODES = POE_OUTPUT_SPEC_CODES
MISSING_DISPLAYS = {"Unknown", "Not Published", "Not Applicable"}


def _template_product(products):
    """Choose the TP-Link benchmark whose template governs the comparison."""
    own_products = [product for product in products if product.brand.is_own_brand]
    if own_products:
        return own_products[0]

    # Competitor-only comparisons still use the first competitor's explicit
    # TP-Link benchmark (or the existing same-type fallback), never a vendor-
    # specific product type as an accidental template source.
    from core.product_spec_layout import reference_product

    return reference_product(products[0]) or products[0]


def parse_product_ids(values):
    raw_values = []
    for value in values:
        raw_values.extend(value.split(","))

    product_ids = []
    for value in raw_values:
        value = value.strip()
        if not value:
            continue
        try:
            product_id = int(value)
        except ValueError as exc:
            raise ValueError("Invalid product selection.") from exc
        if product_id not in product_ids:
            product_ids.append(product_id)
    return product_ids


def load_comparison_products(product_ids):
    if not 2 <= len(product_ids) <= 4:
        raise ValueError("Select 2–4 different products to compare.")

    products = (
        Product.objects.filter(pk__in=product_ids, is_published=True)
        .select_related("brand", "category", "product_model", "product_type")
        .prefetch_related(
            Prefetch(
                "specs",
                queryset=ProductSpec.objects.select_related("definition"),
            )
        )
    )
    products_by_id = {product.pk: product for product in products}
    if len(products_by_id) != len(product_ids):
        raise ValueError("A selected product does not exist or is not published.")
    selected = [products_by_id[product_id] for product_id in product_ids]
    if len({product.category_id for product in selected}) != 1:
        raise ValueError("Only products of the same type can be compared.")
    return selected


def _spec_value(product, specs_by_code, definition, resolver=None):
    spec = resolver.resolve(definition.code) if resolver else specs_by_code.get(definition.code)
    if spec:
        return spec.display_value, spec.effective_source_url

    bands_spec = specs_by_code.get("supported_bands")
    is_dual_band = bool(bands_spec and "6 GHz" not in bands_spec.value_text)
    if is_dual_band and definition.code in {"mimo_6g", "rate_6g_mbps"}:
        return "Not Applicable", bands_spec.effective_source_url
    if definition.code == "max_channel_width_mhz":
        return "Not Published", product.official_url
    return "Unknown", ""


def _switch_poe_state(specs_by_code):
    """Return True/False/None for supported, unsupported, or genuinely unknown."""
    explicit_unsupported = False
    for code in POE_SPEC_CODES:
        spec = specs_by_code.get(code)
        if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
            continue
        if spec.value_number is not None:
            if spec.value_number > 0:
                return True
            explicit_unsupported = True
        elif spec.value_boolean is not None:
            if spec.value_boolean:
                return True
            explicit_unsupported = True
        else:
            text = (spec.value_text or "").strip().casefold()
            if not text:
                continue
            if any(marker in text for marker in ("non-poe", "no poe", "without poe")):
                explicit_unsupported = True
            else:
                return True
    if explicit_unsupported:
        return False
    # A well-populated PPT-backed switch without any PoE field is a non-PoE model.
    if any(
        (spec.source_note or "").startswith("Imported from Omada managed Switch")
        for spec in specs_by_code.values()
    ):
        return False
    return None


def build_comparison_rows(products, only_differences=False, include_extended=False):
    template_product = _template_product(products)
    from core.standard_spec_layout import standard_detail_rows

    # The selected TP-Link product's actual detail layout is the product-level
    # spec template. Workbook-backed products can have richer, reviewed rows
    # than the generic category/form-factor template.
    has_imported_product_template = any(
        spec.definition.code.startswith("matrix-")
        and (spec.source_note or "").startswith("Imported from")
        for spec in template_product.specs.all()
    )
    if has_imported_product_template:
        all_template_rows = [
            row for row in standard_detail_rows(template_product)
            if row.get("definition") is not None
        ]
    else:
        all_template_rows = []
        for field in template_fields(
            template_product.category,
            product_type_code(template_product),
        ):
            definition = field.spec_definition
            template_group = field.display_group or definition.group
            display_group = (
                template_group
                if field.display_group and field.display_group != definition.group
                else workbook_spec_group(template_product.category.slug, definition.group)
            )
            all_template_rows.append(
                {
                    "definition": definition,
                    "display_name": definition.display_name,
                    "display_group": display_group,
                    "priority": field.priority,
                }
            )
    selected_template_rows = all_template_rows
    if not include_extended:
        selected_template_rows = [
            row
            for row in selected_template_rows
            if row["priority"] != TemplateField.Priority.P2
        ]
    specs_by_product = {
        product.pk: {spec.definition.code: spec for spec in product.specs.all()}
        for product in products
    }
    resolvers = {
        product.pk: SpecResolver(
            product,
            [row["definition"] for row in all_template_rows],
        )
        for product in products
    }
    from core.product_spec_layout import competitor_detail_rows
    from comparison.spec_values import label_key

    aligned_rows = {}
    for product in products:
        if product.pk == template_product.pk:
            continue
        product_rows = competitor_detail_rows(
            product,
            standard_detail_rows(product),
            reference_layout=all_template_rows,
        )
        aligned_rows[product.pk] = {
            (label_key(row["display_group"]), label_key(row["display_name"])): row
            for row in product_rows
        }
    category_slug = products[0].category.slug
    poe_states = (
        {
            product.pk: _switch_poe_state(specs_by_product[product.pk])
            for product in products
        }
        if category_slug == "managed-switches"
        else {}
    )
    comparison_has_poe = any(poe_states.values())
    if category_slug == "managed-switches":
        for product in products:
            workbook_poe = resolvers[product.pk].workbook_poe_state()
            if workbook_poe is not None and poe_states[product.pk] is not True:
                poe_states[product.pk] = workbook_poe
        comparison_has_poe = any(poe_states.values())
    rows = []

    def add_row(code, name, group, values, priority=TemplateField.Priority.P0):
        row = {
            "code": code,
            "name": name,
            "group": group,
            "priority": priority,
            "values": [
                {"display": display, "source_url": source_url}
                for display, source_url in values
            ],
        }
        row["is_different"] = len({value["display"] for value in row["values"]}) > 1
        if category_slug == "managed-switches" and all(
            value["display"] in MISSING_DISPLAYS for value in row["values"]
        ):
            return
        if not only_differences or row["is_different"]:
            rows.append(row)

    for template_row in selected_template_rows:
        definition = template_row["definition"]
        if (
            category_slug == "managed-switches"
            and definition.code in POE_SPEC_CODES
            and not comparison_has_poe
        ):
            continue
        values = []
        row_key = (
            label_key(template_row["display_group"]),
            label_key(template_row["display_name"]),
        )
        for product in products:
            if product.pk == template_product.pk:
                values.append(
                    _spec_value(
                        product,
                        specs_by_product[product.pk],
                        definition,
                        resolvers[product.pk],
                    )
                )
                continue
            aligned = aligned_rows[product.pk].get(row_key)
            direct_spec = specs_by_product[product.pk].get(definition.code)
            resolved_value = _spec_value(
                product,
                specs_by_product[product.pk],
                definition,
                resolvers[product.pk],
            )
            if (
                direct_spec
                and direct_spec.value_status == ProductSpec.ValueStatus.NOT_APPLICABLE
            ):
                values.append(resolved_value)
            elif aligned and aligned["display_value"] not in MISSING_DISPLAYS:
                values.append(
                    (aligned["display_value"], aligned.get("source_url", ""))
                )
            elif resolved_value[0] != "Unknown":
                values.append(resolved_value)
            elif aligned:
                values.append(
                    (aligned["display_value"], aligned.get("source_url", ""))
                )
            else:
                values.append(("Unknown", ""))
        if category_slug == "managed-switches" and definition.code in POE_SPEC_CODES:
            values = [
                ("Not Applicable", "")
                if poe_states[product.pk] is False
                else value
                for product, value in zip(products, values, strict=True)
            ]
        add_row(
            definition.code,
            template_row["display_name"],
            template_row["display_group"],
            values,
            template_row["priority"],
        )
    # Even in extended mode, rows are limited to the selected TP-Link product's
    # template. Extended mode only reveals P2 fields from that template.
    return rows


def group_comparison_rows(rows, category_slug=""):
    grouped = OrderedDict()
    for row in rows:
        grouped.setdefault(row["group"], []).append(row)
    return ordered_spec_groups(grouped, category_slug)
