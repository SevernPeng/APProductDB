"""Present competitor values using the corresponding Omada workbook layout."""
from collections import Counter
from catalog.models import Product, ProductSpec, TemplateField
from catalog.spec_applicability import has_published_value
from comparison.models import ProductMatch
from comparison.spec_values import ALIASES, ComparisonValue, SpecResolver, label_key


DISPLAY_LABELS = {
    "ethernet_interfaces": "Interface",
    "supported_bands": "Frequency",
    "max_power_consumption_w": "Max. Power Consumption",
    "power_method": "Power Supply",
    "max_clients": "Concurrent Clients",
    "installation": "Mounting",
    "fan_design": "Fan Quantity",
    "packet_buffer_mb": "Packet Buffer Memory",
    "l2_features": "L2 and L2+ Features",
    "l3_features": "L3 Features",
    "management_methods": "Management Features",
    "controller_management": "Centralized Management",
    "lightning_protection_kv": "Surge Protection",
    "ip_rating": "Weatherproof Enclosure",
}
RATE_CODES = {"rate_2g_mbps": "2.4", "rate_5g_mbps": "5", "rate_6g_mbps": "6"}


def competitor_detail_rows(product, original_rows, reference_layout=None):
    specs = [s for s in product.specs.all() if s.definition.active]
    # Resolve every source field, but emit only fields in the reference layout.
    original_rows = list(original_rows)
    present = {r["definition"].pk for r in original_rows if r.get("definition")}
    original_rows.extend({"definition": s.definition, "display_name": s.definition.display_name,
                          "display_group": s.definition.group, "display_value": s.display_value}
                         for s in specs if s.definition_id not in present)
    definitions = {s.definition.code: s.definition for s in specs}
    definitions.update({r["definition"].code: r["definition"] for r in original_rows if r.get("definition")})
    resolver = SpecResolver(product, list(definitions.values()))
    rows_by_label = {}
    consumed = set()

    def row(name, group, value, definition=None, source_specs=()):
        return {"definition": definition, "display_name": name, "display_group": group,
                "priority": TemplateField.Priority.P1, "display_value": value.display_value,
                "source_url": value.effective_source_url, "source_note": "",
                "verified_date": max((s.verified_date for s in source_specs if s.verified_date), default=None),
                "collected": value.display_value not in {"Unknown", "Not Published"}}

    for original in original_rows:
        definition = original.get("definition")
        if not definition:
            continue
        code = definition.code
        if code in {"antenna_type", "antenna_gain_dbi", *RATE_CODES, "mesh_support", "fast_roaming"}:
            consumed.add(code)
            continue
        value = resolver.resolve(code)
        current = dict(original)
        if value:
            current.update(display_value=value.display_value, source_url=value.effective_source_url)
        current["display_name"] = DISPLAY_LABELS.get(code, definition.display_name)
        rows_by_label[label_key(current["display_name"])] = current

    if product.category.slug in {"access-point", "wireless-bridge"}:
        consumed.update({"antenna_type", "antenna_gain_dbi", *RATE_CODES, "mesh_support", "fast_roaming"})
        rows_by_label["antenna"] = row("Antenna", "HARDWARE FEATURES", resolver.antenna(),
            source_specs=[s for s in specs if s.definition.code in {"antenna_type", "antenna_gain_dbi"}])
        rate_lines = []
        rate_sources = []
        bands = resolver.wireless_bands()
        for code, band in RATE_CODES.items():
            value = resolver.resolve(code)
            if value and value.display_value not in {"Unknown", "Not Published", "Not Applicable"}:
                rate_lines.append(f"• {band} GHz: {value.display_value}")
            elif band in bands:
                rate_lines.append(f"• {band} GHz: {value.display_value if value else 'Unknown'}")
            if value:
                rate_sources.append(value.effective_source_url)
        rows_by_label["signal rate"] = row("Signal Rate", "WIRELESS FEATURES",
            ComparisonValue("\n".join(rate_lines) or "Unknown", rate_sources[0] if len(set(rate_sources)) == 1 else ""),
            source_specs=[s for s in specs if s.definition.code in RATE_CODES])
        rows_by_label["wireless standards"] = row("Wireless Standards", "WIRELESS FEATURES",
            ComparisonValue(product.wifi_standard or "Unknown", product.official_url))
        features = []
        for code, name in (("mesh_support", "Mesh"), ("fast_roaming", "Fast Roaming")):
            value = resolver.resolve(code)
            if value and value.display_value not in {"Unknown", "Not Published", "Not Applicable"}:
                text = value.display_value
                features.append(f"• {name}" if text == "Yes" else f"• {name}: {text}")
        rows_by_label["wireless functions"] = row("Wireless Functions", "WIRELESS FEATURES",
            ComparisonValue("\n".join(features) or "Unknown", ""))
        for label in ("signal rate", "wireless functions"):
            native = next((s for s in resolver.by_label.get(label, []) if has_published_value(s)), None)
            if native:
                rows_by_label[label] = row(native.definition.display_name, native.definition.group,
                                           native, native.definition, [native])

    from core.standard_spec_layout import standard_detail_rows
    if reference_layout is None:
        anchor = reference_product(product)
        layout = standard_detail_rows(anchor) if anchor else standard_detail_rows(product)
    else:
        layout = list(reference_layout)
    label_counts = Counter(label_key(r["display_name"]) for r in layout)
    output = []
    used_labels = set()
    for reference in layout:
        definition = reference.get("definition")
        if definition is None:
            # Computed rows use the competitor's own calculation.
            current = next((r for r in original_rows if r["display_name"] == reference["display_name"]), None)
            if current:
                output.append(dict(current, display_group=reference["display_group"]))
            continue
        label = label_key(reference["display_name"])
        group = label_key(reference["display_group"])
        field_key = (group, label)
        if field_key in used_labels:
            continue
        current = rows_by_label.get(label)
        if label_counts[label] > 1:
            current = next((r for r in original_rows if label_key(r["display_name"]) == label
                            and label_key(r["display_group"]) == group), None)
        native = next((s for s in resolver.by_label.get(label, []) if has_published_value(s)
                       and (label_counts[label] == 1 or label_key(s.definition.group) == group)), None)
        if native:
            current = row(definition.display_name, definition.group, native, native.definition, [native])
        if current is None:
            codes = [code for code, d in definitions.items()
                     if not code.startswith("matrix-")
                     and (label_counts[label] == 1 or label_key(d.group) == group) and label in
                     {label_key(name) for name in (d.display_name, *ALIASES.get(code, ())) }]
            values = [(code, resolver.resolve(code)) for code in codes]
            value = next((value for code, value in values if value and value.display_value not in {"Unknown", "Not Published"}), None)
            if value:
                current = row(definition.display_name, definition.group, value)
                consumed.update(codes)
        if current is None:
            current = row(definition.display_name, definition.group, ComparisonValue("Unknown", ""))
        if current:
            current = dict(current, display_name=reference["display_name"],
                           display_group=reference["display_group"], priority=reference["priority"])
            if current.get("definition") is None:
                current["definition"] = definition
            current["collected"] = True  # Include the shared layout's explicit missing values.
            output.append(current)
            used_labels.add(field_key)
            if current.get("definition"):
                consumed.add(current["definition"].code)
    # `layout` is authoritative. Applying the competitor's own Wi-Fi heuristic
    # here could add or remove Band Width after the rows were aligned to the
    # TP-Link benchmark.
    return output



def ensure_competitor_layout_fields(product):
    """Materialize missing shared fields without copying benchmark values."""
    originals = [{"definition": spec.definition, "display_name": spec.definition.display_name,
                  "display_group": spec.definition.group, "display_value": spec.display_value}
                 for spec in product.specs.select_related("definition").filter(definition__active=True)]
    for row in competitor_detail_rows(product, originals):
        definition = row.get("definition")
        if definition:
            ProductSpec.objects.get_or_create(product=product, definition=definition,
                defaults={"value_status": ProductSpec.ValueStatus.UNKNOWN, "unit": definition.unit})


def reference_product(product):
    """Prefer an explicit benchmark, then a same-type TP-Link product."""
    anchors = Product.objects.filter(brand__slug="tp-link", category_id=product.category_id,
                                     is_published=True).select_related("brand", "category", "product_type").prefetch_related("specs__definition")
    anchor_id = ProductMatch.objects.filter(competitor_product=product,
        our_product__brand__slug="tp-link", our_product__category_id=product.category_id,
        our_product__is_published=True).exclude(status=ProductMatch.Status.REJECTED
        ).order_by("rank", "pk").values_list("our_product_id", flat=True).first()
    if anchor_id:
        return anchors.filter(pk=anchor_id).first()
    return anchors.filter(product_type_id=product.product_type_id).order_by("pk").first() or anchors.order_by("pk").first()
