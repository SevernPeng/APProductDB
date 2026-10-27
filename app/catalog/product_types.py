import re

PRODUCT_TYPE_DEFINITIONS = {
    "access-point": (
        ("ceiling", "Ceiling Mount", "Ceiling-mounted indoor access point."),
        ("wall", "Wall Mount", "Wall-mounted access point."),
        ("wall_plate", "Wall Plate", "In-wall or wall-plate access point."),
        ("outdoor", "Outdoor", "Weather-resistant outdoor access point."),
        ("desktop", "Desktop", "Desktop access point."),
        ("extender", "Extender", "Wireless range extender."),
        ("other", "Other AP", "Other access-point form factor."),
    ),
    "managed-switches": (
        ("campus_poe", "Campus PoE", "Campus-class managed switch with PoE output."),
        ("campus_non_poe", "Campus Non-PoE", "Campus-class managed switch without PoE output."),
        ("l2_poe", "Layer 2 PoE", "Layer 2 or Layer 2+ managed switch with PoE output."),
        ("l2_non_poe", "Layer 2 Non-PoE", "Layer 2 or Layer 2+ managed switch without PoE output."),
        ("l3_poe", "Layer 3 PoE", "Layer 3 managed switch with PoE output."),
        ("l3_non_poe", "Layer 3 Non-PoE", "Layer 3 managed switch without PoE output."),
        ("agile_poe", "Agile PoE", "Omada Agile easy-managed switch with PoE output."),
        ("agile_non_poe", "Agile Non-PoE", "Omada Agile easy-managed switch without PoE output."),
        ("industrial_poe", "Industrial PoE", "Industrial managed switch with PoE output."),
        ("industrial_non_poe", "Industrial Non-PoE", "Industrial managed switch without PoE output."),
        ("unknown", "Unknown Layer", "Management layer requires confirmation."),
    ),
    "unmanaged-easy-smart-switches": (
        ("unmanaged_poe", "Unmanaged PoE", "Plug-and-play unmanaged switch with PoE output."),
        ("unmanaged_non_poe", "Unmanaged Non-PoE", "Plug-and-play unmanaged switch without PoE output."),
        ("easy_smart_poe", "Easy Smart PoE", "Web-managed Easy Smart switch with PoE output."),
        ("easy_smart_non_poe", "Easy Smart Non-PoE", "Web-managed Easy Smart switch without PoE output."),
        ("unknown", "Unknown Management Type", "Management type requires confirmation."),
    ),
    "gateway": (
        ("wired_router", "Wired Router", "Wired VPN or security router."),
        ("wireless_router", "Wireless Router", "Router with integrated Wi-Fi."),
        ("cellular_router", "Cellular Router", "Indoor 4G or 5G cellular router."),
        (
            "outdoor_cellular_router",
            "Outdoor Cellular Router",
            "Outdoor 4G or 5G cellular router.",
        ),
        (
            "integrated_gateway",
            "Integrated Gateway",
            "Gateway integrating controller, switch, PoE, or other platform functions.",
        ),
        ("other", "Other Router", "Other routing product form."),
    ),
    "accessories": (
        ("poe_injector", "PoE Injector", "PoE injector or PoE adapter."),
        ("power_supply", "Power Supply", "Power supply or replaceable power module."),
        ("media_converter", "Media Converter", "Copper/fiber media converter."),
        ("optical_module", "Optical Module", "SFP, SFP+, SFP28, QSFP, or BiDi module."),
        ("dac_cable", "DAC Cable", "Direct-attach copper cable."),
        ("mounting", "Mounting Accessory", "Rack, wall, or magnetic mounting accessory."),
        ("chassis", "Chassis", "Media-converter or accessory chassis."),
        ("antenna", "Antenna", "External antenna or antenna accessory."),
        ("junction_box", "Junction Box", "Outdoor junction or cable-management box."),
        ("other", "Other Accessory", "Other network accessory."),
    ),
}


def infer_switch_management_type(management_type, has_management_features=False):
    normalized = re.sub(r"\s+", " ", (management_type or "").strip()).casefold()
    if has_management_features:
        return "easy_smart"
    if not normalized or normalized in {"unknown", "n/a", "not published"}:
        return ""
    if "unmanaged" in normalized or "un-managed" in normalized:
        return "unmanaged"
    if any(marker in normalized for marker in ("easy smart", "web smart", "smart managed")):
        return "easy_smart"
    return ""


def infer_managed_switch_family(brand_name, model, product_name="", feature_text=""):
    """Infer a managed-switch template family from durable product-line signals.

    This deliberately returns an empty string when the line cannot be identified.
    The caller can then keep the product in the unknown bucket instead of forcing
    an inapplicable Layer 3 template.
    """
    brand = (brand_name or "").strip().casefold()
    upper = (model or "").strip().upper()
    combined = " ".join((model or "", product_name or "", feature_text or "")).casefold()

    if (
        upper.startswith(("DIS-", "TI-", "RG-NIS", "RGS", "DS-3T", "IS4", "PFS"))
        or upper.startswith("DAHUA PFS")
        or "industrial" in combined
    ):
        return "industrial"

    campus_patterns = {
        "aruba": r"^(?:6[23]00|CX\s*8)",
        "cisco": r"^C(?:9[235]|ATALYST)",
        "h3c": r"^S5",
        "huawei": r"^(?:S57|CE)",
        "ruckus": r"^ICX",
        "reyee": r"^RG-(?:S|CS)",
        "ruijie": r"^RG-(?:S|CS)",
    }
    # ICX 8100 is an advanced Layer-2 access family.  The current official
    # data sheet explicitly says Layer-3 routing is not supported, so it must
    # not inherit the broader campus/L3 template used by other ICX families.
    if brand == "ruckus" and re.search(r"^ICX\s*8100", upper):
        return "l2"
    if brand in campus_patterns and re.search(campus_patterns[brand], upper):
        return "campus"

    l3_markers = (
        "ospf",
        "border gateway protocol",
        " bgp",
        "is-is",
        "isis",
        "policy-based routing",
        " pbr",
        "vrrp",
        "routing entries",
        "routing table",
    )
    if any(marker in f" {combined}" for marker in l3_markers):
        return "l3"

    l3_patterns = {
        "aruba": r"^(?:2540|6[23]00|CX)",
        "cisco": r"^(?:C1300|C9|CBS350)",
        "d-link": r"^(?:D[GMQX]S-(?:3|5)|DGS-(?:1510|3)|DXS-(?:3400|3610))",
        "grandstream": r"^GWN78",
        "h3c": r"^S55",
        "huawei": r"^(?:CE|S31|S57)",
        "meraki": r"^MS(?:250|3|4)",
        "netgear": r"^M(?:4[235]|5)",
        "reyee": r"^(?:RG-(?:S|CS)|RG[ -]NBS5|RGNBS5)",
        "ruijie": r"^RG-(?:S|CS)",
        "ubiquiti": r"^(?:ECS-|USW-(?:PRO|ENTERPRISE))",
    }
    if brand in l3_patterns and re.search(l3_patterns[brand], upper):
        return "l3"

    l2_patterns = {
        "aruba": r"^(?:19[26]0|2530)",
        "cisco": r"^CBS250",
        "d-link": r"^(?:DBS-|DES-|DGS-(?:1100|1210|1250)|DMS-(?:1100|1250)|DSS-|DXS-(?:1100|1210))",
        "hpe": r"^19[26]0",
        "hikvision": r"^DS-3E",
        "instant on": r"^(?:18|19|JL)",
        "meraki": r"^MS(?:120|125|2[02]5)",
        "mikrotik": r"^(?:CRS|RB260)",
        "netgear": r"^(?:FS|GC|GS|MS|XS|M4100)",
        "reyee": r"^(?:RG-ES|RG[ -]NBS[123]|RGNBS[123])",
        "trendnet": r"^(?:TEG-|TPE-)",
        "ubiquiti": r"^(?:US-|USW-)",
        "zyxel": r"^(?:GS|XMG)",
    }
    if brand in l2_patterns and re.search(l2_patterns[brand], upper):
        return "l2"
    if brand == "other" and (upper.startswith("HPE 19") or "HPE 19" in combined.upper()):
        return "l2"
    return ""


def infer_managed_switch_poe(brand_name, model, product_name=""):
    """Return a model-line PoE-output signal, or None when naming is ambiguous."""
    brand = (brand_name or "").strip().casefold()
    upper = (model or "").strip().upper()
    combined = f"{model or ''} {product_name or ''}".upper()

    if brand == "instant on":
        poe_skus = {
            "JL681A", "JL684B", "JL686B", "JL807A", "JL809A",
            "JL811A", "JL813A", "JL815A",
        }
        non_poe_skus = {
            "JL680A", "JL682A", "JL685A", "JL806A", "JL808A",
            "JL810A", "JL812A", "JL814A",
        }
        if upper in poe_skus:
            return True
        if upper in non_poe_skus:
            return False
    if brand in {"aruba", "hpe"}:
        if "POE" in combined or "PPOE" in combined or re.search(r"\bJL(?:681|684|686|725|727|728|807|809|811|813|815)A?B?\b", upper):
            return True
        if re.search(r"\bJL(?:658|680|682|685|724|726|806|808|810|812|814)A?B?\b", upper):
            return False
        if re.search(r"\b(?:16G|24G|48G|8G)\s+(?:\d+SFP\+?\s+)?SWITCH\b", upper):
            return False
    if brand == "cisco":
        if re.search(r"-\d*(?:FP|LP|P)-", upper):
            return True
        if re.search(r"-\d*T-", upper):
            return False
    if brand == "d-link":
        if re.search(r"-(?:\d+)?(?:X?MP|PS|PC|TP|SP|P)(?:/|$)", upper):
            return True
        if re.search(r"-(?:\d+)?(?:TS|TC|T|XS|SC|S|X|W)(?:/|$)", upper) or upper.startswith("DQS-"):
            return False
        if upper.startswith(("DBS-", "DES-", "DGS-", "DMS-", "DSS-", "DXS-", "DIS-")):
            return False
    if brand in {"reyee", "ruijie"}:
        if re.search(r"(?:-P|-LP|-HP|-UP|XSP)(?:-|/|$)", upper):
            return True
        return False
    if brand == "ruckus":
        if re.search(r"(?:XZP|ZP|PF|P)\d*(?:-|$)", upper):
            return True
        return False
    if brand == "netgear":
        if "POE" in upper or re.search(r"(?:TP|XP|EP|EPP|EUP)$", upper, re.I):
            return True
        return False
    if brand == "meraki":
        return bool(re.search(r"(?:P|FP|LP)-HW$", upper))
    if brand == "ubiquiti":
        if "POE" in upper or re.search(r"-(?:60|150|500)W$", upper) or upper == "USW-FLEX":
            return True
        return False
    if brand == "h3c":
        return bool(re.search(r"(?:HPWR|PWR)", upper))
    if brand == "huawei":
        return bool(re.search(r"^S\d+[^-]*-[A-Z]*\d+(?:L?P|PN|UN)", upper))
    if brand == "mikrotik":
        return upper.startswith("RB260GSP")
    if brand == "zyxel":
        return bool(re.search(r"(?:HP|P)$", upper))
    if brand == "trendnet":
        return upper.startswith(("TPE-", "TI-P"))
    if brand == "hikvision":
        return bool(re.search(r"(?:HP|P)(?:-|/|$)", upper))
    if brand == "dahua":
        return bool(re.search(r"(?:-DP|-\d+GT-\d+)", upper))
    if "POE" in combined:
        return True
    return None


def infer_product_type_code(
    category_slug,
    model,
    ap_type="",
    management_type="",
    has_management_features=False,
    has_poe=None,
    switch_family="",
    product_name="",
    brand_name="",
    feature_text="",
):
    normalized = (model or "").strip()
    upper = normalized.upper()

    if category_slug == "access-point":
        if "EXTENDER" in upper:
            return "extender"
        if ap_type in {
            "ceiling",
            "wall",
            "wall_plate",
            "outdoor",
            "desktop",
            "other",
        }:
            return ap_type
        if "OUTDOOR" in upper:
            return "outdoor"
        if "WALL" in upper or upper.endswith("-IW"):
            return "wall_plate"
        if "DESKTOP" in upper:
            return "desktop"
        return "ceiling"

    if category_slug == "managed-switches":
        family = (switch_family or "").strip().casefold() or infer_managed_switch_family(
            brand_name,
            normalized,
            product_name,
            feature_text,
        )
        combined = f"{normalized} {product_name}".casefold()
        if has_poe is None:
            has_poe = bool(
                re.search(r"\bpoe(?:\+\+|\+)?\b", combined)
                or re.search(r"(?:MPP|HPP|XPP|GMP|GP|MP|HP|LP|PP|PE|P)(?:-M\d+)?$", upper)
                or re.search(r"(?:MPP|GP)\d", upper)
            )
        suffix = "poe" if has_poe else "non_poe"
        if family in {"campus", "l2", "l3", "agile", "industrial"}:
            return f"{family}_{suffix}"
        if upper.startswith("IES"):
            return f"industrial_{suffix}"
        if upper.startswith("ES"):
            return f"agile_{suffix}"
        if re.match(r"^S[67]500", upper):
            return f"campus_{suffix}"
        if re.match(r"^(S7|S6|SX6|SG6|SG5)", upper) or re.search(
            r"(?:\blite\s+)?\bl3\b|layer\s*3", combined
        ):
            return f"l3_{suffix}"
        if re.match(r"^(SG[23]|SX3)", upper):
            return f"l2_{suffix}"
        return "unknown"

    if category_slug == "unmanaged-easy-smart-switches":
        explicit_type = infer_switch_management_type(
            management_type,
            has_management_features,
        )
        if has_poe is None:
            has_poe = bool(
                re.search(r"\bpoe(?:\+\+|\+)?\b", product_name or "", re.I)
                or re.search(r"(?:MPE|PE|LP|MP|PP|GP|P)(?:-M\d+)?$", upper)
            )
        suffix = "poe" if has_poe else "non_poe"
        if explicit_type:
            return f"{explicit_type}_{suffix}"
        if re.search(r"(?:E|DE|PE|MPE|GE)$", upper):
            return f"easy_smart_{suffix}"
        if upper.startswith(("DS", "LS", "TL-SF", "TL-SG", "TL-SX")):
            return f"unmanaged_{suffix}"
        return "unknown"

    if category_slug == "gateway":
        if "FUSION" in upper or upper.endswith("PC"):
            return "integrated_gateway"
        if ("4G" in upper or "5G" in upper or "LTE" in upper) and "OUTDOOR" in upper:
            return "outdoor_cellular_router"
        if "4G" in upper or "5G" in upper or "LTE" in upper:
            return "cellular_router"
        if re.search(r"(?:^|[- ])W(?:$|[- ])", upper) or re.match(r"^ER\d+W", upper):
            return "wireless_router"
        if upper.startswith(("ER", "UXG", "CCR", "RB", "VIGOR")):
            return "wired_router"
        return "other"

    if category_slug == "accessories":
        if re.search(r"(?:^|[-_])(?:POE|INJ)(?:[-_]|$)", upper) or upper.startswith(
            ("TPE-", "MA-INJ", "RG-POE", "UACC-POE", "902-1162", "902-1180", "DPE-301GI")
        ):
            return "poe_injector"
        if upper.startswith("PSM") or re.search(r"(?:^|[-_])PWR(?:[-_]|$)", upper) or re.match(r"^APS\d+W", upper):
            return "power_supply"
        if upper == "MC1400":
            return "chassis"
        if upper.startswith(("MC", "DMC", "TFC")):
            return "media_converter"
        if (
            "DAC" in upper
            or re.search(r"(?:CU|CB|TWX)[-_]?\d+M?$", upper)
            or re.match(r"^AXC\d+", upper)
            or re.match(r"^(?:I?SM)\d+.*-\d+M$", upper)
        ):
            return "dac_cable"
        if (
            upper.startswith(("SM", "ISM", "SFP", "QSFP", "GLC", "DEM", "AGM", "AXM", "E1MG-"))
            or "SFP" in upper
            or "QSFP" in upper
            or "GBIC" in upper
            or upper.startswith("UACC-OM-")
            or upper in {"J4858D", "J9151E", "JL486A", "DGS-712", "TEG-10GBRJ100"}
        ):
            return "optical_module"
        if upper == "J9281D":
            return "dac_cable"
        if "MOUNT" in upper or "RACK" in upper:
            return "mounting"
        if upper.startswith("APM"):
            return "mounting"
        if upper.startswith("OJB"):
            return "junction_box"
        return "other"

    return "other"


def product_type_code(product):
    if getattr(product, "product_type_id", None):
        return product.product_type.code
    if product.category.slug == "access-point":
        return product.ap_type
    return ""
