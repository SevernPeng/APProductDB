from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    t,
    u,
)


URL_R6P67A = (
    "https://www.hpe.com/jp/ja/product-catalog/options/"
    "pip.specifications.power-management-options.1012978012.html"
)
URL_INSTANT_ON_WIFI6 = (
    "https://www.hpe.com/us/en/collaterals/collateral.a00062175enw.html"
)
URL_R9M77A = (
    "https://www.hpe.com/psnow/generateDDS/"
    "HPE%20Networking%20Instant%20On%2030W%20802.3at%20PoE%20Midspan%20Injector%20"
    "Digital%20Data%20Sheet-PSN1014652680GREN.pdf?cc=GR&deepLink=&lc=EN&"
    "oid=1014652680&prelaunch=false&prelaunchSection=&print=&section=&softroll=0&"
    "softrollSection="
)


PRODUCTS = {
    "R6P67A": {
        "url": URL_R6P67A,
        "page": "Technical specifications; current HPE product page",
        "title": "HPE Aruba Networking AP-POE-ATSR product specifications",
        "values": {
            "dimensions_mm": t("30 x 66 x 163 mm", "Product dimensions (metric): 3 x 6.6 x 16.3 cm"),
            "accessory_interface_type": t("1-port Smart Rate 802.3at PoE midspan injector (30 W)"),
            "accessory_connector_type": t("RJ45 Ethernet data input and RJ45 PoE output"),
            "accessory_compatibility": t("Selected HPE Aruba Networking products supporting this 802.3at Smart Rate midspan injector"),
            "accessory_input_power": u("Electrical input rating is not published on the verified HPE product page"),
        },
    },
    "R8W31A": {
        "url": URL_INSTANT_ON_WIFI6,
        "page": "Power Options tables for Instant On Wi-Fi 6 access points",
        "title": "HPE Networking Instant On Wi-Fi 6 Access Points QuickSpecs",
        "values": {
            "accessory_interface_type": t("1-port 802.3af PoE midspan injector (15.4 W)"),
            "accessory_connector_type": t("RJ45 Ethernet data input and RJ45 PoE output"),
            "accessory_compatibility": t("HPE Networking Instant On AP22 and AP25; also listed as an optional injector for other Instant On access points in HPE QuickSpecs"),
            "accessory_input_power": u("QuickSpecs require a localized AC power cord but do not publish an electrical input rating"),
        },
    },
    "R9M77A": {
        "url": URL_R9M77A,
        "page": "Technical specifications, page 2",
        "title": "HPE Networking Instant On 30W 802.3at PoE Midspan Injector Data Sheet",
        "values": {
            "dimensions_mm": t("61 x 89 x 51 mm", "Product dimensions (metric): 6.1 x 8.9 x 5.1 cm"),
            "accessory_interface_type": t("1-port 802.3at PoE midspan injector (30 W)"),
            "accessory_connector_type": t("RJ45 Ethernet data input and RJ45 PoE output"),
            "accessory_input_power": u("Electrical input rating is not published in the verified HPE data sheet"),
        },
    },
}


class Command(ArubaImportCommand):
    help = "Import manually verified Aruba/HPE PoE injector gap specifications."
    products = PRODUCTS
    document_version = "Official HPE product pages, data sheet, and QuickSpecs; accessed 2026-10-22"
