import re

from catalog.models import ProductSpec


SWITCH_CATEGORY_SLUGS = {
    "managed-switches",
    "unmanaged-easy-smart-switches",
}

POE_OUTPUT_SPEC_CODES = {
    "poe_configuration",
    "poe_standard",
    "poe_ports",
    "poe_budget_w",
    "max_poe_per_port_w",
    "extend_mode",
    "poe_auto_recovery",
}

POE_MODEL_SUFFIXES = (
    "P",
    "PA",
    "PE",
    "FP",
    "LP",
    "HP",
    "MP",
    "PP",
    "GP",
    "UP",
)

MANAGEMENT_FEATURE_SPEC_CODES = {
    "management_methods",
    "vlan_support",
    "link_aggregation",
    "port_mirroring",
    "cable_test",
}

# Configurable switch functions are not applicable to a plain plug-and-play
# switch unless the manufacturer explicitly publishes that individual feature
# (for example, an unmanaged surveillance switch with a physical VLAN toggle).
PLAIN_UNMANAGED_CONFIG_SPEC_CODES = {
    "port_isolation",
    "cable_test",
    "igmp_snooping",
    "link_aggregation",
    "loop_prevention",
    "port_mirroring",
    "vlan_support",
}

BAND_SPEC_CODES = {
    "2.4": {"mimo_2g", "rate_2g_mbps"},
    "5": {"mimo_5g", "rate_5g_mbps"},
    "6": {"mimo_6g", "rate_6g_mbps"},
}

STACKING_DETAIL_SPEC_CODES = {
    "stacking_bandwidth_gbps",
    "stacking_units",
    "stacking_ports",
}


def has_published_value(spec):
    return bool(
        spec
        and spec.value_status == ProductSpec.ValueStatus.PUBLISHED
        and (
            bool((spec.value_text or "").strip())
            or spec.value_number is not None
            or spec.value_boolean is not None
        )
    )


def specs_by_code(product):
    cached = getattr(product, "_prefetched_objects_cache", {}).get("specs")
    specs = cached if cached is not None else product.specs.select_related("definition")
    return {spec.definition.code: spec for spec in specs}


def switch_has_management_features(product_specs):
    return any(
        has_published_value(product_specs.get(code))
        for code in MANAGEMENT_FEATURE_SPEC_CODES
    )


def _text_value(spec):
    if not has_published_value(spec):
        return ""
    if spec.value_text:
        return spec.value_text.strip()
    if spec.value_number is not None:
        return str(spec.value_number)
    return "yes" if spec.value_boolean else "no"


def model_indicates_poe(product):
    upper = (product.model or "").upper()
    if "POE" in upper or product.brand.name.casefold() == "trendnet" and upper.startswith("TPE-"):
        return True
    suffixes = "|".join(POE_MODEL_SUFFIXES)
    return bool(
        re.search(rf"\d(?:{suffixes})(?:[-_/()]|$)", upper)
        or re.search(rf"(?:^|[-_/])(?:{suffixes})(?:[-_/()]|$)", upper)
    )


def switch_poe_state(product, product_specs=None):
    """Return True/False/None for PoE, non-PoE, or not yet established."""
    if product.category.slug not in SWITCH_CATEGORY_SLUGS:
        return None

    product_type_code = getattr(getattr(product, "product_type", None), "code", "")
    if product_type_code.endswith("_non_poe"):
        return False
    if product_type_code.endswith("_poe"):
        return True

    product_specs = product_specs or specs_by_code(product)
    for code in POE_OUTPUT_SPEC_CODES:
        spec = product_specs.get(code)
        if not has_published_value(spec):
            continue
        if spec.value_number is not None:
            if spec.value_number > 0:
                return True
            continue
        if spec.value_boolean is not None:
            if spec.value_boolean:
                return True
            continue
        value = _text_value(spec).casefold()
        if value and not any(
            marker in value for marker in ("non-poe", "no poe", "without poe")
        ):
            return True

    if model_indicates_poe(product):
        return True

    searchable = " ".join(
        filter(
            None,
            (
                product.model,
                product.notes,
                getattr(getattr(product, "product_model", None), "product_name", ""),
                _text_value(product_specs.get("ethernet_interfaces")),
            ),
        )
    )
    lowered = searchable.casefold()
    if re.search(r"\b(?:poe\+\+|poe\+|poe)\b", lowered):
        return True
    if re.search(r"\b(?:non[- ]poe|without poe|no poe)\b", lowered):
        return False

    # A switch already backed by several published official specifications but
    # with no PoE evidence is treated as a non-PoE model. Sparse records remain
    # unknown so a future crawl can still discover PoE support.
    published = [spec for spec in product_specs.values() if has_published_value(spec)]
    official_published = [
        spec
        for spec in published
        if spec.source_url or spec.evidence.exists()
    ]
    management_spec = product_specs.get("management_type")
    interface_spec = product_specs.get("ethernet_interfaces")
    if (
        _text_value(management_spec).casefold() == "unmanaged"
        and management_spec in official_published
        and interface_spec in official_published
    ):
        return False
    if product.brand.name == "TP-Link" and product.official_url:
        return False
    if len(official_published) >= 3:
        return False
    if any(
        (spec.source_note or "").startswith("Imported from Omada managed Switch")
        for spec in published
    ):
        return False
    return None


def supported_wireless_bands(product, product_specs=None):
    product_specs = product_specs or specs_by_code(product)
    value = _text_value(product_specs.get("supported_bands")).casefold()
    if value:
        return {
            band
            for band, markers in {
                "2.4": ("2.4", "2g"),
                "5": ("5 ghz", "5ghz", "5g"),
                "6": ("6 ghz", "6ghz", "6g"),
            }.items()
            if any(marker in value for marker in markers)
        }

    standard = (product.wifi_standard or "").casefold()
    if "wi-fi 7" in standard or "wifi 7" in standard or "802.11be" in standard:
        return {"2.4", "5", "6"}
    if "wi-fi 6e" in standard or "wifi 6e" in standard:
        return {"2.4", "5", "6"}
    if "wi-fi" in standard or "wifi" in standard or "802.11" in standard:
        return {"2.4", "5"}
    return set()


def switch_stacking_state(product, product_specs=None):
    """Return True/False/None when published evidence establishes stacking support."""
    if product.category.slug != "managed-switches":
        return None

    product_specs = product_specs or specs_by_code(product)
    stacking = product_specs.get("stacking")
    if not has_published_value(stacking):
        return None
    if stacking.value_boolean is not None:
        return stacking.value_boolean

    value = _text_value(stacking).strip().casefold()
    if value in {"no", "none", "not supported", "unsupported", "×", "✕"}:
        return False
    if value.startswith(("not supported;", "unsupported;")):
        return False
    if any(
        marker in value
        for marker in (
            "stacking not supported",
            "does not support stacking",
            "stacking is not supported",
            "without stacking",
        )
    ):
        return False
    return True


def field_is_applicable(product, code, product_specs=None):
    product_specs = product_specs or specs_by_code(product)
    management_type = _text_value(product_specs.get("management_type")).casefold()
    if (
        product.category.slug == "unmanaged-easy-smart-switches"
        and code in PLAIN_UNMANAGED_CONFIG_SPEC_CODES
        and management_type.startswith("unmanaged")
        and not has_published_value(product_specs.get(code))
    ):
        return False
    if (
        product.category.slug == "unmanaged-easy-smart-switches"
        and code == "management_methods"
    ):
        return False
    if (
        product.category.slug in SWITCH_CATEGORY_SLUGS
        and code in POE_OUTPUT_SPEC_CODES
    ):
        return switch_poe_state(product, product_specs) is True
    if (
        code in STACKING_DETAIL_SPEC_CODES
        and switch_stacking_state(product, product_specs) is False
    ):
        return False
    if product.category.slug == "gateway" and code in {
        "router_poe_ports",
        "router_poe_budget_w",
    }:
        text = " ".join(
            filter(
                None,
                (
                    product.model,
                    product.notes,
                    getattr(getattr(product, "product_model", None), "product_name", ""),
                ),
            )
        ).casefold()
        has_value = any(
            has_published_value(product_specs.get(item))
            for item in ("router_poe_ports", "router_poe_budget_w")
        )
        if not has_value and "poe" not in text and not product.model.upper().endswith("PC"):
            return False
    if (
        product.category.slug == "accessories"
        and code == "accessory_max_distance_km"
        and product.model.upper() in {"MC220L", "MC420L"}
    ):
        return False
    if product.category.slug == "accessories" and code == "accessory_wavelength_nm":
        medium = " ".join(
            (
                _text_value(product_specs.get("accessory_interface_type")),
                _text_value(product_specs.get("accessory_fiber_mode")),
            )
        ).casefold()
        if any(
            marker in medium
            for marker in ("copper", "base-t", "direct-attach", "direct attach", "twinax")
        ):
            return False
    if (
        product.category.slug == "accessories"
        and code == "dimensions_mm"
        and getattr(getattr(product, "product_type", None), "code", "") == "dac_cable"
    ):
        return False
    for band, codes in BAND_SPEC_CODES.items():
        if code not in codes:
            continue
        bands = supported_wireless_bands(product, product_specs)
        if bands and band not in bands:
            return False
    return True
