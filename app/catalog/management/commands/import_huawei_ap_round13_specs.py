from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    u,
)


URL = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/40764568d113493d899de3de77301291/M3T1A590N1186032560931410210/Huawei%20AirEngine%208776-X7T-T%20_%20AirEngine%208776-X7ET-T%20Access%20Points%20Datasheet.pdf"


PRODUCTS = {
    "AirEngine 8776-X7T-T": {
        "url": URL,
        "page": "Current official datasheet, pp. 2 and 10-13",
        "title": "Huawei AirEngine 8776-X7T-T and 8776-X7ET-T official product specifications",
        "values": {
            "rate_2g_mbps": n(1376),
            "rate_5g_mbps": n(5765),
            "rate_6g_mbps": n(11530),
        },
    },
    "AirEngine 8776-X7ET-T": {
        "url": URL,
        "page": "Current official datasheet, pp. 2 and 10-13",
        "title": "Huawei AirEngine 8776-X7T-T and 8776-X7ET-T official product specifications",
        "values": {
            "rate_2g_mbps": n(1376),
            "rate_5g_mbps": n(5765),
            "rate_6g_mbps": n(11530),
            "antenna_gain_dbi": u("Removed malformed scraped fragment; gain depends on the selected external antenna"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei AirEngine 8776-X7T-T and 8776-X7ET-T per-band rates."
    products = PRODUCTS
    document_version = "Current official Huawei product page and datasheet; accessed 2026-10-19"
    brand_name = "Huawei"
