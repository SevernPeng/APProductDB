"""The specification rows displayed by TP-Link products and their benchmarks."""
from collections import OrderedDict
from catalog.models import ProductSpec, TemplateField
from catalog.product_types import product_type_code
from catalog.services import template_fields
from catalog.spec_applicability import field_is_applicable
from catalog.spec_presentation import ordered_spec_groups, workbook_spec_group


def standard_detail_rows(product):
    specs_by_code = {spec.definition.code: spec for spec in product.specs.all()}
    verified_dates = [
        spec.verified_date for spec in specs_by_code.values() if spec.verified_date
    ]
    latest_verified_date = max(verified_dates, default=None)
    bands_spec = specs_by_code.get("supported_bands")
    is_dual_band = bool(bands_spec and "6 GHz" not in bands_spec.value_text)

    selected_fields = [
        field
        for field in template_fields(product.category, product_type_code(product))
        if field_is_applicable(product, field.spec_definition.code, specs_by_code)
    ]

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
        template_group = template_field.display_group or definition.group
        display_group = (
            template_group
            if template_field.display_group
            and template_field.display_group != definition.group
            else workbook_spec_group(product.category.slug, definition.group)
        )
        spec_rows.append(
            {
                "definition": definition,
                "display_name": definition.display_name,
                "priority": template_field.priority,
                "display_group": display_group,
                "display_value": display_value,
                "source_url": source_url,
                "source_note": source_note,
                "verified_date": verified_date,
                "collected": spec is not None,
            }
        )

    matrix_specs = [
        spec
        for spec in product.specs.all()
        if spec.definition.active and spec.definition.code.startswith("matrix-")
    ]
    if matrix_specs:
        spec_rows = [
            {
                "definition": spec.definition,
                "display_name": spec.definition.display_name,
                "priority": TemplateField.Priority.P1,
                "display_group": spec.definition.group,
                "display_value": spec.display_value,
                "source_url": spec.effective_source_url,
                "source_note": spec.source_note,
                "verified_date": spec.verified_date,
                "collected": True,
            }
            for spec in matrix_specs
        ]
        mimo_rows = []
        for code in ("mimo_2g", "mimo_5g", "mimo_6g"):
            spec = specs_by_code.get(code)
            if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
                continue
            mimo_rows.append(
                {
                    "definition": spec.definition,
                    "display_name": spec.definition.display_name,
                    "priority": TemplateField.Priority.P1,
                    "display_group": "WIRELESS FEATURES",
                    "display_value": spec.display_value,
                    "source_url": "",
                    "source_note": "",
                    "verified_date": None,
                    "collected": True,
                }
            )
        if mimo_rows:
            insert_at = next(
                (
                    index
                    for index, row in enumerate(spec_rows)
                    if row["display_group"].casefold() == "wireless features"
                ),
                len(spec_rows),
            )
            spec_rows[insert_at:insert_at] = mimo_rows

    rate_verified_dates = [
        specs_by_code[code].verified_date
        for code in ("rate_2g_mbps", "rate_5g_mbps", "rate_6g_mbps")
        if code in specs_by_code and specs_by_code[code].verified_date
    ]
    detail_rows = list(spec_rows)
    if product.category.slug == "access-point" and not matrix_specs:
        detail_rows.insert(
            0,
            {
                "display_name": "Aggregate Rate",
                "priority": TemplateField.Priority.P0,
                "display_group": "WIRELESS FEATURES",
                "display_value": f"{product.aggregate_rate_mbps:g} Mbps",
                "source_url": "",
                "source_note": "Calculated from maximum band rates",
                "verified_date": max(rate_verified_dates, default=None),
                "collected": True,
            },
        )

    from catalog.wireless import add_band_width_row
    detail_rows = add_band_width_row(product, detail_rows)
    if product.category.slug == "managed-switches":
        detail_rows = [row for row in detail_rows if row["collected"]]
    if not matrix_specs:
        groups = OrderedDict()
        for row in detail_rows:
            groups.setdefault(row["display_group"], []).append(row)
        detail_rows = [row for group in ordered_spec_groups(groups, product.category.slug) for row in group["rows"]]
    return detail_rows
