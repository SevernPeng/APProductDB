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
        ("l2", "Layer 2", "Layer 2 managed switch."),
        ("l2_plus", "Layer 2+", "Layer 2+ managed switch with static routing features."),
        ("l3", "Layer 3", "Layer 3 managed switch."),
        ("unknown", "Unknown Layer", "Management layer requires confirmation."),
    ),
    "unmanaged-easy-smart-switches": (
        ("unmanaged", "Unmanaged", "Plug-and-play unmanaged switch."),
        ("easy_smart", "Easy Smart", "Web-managed Easy Smart switch."),
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


def infer_product_type_code(category_slug, model, ap_type=""):
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
        if re.match(r"^(S7|S6|SX6|SG6|SG5)", upper):
            return "l3"
        if re.match(r"^(SG3|SX3)", upper):
            return "l2_plus"
        if re.match(r"^(SG2|ES)", upper):
            return "l2"
        return "unknown"

    if category_slug == "unmanaged-easy-smart-switches":
        if re.search(r"(?:E|DE|PE|MPE|GE)$", upper):
            return "easy_smart"
        if upper.startswith(("DS", "LS", "TL-SF", "TL-SG")):
            return "unmanaged"
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
        if upper.startswith("POE"):
            return "poe_injector"
        if upper.startswith("PSM"):
            return "power_supply"
        if upper == "MC1400":
            return "chassis"
        if upper.startswith("MC"):
            return "media_converter"
        if re.match(r"^(?:I?SM)\d+.*-\d+M$", upper):
            return "dac_cable"
        if upper.startswith(("SM", "ISM")):
            return "optical_module"
        if "MOUNT" in upper or "RACK" in upper:
            return "mounting"
        if upper.startswith("APM"):
            return "antenna"
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
