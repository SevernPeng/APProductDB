from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


URL = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/919e8a744231488d82096bc412b62747/M2T1A669N855480289384796450/At-A-Glance%20of%20CloudCampus%20Solution%20and%20Product%20for%20Fast%20Track.pdf"

PRODUCTS = {
    "AirEngine 5762-11W": {
        "url": URL,
        "page": "Page 6, Fast Track 3.0 Healthcare recommended products",
        "title": "Huawei At-A-Glance of CloudCampus Solution and Product for Fast Track",
        "values": {
            "ethernet_interfaces": t(
                "1 x GE uplink; 4 x GE downlink; 2 x RJ45 passthrough",
                "1*GE + 4*GE + 2*RJ45",
            ),
            "total_spatial_streams": n(4, "NSS: 2 (2.4 GHz) + 2 (5 GHz)"),
            "mimo_2g": t("2 spatial streams", "NSS: 2 (2.4 GHz)"),
            "mimo_5g": t("2 spatial streams", "NSS: 2 (5 GHz)"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import official Huawei AirEngine 5762-11W radio-stream and interface specifications."
    products = PRODUCTS
    document_version = "Official Huawei CloudCampus Fast Track portfolio; accessed 2026-10-23"
    brand_name = "Huawei"
