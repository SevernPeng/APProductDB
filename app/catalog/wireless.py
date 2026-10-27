"""Shared Wi-Fi capability and channel-width presentation rules."""
from catalog.models import ProductSpec, SpecDefinition, TemplateField
from catalog.spec_applicability import has_published_value


BAND_WIDTH_CODE = "max_channel_width_mhz"
BAND_WIDTH_LABEL = "Band Width"
WIFI_SPEC_CODES = {"router_wifi_standard", "router_supported_bands", "router_wireless_rate_mbps",
                   "supported_bands", "rate_2g_mbps", "rate_5g_mbps", "rate_6g_mbps"}


def product_has_wifi(product):
    if product.category.slug in {"access-point", "wireless-bridge"}:
        return True
    if product.category.slug != "gateway":
        return False
    specs = list(product.specs.all())
    # Imported TP-Link radio rows are more specific than generic page extraction
    # (which can pick up Wi-Fi navigation text on wired router product pages).
    if product.brand.slug == "tp-link":
        return any(s.definition.code.startswith("matrix-") and
                   "wi-fi" in s.definition.display_name.casefold() and has_published_value(s)
                   for s in specs) or getattr(product.product_type, "code", "") == "wireless_router"
    # These existing records have missing/incorrect product-type metadata.
    # Sources: Cisco MX67/MX68 datasheet, DrayTek Vigor2927 series,
    # and Ubiquiti UMR-Industrial technical specifications.
    if (product.brand.slug, product.model.casefold().replace(" ", "")) in {
        ("cisco", "mx67w"), ("meraki", "mx67w"), ("draytek", "vigor2927ax"),
        ("ubiquiti", "umr-industrial"), ("ubiquiti", "umr-industial"),
    }:
        return True
    # The EG wired series can contain generic Wi-Fi navigation text in scraped
    # specs; the manufacturer's EG-series catalog lists these as Ethernet routers.
    if product.brand.slug == "reyee" and product.model.upper() in {
        "RG-EG105G", "RG-EG1510XS", "RG-EG209GS", "RG-EG210G-E", "RG-EG406XS", "RG-EG710XS",
    }:
        return False
    if getattr(product.product_type, "code", "") == "wireless_router":
        return True
    if getattr(product.product_type, "code", "") == "wired_router":
        return False
    return bool(product.wifi_standard) or any(
        s.definition.code in WIFI_SPEC_CODES and has_published_value(s)
        for s in specs
    )


def band_width_definition():
    return SpecDefinition.objects.filter(code=BAND_WIDTH_CODE, active=True).first()


def ensure_band_width(product):
    if not product_has_wifi(product):
        return
    definition = band_width_definition()
    if definition:
        ProductSpec.objects.get_or_create(product=product, definition=definition,
            defaults={"value_status": ProductSpec.ValueStatus.UNKNOWN, "unit": "MHz"})


def add_band_width_row(product, rows):
    previous = next((r for r in rows if r.get("definition") and r["definition"].code == BAND_WIDTH_CODE), None)
    if not product_has_wifi(product):
        return [r for r in rows if not (r.get("definition") and r["definition"].code == BAND_WIDTH_CODE)]
    definition = band_width_definition()
    if definition is None:
        return rows
    spec = next((s for s in product.specs.all() if s.definition_id == definition.pk), None)
    if previous:
        return [dict(r, display_name=BAND_WIDTH_LABEL,
                     display_value=spec.display_value if spec else r["display_value"])
                if r is previous else r for r in rows]
    rows.append({"definition": definition, "display_name": BAND_WIDTH_LABEL,
        "display_group": "WIRELESS FEATURES", "priority": TemplateField.Priority.P1,
        "display_value": spec.display_value if spec else "Unknown",
        "source_url": spec.effective_source_url if spec else "", "source_note": "",
        "verified_date": spec.verified_date if spec else None, "collected": True})
    return rows
