from collections import OrderedDict

from django.db.models import Prefetch

from catalog.models import Product, ProductSpec, TemplateField
from catalog.product_types import product_type_code
from catalog.services import template_fields

POE_SPEC_CODES = {
    "poe_configuration",
    "poe_standard",
    "poe_ports",
    "poe_budget_w",
    "max_poe_per_port_w",
}
MISSING_DISPLAYS = {"Unknown", "Not Published", "Not Applicable"}


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
            raise ValueError("产品参数无效，请重新选择。") from exc
        if product_id not in product_ids:
            product_ids.append(product_id)
    return product_ids


def load_comparison_products(product_ids):
    if not 2 <= len(product_ids) <= 4:
        raise ValueError("请选择 2–4 个不同的产品进行比较。")

    products = (
        Product.objects.filter(pk__in=product_ids, is_published=True)
        .select_related("brand", "category", "product_model")
        .prefetch_related(
            Prefetch(
                "specs",
                queryset=ProductSpec.objects.select_related("definition"),
            )
        )
    )
    products_by_id = {product.pk: product for product in products}
    if len(products_by_id) != len(product_ids):
        raise ValueError("所选产品不存在或尚未发布。")
    selected = [products_by_id[product_id] for product_id in product_ids]
    if len({product.category_id for product in selected}) != 1:
        raise ValueError("只能比较同一产品类型的产品，请分别比较 AP、网桥、网关或交换机。")
    return selected


def _spec_value(product, specs_by_code, definition):
    spec = specs_by_code.get(definition.code)
    if spec:
        return spec.display_value, spec.effective_source_url

    bands_spec = specs_by_code.get("supported_bands")
    is_dual_band = bool(bands_spec and "6 GHz" not in bands_spec.value_text)
    if is_dual_band and definition.code in {"mimo_6g", "rate_6g_mbps"}:
        return "Not Applicable", bands_spec.effective_source_url
    if definition.code == "max_channel_width_mhz":
        return "Not Published", product.official_url
    return "Unknown", ""


def _format_number(value):
    formatted = format(value, "f")
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted or "0"


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
    product_type_codes = {product_type_code(product) for product in products}
    form_factor = product_type_codes.pop() if len(product_type_codes) == 1 else ""
    selected_fields = template_fields(products[0].category, form_factor)
    if not include_extended:
        selected_fields = [
            field
            for field in selected_fields
            if field.priority != TemplateField.Priority.P2
        ]
    specs_by_product = {
        product.pk: {spec.definition.code: spec for spec in product.specs.all()}
        for product in products
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

    if category_slug == "access-point":
        add_row(
            "ap_type",
            "AP Type",
            "Product",
            [(product.get_ap_type_display(), product.official_url) for product in products],
        )
    elif all(product.product_type_id for product in products):
        add_row(
            "product_type",
            "Product Type",
            "Product",
            [
                (product.product_type.name, product.official_url)
                for product in products
            ],
        )
    if category_slug in {"access-point", "wireless-bridge"}:
        add_row(
            "wifi_standard",
            "Wi-Fi Standard",
            "Product",
            [(product.wifi_standard or "Unknown", product.official_url) for product in products],
        )

    for template_field in selected_fields:
        definition = template_field.spec_definition
        if (
            category_slug == "managed-switches"
            and definition.code in POE_SPEC_CODES
            and not comparison_has_poe
        ):
            continue
        values = [
            _spec_value(product, specs_by_product[product.pk], definition)
            for product in products
        ]
        if category_slug == "managed-switches" and definition.code in POE_SPEC_CODES:
            values = [
                ("Not Applicable", "")
                if poe_states[product.pk] is False
                else value
                for product, value in zip(products, values, strict=True)
            ]
        add_row(
            definition.code,
            definition.display_name,
            template_field.display_group or definition.group,
            values,
            template_field.priority,
        )
        if category_slug == "access-point" and definition.code == "rate_6g_mbps":
            add_row(
                "aggregate_rate_mbps",
                "Aggregate Rate",
                "Performance",
                [
                    (
                        f"{_format_number(product.aggregate_rate_mbps)} Mbps",
                        "",
                    )
                    for product in products
                ],
            )

    return rows


def group_comparison_rows(rows):
    grouped = OrderedDict()
    for row in rows:
        label = f'{row["priority"].upper()} · {row["group"]}'
        grouped.setdefault(label, []).append(row)
    return grouped.items()
