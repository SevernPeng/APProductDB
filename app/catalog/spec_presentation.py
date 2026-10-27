"""Shared specification grouping rules for detail and comparison pages."""

WORKBOOK_GROUP_ORDER = {
    "access-point": (
        "HARDWARE FEATURES", "PoE FEATURES", "WIRELESS FEATURES",
        "Management Features", "Environment",
    ),
    "wireless-bridge": (
        "HARDWARE FEATURES", "WIRELESS FEATURES", "Management Features",
        "Environment",
    ),
    "gateway": (
        "HARDWARE FEATURES", "PoE FEATURES", "5G/4G/3G", "SECURITY",
        "VPN & SD-WAN", "PERFORMANCE", "Management Features",
        "WIRELESS FEATURES", "NETWORK SERVICES", "Environment",
    ),
    "managed-switches": (
        "HARDWARE FEATURES", "PoE FEATURES", "PERFORMANCE", "STACKING",
        "SOFTWARE FEATURES", "Management Features", "OTHERS", "Environment",
    ),
    "unmanaged-easy-smart-switches": (
        "HARDWARE FEATURES", "PERFORMANCE", "PoE FEATURES",
        "SOFTWARE FEATURES", "OTHERS", "Environment",
    ),
}


def workbook_spec_group(category_slug, definition_group):
    """Translate internal groups to the uploaded-workbook presentation layout."""
    group = definition_group or "Other Specifications"
    if category_slug in {"access-point", "wireless-bridge"}:
        if group in {"Interfaces", "Power", "Physical"}:
            return "HARDWARE FEATURES"
        if group in {"Wireless", "Performance", "Capacity", "Coverage", "Security"}:
            return "WIRELESS FEATURES"
        if group == "Management":
            return "Management Features"
        if group == "Environment":
            return "Environment"
    elif category_slug == "gateway":
        return {
            "Interfaces": "HARDWARE FEATURES",
            "Power": "HARDWARE FEATURES",
            "Physical": "HARDWARE FEATURES",
            "PoE": "PoE FEATURES",
            "Cellular": "5G/4G/3G",
            "Security": "SECURITY",
            "Routing": "NETWORK SERVICES",
            "Performance": "PERFORMANCE",
            "Capacity": "PERFORMANCE",
            "Management": "Management Features",
            "Wireless": "WIRELESS FEATURES",
            "Environment": "Environment",
        }.get(group, group)
    elif category_slug == "managed-switches":
        if group in {"Interfaces", "Power", "Physical", "Hardware"}:
            return "HARDWARE FEATURES"
        if group == "PoE":
            return "PoE FEATURES"
        if group in {"Performance", "Capacity"}:
            return "PERFORMANCE"
        if group == "Stacking":
            return "STACKING"
        if group == "Management":
            return "Management Features"
        if group == "Environment":
            return "Environment"
        return "SOFTWARE FEATURES"
    elif category_slug == "unmanaged-easy-smart-switches":
        if group in {"Interfaces", "Power", "Physical"}:
            return "HARDWARE FEATURES"
        if group in {"Performance", "Capacity"}:
            return "PERFORMANCE"
        if group in {"PoE", "PoE Features"}:
            return "PoE FEATURES"
        if group == "Environment":
            return "Environment"
        return "SOFTWARE FEATURES"
    return group


def ordered_spec_groups(grouped_rows, category_slug):
    """Return grouped rows in the same order used by the product detail page."""
    groups = [{"name": name, "rows": rows} for name, rows in grouped_rows.items()]
    group_order = {
        name: index
        for index, name in enumerate(WORKBOOK_GROUP_ORDER.get(category_slug, ()), start=1)
    }
    groups.sort(key=lambda group: group_order.get(group["name"], len(group_order) + 1))
    return groups
