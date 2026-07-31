WIRELESS_CATEGORY_SLUGS = {"access-point", "wireless-bridge"}
WIRED_CATEGORY_SLUGS = {
    "accessories",
    "gateway",
    "managed-switches",
    "unmanaged-easy-smart-switches",
}

OFFICIAL_LATEST_HARDWARE = {
    ("tp-link", "EAP723", "US"): (
        "V2.20",
        "https://www.tp-link.com/us/business-networking/omada-wifi-ceiling-mount/eap723/%28us%29%20v2.20/",
    ),
    ("tp-link", "EAP725OUTDOOR", "US"): (
        "V1",
        "https://www.omadanetworks.com/us/business-networking/omada-wifi-outdoor/eap725-outdoor/%28us%29%20v1/",
    ),
    ("tp-link", "EAP725WALL", "US"): (
        "V1.20",
        "https://www.omadanetworks.com/us/business-networking/omada-wifi-wall-plate/eap725-wall/%28us%29%20v1.20/",
    ),
    ("tp-link", "EAP772", "US"): (
        "V2.20",
        "https://www.omadanetworks.com/us/business-networking/omada-wifi-ceiling-mount/eap772/%28us%29%20v2.20/",
    ),
    ("tp-link", "EAP772OUTDOOR", "US"): (
        "V1.20",
        "https://www.tp-link.com/us/business-networking/omada-wifi-outdoor/eap772-outdoor/v1.20/",
    ),
    ("tp-link", "EAP773", "US"): (
        "V2",
        "https://www.omadanetworks.com/us/business-networking/omada-wifi-ceiling-mount/eap773/",
    ),
    ("tp-link", "EAP775WALL", "US"): (
        "V1",
        "https://www.omadanetworks.com/us/business-networking/omada-wifi-wall-plate/eap775-wall/%28us%29%20v1/",
    ),
}


def canonical_product_region(category_slug):
    if category_slug in WIRELESS_CATEGORY_SLUGS:
        return "US"
    if category_slug in WIRED_CATEGORY_SLUGS:
        return "UN"
    return None
